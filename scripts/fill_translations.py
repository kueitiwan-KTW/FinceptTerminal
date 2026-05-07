#!/usr/bin/env python3
"""批量填入 116 條空翻譯到 fincept_zh_TW.ts"""
import xml.etree.ElementTree as ET
import sys, copy

# 翻譯對照表：(context, source) -> translation
# 正則/符號/專有名詞類原樣保留
TRANSLATIONS = {
    # ── ActivityTab ──
    ("ActivityTab", "  ·  Add a Helius API key in Settings for parsed swap and transfer details."):
        "  ·  請在設定中新增 Helius API 金鑰，以取得已解析的交換與轉帳詳情。",

    # ── AiChatBubble ──
    ("AiChatBubble", "⚠ Voice responses unavailable — Qt TextToSpeech not installed. Input-only mode active."):
        "⚠ 語音回覆不可用 — 未安裝 Qt TextToSpeech。僅限輸入模式。",
    ("AiChatBubble", "⚠ No TTS engine found (install speech-dispatcher on Linux). Input-only mode active."):
        "⚠ 找不到 TTS 引擎（請在 Linux 上安裝 speech-dispatcher）。僅限輸入模式。",

    # ── AiChatScreen ──
    ("AiChatScreen", "Fincept managed AI service\n\nChange in Settings > LLM Configuration"):
        "Fincept 代管 AI 服務\n\n可在設定 > LLM 設定中變更",

    # ── AkShareScreen ──
    ("AkShareScreen", "Select a data source above\nto load available endpoints"):
        "請在上方選擇資料來源\n以載入可用端點",

    # ── AlphaArenaScreen ──
    ("AlphaArenaScreen", "Human-in-the-loop approvals will appear here.\nHigh-risk trades require manual approval before execution."):
        "人工審核核准將顯示於此。\n高風險交易在執行前需要手動核准。",
    ("AlphaArenaScreen", "Market sentiment analysis will appear here.\nMood: RISK_ON / RISK_OFF / MIXED"):
        "市場情緒分析將顯示於此。\n情緒：風險偏好 / 風險規避 / 混合",
    ("AlphaArenaScreen", "Grid trading strategy configuration.\nPlace buy/sell orders at regular price intervals."):
        "網格交易策略設定。\n以固定價格間隔放置買賣訂單。",
    ("AlphaArenaScreen", "SEC filings and company research.\nSearch by ticker to load 10-K, 10-Q, 8-K filings."):
        "SEC 申報與公司研究。\n依股票代號搜尋以載入 10-K、10-Q、8-K 申報文件。",
    ("AlphaArenaScreen", "Broker selection and configuration.\nSupported: Kraken, Binance, Coinbase, and more."):
        "券商選擇與設定。\n支援：Kraken、Binance、Coinbase 等。",

    # ── AltInvestmentsScreen ──
    ("AltInvestmentsScreen", "27 ANALYZERS  \uf0e8  10 ASSET CLASSES  \uf0e8  MULTI-ASSET ANALYTICS"):
        "27 個分析器  \uf0e8  10 種資產類別  \uf0e8  多資產分析",

    # ── CommandBar ──
    ("CommandBar", "›"): "›",

    # ── ComingSoonScreen ──
    ("ComingSoonScreen", "⚡"): "⚡",
    ("ComingSoonScreen", "This module is under active development.\nIt will be available in a future update."):
        "此模組正在積極開發中。\n將在未來的更新中推出。",

    # ── CryptoCenterScreen ──
    ("CryptoCenterScreen", "Connect a Solana wallet to view your $FNCPT balance, SOL holdings, and live USD valuation. Your private keys never leave your wallet."):
        "連接 Solana 錢包以查看您的 $FNCPT 餘額、SOL 持有量與即時美元估值。您的私鑰永遠不會離開您的錢包。",
    ("CryptoCenterScreen", "· public address read-only\n· no private keys, no seed phrases\n· local handshake on 127.0.0.1, single-use token\n· cryptographic signature challenge before connect"):
        "· 僅讀取公開地址\n· 不涉及私鑰或助記詞\n· 在 127.0.0.1 本機握手，一次性 Token\n· 連接前進行密碼學簽名驗證",

    # ── CustomIndexView ──
    ("CustomIndexView", "No custom indices created yet.\nGo to CREATE INDEX tab to build one from your portfolio."):
        "尚未建立自訂指數。\n前往「建立指數」分頁，從您的投資組合建立一個。",

    # ── DBnomicsScreen ──
    ("DBnomicsScreen", "NO COMPARISON SLOTS\nClick  + ADD SLOT  in the left panel to begin"):
        "尚無比較欄位\n點擊左側面板的 + 新增欄位 以開始",

    # ── DBnomicsSelectionPanel ──
    ("DBnomicsSelectionPanel", "●"): "●",
    ("DBnomicsSelectionPanel", "×"): "×",

    # ── DataMappingScreen ──
    ("DataMappingScreen", "Content-Type: application/json\nAccept: application/json"):
        "Content-Type: application/json\nAccept: application/json",
    ("DataMappingScreen", "No mappings saved yet.\nClick CREATE to build your first data mapping."):
        "尚未儲存任何映射。\n點擊「建立」以建構您的第一個資料映射。",

    # ── EquityOverviewTab ──
    ("EquityOverviewTab", "—"): "—",

    # ── EquityTechnicalsTab ──
    ("EquityTechnicalsTab", "—"): "—",

    # ── FeeDiscountPanel ──
    ("FeeDiscountPanel", "Hold ≥ %1 $FNCPT to qualify for the discount on premium screens, AI reports, and deep backtests."):
        "持有 ≥ %1 $FNCPT 即可享受進階畫面、AI 報告和深度回測的折扣。",

    # ── FileManagerScreen ──
    ("FileManagerScreen", "Binary file — preview not available.\nUse SAVE to download."):
        "二進位檔案 — 無法預覽。\n請使用「儲存」下載。",
    ("FileManagerScreen", ""): "",

    # ── FinceptTerminal ──
    ("FinceptTerminal", "%1¢"): "%1¢",
    ("FinceptTerminal", "<br\\s*/?>|</(p|div|li|tr)>"): "<br\\s*/?>|</(p|div|li|tr)>",

    # ── HoldingsBar ──
    ("HoldingsBar", "Public Solana RPC. STREAM may degrade — add a Helius API key in Settings for reliable WebSocket subscriptions."):
        "公共 Solana RPC。串流可能不穩定 — 請在設定中新增 Helius API 金鑰以獲得可靠的 WebSocket 訂閱。",

    # ── IlostatPanel ──
    ("IlostatPanel", "ISO-2 country code, e.g. USA, GBR, DEU\nMultiple: CAN+USA+GBR\nAll countries: ALL"):
        "ISO-2 國家代碼，例如 USA、GBR、DEU\n多國：CAN+USA+GBR\n全部國家：ALL",

    # ── LlmConfigSection ──
    ("LlmConfigSection", "When enabled, the AI can interact with the terminal: navigate screens, fetch market data, manage watchlists, etc."):
        "啟用後，AI 可與終端互動：切換畫面、擷取市場資料、管理自選清單等。",

    # ── LockPanel ──
    ("LockPanel", "DEMO — fincept_lock not deployed; configure SecureStorage fincept.lock_program_id to enable real locks."):
        "展示模式 — fincept_lock 尚未部署；請設定 SecureStorage 的 fincept.lock_program_id 以啟用真實鎖倉。",
    ("LockPanel", "Approve in your wallet to escrow $FNCPT under the fincept_lock program. The terminal does not hold your funds — the on-chain program does, and only releases them after the unlock date."):
        "請在錢包中核准，將 $FNCPT 託管於 fincept_lock 程式。終端不持有您的資金 — 鏈上程式會持有，並僅在解鎖日期後釋放。",
    ("LockPanel", "Locked $FNCPT cannot be withdrawn before the unlock date. If you need liquidity sooner, do not lock."):
        "已鎖倉的 $FNCPT 在解鎖日期前無法提領。若您需要更早取得流動性，請勿鎖倉。",

    # ── MAModulePanel ──
    ("MAModulePanel", "[{acquirer:MSFT, target:ATVI, deal_value:68700, premium:45.3,ev_revenue:8.7, ev_ebitda:23.1}]"):
        "[{acquirer:MSFT, target:ATVI, deal_value:68700, premium:45.3,ev_revenue:8.7, ev_ebitda:23.1}]",

    # ── MarketsListPanel ──
    ("MarketsListPanel", "Demo dataset. Set `fincept.markets_endpoint` in SecureStorage and deploy the fincept_market Anchor program for live trading."):
        "展示資料集。請在 SecureStorage 中設定 `fincept.markets_endpoint` 並部署 fincept_market Anchor 程式以進行實盤交易。",

    # ── NodePropertiesPanel ──
    ("NodePropertiesPanel", "Select a node\nto edit properties"):
        "選取一個節點\n以編輯屬性",

    # ── PolymarketDetailPanel ──
    ("PolymarketDetailPanel", "Connect an account\nto place orders"):
        "連接帳戶\n以下單",

    # ── PortfolioCommandBar ──
    ("PortfolioCommandBar", "⋯"): "⋯",
    ("PortfolioCommandBar", "NO PORTFOLIOS — CREATE ONE  ▾"):
        "尚無投資組合 — 建立一個  ▾",

    # ── PortfolioOptimizationView ──
    ("PortfolioOptimizationView", "▶ RUN OPTIMIZATION"):
        "▶ 執行最佳化",

    # ── PortfolioOrderPanel ──
    ("PortfolioOrderPanel", "✕"): "✕",
    ("PortfolioOrderPanel", "Orders are recorded\nin your portfolio"):
        "訂單已記錄\n於您的投資組合中",

    # ── PortfolioPerfChart ──
    ("PortfolioPerfChart", "Indexed view: rebase portfolio and benchmark to 100 at the start of\nthe selected period. Use when comparing different currencies."):
        "指數化檢視：將投資組合與基準在所選期間起始點重新設為 100。\n用於比較不同幣別時使用。",

    # ── PortfolioScreen ──
    ("PortfolioScreen", "◆"): "◆",
    ("PortfolioScreen", "⌕"): "⌕",

    # ── PortfolioStatsRibbon ──
    ("PortfolioStatsRibbon", "Value at Risk at 95% confidence — the maximum expected\nsingle-day loss 95% of the time based on historical returns."):
        "95% 信賴水準的風險值 (VaR) — 根據歷史報酬，\n95% 的時間內預期的最大單日損失。",
    ("PortfolioStatsRibbon", "Composite risk score from 0 (low) to 100 (high).\nWeighted from: volatility, max drawdown, concentration,\nbeta, and VaR. Lower is safer."):
        "綜合風險分數，從 0（低）到 100（高）。\n加權自：波動率、最大回撤、集中度、\nBeta 和 VaR。數值越低越安全。",

    # ── PredictionAccountDialog ──
    ("PredictionAccountDialog", "<b>Polymarket (Polygon)</b><br>Trading requires a Polygon-compatible private key. The key is signed locally via <code>py_clob_client</code> and never leaves your machine in plaintext — it is stored encrypted in your OS credential manager.<br><br><b>⚠ Security:</b> use a dedicated funding wallet, not your primary wallet."):
        "<b>Polymarket (Polygon)</b><br>交易需要 Polygon 相容的私鑰。私鑰透過 <code>py_clob_client</code> 在本機簽署，永遠不會以明文離開您的電腦 — 它會加密儲存在作業系統的憑證管理員中。<br><br><b>⚠ 安全性：</b>請使用專用的資金錢包，而非您的主錢包。",
    ("PredictionAccountDialog", "<b>Kalshi (CFTC-regulated)</b><br>Generate an API key + RSA private key in your Kalshi dashboard (<code>api.elections.kalshi.com</code>). Requests are signed with RSA-PSS (key stays local, encrypted in your OS credential manager).<br><br>Use <b>Demo mode</b> to target <code>demo-api.kalshi.co</code> for testing."):
        "<b>Kalshi（受 CFTC 監管）</b><br>在您的 Kalshi 儀表板（<code>api.elections.kalshi.com</code>）中產生 API 金鑰 + RSA 私鑰。請求以 RSA-PSS 簽署（金鑰保留在本機，加密儲存於作業系統憑證管理員）。<br><br>使用<b>展示模式</b>可連接 <code>demo-api.kalshi.co</code> 進行測試。",
    ("PredictionAccountDialog", "-----BEGIN RSA PRIVATE KEY-----\n…paste PEM contents here…\n-----END RSA PRIVATE KEY-----"):
        "-----BEGIN RSA PRIVATE KEY-----\n…在此貼上 PEM 內容…\n-----END RSA PRIVATE KEY-----",
    ("PredictionAccountDialog", "This removes your stored Polymarket private key and API credentials from this machine. You will need to re-enter them to resume trading."):
        "這會從本機移除您已儲存的 Polymarket 私鑰和 API 憑證。您需要重新輸入才能繼續交易。",
    ("PredictionAccountDialog", "This removes your stored Kalshi API key and RSA private key from this machine."):
        "這會從本機移除您已儲存的 Kalshi API 金鑰和 RSA 私鑰。",

    # ── ProfileScreen ──
    ("ProfileScreen", "—"): "—",

    # ── PropertiesPanel ──
    ("PropertiesPanel", "Select a component\nto edit properties"):
        "選取一個元件\n以編輯屬性",
    ("PropertiesPanel", "Tip: re-select component after\nediting data to re-render."):
        "提示：編輯資料後請重新選取元件\n以重新渲染。",
    ("PropertiesPanel", "P/E Ratio: 28.4\nMarket Cap: $2.9T\n52W High: $199.62\n52W Low: $124.17\nDividend Yield: 0.51%\nEPS: $6.43"):
        "本益比：28.4\n市值：$2.9T\n52 週最高：$199.62\n52 週最低：$124.17\n殖利率：0.51%\n每股盈餘：$6.43",
    ("PropertiesPanel", "Tip: re-select after editing\ndata to refresh sparkline."):
        "提示：編輯資料後請重新選取\n以重新整理走勢圖。",
    ("PropertiesPanel", "Inserts a page break\nin PDF/print output."):
        "在 PDF/列印輸出中\n插入分頁符。",
    ("PropertiesPanel", "Auto-generated from\nHeading components."):
        "從標題元件\n自動產生。",

    # ── QObject ──
    ("QObject", "This swap would fail on-chain: %1. Refusing to sign."):
        "此交換會在鏈上失敗：%1。拒絕簽署。",
    ("QObject", "Approve in your wallet to forward this transaction to the network. The terminal does not hold any funds."):
        "請在錢包中核准以將此交易轉發至網路。終端不持有任何資金。",
    ("QObject", "PumpSwap will reject the trade if execution drifts more than the slippage tolerance above. Your funds stay in your wallet."):
        "若執行滑點超過上方的容忍值，PumpSwap 將拒絕交易。您的資金會留在錢包中。",
    ("QObject", "Could not verify freshness: %1. Try the swap again."):
        "無法驗證時效性：%1。請重新嘗試交換。",
    ("QObject", "This swap is no longer fresh: %1. Click SWAP again to rebuild."):
        "此交換已過期：%1。請再次點擊「交換」重新建立。",

    # ── QuantModulePanel ──
    ("QuantModulePanel", "JSON parameters (optional)\ne.g. {ticker:AAPL}"):
        "JSON 參數（選填）\n例如 {ticker:AAPL}",
    ("QuantModulePanel", "No schedules configured yet.\nUse the Create Schedule tab to add one."):
        "尚未設定排程。\n請使用「建立排程」分頁新增。",
    ("QuantModulePanel", 'Describe your analysis task...\ne.g. "Conduct a full investment analysis of NVDA: research fundamentals, assess risks, and give a buy/sell/hold recommendation with price target"'):
        '描述您的分析任務…\n例如「對 NVDA 進行全面投資分析：研究基本面、評估風險，並給出買入/賣出/持有建議與目標價」',
    ("QuantModulePanel", "Start/stop the Fincept MCP tool server\nGives RD-Agent loops access to market data,\nfinancial news and economics tools."):
        "啟動/停止 Fincept MCP 工具伺服器\n讓 RD-Agent 迴圈可存取市場資料、\n財經新聞和經濟分析工具。",

    # ── QuantStatsView ──
    ("QuantStatsView", "▶ RUN QUANTSTATS"): "▶ 執行 QuantStats",
    ("QuantStatsView", "▶ RUN MONTE CARLO (1000 paths)"): "▶ 執行蒙地卡羅模擬（1000 條路徑）",

    # ── ScannerPanel ──
    ("ScannerPanel", "RELIANCE\nTCS\nINFY\n..."): "RELIANCE\nTCS\nINFY\n...",

    # ── SettingsTab ──
    ("SettingsTab", "POLL refreshes balances on a TTL via the configured RPC. STREAM opens a WebSocket account subscription — requires Helius or a private RPC."):
        "POLL 透過設定的 RPC 依 TTL 重新整理餘額。STREAM 開啟 WebSocket 帳戶訂閱 — 需要 Helius 或私有 RPC。",
    ("SettingsTab", "Paste a Helius API key for reliable account-subscribe streaming and parsed transaction history. Stored in SecureStorage; never transmitted off-machine except in RPC requests to api.helius.xyz."):
        "貼上 Helius API 金鑰以獲得可靠的帳戶訂閱串流和已解析的交易歷史。儲存於 SecureStorage；除了向 api.helius.xyz 發送 RPC 請求外，永遠不會傳送至機器外。",
    ("SettingsTab", "Default slippage tolerance for swaps. Quotes whose route impact exceeds this value are blocked. Adjustable per-swap on the TRADE tab."):
        "交換的預設滑點容忍值。路由影響超過此值的報價將被阻擋。可在「交易」分頁中逐筆調整。",
    ("SettingsTab", "Pump.fun-launched wallets accumulate airdropped junk over time. By default the holdings panel hides tokens that aren't in Jupiter's verified-tagged list. Toggle this on to see every SPL token account in the wallet."):
        "Pump.fun 發行的錢包會隨時間累積空投的垃圾代幣。預設情況下，持倉面板會隱藏不在 Jupiter 驗證標籤清單中的代幣。開啟此選項可查看錢包中所有 SPL 代幣帳戶。",

    # ── SetupScreen ──
    ("SetupScreen", "We need to download a few tools and data libraries once.\nThis only happens the first time — future launches are instant."):
        "我們需要下載一些工具和資料庫（僅此一次）。\n這只會在首次啟動時發生 — 之後的啟動將會即時完成。",
    ("SetupScreen", "↓ 0 B/s"): "↓ 0 B/s",
    ("SetupScreen", "↑ 0 B/s"): "↑ 0 B/s",
    ("SetupScreen", "↓ "): "↓ ",
    ("SetupScreen", "↑ "): "↑ ",
    ("SetupScreen", "Setup is taking longer than expected — possibly a slow internet connection.\nYou can wait or skip and continue with limited functionality."):
        "設定花費的時間比預期長 — 可能是網路連線較慢。\n您可以等待，或跳過並以有限功能繼續使用。",

    # ── SignTransactionDialog ──
    ("SignTransactionDialog", "Browser opened. Approve the transaction in your wallet. The terminal is waiting on a single-use loopback bridge — this dialog will close automatically when the wallet returns the signature."):
        "瀏覽器已開啟。請在錢包中核准交易。終端正在等待一次性回環橋接 — 當錢包返回簽名後，此對話框將自動關閉。",

    # ── SupportScreen ──
    ("SupportScreen", "Please describe:\n• What were you doing?\n• What did you expect to happen?\n• What actually happened?\n• Steps to reproduce (if applicable)"):
        "請描述：\n• 您當時在做什麼？\n• 您期望發生什麼？\n• 實際發生了什麼？\n• 重現步驟（如適用）",

    # ── SwapPanel ──
    ("SwapPanel", "This pair isn't routable in Phase 2. PumpPortal supports SOL ↔ $FNCPT only; a generalised router lands in Phase 3."):
        "此交易對在第 2 階段無法路由。PumpPortal 僅支援 SOL ↔ $FNCPT；通用路由器將在第 3 階段推出。",

    # ── UpdateService ──
    ("UpdateService", "^(\\d+)\\.(\\d+)\\.(\\d+)$"): "^(\\d+)\\.(\\d+)\\.(\\d+)$",
    ("UpdateService", "Could not reach the update server.\n\n%1"):
        "無法連接更新伺服器。\n\n%1",
    ("UpdateService", "\n…"): "\n…",
    ("UpdateService", "What's new:\n%1\n\n"): "更新內容：\n%1\n\n",
    ("UpdateService", "The installer could not be downloaded.\n\n%1"):
        "安裝程式無法下載。\n\n%1",
    ("UpdateService", "Cannot save the installer to disk:\n%1"):
        "無法將安裝程式儲存至磁碟：\n%1",

    # ── VideoPlayerWidget ──
    ("VideoPlayerWidget", "Qt Multimedia not available.\nBuild with Qt6 Multimedia for inline playback."):
        "Qt Multimedia 不可用。\n請以 Qt6 Multimedia 建構以支援內嵌播放。",

    # ── WebScraperWidget ── (正則保持原樣)
    ("WebScraperWidget", "<table\\b[^>]*>(.*?)</table>"): "<table\\b[^>]*>(.*?)</table>",
    ("WebScraperWidget", "<tr\\b[^>]*>(.*?)</tr>"): "<tr\\b[^>]*>(.*?)</tr>",
    ("WebScraperWidget", "<(t[hd])\\b([^>]*)>(.*?)</\\1>"): "<(t[hd])\\b([^>]*)>(.*?)</\\1>",
    ("WebScraperWidget", "One per line:\nAuthorization: Bearer abc\nX-API-Key: xyz"):
        "每行一個：\nAuthorization: Bearer abc\nX-API-Key: xyz",

    # ── fincept::DockScreenRouter ──
    ("fincept::DockScreenRouter", "DBnomics"): "DBnomics",
    ("fincept::DockScreenRouter", "QuantLib"): "QuantLib",
    ("fincept::DockScreenRouter", "Excel"): "Excel",
}


def main():
    ts_path = sys.argv[1] if len(sys.argv) > 1 else \
        "fincept-qt/translations/fincept_zh_TW.ts"

    tree = ET.parse(ts_path)
    root = tree.getroot()

    filled = 0
    missed = 0
    missing_keys = []

    for ctx in root.findall('context'):
        name = ctx.find('name').text or ''
        for msg in ctx.findall('message'):
            tr = msg.find('translation')
            src = msg.find('source')
            if tr is None or src is None:
                continue
            typ = tr.get('type', '')
            text = (tr.text or '').strip()
            if typ in ('vanished', 'obsolete'):
                continue
            if text:
                continue  # 已有翻譯

            key = (name, src.text or '')
            if key in TRANSLATIONS:
                tr.text = TRANSLATIONS[key]
                # 移除 unfinished 標記
                if 'type' in tr.attrib:
                    del tr.attrib['type']
                filled += 1
            else:
                missed += 1
                missing_keys.append(key)

    # 寫回檔案
    tree.write(ts_path, encoding='unicode', xml_declaration=True)

    print(f"✅ 已填入 {filled} 條翻譯")
    if missed:
        print(f"⚠ 有 {missed} 條未找到對照：")
        for ctx, src in missing_keys:
            preview = src[:60].replace('\n', '\\n')
            print(f"  [{ctx}] {preview}...")


if __name__ == "__main__":
    main()
