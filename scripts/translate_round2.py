#!/usr/bin/env python3
"""第二輪翻譯：處理剩餘的 UI 字串"""
import re

TS_FILE = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts'

# 第二輪翻譯字典
T2 = {
    # 控制面板 / 功能區塊
    "CONTROL PANEL": "控制面板",
    "COMPONENT BROWSER": "元件瀏覽器",
    "CORPORATE FINANCE TOOLKIT": "企業財務工具包",
    "DATA PROVIDERS": "資料供應商",
    "DATA INPUT": "資料輸入",
    "DBNOMICS TERMINAL": "DBnomics 終端機",
    "DEAL TERMS": "交易條款",
    "EXCEL SPREADSHEET": "Excel 試算表",
    "FINCEPT MARITIME INTELLIGENCE": "Fincept 海事情報",
    "FINCEPT TERMINAL": "Fincept 終端機",
    "GENERATOR TYPE": "產生器類型",
    "GEOPOLITICAL RELATIONSHIP NETWORK": "地緣政治關係網路",
    "HDX HUMANITARIAN DATA": "HDX 人道主義資料",
    "INDICATOR SIGNALS": "指標訊號",
    "INDICATOR TYPE": "指標類型",
    "KEY POINTS": "重點摘要",
    "KEYWORD MONITORS": "關鍵字監控",
    "LABEL TYPE": "標籤類型",
    "MARKET DATA": "市場資料",
    "ML LABELS": "ML 標籤",
    "MODULE INFO": "模組資訊",
    "MONITOR MATCHES": "監控匹配",
    "MONTE CARLO": "蒙地卡羅",
    "MY INDICES": "我的指數",
    "MY TRADES": "我的交易",
    "NEARBY INFRASTRUCTURE": "附近基礎設施",
    "OBSERVATION DATA": "觀測資料",
    "PLATFORM STATS": "平台統計",
    "PYTHON NOTEBOOK": "Python 筆記本",
    "RAW DATA": "原始資料",
    "RAW JSON": "原始 JSON",
    "RETURNS ANALYSIS": "報酬分析",
    "RISK CONTRIBUTION": "風險貢獻",
    "RISK MANAGEMENT": "風險管理",
    "RISK OVERVIEW": "風險概覽",
    "RISK SIGNALS": "風險訊號",
    "ROLLING WINDOW": "滾動窗口",
    "SCAN CONDITIONS": "掃描條件",
    "SCAN MARKET": "掃描市場",
    "SCAN RESULTS": "掃描結果",
    "SEARCH AREA": "搜尋區域",
    "SELECTED EVENT": "已選事件",
    "SELECTED ROUTE": "已選航線",
    "SIGNAL GENERATORS": "訊號產生器",
    "SIGNAL MODE": "訊號模式",
    "SPLITTER TYPE": "分割器類型",
    "CV SPLITS": "交叉驗證分割",
    "ENTRY CONDITIONS": "進場條件",
    "EXIT CONDITIONS": "出場條件",
    "POSITION SIZING": "部位大小",
    "STOP ALL": "全部停止",
    "STATUS / ERRORS": "狀態 / 錯誤",

    # 按鈕 / 動作
    "CHECK STATUS": "檢查狀態",
    "COPY URL": "複製 URL",
    "CREATE COMPETITION": "建立競賽",
    "CREATE CUSTOM INDEX": "建立自訂指數",
    "CREATE INDEX": "建立指數",
    "CREATE NEW PORTFOLIO": "建立新投資組合",
    "CREATE NEW POST": "建立新貼文",
    "DELETE ACCOUNT": "刪除帳號",
    "DELETE ALL": "全部刪除",
    "DELETE LIST": "刪除清單",
    "DELETE MY ACCOUNT": "刪除我的帳號",
    "DELETE SEL": "刪除所選",
    "DELETE SELECTED": "刪除已選",
    "Fetch Data": "擷取資料",
    "Full Report": "完整報表",
    "Install / Upgrade Selected": "安裝 / 升級所選",
    "Install Missing": "安裝缺少項目",
    "LOAD SAMPLE": "載入範例",
    "LOAD VESSELS (MUMBAI AREA)": "載入船隻（孟買區域）",
    "OPEN LOG VIEWER": "開啟日誌檢視器",
    "REFRESH:": "重新整理：",
    "RUN ALL": "全部執行",
    "RUN ANALYSIS": "執行分析",
    "RUN BACKTEST": "執行回測",
    "Run Now": "立即執行",
    "SAVE & CONNECT": "儲存並連線",
    "SAVE STRATEGY": "儲存策略",
    "SKIP & CONTINUE": "跳過並繼續",
    "Create & Switch": "建立並切換",
    "Create Model": "建立模型",
    "Create Pipeline": "建立管線",
    "Create Schedule": "建立排程",
    "Deep Analysis": "深度分析",
    "Download && Install": "下載並安裝",
    "Execute Retrain": "執行重新訓練",
    "Evaluate Forecast": "評估預測",
    "Incremental Train": "增量訓練",
    "Process Data": "處理資料",
    "Predict": "預測",
    "Rename": "重新命名",
    "Compare": "比較",

    # 分析方法 / 模型
    "Collar": "Collar 策略",
    "Contribution": "貢獻度",
    "Confidence Intervals": "信賴區間",
    "Covariance": "共變異數",
    "CVaR Optimize": "CVaR 最佳化",
    "Debt Schedule": "負債排程",
    "Decay Weights": "衰減權重",
    "Descriptive": "描述統計",
    "Distribution Fit": "分配擬合",
    "Earnout": "Earnout（績效對價）",
    "Efficient Frontier": "效率前緣",
    "Ensemble": "集成方法",
    "Expression Engine": "表達式引擎",
    "Factor Analysis": "因子分析",
    "Factor Library": "因子庫",
    "Factor Mining": "因子探勘",
    "Factor Quantiles": "因子分位數",
    "Fairness Analysis": "公平性分析",
    "Feature Importance": "特徵重要性",
    "Feature Selection": "特徵選取",
    "Financial Services": "金融服務",
    "Financials": "財務數據",
    "First Chicago": "First Chicago 估值法",
    "Forecast": "預測",
    "Granger Causality": "Granger 因果檢定",
    "Greeks": "Greeks（希臘值）",
    "Healthcare": "醫療保健",
    "Hyperparameter Tuning": "超參數調校",
    "IC Analysis": "IC 分析",
    "IC Metrics": "IC 指標",
    "Indicators": "指標",
    "Industry": "產業",
    "LBO Model": "LBO 模型",
    "LBO Returns": "LBO 報酬",
    "Live Order Book": "即時委託簿",
    "Metrics": "指標",
    "Microstructure": "市場微結構",
    "Model Optimization": "模型最佳化",
    "Model Performance": "模型表現",
    "Model Selection": "模型選擇",
    "Models": "模型",
    "Monte Carlo": "蒙地卡羅",
    "MV Optimize": "均值-變異數最佳化",
    "OLS Regression": "OLS 迴歸",
    "Overview": "概覽",
    "Payment": "付款",
    "Peers": "同業比較",
    "Portfolio Metrics": "投資組合指標",
    "Precedent Txns": "先例交易",
    "Premium Analysis": "溢價分析",
    "Pro Forma": "預估損益",
    "Probabilistic Forecast": "機率預測",
    "Process Quality": "處理品質",
    "Quant Research": "量化研究",
    "Quantile Forecast": "分位數預測",
    "Rank": "排名",
    "Regression": "迴歸分析",
    "Restrictions": "限制條件",
    "Risk Factor": "風險因子",
    "Risk Metrics": "風險指標",
    "Risk Parity": "風險均等",
    "Risk Report": "風險報表",
    "Accretion/Dilution": "增值/稀釋",
    "Exchange Ratio": "換股比率",
    "Calendar": "行事曆",

    # 標籤 / 說明
    "CHART:": "圖表：",
    "COMMISSION (%)": "佣金 (%)",
    "CREDITS: —": "額度：—",
    "Configure — Today P&L": "設定 — 今日損益",
    "Dataset:": "資料集：",
    "ENGINE:": "引擎：",
    "IMO NUMBER": "IMO 編號",
    "LATENCY —": "延遲 —",
    "LOGIC:": "邏輯：",
    "Logic:": "邏輯：",
    "LOOKBACK (DAYS)": "回顧天數",
    "MAX ITERATIONS": "最大迭代次數",
    "NUMBER OF SPLITS": "分割數量",
    "PROVIDERS:": "供應商：",
    "SLIPPAGE (%)": "滑價 (%)",
    "SORT:": "排序：",
    "STEP SIZE": "步長",
    "STOP LOSS (%)": "停損 (%)",
    "STRATEGIES:": "策略：",
    "PROFILE & ACCOUNT": "個人資料與帳號",
    "STORAGE & DATA MANAGEMENT": "儲存與資料管理",
    "Markets & Data": "市場與資料",
    "Economics && Data": "經濟與資料",
    "Research & Intelligence": "研究與情報",
    "AI && Quant": "AI 與量化",
    "M&&A Analytics": "M&A 分析",
    "M&A Analytics": "M&A 分析",
    "M&A ANALYTICS": "M&A 分析",
    "DRAWDOWN & RISK METRICS": "回撤與風險指標",
    "RISK-ADJUSTED RATIOS & WIN/LOSS BREAKDOWN": "風險調整比率與勝負分析",
    "CLASSIFIED // TRADE ROUTE ANALYSIS": "機密 // 貿易航線分析",
    "CLASSIFIED — AUTHORIZED PERSONNEL ONLY": "機密 — 僅限授權人員",
    "Idle": "閒置",
    "Page 1 of 1": "第 1 頁，共 1 頁",
    "NEXT ▶": "下一步 ▶",

    # 長句
    "Drag any symbol here to pin": "拖曳任何代碼至此處以釘選",
    "Calculating Sources & Uses...": "計算資金來源與用途...",
    "Calculates each party's % contribution to the combined entity.":
        "計算各方對合併實體的百分比貢獻。",
    "Chart title (e.g. Strategy vs S&P 500)": "圖表標題（例如：策略 vs S&P 500）",
    "Daily returns (>= 30 values)": "每日報酬（≥ 30 個數值）",
    "Dependent variable y (>= 10 values)": "因變數 y（≥ 10 個數值）",
    "Enter target ticker and comparable tickers (comma-separated):":
        "輸入目標代碼與可比較代碼（以逗號分隔）：",
    "Factor / signal values (decimals, >= 20)": "因子/訊號值（小數，≥ 20）",
    "Fincept managed AI service\\n\\nChange in Settings > LLM Configuration":
        "Fincept 託管 AI 服務\\n\\n在設定 > LLM 設定中變更",
    "Fincept AI": "Fincept AI",
    "Incrementally trained models that update on each new data point.":
        "增量訓練模型，每當有新資料點時自動更新。",
    "Invalid size — must be > 0": "大小無效 — 必須 > 0",
    "LLM profile for this agent. Configure profiles in Settings > LLM Config.":
        "此代理的 LLM 設定檔。在設定 > LLM 設定中配置。",
    "List all available Qlib models (LightGBM, XGBoost, LSTM, Transformer, etc.).":
        "列出所有可用的 Qlib 模型（LightGBM、XGBoost、LSTM、Transformer 等）。",
    "Loading HDX data...": "正在載入 HDX 資料...",
    "MARKET MAKING  —  Avellaneda-Stoikov Model": "造市 — Avellaneda-Stoikov 模型",
    "Model predictions (decimals, >= 10 values)": "模型預測（小數，≥ 10 個數值）",
    "Model predictions (decimals, >= 20 values)": "模型預測（小數，≥ 20 個數值）",
    "Need 2+ holdings for correlation analysis": "需要 2 個以上持股才能進行相關性分析",
    "No LLM provider configured — go to Settings > LLM Configuration":
        "尚未設定 LLM 供應商 — 前往設定 > LLM 設定",
    "No deployments loaded.": "尚未載入部署。",
    "No provider configured — go to Settings > LLM Config":
        "尚未設定供應商 — 前往設定 > LLM 設定",
    "No provider — Settings > LLM Config": "無供應商 — 設定 > LLM 設定",
    "No provider — go to Settings > LLM Config": "無供應商 — 前往設定 > LLM 設定",
    "No schedules configured yet.\\nUse the Create Schedule tab to add one.":
        "尚未設定排程。\\n使用「建立排程」分頁新增。",
    "Numeric values (>= 30). Fits normal, student-t, lognormal (positive only), skewnormal.":
        "數值（≥ 30）。擬合常態、Student-t、對數常態（僅正值）、偏態常態分配。",
    "Numeric values (>= 8). Includes Jarque-Bera + Shapiro-Wilk normality tests.":
        "數值（≥ 8）。包含 Jarque-Bera + Shapiro-Wilk 常態性檢定。",
    "NORMALITY  (H₀: data is normally distributed; p > 0.05 ⇒ cannot reject normal)":
        "常態性（H₀：資料為常態分配；p > 0.05 ⇒ 無法拒絕常態）",
    "NO COMPARISON SLOTS\\nClick  + ADD SLOT  in the left panel to begin":
        "無比較欄位\\n點擊左側面板的 + 新增欄位 開始",
    "One per line:  <asset_id> | <label>": "每行一個：<asset_id> | <label>",
    "One per line:\\nAuthorization: Bearer abc\\nX-API-Key: xyz":
        "每行一個：\\nAuthorization: Bearer abc\\nX-API-Key: xyz",
    "Per-holding contribution to portfolio value, P&L, and risk":
        "各持股對投資組合價值、損益與風險的貢獻",
    "(P&L return proxy, top 6 by weight)": "（損益代理報酬，權重前 6 名）",
    "Realized actuals (>= 5 values)": "實際值（≥ 5 個數值）",
    "Run a backtest to see results": "執行回測以查看結果",
    "Runs all 5 methods with current inputs and returns a consensus range.":
        "以目前輸入執行全部 5 種方法，回傳共識範圍。",
    "SLIPPAGE ESTIMATOR  —  Real Order Book Walk": "滑價估算器 — 實際委託簿模擬",
    "Auto-generated from\\nHeading components.": "從標題元件自動產生。",
    "Ctrl+Enter: RUN  |  Shift+Enter: RUN & NEXT  |  Tab: 4 SPACES  |  Ctrl+S: SAVE":
        "Ctrl+Enter：執行 | Shift+Enter：執行並下一步 | Tab：4 空格 | Ctrl+S：儲存",
    "Qt Multimedia not available.\\nBuild with Qt6 Multimedia for inline playback.":
        "Qt Multimedia 不可用。\\n請以 Qt6 Multimedia 建構以支援內嵌播放。",
    "RD-Agent": "RD-Agent",
    "RD-Agent ready": "RD-Agent 就緒",
    "AIS FEED + FINCEPT API": "AIS 資料流 + Fincept API",
    "NEWS-EVENTS API + HDX": "新聞事件 API + HDX",
    "PYTHON + C++": "Python + C++",
    "QLIB + GS QUANT + PYTHON": "Qlib + GS Quant + Python",
    "1000+ CHINESE & GLOBAL FINANCIAL DATA ENDPOINTS": "1000+ 中國與全球金融資料端點",
    "Content-Type: application/json\\nAccept: application/json":
        "Content-Type: application/json\\nAccept: application/json",
    "IV method:": "隱含波動率方法：",
}


def main():
    with open(TS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed = 0
    for eng, zhtw in T2.items():
        if eng == zhtw:
            continue
        # 精確匹配 <source>eng</source> ... <translation>eng</translation>
        eng_xml = eng.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        zhtw_xml = zhtw.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        eng_escaped = re.escape(eng_xml)

        pattern = f'(<source>{eng_escaped}</source>\\s*<translation[^>]*>){eng_escaped}(</translation>)'
        new_content, n = re.subn(pattern, f'\\g<1>{zhtw_xml}\\2', content)
        if n > 0:
            content = new_content
            fixed += n

    with open(TS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 第二輪翻譯完成：修復 {fixed} 個字串")

    # 統計剩餘
    pairs = re.findall(r'<source>(.*?)</source>\s*<translation[^>]*>(.*?)</translation>', content, re.DOTALL)
    same = 0
    for src, trans in pairs:
        if src.strip() == trans.strip() and re.search(r'[a-zA-Z]{3,}', src):
            same += 1
    print(f"剩餘英文=中文的字串：{same} 個")


if __name__ == '__main__':
    main()
