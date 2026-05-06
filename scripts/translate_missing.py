#!/usr/bin/env python3
"""
批量翻譯腳本：掃描 .cpp 中的 tr() 字串，補入 .ts 檔的繁體中文翻譯。
專業金融/技術名詞保留英文，其餘全部中文化。
"""
import re, os, glob, xml.etree.ElementTree as ET

SRC_DIR = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/src'
TS_FILE = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts'

# ── 翻譯字典（UI 常見字串 → 繁體中文）──
TRANSLATIONS = {
    # 導覽 / 選單
    "Settings": "設定", "SETTINGS": "設定", "Preferences": "偏好設定",
    "Credentials": "憑證", "Appearance": "外觀", "Notifications": "通知",
    "Storage Cache": "儲存快取", "Data Sources": "資料來源",
    "LLM Config": "LLM 設定", "LLM Configuration": "LLM 設定",
    "LLM CONFIGURATION": "LLM 設定",
    "MCP Servers": "MCP 伺服器", "Logging": "日誌", "Security": "安全性",
    "Profiles": "設定檔", "PROFILES": "設定檔",
    "Keybindings": "快捷鍵", "Python Env": "Python 環境",
    "Developer": "開發者", "Voice": "語音",
    "GLOBAL SETTINGS": "全域設定",

    # 按鈕 / 動作
    "Save": "儲存", "Cancel": "取消", "OK": "確定", "Apply": "套用",
    "Close": "關閉", "Delete": "刪除", "Remove": "移除", "Add": "新增",
    "+ Add": "+ 新增", "Edit": "編輯", "Copy": "複製", "Paste": "貼上",
    "Undo": "復原", "Redo": "重做", "Search": "搜尋", "Filter": "篩選",
    "Reset": "重設", "Refresh": "重新整理", "Retry": "重試",
    "Submit": "提交", "Confirm": "確認", "Back": "返回",
    "Next": "下一步", "Previous": "上一步", "Continue": "繼續",
    "Start": "開始", "Stop": "停止", "Pause": "暫停", "Resume": "繼續",
    "Run": "執行", "Execute": "執行", "Load": "載入", "Import": "匯入",
    "Export": "匯出", "Download": "下載", "Upload": "上傳",
    "Connect": "連線", "Disconnect": "斷線",
    "Enable": "啟用", "Disable": "停用",
    "Select": "選取", "Select All": "全選", "Clear": "清除",
    "Clear All": "全部清除", "Apply & Save": "套用並儲存",
    "Save ,Set Active": "儲存並啟用", "Test Connection": "測試連線",
    "Browse": "瀏覽", "Explore": "探索",
    "APPLY FILTERS": "套用篩選", "ADVANCED": "進階",
    "< BACK": "< 返回", "<<": "<<", ">>": ">>",

    # Provider / LLM 設定
    "Provider": "供應商", "Provider Configuration": "供應商設定",
    "PROVIDERS": "供應商", "Providers": "供應商",
    "API Key": "API 金鑰", "Model": "模型", "Base URL": "基礎 URL",
    "API CONFIGURATION & SCHEMA TRANSFORMATION": "API 設定與結構轉換",
    "Enable MCP Tools (navigation, market data, portfolio, etc.)":
        "啟用 MCP 工具（導覽、市場數據、投資組合等）",
    "Active LLM — configure in Settings > LLM Configuration":
        "目前使用的 LLM — 在設定 > LLM 設定中配置",
    "Active Model — change in Settings > LLM Configuration":
        "目前模型 — 在設定 > LLM 設定中變更",
    "Active model — change in Settings > LLM Configuration":
        "目前模型 — 在設定 > LLM 設定中變更",
    "Linked to your Fincept account: %1":
        "已連結至您的 Fincept 帳號：%1",
    "CACHE & SECURITY SETTINGS": "快取與安全設定",
    "Automatically select the best model from a set of candidates.":
        "從候選模型中自動選取最佳模型。",

    # 狀態 / 標籤
    "Status": "狀態", "Status:": "狀態：", "Error": "錯誤",
    "Error:": "錯誤：", "Warning": "警告", "Success": "成功",
    "Loading": "載入中", "Loading...": "載入中...",
    "Ready": "就緒", "Active": "使用中", "Inactive": "未啟用",
    "Online": "線上", "Offline": "離線",
    "Connected": "已連線", "Disconnected": "已斷線",
    "Pending": "等待中", "Processing": "處理中",
    "Completed": "已完成", "Failed": "失敗",
    "None": "無", "N/A": "不適用", "Unknown": "未知",
    "Default": "預設", "Custom": "自訂",
    "All": "全部", "Other": "其他", "More": "更多",
    "Details": "詳情", "Info": "資訊", "Summary": "摘要",
    "Description": "描述", "Name": "名稱", "Type": "類型",
    "Value": "數值", "Date": "日期", "Time": "時間",
    "Size": "大小", "Count": "數量", "Total": "合計",
    "Average": "平均", "Min": "最小", "Max": "最大",
    "Report:": "報表：", "Sort:": "排序：", "Mode:": "模式：",
    "Fields:": "欄位：", "Schema:": "結構：",
    "View": "檢視", "VIEW:": "檢視：",
    "hidden": "已隱藏", "[ERROR]": "[錯誤]",
    "[RETRY]": "[重試]", "[THINK]": "[思考中]",

    # 市場 / 交易
    "ALLOCATION": "配置", "ATTRIBUTION": "歸因",
    "BACKTEST": "回測", "BACKTESTING": "回測",
    "BACKTEST PARAMETERS": "回測參數",
    "Backtest": "回測", "Benchmark": "基準",
    "BENCHMARK": "基準", "BOOKMARK": "書籤",
    "CALENDAR": "行事曆",
    "ALGO TRADING": "演算法交易",
    "AI ANALYSIS": "AI 分析", "AI QUANT LAB": "AI 量化實驗室",
    "AI && Quant": "AI 與量化",
    "Analysis": "分析", "ANALYSIS PARAMETERS": "分析參數",
    "Anomalies": "異常值",
    "AREA SEARCH": "區域搜尋",
    "ARTICLE DETAIL": "文章詳情",
    "AIS FEED + FINCEPT API": "AIS 資料流 + Fincept API",
    "AIS: STREAMING": "AIS：串流中",
    "0 EVENTS": "0 事件", "0 LIVE": "0 即時",
    "0 VESSELS": "0 船隻", "0 WATCHES": "0 觀察",
    "0 datasets": "0 個資料集", "0 strategies": "0 個策略",
    "+ ADD CONDITION": "+ 新增條件",
    "+ ADD ENTRY CONDITION": "+ 新增進場條件",
    "+ ADD EXIT CONDITION": "+ 新增出場條件",
    "All Methods": "所有方法",
    "BIDS": "買單", "ASKS": "賣單",

    # 投資 / 估值
    "Accretion/Dilution": "增值/稀釋",
    "Benefits & Costs": "收益與成本",
    "Benefits & Costs of Trade": "貿易收益與成本",
    "Barrier Removal": "障礙移除",
    "B-L MODEL": "B-L 模型",
    "Black-Litterman": "Black-Litterman",

    # 分析方法
    "ACF / PACF": "ACF / PACF",
    "ARIMA": "ARIMA",

    # 資料 / 圖表
    "3D": "3D", "5 MIN": "5 分鐘", "1min": "1 分鐘", "5min": "5 分鐘",

    # 訊息
    "Tool '%1' threw unknown exception": "工具 '%1' 發生未知例外",
    "Warning: already used by ": "警告：已被以下使用 ",
    "<none>": "<無>",
    "Kalshi credentials saved.": "Kalshi 憑證已儲存。",
    "Polymarket credentials saved.": "Polymarket 憑證已儲存。",
    "Could not read %1.": "無法讀取 %1。",
    "Private key is required.": "需要私鑰。",
    "Save failed — see logs.": "儲存失敗 — 請查看日誌。",
    "> Enter Command or /type ...": "> 輸入指令或 /輸入 ...",

    # 貿易分析
    "Analyzes economic impact of tariffs, quotas, export subsidies, and non-tariff barriers.":
        "分析關稅、配額、出口補貼及非關稅障礙的經濟影響。",
    "Analyzes trade creation vs. diversion effects for regional trade blocs and economic unions.":
        "分析區域貿易集團與經濟聯盟的貿易創造與貿易轉移效果。",
    "Assesses FDI, employment, wage, and GDP impact of removing trade barriers.":
        "評估移除貿易障礙對 FDI、就業、薪資及 GDP 的影響。",
    "Browse all available data normalizers and transformation processors.":
        "瀏覽所有可用的資料正規化器與轉換處理器。",
    "Browse all built-in Qlib alpha factors and expressions.":
        "瀏覽所有內建的 Qlib Alpha 因子與表達式。",
    "1000+ CHINESE & GLOBAL FINANCIAL DATA ENDPOINTS":
        "1000+ 中國與全球金融資料端點",

    # 通用 UI
    "From:": "來源：", "Date:": "日期：",
    "Content-Type:": "內容類型：", "Content-Length:": "內容長度：",
    "Installing to:": "安裝至：", "Rebind:": "重新綁定：",
    "CATEGORY:": "分類：", "COMP:": "元件：",
    "INSTRUMENT:": "商品：", "INTERVAL:": "間隔：",
    "MODULE:": "模組：", "REGION:": "區域：", "SOURCE:": "來源：",
    "Sched": "排程", "Mem": "記憶體", "Idx:--": "索引：--",

    # 方法 / 演算法名詞（保留英文）
    "Berkus": "Berkus", "Cycle": "週期", "Cycle 0": "週期 0",
    "CYCLE": "週期", "CYCLE 0": "週期 0",
    "Polymarket": "Polymarket", "Kalshi": "Kalshi",
    "Zerodha": "Zerodha", "POLYMARKET": "POLYMARKET",
    "RELIANCE": "RELIANCE", "BANK NIFTY": "BANK NIFTY",
    "SH000300 (CSI300)": "SH000300 (CSI300)",
    "RFC 8628": "RFC 8628", "AES-256-GCM": "AES-256-GCM",
    "HTTP/1.1": "HTTP/1.1", "XXXX-XXXX": "XXXX-XXXX",
    "IMO:": "IMO：", "VOL:": "成交量：",
}


def scan_tr_strings():
    """掃描所有 .cpp/.h 中的 tr() 呼叫"""
    strings = {}
    for ext in ['*.cpp', '*.h']:
        for f in glob.glob(os.path.join(SRC_DIR, '**', ext), recursive=True):
            with open(f, 'r', errors='ignore') as fh:
                content = fh.read()
            matches = re.findall(r'(?:QObject::)?tr\("((?:[^"\\]|\\.)*)"\)', content)
            for m in matches:
                if m not in strings:
                    # 記錄來源檔案（取相對路徑）
                    rel = os.path.relpath(f, os.path.dirname(SRC_DIR))
                    strings[m] = rel
    return strings


def get_translation(source):
    """取得翻譯：字典查找 → 啟發式翻譯 → 保留原文"""
    # 先精確查找
    if source in TRANSLATIONS:
        return TRANSLATIONS[source]

    # 處理 HTML span 包裝的字串
    inner = re.sub(r"<span[^>]*>|</span>", "", source)
    if inner in TRANSLATIONS:
        return source.replace(inner, TRANSLATIONS[inner])

    # 純數字/符號/placeholder → 保留原文
    if re.match(r'^[\d%\s\.\-\+\$\[\]\(\)\/\\×·|,#:@=_{}^!?&<>]+$', source):
        return source

    # 純大寫英文 + 數字（通常是代碼/ticker）→ 保留
    if re.match(r'^[A-Z0-9\s\-_\.\/\^]+$', source) and len(source) <= 12:
        return source

    # 檔名/路徑/email/URL 格式 → 保留
    if re.search(r'\.(db|json|txt|csv|py|js|ts|cpp|h|qm|ts|xml|html|css)$', source):
        return source
    if re.search(r'@|https?://|www\.', source):
        return source
    if re.search(r'^[a-z_]+\.[a-z_]+', source):  # 像 account.%1.%2
        return source

    # 正則表達式 → 保留
    if re.search(r'\\\\[sbdw]|[*+?]{2}|\(\?', source):
        return source

    return None  # 無法自動翻譯，需要手動


def parse_existing_ts():
    """解析現有 .ts 檔，回傳已有的 source 字串集合"""
    with open(TS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    sources = set(re.findall(r'<source>(.*?)</source>', content, re.DOTALL))
    return sources, content


def add_missing_to_ts(missing_with_trans, ts_content):
    """將缺失的翻譯加入 .ts 檔"""
    # 找到最後一個 </context> 之前插入新的 context
    # 或者在適當的 context 中加入 message
    
    # 建立新的 messages XML
    new_messages = []
    for source, translation in sorted(missing_with_trans.items()):
        # XML 轉義
        src_escaped = source.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        trans_escaped = translation.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        
        if translation == source:
            # 保留原文的用 vanished type
            new_messages.append(f'''    <message>
        <source>{src_escaped}</source>
        <translation>{trans_escaped}</translation>
    </message>''')
        else:
            new_messages.append(f'''    <message>
        <source>{src_escaped}</source>
        <translation>{trans_escaped}</translation>
    </message>''')

    if not new_messages:
        return ts_content

    # 在最後一個 </context> 前插入新 context
    insert_block = f'''<context>
    <name>BatchTranslate</name>
{chr(10).join(new_messages)}
</context>
'''
    # 在 </TS> 前插入
    ts_content = ts_content.replace('</TS>', insert_block + '</TS>')
    return ts_content


def fix_untranslated_existing(ts_content):
    """修復現有 .ts 中英文=中文的項目"""
    fixed = 0
    for eng, zhtw in TRANSLATIONS.items():
        if eng == zhtw:
            continue
        # 找到 <source>eng</source>\n        <translation>eng</translation> 的模式
        eng_escaped = re.escape(eng.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        pattern = f'(<source>{eng_escaped}</source>\\s*<translation[^>]*>){eng_escaped}(</translation>)'
        replacement = f'\\g<1>{zhtw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}\\2'
        new_content, n = re.subn(pattern, replacement, ts_content)
        if n > 0:
            ts_content = new_content
            fixed += n
    return ts_content, fixed


def main():
    print("=" * 60)
    print("  Fincept Terminal 繁體中文翻譯批量更新")
    print("=" * 60)

    # 1. 掃描原始碼
    tr_strings = scan_tr_strings()
    print(f"\n[1] 掃描完成：原始碼中有 {len(tr_strings)} 個 tr() 字串")

    # 2. 讀取現有 .ts
    existing, ts_content = parse_existing_ts()
    print(f"[2] 現有 .ts 檔中有 {len(existing)} 個字串")

    # 3. 找缺失的
    missing = {s: f for s, f in tr_strings.items() if s not in existing}
    print(f"[3] 缺失字串：{len(missing)} 個")

    # 4. 翻譯缺失字串
    translated = {}
    kept_original = 0
    auto_translated = 0
    manual_needed = []

    for source in missing:
        trans = get_translation(source)
        if trans is None:
            # 無法自動翻譯 → 先保留原文，標記需要手動
            translated[source] = source
            manual_needed.append(source)
            kept_original += 1
        elif trans == source:
            translated[source] = source
            kept_original += 1
        else:
            translated[source] = trans
            auto_translated += 1

    print(f"[4] 翻譯結果：自動翻譯 {auto_translated}，保留原文 {kept_original}")

    # 5. 修復現有的英文=中文項目
    ts_content, fixed = fix_untranslated_existing(ts_content)
    print(f"[5] 修復現有未翻譯項目：{fixed} 個")

    # 6. 加入缺失的翻譯
    ts_content = add_missing_to_ts(translated, ts_content)
    print(f"[6] 已加入 {len(translated)} 個新翻譯項目")

    # 7. 寫回檔案
    with open(TS_FILE, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    print(f"[7] ✅ 已寫入 {TS_FILE}")

    # 8. 輸出需手動翻譯的字串
    if manual_needed:
        print(f"\n⚠️ 以下 {len(manual_needed)} 個字串需要手動翻譯：")
        for s in sorted(manual_needed)[:50]:
            print(f"  - {s}")
        if len(manual_needed) > 50:
            print(f"  ... 還有 {len(manual_needed) - 50} 個")

    print("\n✅ 完成！")


if __name__ == '__main__':
    main()
