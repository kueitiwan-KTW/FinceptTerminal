#!/usr/bin/env python3
"""
同步翻譯檔：掃描所有 tr() 字串，找出 .ts 中缺少的翻譯，
以 unfinished 狀態插入。已有翻譯的不動。
"""
import xml.etree.ElementTree as ET
import subprocess, re, sys
from pathlib import Path

TS_FILE = "translations/fincept_zh_TW.ts"
SRC_DIRS = ["src/screens", "src/ui", "src/services", "src/python"]

# 常見 UI 用語自動翻譯對照（高頻優先）
AUTO_TRANSLATE = {
    # 通用操作
    "SETTINGS": "設定", "Settings": "設定",
    "CANCEL": "取消", "Cancel": "取消",
    "CONFIRM": "確認", "Confirm": "確認",
    "SAVE": "儲存", "Save": "儲存",
    "DELETE": "刪除", "Delete": "刪除",
    "EDIT": "編輯", "Edit": "編輯",
    "ADD": "新增", "Add": "新增",
    "REMOVE": "移除", "Remove": "移除",
    "CLOSE": "關閉", "Close": "關閉",
    "APPLY": "套用", "Apply": "套用",
    "RESET": "重設", "Reset": "重設",
    "SEARCH": "搜尋", "Search": "搜尋",
    "FILTER": "篩選", "Filter": "篩選",
    "SORT": "排序", "Sort": "排序",
    "EXPORT": "匯出", "Export": "匯出",
    "IMPORT": "匯入", "Import": "匯入",
    "REFRESH": "重新整理", "Refresh": "重新整理",
    "LOADING": "載入中", "Loading": "載入中",
    "Loading...": "載入中...", "LOADING...": "載入中...",
    "SUBMIT": "送出", "Submit": "送出",
    "COPY": "複製", "Copy": "複製",
    "PASTE": "貼上", "Paste": "貼上",
    "CLEAR": "清除", "Clear": "清除",
    "SELECT": "選取", "Select": "選取",
    "SELECT ALL": "全選", "Select All": "全選",
    "BACK": "返回", "Back": "返回",
    "NEXT": "下一步", "Next": "下一步",
    "PREVIOUS": "上一步", "Previous": "上一步",
    "DONE": "完成", "Done": "完成",
    "UPDATE": "更新", "Update": "更新",
    "CREATE": "建立", "Create": "建立",
    "DOWNLOAD": "下載", "Download": "下載",
    "UPLOAD": "上傳", "Upload": "上傳",
    "RUN": "執行", "Run": "執行",
    "STOP": "停止", "Stop": "停止",
    "START": "開始", "Start": "開始",
    "PAUSE": "暫停", "Pause": "暫停",
    "RESUME": "繼續", "Resume": "繼續",
    "RETRY": "重試", "Retry": "重試",
    "YES": "是", "Yes": "是",
    "NO": "否", "No": "否",
    "OK": "確定",
    "ENABLED": "啟用", "Enabled": "已啟用",
    "DISABLED": "停用", "Disabled": "已停用",
    "ON": "開啟", "OFF": "關閉",
    "SHOW": "顯示", "Show": "顯示",
    "HIDE": "隱藏", "Hide": "隱藏",
    "EXPAND": "展開", "Expand": "展開",
    "COLLAPSE": "收合", "Collapse": "收合",
    "SEND": "傳送", "Send": "傳送",

    # 狀態
    "CONNECTED": "已連線", "Connected": "已連線",
    "DISCONNECTED": "已斷線", "Disconnected": "已斷線",
    "ACTIVE": "啟用中", "Active": "啟用中",
    "INACTIVE": "未啟用", "Inactive": "未啟用",
    "READY": "就緒", "Ready": "就緒",
    "ERROR": "錯誤", "Error": "錯誤",
    "WARNING": "警告", "Warning": "警告",
    "SUCCESS": "成功", "Success": "成功",
    "FAILED": "失敗", "Failed": "失敗",
    "PENDING": "待處理", "Pending": "待處理",
    "RUNNING": "執行中", "Running": "執行中",
    "COMPLETED": "已完成", "Completed": "已完成",
    "CANCELLED": "已取消", "Cancelled": "已取消",
    "EMPTY": "空白", "Empty": "空白",
    "UNKNOWN": "未知", "Unknown": "未知",
    "EXPIRED": "已過期", "Expired": "已過期",
    "VERIFIED": "已驗證", "Verified": "已驗證",

    # 資料表頭
    "NAME": "名稱", "Name": "名稱",
    "DATE": "日期", "Date": "日期",
    "TIME": "時間", "Time": "時間",
    "TYPE": "類型", "Type": "類型",
    "STATUS": "狀態", "Status": "狀態",
    "DESCRIPTION": "說明", "Description": "說明",
    "VALUE": "值", "Value": "值",
    "SIZE": "大小", "Size": "大小",
    "COUNT": "數量", "Count": "數量",
    "TOTAL": "合計", "Total": "合計",
    "PRICE": "價格", "Price": "價格",
    "AMOUNT": "金額", "Amount": "金額",
    "VOLUME": "成交量", "Volume": "成交量",
    "CHANGE": "漲跌", "Change": "漲跌",
    "SYMBOL": "代號", "Symbol": "代號",
    "COUNTRY": "國家", "Country": "國家",
    "REGION": "地區", "Region": "地區",
    "CATEGORY": "分類", "Category": "分類",
    "SOURCE": "來源", "Source": "來源",
    "ACTION": "操作", "Action": "操作",
    "ENTRIES": "筆數", "Entries": "筆數",
    "STORE": "儲存區", "Store": "儲存區",

    # 金融 / 市場
    "OPEN": "開盤", "Open": "開盤",
    "HIGH": "最高", "High": "最高",
    "LOW": "最低", "Low": "最低",
    "MARKET CAP": "市值", "Market Cap": "市值",
    "P/E RATIO": "本益比", "P/E Ratio": "本益比",
    "DIVIDEND YIELD": "殖利率", "Dividend Yield": "殖利率",
    "BUY": "買入", "Buy": "買入",
    "SELL": "賣出", "Sell": "賣出",
    "HOLD": "持有", "Hold": "持有",
    "BID": "買價", "Bid": "買價",
    "ASK": "賣價", "Ask": "賣價",
    "SPREAD": "價差", "Spread": "價差",
    "ORDER": "委託", "Order": "委託",
    "LIMIT": "限價", "Limit": "限價",
    "MARKET": "市價", "Market": "市價",
    "SHARES": "股數", "Shares": "股數",
    "POSITION": "部位", "Position": "部位",
    "POSITIONS": "部位", "Positions": "部位",
    "SECTOR": "產業", "Sector": "產業",
    "INDUSTRY": "行業", "Industry": "行業",
    "EXCHANGE": "交易所", "Exchange": "交易所",
    "INDEX": "指數", "Index": "指數",
    "CURRENCY": "貨幣", "Currency": "貨幣",
    "COMMODITY": "商品", "Commodity": "商品",
    "BOND": "債券", "Bond": "債券",
    "BONDS": "債券", "Bonds": "債券",
    "EQUITY": "股票", "Equity": "股票",
    "EQUITIES": "股票", "Equities": "股票",
    "FUTURES": "期貨", "Futures": "期貨",
    "OPTIONS": "選擇權", "Options": "選擇權",
    "ETF": "ETF",
    "CRYPTO": "加密貨幣", "Crypto": "加密貨幣",
    "FOREX": "外匯", "Forex": "外匯",
    "YIELD": "殖利率", "Yield": "殖利率",
    "RETURN": "報酬率", "Return": "報酬率",
    "RISK": "風險", "Risk": "風險",
    "VOLATILITY": "波動率", "Volatility": "波動率",
    "BENCHMARK": "基準", "Benchmark": "基準",
    "ALLOCATION": "配置", "Allocation": "配置",
    "PERFORMANCE": "績效", "Performance": "績效",
    "REVENUE": "營收", "Revenue": "營收",
    "PROFIT": "獲利", "Profit": "獲利",
    "LOSS": "虧損", "Loss": "虧損",
    "BALANCE SHEET": "資產負債表", "Balance Sheet": "資產負債表",
    "INCOME STATEMENT": "損益表", "Income Statement": "損益表",
    "CASH FLOW": "現金流量", "Cash Flow": "現金流量",

    # 設定頁面
    "API CREDENTIALS": "API 憑證",
    "TYPOGRAPHY": "字型排版",
    "THEME": "主題",
    "INTERFACE": "介面",
    "NOTIFICATION PROVIDERS": "通知供應商",
    "ALERT TRIGGERS": "警示觸發條件",
    "STORAGE & DATA MANAGEMENT": "儲存與資料管理",
    "DANGER ZONE": "危險操作區",
    "Not set": "未設定",
    "Cleared": "已清除",
    "Clear All Cache": "清除所有快取",
    "Clear All Databases": "清除所有資料庫",
    "Factory Reset": "恢復原廠設定",

    # 儀表板
    "OVERVIEW": "總覽", "Overview": "總覽",
    "ANALYTICS": "分析", "Analytics": "分析",
    "CHART": "圖表", "Chart": "圖表",
    "TABLE": "表格", "Table": "表格",
    "LIST": "清單", "List": "清單",
    "GRID": "格狀", "Grid": "格狀",
    "MAP": "地圖", "Map": "地圖",
    "TIMELINE": "時間軸", "Timeline": "時間軸",
    "HISTORY": "歷史", "History": "歷史",
    "RECENT": "最近", "Recent": "最近",
    "FAVORITES": "收藏", "Favorites": "收藏",
    "TRENDING": "趨勢", "Trending": "趨勢",
    "POPULAR": "熱門", "Popular": "熱門",
    "NEW": "最新", "New": "最新",
    "ALL": "全部", "All": "全部",

    # 頁面標題
    "MARKETS": "市場",
    "NEWS": "新聞", "News": "新聞",
    "PORTFOLIO": "投資組合",
    "ECONOMICS": "經濟",
    "DERIVATIVES": "衍生性商品",
    "GEOPOLITICS": "地緣政治",
    "MARITIME": "海運",
    "FORUM": "論壇",
    "NOTES": "筆記",
    "PROFILE": "個人檔案",
    "HELP": "說明",
    "LAUNCHPAD": "啟動台",
    "WATCHLIST": "自選清單",

    # 其他常見
    "DETAILS": "詳細資料", "Details": "詳細資料",
    "SUMMARY": "摘要", "Summary": "摘要",
    "COMMENTS": "留言", "Comments": "留言",
    "TAGS": "標籤", "Tags": "標籤",
    "LABEL": "標籤", "Label": "標籤",
    "PREVIEW": "預覽", "Preview": "預覽",
    "NOTIFICATIONS": "通知", "Notifications": "通知",
    "GENERAL": "一般", "General": "一般",
    "ADVANCED": "進階", "Advanced": "進階",
    "CUSTOM": "自訂", "Custom": "自訂",
    "DEFAULT": "預設", "Default": "預設",
    "TITLE": "標題", "Title": "標題",
    "CONTENT": "內容", "Content": "內容",
    "AUTHOR": "作者", "Author": "作者",
    "PUBLISHED": "已發布", "Published": "已發布",
    "DRAFT": "草稿", "Draft": "草稿",
    "ARCHIVED": "已封存", "Archived": "已封存",
    "PINNED": "已置頂", "Pinned": "已置頂",
    "STARRED": "已加星", "Starred": "已加星",
    "No data available": "無可用資料",
    "No results found": "找不到結果",
    "No items": "沒有項目",
    "None": "無",
    "N/A": "不適用",
}


def extract_tr_strings():
    """從原始碼提取所有 tr() 字串"""
    strings = set()
    for d in SRC_DIRS:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.rglob("*.cpp"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'tr\("([^"]+)"\)', text):
                strings.add(m.group(1))
    return strings


def get_existing_translations():
    """讀取 .ts 中已有的翻譯"""
    tree = ET.parse(TS_FILE)
    root = tree.getroot()
    ctx = root.find("context")
    existing = {}
    if ctx is not None:
        for msg in ctx.findall("message"):
            src = msg.find("source")
            trans = msg.find("translation")
            if src is not None and src.text:
                existing[src.text] = trans.text if trans is not None else None
    return existing, tree, root


def auto_translate(s):
    """嘗試自動翻譯，成功返回翻譯，失敗返回 None"""
    if s in AUTO_TRANSLATE:
        return AUTO_TRANSLATE[s]
    return None


def main():
    tr_strings = extract_tr_strings()
    existing, tree, root = get_existing_translations()
    ctx = root.find("context")

    missing = tr_strings - set(existing.keys())
    if not missing:
        print("所有 tr() 字串已在翻譯檔中，無須新增")
        return

    added = 0
    auto = 0
    unfinished = 0
    for s in sorted(missing):
        msg = ET.SubElement(ctx, "message")
        src_el = ET.SubElement(msg, "source")
        src_el.text = s
        trans_el = ET.SubElement(msg, "translation")

        t = auto_translate(s)
        if t:
            trans_el.text = t
            auto += 1
        else:
            trans_el.set("type", "unfinished")
            trans_el.text = s  # 暫時保留原文
            unfinished += 1
        added += 1

    ET.indent(tree, space="    ")
    tree.write(TS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"新增 {added} 筆（自動翻譯 {auto}, 待翻譯 {unfinished}）")


if __name__ == "__main__":
    main()
