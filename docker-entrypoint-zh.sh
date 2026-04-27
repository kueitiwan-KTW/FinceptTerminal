#!/bin/bash
# FinceptTerminal 繁體中文版 — Docker 容器啟動腳本
# 啟動 Xvfb + fluxbox + noVNC + FinceptTerminal

set -e

# 顯示設定
DISPLAY_NUM="${DISPLAY_NUM:-99}"
export DISPLAY=":${DISPLAY_NUM}"
RESOLUTION="${RESOLUTION:-1920x1080x24}"
VNC_PORT="${VNC_PORT:-5999}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

echo "[啟動] FinceptTerminal 繁體中文版"
echo "[設定] 解析度: ${RESOLUTION}, VNC 端口: ${VNC_PORT}, noVNC 端口: ${NOVNC_PORT}"
echo "[i18n] FINCEPT_LANG=${FINCEPT_LANG}, LANG=${LANG}"

# 啟動虛擬顯示
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

# 啟動 FinceptTerminal
cd /opt/fincept
export QT_QPA_PLATFORM=xcb
export QT_LOGGING_RULES="qt.*=false"

# 確認翻譯檔存在
if [ -f "/opt/fincept/translations/fincept_zh_TW.qm" ]; then
    echo "[i18n] ✅ 翻譯檔就緒: fincept_zh_TW.qm"
else
    echo "[i18n] ⚠️ 找不到翻譯檔，使用英文介面"
fi

exec /opt/fincept/bin/FinceptTerminal "$@"
