#!/usr/bin/env python3
"""第三輪翻譯：剩餘 UI 字串"""
import re

TS_FILE = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts'

T3 = {
    "STRATEGY DEFINITION": "策略定義",
    "STRESS TEST": "壓力測試", "Stress Test": "壓力測試",
    "SYMBOLS & PARAMETERS": "代碼與參數",
    "SYMBOLS (comma or newline separated)": "代碼（以逗號或換行分隔）",
    "SYSTEM STATUS": "系統狀態",
    "Save & Set Active": "儲存並啟用",
    "Scan Days:": "掃描天數：",
    "Schedules": "排程",
    "Schema:": "結構：",
    "Science & Tech": "科學與科技",
    "Scorecard": "計分卡",
    "Seasonal Naive": "季節性樸素法",
    "Seasonality": "季節性",
    "Select a deployment to view curve": "選取部署以檢視曲線",
    "Select an article": "選取文章",
    "Send  ↑": "送出 ↑",
    "Sensitivity": "敏感度分析",
    "Sensitivity analysis varies entry multiple and exit multiple around base case.":
        "敏感度分析在基準情境周圍變動進場倍數與出場倍數。",
    "Sentiment": "情緒分析",
    "Session error — please restart.": "工作階段錯誤 — 請重新啟動。",
    "Sheet1": "工作表1",
    "Show Raw JSON": "顯示原始 JSON",
    "Signal Data": "訊號資料",
    "Slippage Estimator": "滑價估算器",
    "Sources & Uses": "資金來源與用途",
    "Spot: —": "現貨：—",
    "Stationarity": "定態性",
    "Statistics": "統計",
    "Status:": "狀態：",
    "Synergies": "綜效",
    "T&S": "成交明細",
    "TAKE PROFIT (%)": "停利 (%)",
    "TEST & SAVE": "測試並儲存",
    "THREAT: LOW": "威脅：低",
    "TIME & SALES": "成交明細",
    "TOP CATEGORIES": "熱門分類",
    "TOP STORIES": "頭條新聞",
    "TOPIC:": "主題：",
    "TOXIC FLOW DETECTION  —  PIN Score Model": "毒性流動偵測 — PIN 分數模型",
    "TRADE CORRIDORS": "貿易走廊",
    "TRADE GEOPOLITICS ANALYSIS": "貿易地緣政治分析",
    "TRAIN RATIO": "訓練比例",
    "Task Monitor": "任務監控",
    "Technicals": "技術面",
    "Technology": "科技",
    "Trading & Portfolio": "交易與投資組合",
    "Trading Blocs": "貿易集團",
    "Trading Comps": "交易比較",
    "Train Model": "訓練模型",
    "Upgrade All": "全部升級",
    "VC Method": "VC 估值法",
    "VESSEL SEARCH": "船隻搜尋",
    "VESSEL TRACKING — AIS FEED": "船隻追蹤 — AIS 資料流",
    "VIEW RAW RESPONSE": "檢視原始回應",
    "VOYAGE HISTORY": "航程歷史",
    "View Plans & Pricing": "查看方案與定價",
    "Voice mode active": "語音模式啟用中",
    "WINDOW LENGTH": "窗口長度",
    "IMPORT CSV": "匯入 CSV",
    "CATEGORY:": "分類：",
    "COMP:": "元件：",
    "INSTRUMENT:": "商品：",
    "INTERVAL:": "間隔：",
    "MODULE:": "模組：",
    "REGION:": "區域：",
    "SOURCE:": "來源：",
    "Error:": "錯誤：",
    "Fields:": "欄位：",
    "From:": "來源：",
    "Installing to:": "安裝至：",
    "Rebind:": "重新綁定：",
    "Report:": "報表：",
    "VIEW:": "檢視：",
    "IMO:": "IMO：",
    "◀ PREV": "◀ 上一步",
    "■ Stop": "■ 停止",
    "not configured": "尚未設定",
    "hidden": "已隱藏",
    "datasets": "資料集",
    "market": "市場",
    "[ERROR]": "[錯誤]",
    "[THINK]": "[思考中]",
    "Content-Length:": "內容長度：",
    "Content-Type:": "內容類型：",
    "Date:": "日期：",
    "Sort:": "排序：",
    "Mode:": "模式：",
    "auto (from Content-Type / <meta>)": "自動（從 Content-Type / <meta> 偵測）",
    "strategy builder · backtesting · live deployment": "策略建構器 · 回測 · 即時部署",
    "fincept_lock not deployed — Settings > Lock program ID":
        "fincept_lock 尚未部署 — 設定 > Lock 程式 ID",
    "Tickers (comma-separated, >= 2). Returns fetched via Yahoo Finance.":
        "代碼（逗號分隔，≥ 2 個）。報酬經由 Yahoo Finance 擷取。",
    "Time series values (>= 20)": "時間序列值（≥ 20）",
    "Time series values (>= 20). Used for ARIMA(p,q) order selection.":
        "時間序列值（≥ 20）。用於 ARIMA(p,q) 階數選擇。",
    "Time series values (>= 24). Period auto-detected if left at 0.":
        "時間序列值（≥ 24）。週期設為 0 時自動偵測。",
    "Time series values (>= 30)": "時間序列值（≥ 30）",
    "Time series values (>= 30). CSV, space, or newline separated.":
        "時間序列值（≥ 30）。以 CSV、空格或換行分隔。",
    "Series values (>= 1). Forecast = repeat last `season_length` observations.":
        "序列值（≥ 1）。預測 = 重複最後 season_length 個觀測值。",
    "Series values (>= 30)": "序列值（≥ 30）",
    "Series values (>= 30) — runs ADF + KPSS at each differencing order":
        "序列值（≥ 30）— 在每個差分階數執行 ADF + KPSS",
    "Series values (>= 30). Bootstrap residual ensemble forecasts the next H steps with quantile bands.":
        "序列值（≥ 30）。Bootstrap 殘差集成預測接下來 H 步驟，附分位數帶。",
    "Series values (training history, >= 30)": "序列值（訓練歷史，≥ 30）",
    "Tip: re-select component after\\nediting data to re-render.":
        "提示：編輯資料後重新選取元件以重新渲染。",
    "Type a command (e.g. 'layout switch Morning', AAPL, ?). Esc to dismiss.":
        "輸入指令（例如：'layout switch Morning'、AAPL、?）。按 Esc 關閉。",
    "JSON parameters (optional)\\ne.g. {ticker:AAPL}":
        "JSON 參數（選填）\\n例如 {ticker:AAPL}",
    "ISO-2 country code, e.g. USA, GBR, DEU\\n":
        "ISO-2 國家代碼，如 USA、GBR、DEU\\n",
    "GRID [%1] already placed, syncing grid": "GRID [%1] 已放置，同步中",
    "Feature values JSON: {rsi:[...],macd:[...]}": "特徵值 JSON：{rsi:[...],macd:[...]}",
}


def main():
    with open(TS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed = 0
    for eng, zhtw in T3.items():
        if eng == zhtw:
            continue
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

    print(f"✅ 第三輪翻譯完成：修復 {fixed} 個字串")

    # 統計
    pairs = re.findall(r'<source>(.*?)</source>\s*<translation[^>]*>(.*?)</translation>', content, re.DOTALL)
    total = len(pairs)
    same_meaningful = 0
    for src, trans in pairs:
        s, t = src.strip(), trans.strip()
        if s == t and re.search(r'[a-zA-Z]{3,}', s):
            if not re.search(r'\\\\[sbd]|\(\?|QListWidget|QPlainText|\.db$|@|https?://|^[A-Z\d\-_\.\^\/]{1,12}$', s):
                same_meaningful += 1

    translated = total - same_meaningful
    print(f"翻譯覆蓋率：{translated}/{total} ({100*translated/total:.1f}%)")


if __name__ == '__main__':
    main()
