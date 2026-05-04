/**
 * KTW SaaS — Fincept Terminal 容器池管理器
 *
 * 職責：
 * 1. 維護一組預熱的 Terminal 容器（warm pool）
 * 2. 分配容器給租戶（attach）— 注入環境變數 + 掛載資料卷
 * 3. 回收閒置容器（detach）— 儲存租戶資料後歸池
 * 4. 健康檢查 + 自動替換異常容器
 *
 * API 端點（供 SaaS Platform 呼叫）：
 *   POST   /api/pool/allocate   — 分配容器給租戶
 *   POST   /api/pool/release    — 釋放租戶容器（歸池）
 *   GET    /api/pool/status     — 容器池狀態
 *   GET    /api/pool/tenant/:id — 查詢租戶的容器
 *   GET    /health              — 管理器健康檢查
 */

import { createServer } from 'node:http'
import Docker from 'dockerode'

// ── 設定 ────────────────────────────────────────────────────────────────────
const PORT = parseInt(process.env.POOL_MANAGER_PORT || '9090')
const SAAS_URL = process.env.KTW_SAAS_URL || 'https://ktwsmart.com'
const POOL_SIZE = parseInt(process.env.POOL_SIZE || '3')        // 預熱容器數
const MAX_SIZE = parseInt(process.env.POOL_MAX_SIZE || '10')    // 最大容器數
const IDLE_TIMEOUT = parseInt(process.env.POOL_IDLE_TIMEOUT || '300') // 閒置逾時（秒）
const IMAGE_NAME = 'ktw/fincept-terminal:zh-latest'

// Token Refresh 設定
const FINCEPT_POOL_SECRET = process.env.FINCEPT_POOL_SECRET || ''
const TOKEN_REFRESH_INTERVAL = parseInt(process.env.TOKEN_REFRESH_INTERVAL || '1800000') // 30 分鐘

const docker = new Docker({ socketPath: process.env.DOCKER_SOCKET || '/var/run/docker.sock' })

// ── 容器池狀態 ──────────────────────────────────────────────────────────────

/** @type {Map<string, PoolEntry>} containerId -> 狀態 */
const pool = new Map()

// 健康檢查設定
const HEALTH_CHECK_TIMEOUT = parseInt(process.env.HEALTH_CHECK_TIMEOUT || '5000')  // HTTP 探測逾時（毫秒）
const HEALTH_FAIL_THRESHOLD = parseInt(process.env.HEALTH_FAIL_THRESHOLD || '3')   // 連續失敗幾次清理

/**
 * @typedef {Object} PoolEntry
 * @property {string} containerId    - Docker 容器 ID
 * @property {'idle'|'assigned'|'starting'|'stopping'} status
 * @property {string|null} tenantId  - 分配給的租戶
 * @property {string|null} noVncUrl  - noVNC 存取 URL
 * @property {number} port           - noVNC 外部端口
 * @property {number} assignedAt     - 分配時間戳
 * @property {number} lastActivity   - 最後活動時間
 * @property {number} healthFailures - 連續健康檢查失敗次數
 */

let nextPort = 6081 // noVNC 端口分配起始值

// ── 啟動時掃描既有容器 ─────────────────────────────────────────────────────

/**
 * 掃描 Docker 中帶有 ktw.pool=terminal label 的已存在容器
 * 將正在運行的容器納入記憶體池，避免重啟後容器脫鉤導致名稱衝突（409）
 */
async function scanExistingContainers() {
  try {
    const containers = await docker.listContainers({
      all: true, // 包含已停止的
      filters: { label: ['ktw.pool=terminal'] },
    })

    let adopted = 0
    let cleaned = 0

    for (const info of containers) {
      const shortId = info.Id.substring(0, 12)
      const name = (info.Names?.[0] || '').replace(/^\//, '')
      const isRunning = info.State === 'running'
      const tenantLabel = info.Labels?.['ktw.tenant'] || ''

      // 從端口綁定中取得 noVNC 端口（6080 對應的 HostPort）
      let hostPort = 0
      const portBindings = info.Ports || []
      for (const p of portBindings) {
        if (p.PrivatePort === 6080 && p.PublicPort) {
          hostPort = p.PublicPort
          break
        }
      }

      if (!isRunning) {
        // 已停止的容器 → 移除，避免名稱佔用
        try {
          const container = docker.getContainer(info.Id)
          await container.remove({ force: true })
          cleaned++
          console.log(`[掃描] 🧹 已移除停止的容器: ${name || shortId}`)
        } catch (err) {
          console.error(`[掃描] 移除失敗: ${name || shortId}`, err.message)
        }
        continue
      }

      if (!hostPort) {
        console.log(`[掃描] ⚠️ 容器 ${name || shortId} 無 noVNC 端口綁定，跳過`)
        continue
      }

      // 納入記憶體池
      const entry = {
        containerId: shortId,
        status: tenantLabel ? 'assigned' : 'idle',
        tenantId: tenantLabel || null,
        noVncUrl: tenantLabel ? `http://localhost:${hostPort}/vnc.html` : null,
        port: hostPort,
        assignedAt: tenantLabel ? now() : 0,
        lastActivity: now(),
        healthFailures: 0,
      }
      pool.set(shortId, entry)
      adopted++

      // 同步 nextPort：確保不會分配到已佔用的端口
      if (hostPort >= nextPort) {
        nextPort = hostPort + 1
        if (nextPort > 6200) nextPort = 6081
      }

      console.log(`[掃描] ✅ 納管容器: ${name || shortId} (port=${hostPort}${tenantLabel ? `, tenant=${tenantLabel}` : ''})`)
    }

    console.log(`[掃描] 完成 — 納管 ${adopted} 個運行中容器，清理 ${cleaned} 個已停止容器`)
  } catch (err) {
    console.error('[掃描] ❌ 掃描失敗:', err.message)
  }
}

// ── 工具函式 ────────────────────────────────────────────────────────────────

function now() { return Date.now() }

function json(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json' })
  res.end(JSON.stringify(data))
}

async function readBody(req) {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  return JSON.parse(Buffer.concat(chunks).toString())
}

/**
 * noVNC HTTP 健康探測 — 檢查容器的 noVNC port 是否回應
 * @param {number} port - noVNC 外部端口
 * @returns {boolean} true = 健康
 */
async function checkNoVncHealth(port) {
  try {
    const res = await fetch(`http://localhost:${port}/vnc_lite.html`, {
      signal: AbortSignal.timeout(HEALTH_CHECK_TIMEOUT),
    })
    return res.ok
  } catch {
    return false
  }
}

/**
 * 清理幽靈容器 — 停止 + 移除 Docker 容器，從 pool 中刪除
 * Volume 保留（租戶資料不丟失）
 * @param {string} id - pool 中的容器 ID
 * @param {PoolEntry} entry - 容器池項目
 * @param {string} reason - 清理原因（記錄用）
 */
async function cleanupGhostContainer(id, entry, reason) {
  console.log(`[健康檢查] 🧹 清理幽靈容器 ${id} (tenant=${entry.tenantId}, port=${entry.port}): ${reason}`)
  try {
    const container = docker.getContainer(entry.containerId)
    await container.stop({ t: 5 }).catch(() => {}) // 可能已停止
    await container.remove({ force: true })
  } catch (err) {
    console.error(`[健康檢查] 移除容器 ${id} 失敗:`, err.message)
  }
  pool.delete(id)
}

// ── 容器管理 ────────────────────────────────────────────────────────────────

/**
 * 建立一個新的 Terminal 容器
 * @param {string|null} tenantId - 指定租戶時掛載對應的具名 Volume
 * @param {Object} options - 環境變數選項
 */
async function createTerminalContainer(tenantId = null, options = {}) {
  const port = nextPort++
  if (nextPort > 6200) nextPort = 6081 // 端口循環使用

  // 環境變數（容器啟動時 entrypoint.sh 會讀取這些值）
  const env = [
    `KTW_SAAS_URL=${SAAS_URL}`,
    'KTW_HEALTH_PORT=8888',
    'FINCEPT_LANG=zh_TW',
    'LANG=zh_TW.UTF-8',
    'TZ=Asia/Taipei',
    'RESOLUTION=1920x1080x24',
    `KTW_TENANT_ID=${tenantId || ''}`,
    `KTW_JWT_TOKEN=${options.jwtToken || ''}`,
    `KTW_LLM_TIER=${options.llmTier || 'L1'}`,
    `KTW_INTELLIGENCE_ENABLED=${options.intelligenceEnabled !== false}`,
    `KTW_TRADING_ENABLED=${options.tradingEnabled === true}`,
  ]

  // Volume 掛載：租戶資料隔離
  const binds = []
  if (tenantId) {
    // 使用 Docker 具名 Volume（fincept-tenant-{id}-data）
    // entrypoint.sh 會將 /data/tenant 內的子目錄 symlink 到 Fincept 工作目錄
    binds.push(`fincept-tenant-${tenantId}-data:/data/tenant`)
  }

  // 建立容器（含 409 名稱衝突自動清理重試）
  const containerName = tenantId ? `fincept-${tenantId}` : undefined

  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const container = await docker.createContainer({
        Image: IMAGE_NAME,
        name: containerName,
        Env: env,
        ExposedPorts: { '6080/tcp': {}, '8888/tcp': {} },
        HostConfig: {
          PortBindings: {
            '6080/tcp': [{ HostPort: String(port) }],
            '8888/tcp': [{ HostPort: String(port + 1000) }],
          },
          Binds: binds.length > 0 ? binds : undefined,
          RestartPolicy: { Name: 'unless-stopped' },
          Memory: 2 * 1024 * 1024 * 1024,  // 2GB
          NanoCpus: 2 * 1e9,               // 2 CPU
        },
        Labels: {
          'ktw.pool': 'terminal',
          'ktw.status': tenantId ? 'assigned' : 'idle',
          'ktw.tenant': tenantId || '',
        },
      })

      await container.start()

      const entry = {
        containerId: container.id.substring(0, 12),
        status: tenantId ? 'assigned' : 'idle',
        tenantId: tenantId || null,
        noVncUrl: tenantId ? `http://localhost:${port}/vnc.html` : null,
        port,
        assignedAt: tenantId ? now() : 0,
        lastActivity: now(),
        healthFailures: 0,
      }

      pool.set(entry.containerId, entry)
      console.log(`[Pool] ✅ 容器已建立: ${entry.containerId} (port=${port}${tenantId ? `, tenant=${tenantId}` : ''})`)
      return entry
    } catch (err) {
      // HTTP 409: 容器名稱衝突 → 移除舊容器後重試
      if (err.statusCode === 409 && containerName && attempt === 0) {
        console.log(`[Pool] ⚠️ 名稱衝突: ${containerName}，嘗試移除舊容器後重建...`)
        try {
          const old = docker.getContainer(containerName)
          await old.stop({ t: 5 }).catch(() => {}) // 可能已停止
          await old.remove({ force: true })
          console.log(`[Pool] 🧹 舊容器 ${containerName} 已移除`)
          continue // 重試建立
        } catch (cleanErr) {
          console.error(`[Pool] ❌ 移除舊容器失敗:`, cleanErr.message)
        }
      }
      console.error(`[Pool] ❌ 建立容器失敗:`, err.message)
      return null
    }
  }
  return null
}

/**
 * 分配容器給租戶
 * 策略：直接建立帶有正確 env + volume 的容器（非 exec 注入，因為 exec export 只在子 shell 生效）
 */
async function allocateContainer(tenantId, jwtToken, options = {}) {
  // 檢查該租戶是否已有容器
  for (const [id, entry] of pool) {
    if (entry.tenantId === tenantId && entry.status === 'assigned') {
      // ⭐ 分配前先驗證 noVNC 是否存活，避免回傳死容器
      const healthy = await checkNoVncHealth(entry.port)
      if (healthy) {
        entry.lastActivity = now()
        entry.healthFailures = 0 // 重置失敗計數
        return entry
      }
      // noVNC 無回應 → 清理幽靈容器，繼續建新的
      console.log(`[Pool] ⚠️ 租戶 ${tenantId} 的容器 ${id} noVNC 無回應，清理後重建`)
      await cleanupGhostContainer(id, entry, 'allocate 時 noVNC 探測失敗')
      break
    }
  }

  // 超過上限 → 拒絕
  if (pool.size >= MAX_SIZE) {
    return null
  }

  // 直接建立帶租戶設定的容器（環境變數 + Volume 掛載在 create 時設定）
  const entry = await createTerminalContainer(tenantId, {
    jwtToken,
    llmTier: options.llmTier,
    intelligenceEnabled: options.intelligenceEnabled,
    tradingEnabled: options.tradingEnabled,
  })

  if (!entry) return null

  console.log(`[Pool] 🔗 容器 ${entry.containerId} 已分配給租戶 ${tenantId}`)
  return entry
}

/**
 * 釋放租戶容器（停止 + 移除，因為每個容器帶有租戶專屬 Volume 和 env）
 * 租戶資料保留在具名 Volume 中（fincept-tenant-{id}-data），下次 allocate 會重新掛載
 */
async function releaseContainer(tenantId) {
  for (const [id, entry] of pool) {
    if (entry.tenantId === tenantId && entry.status === 'assigned') {
      try {
        const container = docker.getContainer(entry.containerId)
        await container.stop({ t: 10 })
        await container.remove()
        pool.delete(id)
        console.log(`[Pool] 🔓 容器 ${entry.containerId} 已停止並移除（租戶 ${tenantId}，資料保留在 Volume）`)
      } catch (err) {
        console.error(`[Pool] 釋放失敗: ${entry.containerId}`, err.message)
        pool.delete(id)
      }
      return true
    }
  }
  return false
}

// ── 定期維護 ────────────────────────────────────────────────────────────────

/**
 * 健康檢查 + 清理異常容器
 *
 * 檢查層級（由淺到深）：
 *   1. Docker 層級 — 容器是否 Running
 *   2. noVNC 層級 — HTTP 探測 port 是否回應
 *
 * 連續失敗 HEALTH_FAIL_THRESHOLD 次才清理（避免單次網路抖動誤殺）
 */
async function maintenance() {
  const entries = [...pool.entries()]
  if (entries.length === 0) return

  for (const [id, entry] of entries) {
    if (entry.status !== 'assigned') continue

    // === 第 1 層：Docker 容器狀態 ===
    let dockerRunning = false
    try {
      const container = docker.getContainer(entry.containerId)
      const info = await container.inspect()
      dockerRunning = info.State.Running
    } catch {
      // Docker API 找不到容器 → 直接移除記錄
      console.log(`[維護] ⚠️ 容器 ${id} 不存在於 Docker，從池中移除`)
      pool.delete(id)
      continue
    }

    if (!dockerRunning) {
      await cleanupGhostContainer(id, entry, 'Docker 容器已停止')
      continue
    }

    // === 第 2 層：noVNC HTTP 探測 ===
    const noVncAlive = await checkNoVncHealth(entry.port)

    if (noVncAlive) {
      // 健康 → 重置失敗計數
      if (entry.healthFailures > 0) {
        console.log(`[維護] ✅ 容器 ${id} noVNC 恢復健康（之前失敗 ${entry.healthFailures} 次）`)
        entry.healthFailures = 0
      }
    } else {
      // 不健康 → 累計失敗次數
      entry.healthFailures = (entry.healthFailures || 0) + 1
      console.log(`[維護] ⚠️ 容器 ${id} (tenant=${entry.tenantId}, port=${entry.port}) noVNC 無回應 (${entry.healthFailures}/${HEALTH_FAIL_THRESHOLD})`)

      if (entry.healthFailures >= HEALTH_FAIL_THRESHOLD) {
        await cleanupGhostContainer(id, entry, `noVNC 連續 ${HEALTH_FAIL_THRESHOLD} 次無回應`)
      }
    }
  }
}

// 每 30 秒維護一次（從 60s 縮短，加速偵測幽靈容器）
setInterval(maintenance, 30_000)

// ── Token Refresh ───────────────────────────────────────────────────────────

/**
 * 為單一容器刷新 JWT Token
 * 流程：呼叫 Platform API → 取得新 JWT → docker exec 寫入 /tmp/.ktw_jwt
 * @param {PoolEntry} entry - 容器池項目
 * @returns {boolean} 是否成功
 */
async function refreshTokenForContainer(entry) {
  if (!entry.tenantId || entry.status !== 'assigned') return false
  if (!FINCEPT_POOL_SECRET) {
    console.warn('[Token Refresh] ⚠️ FINCEPT_POOL_SECRET 未設定，跳過')
    return false
  }

  try {
    // 1. 呼叫 Platform Token Refresh API
    const res = await fetch(`${SAAS_URL}/api/fincept/token/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenantId: entry.tenantId,
        secret: FINCEPT_POOL_SECRET,
      }),
      signal: AbortSignal.timeout(10_000),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      console.error(`[Token Refresh] ❌ 租戶 ${entry.tenantId} 刷新失敗 (${res.status}):`, err.error)
      return false
    }

    const data = await res.json()
    if (!data.token) {
      console.error(`[Token Refresh] ❌ 租戶 ${entry.tenantId} 回傳無 token`)
      return false
    }

    // 2. 透過 docker exec 將新 JWT 寫入容器的 /tmp/.ktw_jwt
    const container = docker.getContainer(entry.containerId)
    const exec = await container.exec({
      Cmd: ['bash', '-c', `echo '${data.token}' > /tmp/.ktw_jwt && chmod 600 /tmp/.ktw_jwt`],
      AttachStdout: true,
      AttachStderr: true,
    })
    await exec.start({ Detach: false })

    console.log(`[Token Refresh] ✅ 租戶 ${entry.tenantId} (容器 ${entry.containerId}) JWT 已刷新 → /tmp/.ktw_jwt`)
    return true
  } catch (err) {
    console.error(`[Token Refresh] ❌ 租戶 ${entry.tenantId} 例外:`, err.message)
    return false
  }
}

/**
 * 為所有 assigned 容器刷新 JWT
 * 啟動時立即執行一次 + 之後每 30 分鐘執行
 */
async function refreshAllTokens() {
  const assigned = [...pool.values()].filter(e => e.status === 'assigned')
  if (assigned.length === 0) return

  console.log(`[Token Refresh] 🔄 開始為 ${assigned.length} 個容器刷新 JWT...`)
  let success = 0
  let failed = 0

  for (const entry of assigned) {
    const ok = await refreshTokenForContainer(entry)
    if (ok) success++
    else failed++
  }

  console.log(`[Token Refresh] 完成 — 成功 ${success}，失敗 ${failed}`)
}

// 每 30 分鐘刷新所有容器的 JWT
setInterval(refreshAllTokens, TOKEN_REFRESH_INTERVAL)

// ── HTTP 伺服器 ─────────────────────────────────────────────────────────────

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`)

  try {
    // 健康檢查
    if (url.pathname === '/health') {
      const values = [...pool.values()]
      const assigned = values.filter(e => e.status === 'assigned').length
      const idle = values.filter(e => e.status === 'idle').length
      const unhealthy = values.filter(e => (e.healthFailures || 0) > 0).length
      return json(res, 200, {
        status: 'ok',
        pool: { total: pool.size, assigned, idle, unhealthy, maxSize: MAX_SIZE },
      })
    }

    // 分配容器
    if (req.method === 'POST' && url.pathname === '/api/pool/allocate') {
      const body = await readBody(req)
      if (!body.tenantId) return json(res, 400, { error: '缺少 tenantId' })

      const entry = await allocateContainer(body.tenantId, body.jwtToken, {
        llmTier: body.llmTier,
        intelligenceEnabled: body.intelligenceEnabled,
        tradingEnabled: body.tradingEnabled,
      })

      if (!entry) return json(res, 503, { error: '容器池已滿，請稍後重試' })

      return json(res, 200, {
        success: true,
        container: {
          id: entry.containerId,
          noVncUrl: entry.noVncUrl,
          port: entry.port,
          assignedAt: entry.assignedAt,
        },
      })
    }

    // 釋放容器
    if (req.method === 'POST' && url.pathname === '/api/pool/release') {
      const body = await readBody(req)
      if (!body.tenantId) return json(res, 400, { error: '缺少 tenantId' })

      const released = await releaseContainer(body.tenantId)
      return json(res, 200, { success: released })
    }

    // 容器池狀態
    if (req.method === 'GET' && url.pathname === '/api/pool/status') {
      const entries = [...pool.values()].map(e => ({
        containerId: e.containerId,
        status: e.status,
        tenantId: e.tenantId,
        port: e.port,
        noVncUrl: e.noVncUrl,
        idleSeconds: e.status === 'idle' ? Math.floor((now() - e.lastActivity) / 1000) : 0,
      }))
      return json(res, 200, { pool: entries, config: { poolSize: POOL_SIZE, maxSize: MAX_SIZE, idleTimeout: IDLE_TIMEOUT } })
    }

    // 手動觸發 Token Refresh（管理端點）
    if (req.method === 'POST' && url.pathname === '/api/pool/refresh-tokens') {
      await refreshAllTokens()
      return json(res, 200, { success: true, message: '已觸發全量 Token Refresh' })
    }

    // 手動觸發健康檢查（管理端點）
    if (req.method === 'POST' && url.pathname === '/api/pool/health-check') {
      await maintenance()
      const entries = [...pool.values()].map(e => ({
        containerId: e.containerId,
        tenantId: e.tenantId,
        port: e.port,
        status: e.status,
        healthFailures: e.healthFailures || 0,
      }))
      return json(res, 200, { success: true, pool: entries, message: '健康檢查完成' })
    }

    // 查詢租戶容器
    if (req.method === 'GET' && url.pathname.startsWith('/api/pool/tenant/')) {
      const tenantId = url.pathname.split('/').pop()
      const entry = [...pool.values()].find(e => e.tenantId === tenantId)
      if (!entry) return json(res, 404, { error: '該租戶無分配容器' })
      return json(res, 200, {
        containerId: entry.containerId,
        noVncUrl: entry.noVncUrl,
        port: entry.port,
        status: entry.status,
      })
    }

    json(res, 404, { error: 'Not found' })
  } catch (err) {
    console.error('[API] ❌', err)
    json(res, 500, { error: err.message })
  }
})

// ── 啟動 ────────────────────────────────────────────────────────────────────

server.listen(PORT, async () => {
  console.log(`\n${'═'.repeat(60)}`)
  console.log(`  KTW SaaS — Fincept Terminal 容器池管理器`)
  console.log(`  端口: ${PORT}`)
  console.log(`  SaaS URL: ${SAAS_URL}`)
  console.log(`  最大容器數: ${MAX_SIZE}`)
  console.log(`  模式: 按需建立（allocate 時建立，release 時銷毀）`)
  console.log(`${'═'.repeat(60)}\n`)

  // 啟動時掃描並納管已存在的 Docker 容器
  await scanExistingContainers()

  // 啟動後立即為所有已分配容器刷新 JWT（修復舊容器 Token 過期問題）
  if (FINCEPT_POOL_SECRET) {
    console.log('[啟動] 🔑 FINCEPT_POOL_SECRET 已設定，將執行首次 Token Refresh...')
    setTimeout(refreshAllTokens, 3000) // 延遲 3 秒，確保容器掃描完成
  } else {
    console.warn('[啟動] ⚠️ FINCEPT_POOL_SECRET 未設定，Token Refresh 功能停用')
  }

  console.log(`[啟動] ✅ 容器池管理器就緒（池中 ${pool.size} 個容器），等待租戶分配請求...`)
})
