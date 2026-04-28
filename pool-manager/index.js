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
 * 建立一個新的 Terminal 容器（預熱狀態）
 */
async function createTerminalContainer() {
  const port = nextPort++
  if (nextPort > 6200) nextPort = 6081 // 端口循環使用

  try {
    const container = await docker.createContainer({
      Image: IMAGE_NAME,
      Env: [
        `KTW_SAAS_URL=${SAAS_URL}`,
        'KTW_HEALTH_PORT=8888',
        'FINCEPT_LANG=zh_TW',
        'LANG=zh_TW.UTF-8',
        'TZ=Asia/Taipei',
        'RESOLUTION=1920x1080x24',
      ],
      ExposedPorts: { '6080/tcp': {}, '8888/tcp': {} },
      HostConfig: {
        PortBindings: {
          '6080/tcp': [{ HostPort: String(port) }],
          '8888/tcp': [{ HostPort: String(port + 1000) }], // 健康檢查端口 = noVNC + 1000
        },
        RestartPolicy: { Name: 'unless-stopped' },
        Memory: 2 * 1024 * 1024 * 1024,  // 2GB
        NanoCpus: 2 * 1e9,               // 2 CPU
      },
      Labels: {
        'ktw.pool': 'terminal',
        'ktw.status': 'idle',
      },
    })

    await container.start()

    const entry = {
      containerId: container.id.substring(0, 12),
      status: 'idle',
      tenantId: null,
      noVncUrl: null,
      port,
      assignedAt: 0,
      lastActivity: now(),
    }

    pool.set(entry.containerId, entry)
    console.log(`[Pool] ✅ 容器已建立: ${entry.containerId} (port=${port})`)
    return entry
  } catch (err) {
    console.error(`[Pool] ❌ 建立容器失敗:`, err.message)
    return null
  }
}

/**
 * 分配容器給租戶
 */
async function allocateContainer(tenantId, jwtToken, options = {}) {
  // 檢查該租戶是否已有容器
  for (const [, entry] of pool) {
    if (entry.tenantId === tenantId && entry.status === 'assigned') {
      entry.lastActivity = now()
      return entry
    }
  }

  // 找一個閒置容器
  let target = null
  for (const [, entry] of pool) {
    if (entry.status === 'idle') {
      target = entry
      break
    }
  }

  // 沒有閒置容器 → 動態建立（不超過上限）
  if (!target) {
    if (pool.size >= MAX_SIZE) {
      return null // 容器池已滿
    }
    target = await createTerminalContainer()
    if (!target) return null
  }

  // 注入租戶環境變數（透過 Docker exec 設定）
  try {
    const container = docker.getContainer(target.containerId)

    // 透過 exec 寫入租戶設定檔
    const exec = await container.exec({
      Cmd: ['sh', '-c', `
        export KTW_TENANT_ID="${tenantId}"
        export KTW_JWT_TOKEN="${jwtToken || ''}"
        export KTW_LLM_TIER="${options.llmTier || 'L1'}"
        export KTW_INTELLIGENCE_ENABLED="${options.intelligenceEnabled !== false}"
        export KTW_TRADING_ENABLED="${options.tradingEnabled === true}"
        echo '{"tenantId":"${tenantId}","assignedAt":"'$(date -Iseconds)'"}' > /data/tenant/assignment.json
      `],
      AttachStdout: false,
      AttachStderr: false,
    })
    await exec.start()

    target.status = 'assigned'
    target.tenantId = tenantId
    target.noVncUrl = `http://localhost:${target.port}/vnc.html`
    target.assignedAt = now()
    target.lastActivity = now()

    console.log(`[Pool] 🔗 容器 ${target.containerId} 已分配給租戶 ${tenantId}`)
    return target
  } catch (err) {
    console.error(`[Pool] ❌ 分配失敗:`, err.message)
    return null
  }
}

/**
 * 釋放租戶容器（歸池）
 */
async function releaseContainer(tenantId) {
  for (const [, entry] of pool) {
    if (entry.tenantId === tenantId && entry.status === 'assigned') {
      entry.status = 'idle'
      entry.tenantId = null
      entry.noVncUrl = null
      entry.assignedAt = 0
      entry.lastActivity = now()

      console.log(`[Pool] 🔓 容器 ${entry.containerId} 已歸池（租戶 ${tenantId}）`)
      return true
    }
  }
  return false
}

// ── 定期維護 ────────────────────────────────────────────────────────────────

/**
 * 清理閒置過久的容器（保留最低 POOL_SIZE 個）
 */
async function maintenance() {
  const idleEntries = [...pool.values()].filter(e => e.status === 'idle')

  // 超過基礎池大小的閒置容器，且閒置超過逾時
  for (const entry of idleEntries) {
    if (pool.size <= POOL_SIZE) break
    if (now() - entry.lastActivity > IDLE_TIMEOUT * 1000) {
      try {
        const container = docker.getContainer(entry.containerId)
        await container.stop({ t: 10 })
        await container.remove()
        pool.delete(entry.containerId)
        console.log(`[維護] 🗑️ 移除閒置容器: ${entry.containerId}`)
      } catch (err) {
        console.error(`[維護] 移除失敗: ${entry.containerId}`, err.message)
      }
    }
  }

  // 確保池中至少有 POOL_SIZE 個容器
  const total = pool.size
  if (total < POOL_SIZE) {
    const needed = POOL_SIZE - total
    console.log(`[維護] 預熱 ${needed} 個容器...`)
    for (let i = 0; i < needed; i++) {
      await createTerminalContainer()
    }
  }
}

// 每 30 秒維護一次
setInterval(maintenance, 30_000)

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
  console.log(`  池大小: ${POOL_SIZE} (最大: ${MAX_SIZE})`)
  console.log(`  閒置逾時: ${IDLE_TIMEOUT}s`)
  console.log(`${'═'.repeat(60)}\n`)

  // 初始預熱
  console.log(`[啟動] 預熱 ${POOL_SIZE} 個 Terminal 容器...`)
  for (let i = 0; i < POOL_SIZE; i++) {
    await createTerminalContainer()
  }
  console.log(`[啟動] ✅ 預熱完成，容器池就緒`)
})
