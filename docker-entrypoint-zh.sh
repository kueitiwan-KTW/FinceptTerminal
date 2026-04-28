#!/bin/bash
# FinceptTerminal 繁體中文版 — Docker 容器啟動腳本
# 支援 KTW SaaS 多租戶容器池模式
# 啟動 Xvfb + fluxbox + noVNC + FinceptTerminal

set -e

# ── 顯示設定 ──────────────────────────────────────────────────────────────────
DISPLAY_NUM="${DISPLAY_NUM:-99}"
export DISPLAY=":${DISPLAY_NUM}"
RESOLUTION="${RESOLUTION:-1920x1080x24}"
VNC_PORT="${VNC_PORT:-5999}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

echo "[啟動] FinceptTerminal 繁體中文版"
echo "[設定] 解析度: ${RESOLUTION}, VNC 端口: ${VNC_PORT}, noVNC 端口: ${NOVNC_PORT}"
echo "[i18n] FINCEPT_LANG=${FINCEPT_LANG}, LANG=${LANG}"

# ── KTW SaaS 模式偵測與設定 ──────────────────────────────────────────────────
if [ -n "${KTW_SAAS_URL}" ]; then
    echo "[SaaS] ✅ 已啟用 SaaS 模式"
    echo "[SaaS] 平台 URL: ${KTW_SAAS_URL}"

    # 租戶 ID（由容器編排系統注入）
    if [ -n "${KTW_TENANT_ID}" ]; then
        echo "[SaaS] 租戶 ID: ${KTW_TENANT_ID}"
    fi

    # JWT Token（由 SaaS 平台動態簽發）
    if [ -n "${KTW_JWT_TOKEN}" ]; then
        echo "[SaaS] JWT Token: (已設定, 長度=${#KTW_JWT_TOKEN})"
    fi

    # LLM Tier 設定（L1/L2/L3）
    if [ -n "${KTW_LLM_TIER}" ]; then
        echo "[SaaS] LLM Tier: ${KTW_LLM_TIER}"
    fi

    # 功能開關
    echo "[SaaS] 功能: Intelligence=${KTW_INTELLIGENCE_ENABLED:-true}, Trading=${KTW_TRADING_ENABLED:-false}"
else
    echo "[SaaS] ⚠️ 未設定 KTW_SAAS_URL，使用原生 Fincept 模式"
fi

# ── 租戶資料卷掛載 ────────────────────────────────────────────────────────────
# 容器池模式：租戶的持久化資料透過 Volume 掛載
TENANT_DATA_DIR="/data/tenant"

if [ -d "${TENANT_DATA_DIR}" ]; then
    echo "[資料] 租戶資料卷已掛載: ${TENANT_DATA_DIR}"

    # 恢復租戶本地設定（watchlists, 偏好, 快取）
    if [ -d "${TENANT_DATA_DIR}/config" ]; then
        echo "[資料] 恢復租戶設定..."
        mkdir -p "${HOME}/.config/fincept"
        cp -r "${TENANT_DATA_DIR}/config/"* "${HOME}/.config/fincept/" 2>/dev/null || true
    fi

    # 恢復租戶 Session 資料
    if [ -f "${TENANT_DATA_DIR}/session.json" ]; then
        echo "[資料] 恢復 Session..."
        mkdir -p "${HOME}/.local/share/fincept"
        cp "${TENANT_DATA_DIR}/session.json" "${HOME}/.local/share/fincept/" 2>/dev/null || true
    fi
else
    echo "[資料] 無租戶資料卷掛載（首次使用或非容器池模式）"
    mkdir -p "${TENANT_DATA_DIR}"
fi

# ── 設定 Session 自動儲存（容器停止前保存租戶資料）────────────────────────────
save_tenant_data() {
    if [ -d "${TENANT_DATA_DIR}" ] && [ -n "${KTW_TENANT_ID}" ]; then
        echo "[資料] 正在儲存租戶 ${KTW_TENANT_ID} 資料..."
        mkdir -p "${TENANT_DATA_DIR}/config"

        # 儲存設定
        if [ -d "${HOME}/.config/fincept" ]; then
            cp -r "${HOME}/.config/fincept/"* "${TENANT_DATA_DIR}/config/" 2>/dev/null || true
        fi

        # 儲存 Session
        if [ -f "${HOME}/.local/share/fincept/session.json" ]; then
            cp "${HOME}/.local/share/fincept/session.json" "${TENANT_DATA_DIR}/" 2>/dev/null || true
        fi

        echo "[資料] ✅ 租戶資料已儲存"
    fi
}

# 捕捉容器停止信號，先儲存資料再退出
trap save_tenant_data SIGTERM SIGINT EXIT

# ── 啟動虛擬顯示 ──────────────────────────────────────────────────────────────
Xvfb "${DISPLAY}" -screen 0 "${RESOLUTION}" -ac +extension GLX &
sleep 1

# 啟動視窗管理器
fluxbox -display "${DISPLAY}" &
sleep 0.5

# 啟動 VNC 伺服器
x11vnc -display "${DISPLAY}" -rfbport "${VNC_PORT}" \
    -nopw -shared -forever -noxdamage \
    -bg -o /tmp/x11vnc.log

# 啟動 noVNC（WebSocket 代理）
websockify --web=/usr/share/novnc "${NOVNC_PORT}" "localhost:${VNC_PORT}" &
sleep 0.5

echo "[就緒] noVNC 可在 http://localhost:${NOVNC_PORT}/vnc.html 存取"

# ── 啟動 FinceptTerminal ──────────────────────────────────────────────────────
cd /opt/fincept
export QT_QPA_PLATFORM=xcb
export QT_LOGGING_RULES="qt.*=false"

# 確認翻譯檔存在
if [ -f "/opt/fincept/translations/fincept_zh_TW.qm" ]; then
    echo "[i18n] ✅ 翻譯檔就緒: fincept_zh_TW.qm"
else
    echo "[i18n] ⚠️ 找不到翻譯檔，使用英文介面"
fi

# 健康檢查端點（容器池管理用）
if [ -n "${KTW_HEALTH_PORT}" ]; then
    echo "[健康] 啟動健康檢查端點 port=${KTW_HEALTH_PORT}"
    while true; do
        echo -e "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"running\",\"tenant\":\"${KTW_TENANT_ID:-none}\",\"uptime\":$(cat /proc/uptime | cut -d' ' -f1)}" \
            | nc -l -p "${KTW_HEALTH_PORT}" -q 1 2>/dev/null || true
    done &
fi

exec /opt/fincept/bin/FinceptTerminal "$@"
