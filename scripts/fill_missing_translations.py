#!/usr/bin/env python3
"""
自動補齊所有缺失翻譯。

策略：
1. 從 scan_missing.py 的輸出（/tmp/missing_translations.json）讀取缺失清單
2. 用預建的翻譯對照表翻譯
3. 注入 .ts 檔案
4. 處理 XML 特殊字符（& → &amp;）的匹配問題
"""

import re
import json
from pathlib import Path

TS_FILE = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts")

# 翻譯對照表 — 常見 UI 字串
TRANSLATIONS = {
    # --- AuthTypes.h 硬編碼 ---
    "Email is required": "電子郵件為必填",
    "Invalid email format": "電子郵件格式無效",
    
    # --- SettingsScreen ---
    "Apply & Save": "套用並儲存",
    "Create & Switch": "建立並切換",
    "STORAGE & DATA MANAGEMENT": "儲存與資料管理",
    "Storage & Cache": "儲存與快取",
    "Failed Attempts": "失敗次數",
    "PIN lockout engages after 5 consecutive failures.": "連續 5 次失敗後鎖定 PIN。",
    
    # --- SetupScreen ---
    "SKIP & CONTINUE": "跳過並繼續",
    "Welcome to Fincept": "歡迎使用 Fincept",
    
    # --- SwapPanel ---
    "Aborted.": "已中止。",
    "Approve the swap in your wallet to complete the trade.": "在您的錢包中批准交換以完成交易。",
    "Awaiting wallet signature…": "等待錢包簽名…",
    "Confirmed: %1…": "已確認: %1…",
    "Failed.": "失敗。",
    "No confirmation after 60 s. Check Solscan.": "60 秒後未確認。請查看 Solscan。",
    "Re-checking freshness…": "重新檢查最新狀態…",
    "Reverted.": "已回滾。",
    "Sent. Waiting for confirmation…": "已發送。等待確認…",
    "Sign swap": "簽署交換",
    "Simulating…": "模擬中…",
    "Simulation OK ✓ — ready to sign.": "模擬成功 ✓ — 準備簽署。",
    "Simulation failed — swap might revert.": "模擬失敗 — 交換可能回滾。",
    "Swap failed — insufficient balance or slippage too tight.": "交換失敗 — 餘額不足或滑點設定過緊。",
    "Swap signature cancelled.": "交換簽名已取消。",
    "The quote expired while building the transaction. Tap SWAP to re-fetch.": "建立交易時報價已過期。點擊交換以重新獲取。",
    "Token pair not routable in Phase 2 — SOL ↔ $FNCPT only.": "此代幣對在第 2 階段不可路由 — 僅限 SOL ↔ $FNCPT。",
    "Transaction error: %1": "交易錯誤: %1",
    "Unexpected error: %1": "意外錯誤: %1",
    
    # --- LoginScreen / Auth ---
    "Please check your input and try again.": "請確認您的輸入後重試。",
    "Failed to send reset code": "發送重設碼失敗",
    "Failed to fetch plans": "取得方案失敗",
    
    # --- DockScreenRouter / ToolBar ---
    "AI && Quant": "AI 與量化",
    "Economics && Data": "經濟與資料",
    "M&&A Analytics": "併購分析",
    "M&A Analytics": "併購分析",
    "Markets & Data": "市場與資料",
    "Research & Intelligence": "研究與情報",
    "Trading & Portfolio": "交易與投資組合",
    "View Plans & Pricing": "查看方案與定價",
    
    # --- AgentChatPanel ---
    "Active LLM — configure in Settings > LLM Configuration": "使用中的 LLM — 在 設定 > LLM 設定 中配置",
    "No LLM provider configured — go to Settings > LLM Configuration": "未設定 LLM 提供者 — 前往 設定 > LLM 設定",
    
    # --- AgentsViewPanel ---
    "No provider configured — go to Settings > LLM Config": "未設定提供者 — 前往 設定 > LLM 設定",
    
    # --- AiChatScreen ---
    "Active Model — change in Settings > LLM Configuration": "使用中的模型 — 在 設定 > LLM 設定 中變更",
    "Active model — change in Settings > LLM Configuration": "使用中的模型 — 在 設定 > LLM 設定 中變更",
    "Fincept managed AI service\\n\\nChange in Settings > LLM Configuration": "Fincept 託管 AI 服務\\n\\n在 設定 > LLM 設定 中變更",
    
    # --- CodeEditorScreen ---
    "Ctrl+Enter: RUN  |  Shift+Enter: RUN & NEXT  |  Tab: 4 SPACES  |  Ctrl+S: SAVE": "Ctrl+Enter: 執行  |  Shift+Enter: 執行並跳至下一個  |  Tab: 4 空格  |  Ctrl+S: 儲存",
    
    # --- ContactScreen / PrivacyScreen / TermsScreen / TrademarksScreen ---
    "< BACK": "< 返回",
    
    # --- CreateAgentPanel ---
    "LLM profile for this agent. Configure profiles in Settings > LLM Config.": "此代理的 LLM 設定檔。在 設定 > LLM 設定 中配置。",
    "No provider — Settings > LLM Config": "無提供者 — 設定 > LLM 設定",
    
    # --- DataMappingScreen ---
    "API CONFIGURATION & SCHEMA TRANSFORMATION": "API 配置與結構轉換",
    "CACHE & SECURITY SETTINGS": "快取與安全設定",
    "TEST & SAVE": "測試並儲存",
    
    # --- EconomicsView ---
    "Per-holding contribution to portfolio value, P&L, and risk": "每筆持倉對投資組合價值、損益和風險的貢獻",
    
    # --- EquityResearchScreen ---
    "Loading\xe2\x80\xa6": "載入中…",
    
    # --- LlmConfigSection ---
    "Save & Set Active": "儲存並設為使用中",
    "Cannot remove built-in Fincept provider": "無法移除內建的 Fincept 提供者",
    "Failed to save global settings": "儲存全域設定失敗",
    
    # --- MAAnalyticsScreen ---
    "M&A ANALYTICS": "併購分析",
    
    # --- MAModulePanel ---
    "Calculating Sources & Uses...": "計算來源與用途中...",
    "Sources & Uses": "來源與用途",
    
    # --- PortfolioSectorPanel ---
    "(P&L return proxy, top 6 by weight)": "(損益回報近似值，權重前 6 名)",
    
    # --- ProfileScreen ---
    "PROFILE & ACCOUNT": "個人檔案與帳戶",
    
    # --- QuantStatsView ---
    "DRAWDOWN & RISK METRICS": "回撤與風險指標",
    "RISK-ADJUSTED RATIOS & WIN/LOSS BREAKDOWN": "風險調整比率與勝負分析",
    
    # --- ScannerPanel ---
    "SYMBOLS & PARAMETERS": "代碼與參數",
    
    # --- TeamsViewPanel ---
    "No provider — go to Settings > LLM Config": "無提供者 — 前往 設定 > LLM 設定",
    
    # --- TradeAnalysisPanel ---
    "Benefits & Costs": "收益與成本",
    "Benefits & Costs of Trade": "交易的收益與成本",
    
    # --- TradeVizScreen ---
    "<<": "<<",
    ">>": ">>",
    
    # --- UnescoPanel ---
    "Science & Tech": "科學與科技",
    
    # --- WorkflowsViewPanel ---
    "No provider — Settings > LLM Config": "無提供者 — 設定 > LLM 設定",
    
    # --- CryptoBottomPanel ---
    "T&S": "成交明細",
    
    # --- CryptoCredentials ---
    "SAVE & CONNECT": "儲存並連線",
    
    # --- EquityBottomPanel ---
    "TIME & SALES": "成交明細",
    "AI Analysis": "AI 分析",
    
    # --- ActiveLocksPanel ---
    "fincept_lock not deployed — Settings > Lock program ID": "fincept_lock 未部署 — 設定 > Lock program ID",
    
    # --- PolymarketDetailPanel ---
    "Invalid size — must be > 0": "無效數量 — 必須大於 0",
    
    # --- PredictionAccountDialog ---
    "<span style='color:#16a34a'>Kalshi credentials saved.</span>": "<span style='color:#16a34a'>Kalshi 憑證已儲存。</span>",
    "<span style='color:#16a34a'>Polymarket credentials saved.</span>": "<span style='color:#16a34a'>Polymarket 憑證已儲存。</span>",
    "<span style='color:#dc2626'>%1 does not look like a PEM file.</span>": "<span style='color:#dc2626'>%1 看起來不是 PEM 檔案。</span>",
    "<span style='color:#dc2626'>Both API Key ID and PEM private key are required.</span>": "<span style='color:#dc2626'>需要 API Key ID 和 PEM 私鑰。</span>",
    "<span style='color:#dc2626'>Could not read %1.</span>": "<span style='color:#dc2626'>無法讀取 %1。</span>",
    "<span style='color:#dc2626'>Private key is required.</span>": "<span style='color:#dc2626'>需要私鑰。</span>",
    "<span style='color:#dc2626'>Private key must be a PEM-encoded RSA key.</span>": "<span style='color:#dc2626'>私鑰必須為 PEM 編碼的 RSA 金鑰。</span>",
    "<span style='color:#dc2626'>Private key should be 0x + 64 hex chars.</span>": "<span style='color:#dc2626'>私鑰應為 0x + 64 個十六進位字元。</span>",
    "<span style='color:#dc2626'>Save failed — see logs.</span>": "<span style='color:#dc2626'>儲存失敗 — 請查看日誌。</span>",
    
    # --- PolymarketPriceWidget ---
    "One per line:  <asset_id> | <label>": "每行一個:  <asset_id> | <label>",
    
    # --- TodayPnLWidget ---
    "Configure — Today P&L": "設定 — 今日損益",
    
    # --- UpdateService ---
    "<none>": "<無>",
    "Download && Install": "下載並安裝",
    
    # --- CommandBar ---
    "> Enter Command or /type ...": "> 輸入指令或 /type ...",
    
    # --- AkShareScreen ---
    "1000+ CHINESE & GLOBAL FINANCIAL DATA ENDPOINTS": "1000+ 中國與全球金融數據端點",
    
    # --- PythonSetupManager ---
    "Failed to download UV": "下載 UV 失敗",
    "Failed to install Python": "安裝 Python 失敗",
    "Failed to create virtual environments": "建立虛擬環境失敗",
    
    # --- PythonEnvSection ---
    "Loading...": "載入中...",
    "Package": "套件",
    "Venv": "虛擬環境",
    "Required": "必要",
    "Installed": "已安裝",
    "Status": "狀態",
    "Action": "操作",
    
    # --- McpServersSection ---
    "Error": "錯誤",
    
    # --- QuantModulePanel (通用) ---
    "JSON parameters (optional)\\ne.g. {ticker:AAPL}": "JSON 參數（選填）\\n例如 {ticker:AAPL}",
    "No schedules configured yet.\\nUse the Create Schedule tab to add one.": "尚未配置排程。\\n使用「建立排程」分頁新增。",
    "LOAD SAMPLE": "載入範例",
    
    # --- QuantModulePanel_Gluonts ---
    "Distribution Fit": "分佈擬合",
    "Evaluate Forecast": "評估預測",
    "FORECAST BY STEP": "逐步預測",
    "GluonTS backend ready": "GluonTS 後端就緒",
    "0.05, 0.25, 0.5, 0.75, 0.95": "0.05, 0.25, 0.5, 0.75, 0.95",
    "Lower band (optional, same length as actuals)": "下限帶（選填，與實際值等長）",
    "Point forecast (same length as actuals)": "點預測（與實際值等長）",
    "PER-QUANTILE SUMMARY": "分位數摘要",
    
    # --- QuantModulePanel_Misc (部分常見) ---
    "  ASKS": "  賣出",
    "  BIDS": "  買入",
    "Analyzing...": "分析中...",
    "Backtest": "回測",
    "BTC/USDT": "BTC/USDT",
    "Asset names (comma-separated)": "資產名稱（逗號分隔）",
    "Asset names (comma-separated, e.g. AAPL,GOOG,MSFT)": "資產名稱（逗號分隔，例如 AAPL,GOOG,MSFT）",
    
    # --- QuantModulePanel_QuantReporting ---
    "Cumulative Returns": "累計回報",
    "Factor Quantiles": "因子分位數",
    "IC Analysis": "IC 分析",
    "Model": "模型",
    "Model Performance": "模型表現",
    
    # --- QuantModulePanel_RL ---
    "AAPL": "AAPL",
    "Training RL Agent...": "訓練 RL 代理中...",
    "step 0 / — · reward — · loss —": "步驟 0 / — · 獎勵 — · 損失 —",
    
    # --- QuantModulePanel_Statsmodels ---
    "ACF / PACF": "ACF / PACF",
    "ARIMA": "ARIMA",
    "Descriptive": "描述性統計",
    "Granger Causality": "格蘭傑因果",
}

# 額外批量翻譯 - 量化模組字串（技術參數保持原文或簡單翻譯）
QUANT_TRANSLATIONS = {
    "Actual returns (comma-separated)": "實際回報（逗號分隔）",
    "Asset returns matrix JSON: [[0.01,-0.02,...],[...]]": "資產回報矩陣 JSON: [[0.01,-0.02,...],[...]]",
    "Automatically select the best model from a set of candidates.": "從候選模型中自動選擇最佳模型。",
    "Benchmark returns (optional; same length as portfolio if provided)": "基準回報（選填；如提供則需與投資組合等長）",
    "Chart title (e.g. Strategy vs S&P 500)": "圖表標題（例如 策略 vs S&P 500）",
    "Daily returns (>= 30 values)": "日回報（>= 30 個值）",
    "Factor / signal values (decimals, >= 20)": "因子/信號值（小數，>= 20 個）",
    "Dependent variable y (>= 10 values)": "因變量 y（>= 10 個值）",
    "Effect series y (the one we ask: 'is this caused by x?')": "效果序列 y（我們想問的：「這是由 x 引起的嗎？」）",
    "Numeric values (e.g. 10.5, 11.2, 9.8, 12.1, ...). Need at least 2.": "數值（例如 10.5, 11.2, 9.8, 12.1, ...）。至少需要 2 個。",
    "Numeric values (>= 30). Fits normal, student-t, lognormal (positive only), skewnormal.": "數值（>= 30 個）。擬合常態、t 分佈、對數常態（僅正值）、偏態常態。",
    "Portfolio": "投資組合",
    "Portfolio daily returns (decimals, same length as benchmark)": "投資組合日回報（小數，與基準等長）",
    "Risk Metrics": "風險指標",
    "ADF (H₀: unit root → non-stationary)": "ADF（H₀: 單位根 → 非定態）",
    "KPSS (H₀: stationary)": "KPSS（H₀: 定態）",
    "NORMALITY  (H₀: data is normally distributed; p > 0.05 ⇒ cannot reject normal)": "常態性（H₀: 資料為常態分佈；p > 0.05 ⇒ 無法拒絕常態）",
}

TRANSLATIONS.update(QUANT_TRANSLATIONS)

def escape_xml(s: str) -> str:
    """轉換特殊字元為 XML 實體"""
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace("'", '&apos;')
    return s

def main():
    print("=" * 60)
    print("自動補齊缺失翻譯")
    print("=" * 60)
    
    # 讀取缺失清單
    with open('/tmp/missing_translations.json') as f:
        missing = json.load(f)
    
    total_missing = sum(len(v) for v in missing.values())
    print(f"📋 缺失: {len(missing)} 個 context, {total_missing} 條字串")
    
    # 讀取 .ts 檔案
    content = TS_FILE.read_text(encoding='utf-8')
    
    added = 0
    skipped = 0
    
    for ctx_name, sources in sorted(missing.items()):
        new_msgs = []
        for source in sources:
            # 查翻譯對照表
            translation = TRANSLATIONS.get(source)
            if not translation:
                # 嘗試去除 XML encoding 差異
                decoded = source.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                translation = TRANSLATIONS.get(decoded)
            
            if translation:
                new_msgs.append((source, translation))
                added += 1
            else:
                skipped += 1
        
        if not new_msgs:
            continue
        
        # 找到 context block 並在結尾前插入新 message
        ctx_pattern = rf'(<context>\s*<name>{re.escape(ctx_name)}</name>)(.*?)(</context>)'
        match = re.search(ctx_pattern, content, re.DOTALL)
        
        if match:
            # 在已有 context 中追加
            before = match.group(1)
            body = match.group(2)
            after = match.group(3)
            
            insert_lines = []
            for source, translation in new_msgs:
                # 處理 XML 特殊字元
                xml_source = escape_xml(source)
                xml_translation = escape_xml(translation)
                insert_lines.append(f'    <message>\n        <source>{xml_source}</source>\n        <translation>{xml_translation}</translation>\n    </message>')
            
            new_body = body.rstrip() + '\n' + '\n'.join(insert_lines) + '\n'
            new_block = before + new_body + after
            content = content[:match.start()] + new_block + content[match.end():]
        else:
            # context 不存在，在 </TS> 前插入整個 context
            insert_lines = [f'<context>', f'    <name>{ctx_name}</name>']
            for source, translation in new_msgs:
                xml_source = escape_xml(source)
                xml_translation = escape_xml(translation)
                insert_lines.append(f'    <message>\n        <source>{xml_source}</source>\n        <translation>{xml_translation}</translation>\n    </message>')
            insert_lines.append('</context>')
            
            insert_point = content.rfind('</TS>')
            content = content[:insert_point] + '\n'.join(insert_lines) + '\n' + content[insert_point:]
    
    # 寫入
    TS_FILE.write_text(content, encoding='utf-8')
    
    print(f"\n✅ 完成!")
    print(f"  已翻譯: {added}")
    print(f"  跳過（無翻譯）: {skipped}")
    print(f"  檔案: {TS_FILE}")

if __name__ == '__main__':
    main()
