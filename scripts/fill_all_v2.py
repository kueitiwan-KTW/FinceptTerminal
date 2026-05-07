#!/usr/bin/env python3
"""
全量翻譯補齊 v2 — 包含所有量化模組。
直接從 C++ 提取全部 tr()，對照 .ts，缺什麼補什麼。
"""

import re
from pathlib import Path
from collections import defaultdict

SRC_DIR = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/src")
TS_FILE = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts")

def escape_xml(s: str) -> str:
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace("'", '&apos;')
    return s

def unescape_xml(s: str) -> str:
    s = s.replace('&amp;', '&')
    s = s.replace('&lt;', '<')
    s = s.replace('&gt;', '>')
    s = s.replace('&apos;', "'")
    return s

def load_binary_contexts():
    mapping = {}
    with open('/tmp/binary_contexts.txt') as f:
        for line in f:
            ctx = line.strip()
            if ctx and '::' in ctx:
                short = ctx.split('::')[-1]
                mapping[short] = ctx
    return mapping

def extract_tr_from_cpp():
    binary_ns = load_binary_contexts()
    results = defaultdict(set)
    
    for cpp in SRC_DIR.rglob("*.cpp"):
        content = cpp.read_text(encoding='utf-8', errors='ignore')
        class_name = cpp.stem
        ns_ctx = binary_ns.get(class_name, class_name)
        
        for match in re.finditer(r'\btr\(\s*"((?:[^"\\]|\\.)*)"\s*\)', content):
            source = match.group(1)
            if source.strip() and len(source.strip()) > 1:
                results[ns_ctx].add(source)
    
    return results

def get_existing_sources():
    """取得 {context: {source_escaped, ...}}"""
    content = TS_FILE.read_text(encoding='utf-8')
    existing = defaultdict(set)
    
    for match in re.finditer(r'<context>\s*<name>(.*?)</name>(.*?)</context>', content, re.DOTALL):
        ctx = match.group(1)
        body = match.group(2)
        for msg in re.finditer(r'<source>(.*?)</source>', body, re.DOTALL):
            src_escaped = msg.group(1)
            existing[ctx].add(src_escaped)
            existing[ctx].add(unescape_xml(src_escaped))
    
    return existing

# 超大翻譯表
TRANSLATIONS = {
    # === 量化模組 (QuantModulePanel_Misc) ===
    "  ASKS": "  賣出",
    "  BIDS": "  買入",
    "Actual returns (comma-separated)": "實際回報（逗號分隔）",
    "Analyzing...": "分析中...",
    "Asset names (comma-separated)": "資產名稱（逗號分隔）",
    "Asset names (comma-separated, e.g. AAPL,GOOG,MSFT)": "資產名稱（逗號分隔，例如 AAPL,GOOG,MSFT）",
    "Asset returns matrix JSON: [[0.01,-0.02,...],[...]]": "資產回報矩陣 JSON: [[0.01,-0.02,...],[...]]",
    "Automatically select the best model from a set of candidates.": "從候選模型中自動選擇最佳模型。",
    "BTC/USDT": "BTC/USDT",
    "Backtest": "回測",
    "Benchmark returns (optional; same length as portfolio if provided)": "基準回報（選填；如提供則需與投資組合等長）",
    "Building depth snapshot…": "建構深度快照…",
    "CLOSE": "收盤",
    "Calculating…": "計算中…",
    "Candles per chart: 30–500": "每圖K線數: 30–500",
    "Cause series x (the one we hypothesize as driver)": "因果序列 x（我們假設為驅動因素的序列）",
    "Comma-separated (e.g. AAPL,GOOG,MSFT)": "逗號分隔（例如 AAPL,GOOG,MSFT）",
    "Comma-separated numeric returns": "逗號分隔的數值回報",
    "Comma-separated numeric returns (e.g. 0.05,-0.03,0.01,…)": "逗號分隔的數值回報（例如 0.05,-0.03,0.01,…）",
    "Comma-separated numbers (prices, returns, etc.)": "逗號分隔的數字（價格、回報等）",
    "Comma-separated values": "逗號分隔的值",
    "Comma-separated values (e.g. 0.05,-0.03,0.01,…)": "逗號分隔的值（例如 0.05,-0.03,0.01,…）",
    "Confidence level (0–1, e.g. 0.95)": "信賴水準（0–1，例如 0.95）",
    "Connected to %1.  Streaming %2 live.": "已連線至 %1。串流 %2 即時資料。",
    "Copy full text": "複製全文",
    "Daily PnL": "每日損益",
    "Daily returns (comma-separated)": "日回報（逗號分隔）",
    "Daily returns (comma-separated, e.g. 0.01,-0.02,0.015,…)": "日回報（逗號分隔，例如 0.01,-0.02,0.015,…）",
    "Disconnected.": "已斷線。",
    "EMA fast / slow / signal (defaults: 12 / 26 / 9)": "EMA 快/慢/信號（預設: 12 / 26 / 9）",
    "ERROR": "錯誤",
    "Efficient Frontier": "效率前緣",
    "End date (YYYY-MM-DD)": "結束日期 (YYYY-MM-DD)",
    "Estimated alpha": "估計 Alpha",
    "Expected returns (comma-sep, e.g. 0.08,0.12,0.06)": "預期回報（逗號分隔，例如 0.08,0.12,0.06）",
    "Fee per trade (e.g. 0.001 = 0.1%)": "每筆交易費用（例如 0.001 = 0.1%）",
    "Fit-lines overlay (least-squares)": "擬合線覆蓋（最小平方法）",
    "Forecast steps": "預測步數",
    "Frequency: daily, weekly, monthly (default: daily)": "頻率: daily, weekly, monthly（預設: daily）",
    "Generating chart…": "產生圖表…",
    "HIGH": "最高",
    "Historical window in days (default 252)": "歷史視窗天數（預設 252）",
    "Hold days (optional int; default = hold to end)": "持有天數（選填整數；預設 = 持有至結束）",
    "Initial capital ($)": "初始資金 ($)",
    "LOW": "最低",
    "Lag (max lags for Granger, ≥ 1)": "延遲（格蘭傑最大延遲數，≥ 1）",
    "Lookback (comma-separated days, e.g. 30,60,90)": "回溯（逗號分隔天數，例如 30,60,90）",
    "MAX DRAWDOWN": "最大回撤",
    "Max lags (positive integer; default 20)": "最大延遲（正整數；預設 20）",
    "Min variance / Max Sharpe / Equal-weight": "最小變異/最大夏普/等權重",
    "NO DATA": "無資料",
    "No data yet.": "尚無資料。",
    "Numeric values (e.g. 10.5, 11.2, 9.8, 12.1, ...). Need at least 2.": "數值（例如 10.5, 11.2, 9.8, 12.1, ...）。至少需要 2 個。",
    "Numeric values (>= 30). Fits normal, student-t, lognormal (positive only), skewnormal.": "數值（>= 30 個）。擬合常態、t 分佈、對數常態（僅正值）、偏態常態。",
    "OPEN": "開盤",
    "OHLCV data or signals": "OHLCV 資料或信號",
    "Optimize Portfolio": "最佳化投資組合",
    "Paired observations y (same length as x)": "配對觀測值 y（與 x 等長）",
    "Plot Correlation": "繪製相關性",
    "Plot Drawdown": "繪製回撤",
    "Plot Factor Returns": "繪製因子回報",
    "Portfolio": "投資組合",
    "Portfolio daily returns (decimals, same length as benchmark)": "投資組合日回報（小數，與基準等長）",
    "Ready": "就緒",
    "Return series (numeric, comma-separated, e.g. 0.01,-0.02,0.005,…)": "回報序列（數值，逗號分隔，例如 0.01,-0.02,0.005,…）",
    "Risk Metrics": "風險指標",
    "Run Backtest": "執行回測",
    "Run Forecast": "執行預測",
    "Run Monte Carlo": "執行蒙特卡洛",
    "Run OLS": "執行 OLS",
    "Run Test": "執行測試",
    "SYMBOL": "代碼",
    "Sample data (comma-separated)": "範例資料（逗號分隔）",
    "Sample observations x (≥ 20 values)": "樣本觀測值 x（≥ 20 個值）",
    "Scatter + Regression": "散佈圖 + 迴歸",
    "Short MA window (int)": "短期 MA 視窗（整數）",
    "Signals/returns for regime: comma-separated": "信號/回報（區間制：逗號分隔）",
    "Start date (YYYY-MM-DD)": "開始日期 (YYYY-MM-DD)",
    "Stop-loss (fraction, e.g. 0.02 = 2%)": "停損（比率，例如 0.02 = 2%）",
    "Streaming %1 tickers…": "串流 %1 個代碼…",
    "Streaming active – close to disconnect.": "串流進行中 — 關閉以斷線。",
    "TARGET": "目標",
    "Target return (annual, 0–1)": "目標回報（年化，0–1）",
    "Ticker / pair  e.g. AAPL or BTC/USDT": "代碼/交易對，例如 AAPL 或 BTC/USDT",
    "Ticker/pair": "代碼/交易對",
    "Tickers (comma-separated, e.g. AAPL,GOOG,MSFT)": "代碼（逗號分隔，例如 AAPL,GOOG,MSFT）",
    "Time Series": "時間序列",
    "Trading days (default 252)": "交易天數（預設 252）",
    "VOLUME": "成交量",
    "Variates (comma-separated, e.g. 1.2,3.4,5.6)": "變量（逗號分隔，例如 1.2,3.4,5.6）",
    "Weights (comma-sep, e.g. 0.4,0.3,0.3)": "權重（逗號分隔，例如 0.4,0.3,0.3）",
    "Window (periods)": "視窗（期數）",
    "Window size (rolling correlation)": "視窗大小（滾動相關性）",
    "corr": "相關性",
    "ols": "OLS",
    "pair_corr": "配對相關",
    "scatter": "散佈圖",
    "rolling_corr": "滾動相關",
    "heatmap": "熱力圖",
    "frontier": "前緣",
    "mean_var": "均值-變異",
    "scenario": "情境",
    "risk_parity": "風險平價",
    "backtest": "回測",
    "montecarlo": "蒙特卡洛",
    "Long MA window (int, > short)": "長期 MA 視窗（整數，> 短期）",
    "forecast": "預測",
    "adf_kpss": "ADF/KPSS",
    "acf_pacf": "ACF/PACF",
    "granger": "格蘭傑",
    "normality": "常態性",
    "descriptive": "描述性",
    "arima": "ARIMA",
    "var": "VaR",
    "cvar": "CVaR",
    "sharpe": "夏普",
    "max_drawdown": "最大回撤",
    "Simulations (100–10000)": "模擬次數（100–10000）",
    "Num. regimes (integer ≥ 2)": "區間數（整數 ≥ 2）",
    "dist_fit": "分佈擬合",
    "regime": "區間",
    "vol_surface": "波動率曲面",
    "eval_forecast": "評估預測",
    "gluonts_forecast": "GluonTS 預測",
    "rl_train": "RL 訓練",
    
    # === QuantModulePanel_Gluonts ===
    "0.05, 0.25, 0.5, 0.75, 0.95": "0.05, 0.25, 0.5, 0.75, 0.95",
    "Distribution Fit": "分佈擬合",
    "Evaluate Forecast": "評估預測",
    "FORECAST BY STEP": "逐步預測",
    "GluonTS backend ready": "GluonTS 後端就緒",
    "Lower band (optional, same length as actuals)": "下限帶（選填，與實際值等長）",
    "Point forecast (same length as actuals)": "點預測（與實際值等長）",
    "PER-QUANTILE SUMMARY": "分位數摘要",
    "Actual values (comma-separated numeric, ≥ 30)": "實際值（逗號分隔數值，≥ 30 個）",
    "Context length (int, default = series_len × 0.8)": "上下文長度（整數，預設 = 序列長度 × 0.8）",
    "Custom quantiles (comma-separated, 0–1)": "自訂分位數（逗號分隔，0–1）",
    "Prediction length (int, default = remaining 20%)": "預測長度（整數，預設 = 剩餘 20%）",
    "Quantile band (0–1)": "分位數帶（0–1）",
    "Upper band (optional, same length as actuals)": "上限帶（選填，與實際值等長）",
    "median_step_error": "中位數步驟誤差",
    "Model type: DeepAR, TFT, SimpleFeedForward, PatchTST": "模型類型: DeepAR, TFT, SimpleFeedForward, PatchTST",
    "fit_distribution": "擬合分佈",
    
    # === QuantModulePanel_QuantReporting ===
    "Chart title (e.g. Strategy vs S&P 500)": "圖表標題（例如 策略 vs S&P 500）",
    "Cumulative Returns": "累計回報",
    "Daily returns (>= 30 values)": "日回報（>= 30 個值）",
    "Factor / signal values (decimals, >= 20)": "因子/信號值（小數，>= 20 個）",
    "Factor Quantiles": "因子分位數",
    "IC Analysis": "IC 分析",
    "LOAD SAMPLE": "載入範例",
    "Model": "模型",
    "Model Performance": "模型表現",
    "Predicted values (decimals, same length as actual)": "預測值（小數，與實際值等長）",
    "Predictions (same length as labels)": "預測（與標籤等長）",
    "Quantile Buckets": "分位數分桶",
    "Strategy returns (comma-separated decimals, >= 30)": "策略回報（逗號分隔小數，>= 30 個）",
    "True 0/1 labels (comma-separated, same count)": "真實 0/1 標籤（逗號分隔，數量相同）",
    "cumulative": "累計",
    "ic": "IC",
    "factor_quantiles": "因子分位數",
    "perf": "表現",
    "confusion": "混淆",
    
    # === QuantModulePanel_RL ===
    "AAPL": "AAPL",
    "Training RL Agent...": "訓練 RL 代理中...",
    "step 0 / — · reward — · loss —": "步驟 0 / — · 獎勵 — · 損失 —",
    
    # === QuantModulePanel_Statsmodels ===
    "ACF / PACF": "ACF / PACF",
    "ADF (H₀: unit root → non-stationary)": "ADF（H₀: 單位根 → 非定態）",
    "ARIMA": "ARIMA",
    "Dependent variable y (>= 10 values)": "因變量 y（>= 10 個值）",
    "Descriptive": "描述性統計",
    "Effect series y (the one we ask: 'is this caused by x?')": "效果序列 y（我們想問的：「這是由 x 引起的嗎？」）",
    "Granger Causality": "格蘭傑因果",
    "KPSS (H₀: stationary)": "KPSS（H₀: 定態）",
    "NORMALITY  (H₀: data is normally distributed; p > 0.05 ⇒ cannot reject normal)": "常態性（H₀: 資料為常態分佈；p > 0.05 ⇒ 無法拒絕常態）",
    "Observations (numeric, comma-separated)": "觀測值（數值，逗號分隔）",
    "One value per line or comma-separated (≥ 30)": "每行一個值或逗號分隔（≥ 30 個）",
    "Order (p,d,q) e.g. 1,1,1": "階數 (p,d,q) 例如 1,1,1",
    "Seasonal order (P,D,Q,m) e.g. 1,1,1,12": "季節階數 (P,D,Q,m) 例如 1,1,1,12",
    "Time series values (numeric, comma-sep, ≥ 30)": "時間序列值（數值，逗號分隔，≥ 30 個）",
    "X values (independent, >= 10)": "X 值（自變量，>= 10 個）",
    
    # === QuantModulePanel_VolSurface ===
    "Expiry date": "到期日",
    "Option chain": "選擇權鏈",
    "Spot price": "現貨價格",
    "Strike prices": "履約價",
    "IV values": "隱含波動率值",
    "vol_smile": "波動率微笑",
    "term_structure": "期限結構",
    "surface_3d": "3D 曲面",
    
    # === EquityBottomPanel 缺漏 ===
    "AI Analysis": "AI 分析",
    "TIME & SALES": "成交明細",
    
    # === DataMappingScreen ===
    "Field": "欄位",
    "Type": "類型",
    "Description": "描述",
    
    # === SettingsScreen 額外 ===
    "Trace": "追蹤",
    "Debug": "除錯",
    "Info": "資訊",
    "Warn": "警告",
    "Fatal": "嚴重",
    
    # === 通用符號/極短 ===
    "\u2315": "\u2315",  # ⌕ 搜尋符號
    "\u25C6": "\u25C6",  # ◆ 菱形符號
    "\u2191 ": "\u2191 ",  # ↑
    "\u2191 0 B/s": "\u2191 0 B/s",
    "\u2193 ": "\u2193 ",  # ↓
    "\u2193 0 B/s": "\u2193 0 B/s",
    "\xe2\x80\x94": "—",
    "Loading\xe2\x80\xa6": "載入中…",
    
    # === WebScraperWidget (regex 不需翻譯) ===
    "<(t[hd])\\\\b([^>]*)>(.*?)</\\\\1>": "<(t[hd])\\\\b([^>]*)>(.*?)</\\\\1>",
    "<caption[^>]*>(.*?)</caption>": "<caption[^>]*>(.*?)</caption>",
    "<table\\\\b[^>]*>(.*?)</table>": "<table\\\\b[^>]*>(.*?)</table>",
    "<tr\\\\b[^>]*>(.*?)</tr>": "<tr\\\\b[^>]*>(.*?)</tr>",
    "auto (from Content-Type / <meta>)": "自動（從 Content-Type / <meta> 偵測）",
    "<%1> × %2": "<%1> × %2",
    
    # === 其餘 ===
    "> Enter Command or /type ...": "> 輸入指令或 /type ...",
    "< BACK": "< 返回",
    "<<": "<<",
    ">>": ">>",
    "<none>": "<無>",
    "Download && Install": "下載並安裝",
}

def main():
    print("=" * 60)
    print("全量翻譯補齊 v2")
    print("=" * 60)
    
    # 提取 C++ tr()
    all_tr = extract_tr_from_cpp()
    existing = get_existing_sources()
    
    # 找缺失
    to_add = defaultdict(list)
    for ctx, sources in all_tr.items():
        for src in sources:
            xml_escaped = escape_xml(src)
            if ctx in existing:
                if src in existing[ctx] or xml_escaped in existing[ctx]:
                    continue
            
            # 查翻譯表
            trans = TRANSLATIONS.get(src)
            if trans:
                to_add[ctx].append((src, trans))
    
    total = sum(len(v) for v in to_add.values())
    print(f"📋 需注入: {len(to_add)} 個 context, {total} 條")
    
    if total == 0:
        print("✅ 已全部覆蓋！")
        return
    
    # 注入到 .ts
    content = TS_FILE.read_text(encoding='utf-8')
    
    added = 0
    for ctx_name, pairs in sorted(to_add.items()):
        # 先構造要插入的 XML
        msg_blocks = []
        for source, translation in sorted(pairs):
            xml_src = escape_xml(source)
            xml_trl = escape_xml(translation)
            msg_blocks.append(f'    <message>\n        <source>{xml_src}</source>\n        <translation>{xml_trl}</translation>\n    </message>')
        
        # 找到 context block
        ctx_pattern = rf'(<context>\s*<name>{re.escape(ctx_name)}</name>)(.*?)(</context>)'
        match = re.search(ctx_pattern, content, re.DOTALL)
        
        if match:
            before = match.group(1)
            body = match.group(2)
            after = match.group(3)
            new_body = body.rstrip() + '\n' + '\n'.join(msg_blocks) + '\n'
            content = content[:match.start()] + before + new_body + after + content[match.end():]
        else:
            # 不存在，新建 context
            new_ctx = f'<context>\n    <name>{ctx_name}</name>\n' + '\n'.join(msg_blocks) + '\n</context>'
            insert_point = content.rfind('</TS>')
            content = content[:insert_point] + new_ctx + '\n' + content[insert_point:]
        
        added += len(pairs)
    
    TS_FILE.write_text(content, encoding='utf-8')
    
    print(f"\n✅ 注入完成!")
    print(f"  新增: {added} 條")
    print(f"  檔案: {TS_FILE}")

if __name__ == '__main__':
    main()
