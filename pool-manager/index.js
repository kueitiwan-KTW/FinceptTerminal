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
const SAAS_URL = process.env.KTW_SAAS_URL || 'https://platform.ktweb.io'
const POOL_SIZE = parseInt(process.env.POOL_SIZE || '3')        // 預熱容器數
const MAX_SIZE = parseInt(process.env.POOL_MAX_SIZE || '10')    // 最大容器數
const IDLE_TIMEOUT = parseInt(process.env.POOL_IDLE_TIMEOUT || '300') // 閒置逾時（秒）
const IMAGE_NAME = 'ktw/fincept-terminal:zh-latest'

const docker = new Docker({ socketPath: process.env.DOCKER_SOCKET || '/var/run/docker.sock' })

// ── 容器池狀態 ──────────────────────────────────────────────────────────────

/** @type {Map<string, PoolEntry>} containerId -> 狀態 */
const pool = new Map()

/**
 * @typedef {Object} PoolEntry
 * @property {string} containerId    - Docker 容器 ID
 * @property {'idle'|'assigned'|'starting'|'stopping'} status
 * @property {string|null} tenantId  - 分配給的租戶
 * @property {string|null} noVncUrl  - noVNC 存取 URL
 * @property {number} port           - noVNC 外部端口
 * @property {number} assignedAt     - 分配時間戳
 * @property {number} lastActivity   - 最後活動時間
 */

let nextPort = 6081 // noVNC 端口分配起始值

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

  try {
    const container = await docker.createContainer({
      Image: IMAGE_NAME,
      name: tenantId ? `fincept-${tenantId}` : undefined,
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
    }

    pool.set(entry.containerId, entry)
    console.log(`[Pool] ✅ 容器已建立: ${entry.containerId} (port=${port}${tenantId ? `, tenant=${tenantId}` : ''})`)
    return entry
  } catch (err) {
    console.error(`[Pool] ❌ 建立容器失敗:`, err.message)
    return null
  }
}

/**
 * 分配容器給租戶
 * 策略：直接建立帶有正確 env + volume 的容器（非 exec 注入，因為 exec export 只在子 shell 生效）
 */
async function allocateContainer(tenantId, jwtToken, options = {}) {
  // 檢查該租戶是否已有容器
  for (const [, entry] of pool) {
    if (entry.tenantId === tenantId && entry.status === 'assigned') {
      entry.lastActivity = now()
      return entry
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
 * 按需建立模式下不需要預熱，只需要清理
 */
async function maintenance() {
  for (const [id, entry] of pool) {
    if (entry.status === 'assigned') {
      // 檢查已分配容器是否還活著
      try {
        const container = docker.getContainer(entry.containerId)
        const info = await container.inspect()
        if (!info.State.Running) {
          console.log(`[維護] ⚠️ 容器 ${id} 已停止，從池中移除`)
          pool.delete(id)
        }
      } catch {
        console.log(`[維護] ⚠️ 容器 ${id} 不存在，從池中移除`)
        pool.delete(id)
      }
    }
  }
}

// 每 60 秒維護一次
setInterval(maintenance, 60_000)

// ── HTTP 伺服器 ─────────────────────────────────────────────────────────────

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`)

  try {
    // 健康檢查
    if (url.pathname === '/health') {
      const assigned = [...pool.values()].filter(e => e.status === 'assigned').length
      const idle = [...pool.values()].filter(e => e.status === 'idle').length
      return json(res, 200, {
        status: 'ok',
        pool: { total: pool.size, assigned, idle, maxSize: MAX_SIZE },
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

  console.log(`[啟動] ✅ 容器池管理器就緒，等待租戶分配請求...`)
})
