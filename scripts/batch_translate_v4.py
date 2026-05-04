#!/usr/bin/env python3
"""Translate unchanged English entries in fincept_zh_TW.ts.

Only entries where translation text exactly equals source text are considered.
The script uses conservative dictionaries and skip rules so technical strings,
paths, regexes, brands, examples, and code snippets remain untouched.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "fincept-qt" / "translations" / "fincept_zh_TW.ts"
ZH_RE = re.compile(r"[\u4e00-\u9fff]")
PLACEHOLDER_RE = re.compile(r"%\d+")


EXACT_TRANSLATIONS = {
    "%1 LOADING": "%1 載入中",
    "%1 FETCHING DATA...": "%1 正在擷取資料...",
    "%1 LOADING OBSERVATIONS...": "%1 正在載入觀察資料...",
    "EVENTS %1": "事件 %1",
    "%1 ALERTS": "%1 警示",
    "%1 AVAILABLE": "%1 可用",
    "%1 CONNECTORS": "%1 連接器",
    "%1 EVENTS": "%1 事件",
    "%1 ITEMS | %2 PEERS | %3 HOLDERS": "%1 項目 | %2 同業 | %3 持有者",
    "%1 LIVE": "%1 即時",
    "%1 MODULES": "%1 模組",
    "%1 NEUTRAL": "%1 中性",
    "%1 NEW": "%1 新",
    "%1 VESSELS": "%1 船舶",
    "%1 WATCHES": "%1 觀察",
    "%1 WIDGETS": "%1 小工具",
    "%1 agents": "%1 個代理",
    "%1 days": "%1 天",
    "%1 factors": "%1 個因子",
    "%1 fields": "%1 個欄位",
    "%1 files | %2": "%1 個檔案 | %2",
    "%1 holdings": "%1 個持股",
    "%1 internal tools active": "%1 個內部工具啟用中",
    "%1 model(s)": "%1 個模型",
    "%1 packages — %2 missing": "%1 個套件 — %2 個缺失",
    "%1 result(s)": "%1 個結果",
    "%1 schedule(s)": "%1 個排程",
    "%1 server(s) | %2 tools": "%1 個伺服器 | %2 個工具",
    "%1 sessions | %2 messages": "%1 個工作階段 | %2 則訊息",
    "%1 sources": "%1 個來源",
    "%1 sources live": "%1 個即時來源",
    "%1 tools": "%1 個工具",
    "%1 transactions": "%1 筆交易",
    "DONE %1": "完成 %1",
    "FAILED %1": "失敗 %1",
    "CREATE ACCOUNT": "建立帳戶",
    "CREATING...": "建立中...",
    "VERIFYING...": "驗證中...",
    "ANALYZING...": "分析中...",
    "FETCH COMMODITY VOL": "擷取商品波動率",
    "FETCH CRACK SPREAD": "擷取裂解價差",
    "FETCH FORWARD RATE": "擷取遠期利率",
    "FETCH FUTURES CURVE": "擷取期貨曲線",
    "FETCH FX FORWARDS": "擷取外匯遠期",
    "FETCH IMPLIED DIV": "擷取隱含股息",
    "FETCH LIQUIDITY": "擷取流動性",
    "FETCH LIVE DATA": "擷取即時資料",
    "FETCH LOCAL VOL": "擷取局部波動率",
    "FETCH OPTIONS CHAIN": "擷取選擇權鏈",
    "FETCH RATE PATH": "擷取利率路徑",
    "FETCH STRESS TEST": "擷取壓力測試",
    "FETCH YIELD CURVE": "擷取殖利率曲線",
    "RUN %1 ANALYSIS": "執行 %1 分析",
    "RE-RUN %1 ANALYSIS": "重新執行 %1 分析",
    "RE-RUN AGENT": "重新執行代理",
    "SELL %1": "賣出 %1",
    "BID %1": "出價 %1",
    "ASK %1": "賣價 %1",
    "PLACE %1": "下單 %1",
    "OPEN %1 ORDER": "開啟 %1 訂單",
    "ADD TO COL %1": "加入欄 %1",
    "ADD TO TEAM": "加入團隊",
    "EDIT %1 — %2": "編輯 %1 — %2",
    "SLOT %1": "插槽 %1",
    "ALERTS [%1]": "警示 [%1]",
    "MARKETS %1": "市場 %1",
    "NO COMPETITION": "無競賽",
    "NO DATA — SELECT A SERIES FROM THE LEFT PANEL": "無資料 — 請從左側面板選擇一個序列",
    "NO PORTFOLIOS — CREATE ONE": "無投資組合 — 建立一個",
    "NO PORTFOLIOS \\u2014 CREATE ONE \\u25BE": "無投資組合 — 建立一個 ▾",
    "NO DISCUSSIONS YET": "尚無討論",
    "NO POSTS YET": "尚無文章",
    "NO REPLIES YET": "尚無回覆",
    "DEVIATION: %1 news spike": "偏差: %1 新聞突增",
    "PERFORMANCE — %1": "績效 — %1",
    "PERFORMANCE — %1 (no data)": "績效 — %1（無資料）",
    "PIN is too simple — avoid sequential digits": "PIN 碼太簡單 — 避免連續數字",
    "PIN is too simple — use unique digits": "PIN 碼太簡單 — 請使用不重複的數字",
    "PINs do not match": "PIN 碼不一致",
    "PORTFOLIO TERMINAL v4.0": "投資組合終端 v4.0",
    "API CREDENTIALS %1": "API 認證資訊 %1",
    "API Credentials — %1": "API 認證資訊 — %1",
    "Close time:": "收盤時間：",
    "Closes": "收盤",
    "Next open:": "下次開盤：",
    "Last fetch:": "上次擷取：",
    "BREAKING: %1": "突發: %1",
    "▲ TRENDING POSTS": "▲ 熱門文章",
    "● LIVE": "● 即時",
    "● LOADING": "● 載入中",
    "○ OFF": "○ 關閉",
    "✓ SAVED": "✓ 已儲存",
    "✓ ADDED": "✓ 已加入",
    "✓ VOTED": "✓ 已投票",
    "✗ FAILED": "✗ 失敗",
    "⟳ STARTING...": "⟳ 啟動中...",
    "⣾ FETCHING DATA...": "⣾ 正在擷取資料...",
    "⣾ LOADING OBSERVATIONS...": "⣾ 正在載入觀察資料...",
    "↗ OPEN": "↗ 開啟",
    "▲ Upvote": "▲ 按讚",
    "◆ 0 replies": "◆ 0 則回覆",
    "◉ 0 views": "◉ 0 次瀏覽",
    "● HOT": "● 熱門",
    "⚠ DELETE PORTFOLIO": "⚠ 刪除投資組合",
    "READ FULL ARTICLE →": "閱讀完整文章 →",
    "CATEGORY: REALTIME": "分類: 即時",
    "REGION: CN_A": "地區: 中國 A 股",
    "MODULE: CORE": "模組: 核心",
    "INSTRUMENT: BONDS": "工具: 債券",
    "0 credits": "0 點數",
    "0 tokens": "0 代幣",
    "Kalshi credentials saved.": "Kalshi 認證資訊已儲存。",
    "Polymarket credentials saved.": "Polymarket 認證資訊已儲存。",
    "Could not read %1.": "無法讀取 %1。",
    "Private key is required.": "私鑰為必填。",
    "Save failed — see logs.": "儲存失敗 — 請查看日誌。",
    "How can I help you?": "有什麼我可以幫您的嗎？",
    "Loading…": "載入中…",
    "Loading...": "載入中...",
    "Aborted.": "已中止。",
    "Cancelled.": "已取消。",
    "Complete": "完成",
    "Failed.": "失敗。",
    "Failed: %1": "失敗：%1",
    "Reverted.": "已還原。",
    "Stale.": "已過期。",
    "Timed out.": "已逾時。",
    "Waiting": "等候中",
    "Duplicate": "複製",
    "Reply": "回覆",
    "Provider": "供應商",
    "Providers": "供應商",
    "Quarterly": "每季",
    "Reopen": "重新開啟",
    "Streaming": "串流中",
    "Temperature": "溫度",
    "Withdraw": "提領",
    "Culture": "文化",
    "Education": "教育",
    "Registry": "登錄",
    "Exports": "匯出",
    "Center": "中心",
    "hidden": "隱藏",
    "enter password": "輸入密碼",
    "All Commodities": "所有商品",
    "All Publishers": "所有發布者",
    "All Types": "所有類型",
    "Choose Dashboard Template": "選擇儀表板範本",
    "Choose a template:": "選擇範本：",
    "Choose an amount and duration.": "選擇金額與期間。",
    "Clear ALL User Data": "清除所有使用者資料",
    "Clear Cell": "清除儲存格",
    "Click any post from the feed to read it": "點擊動態中的任何文章來閱讀",
    "Configure a URL via the gear icon": "透過齒輪圖示設定 URL",
    "Configure — Maritime Vessels": "設定 — 海運船舶",
    "Connection Name": "連線名稱",
    "Data Services": "資料服務",
    "DataHub Inspector": "DataHub 檢視器",
    "Discovering agents…": "正在探索代理…",
    "Double-click to configure": "雙擊以設定",
    "Edit Symbols...": "編輯代碼...",
    "Environment Variables": "環境變數",
    "Execute From Here": "從此處執行",
    "Fields marked with * are required.": "標有 * 的欄位為必填。",
    "Fincept Launchpad": "Fincept 啟動台",
    "Get in touch with our team": "與我們的團隊聯繫",
    "Load from file…": "從檔案載入…",
    "Merge transactions into existing portfolio:": "將交易合併至現有投資組合：",
    "No anomalies detected at the configured threshold.": "在設定的閾值下未偵測到異常。",
    "No markets configured — click gear to add": "尚未設定市場 — 點擊齒輪新增",
    "No related markets": "無相關市場",
    "No servers match the current filter.": "沒有伺服器符合目前的篩選條件。",
    "No snapshot available.": "無可用快照。",
    "No transactions yet.": "尚無交易。",
    "No vessels configured — click gear to add IMOs": "尚未設定船舶 — 點擊齒輪新增 IMO",
    "One IMO per line": "每行一個 IMO",
    "One IMO per line (e.g. 9811000)": "每行一個 IMO（例如 9811000）",
    "Output Format": "輸出格式",
    "Per-Tag Overrides": "依標籤覆寫",
    "Recent Layouts": "最近佈局",
    "Rename Cell": "重新命名儲存格",
    "Reopen browser": "重新開啟瀏覽器",
    "Share your insights with the community": "與社群分享您的見解",
    "Sign transaction": "簽署交易",
    "Store API keys securely in the OS keychain. Keys are never written to disk in plain text.": "將 API 金鑰安全儲存在作業系統鑰匙圈中。金鑰不會以明文寫入磁碟。",
    "Switch Profile…": "切換設定檔…",
    "System Prompt": "系統提示詞",
    "Your terminal file index is empty.": "您的終端檔案索引為空。",
    "Browser login": "瀏覽器登入",
    "Auto-start on launch": "啟動時自動開始",
    "Fincept Terminal": "Fincept 終端",
    "Fincept LLM": "Fincept 大語言模型",
    "My Custom Index": "我的自訂指數",
    "My Strategy": "我的策略",
    "Model ID": "模型 ID",
    "Base URL": "基礎 URL",
    "Private Key:": "私鑰：",
    "Private Key (PEM):": "私鑰（PEM）：",
    "Extend lock…": "延長鎖定…",
    "Mark all read": "全部標為已讀",
    "Send Reply →": "傳送回覆 →",
    "Submit Ticket →": "提交工單 →",
    "Awaiting events…": "等候事件…",
    "Waiting for spot prices…": "等候現貨價格…",
    "All Fincept Terminal features unlocked.": "所有 Fincept 終端功能已解鎖。",
}


SEED_WORDS = {
    "SAVE": "儲存", "FETCH": "擷取", "CALCULATE": "計算", "RUN": "執行",
    "APPLY": "套用", "VERIFY": "驗證", "CREATE": "建立", "DELETE": "刪除",
    "CANCEL": "取消", "CONFIRM": "確認", "SUBMIT": "提交", "REFRESH": "重新整理",
    "GENERATE": "產生", "ANALYZE": "分析", "EXPORT": "匯出", "IMPORT": "匯入",
    "DOWNLOAD": "下載", "UPLOAD": "上傳", "CONNECT": "連線", "DISCONNECT": "斷線",
    "SUBSCRIBE": "訂閱", "PUBLISH": "發布", "ARCHIVE": "封存", "DUPLICATE": "複製",
    "RECORD": "錄製", "PLAY": "播放", "SEND": "傳送", "RECEIVE": "接收",
    "STAKE": "質押", "WITHDRAW": "提領", "TRANSLATE": "翻譯", "REGENERATE": "重新產生",
    "REOPEN": "重新開啟", "UNLINK": "取消連結", "EXECUTE": "執行", "COPY": "複製",
    "REPLY": "回覆", "OPEN": "開啟", "CLOSE": "關閉", "ADD": "新增",
    "EDIT": "編輯", "UPDATE": "更新", "REMOVE": "移除", "RESET": "重設",
    "CLEAR": "清除", "SEARCH": "搜尋", "SELECT": "選取", "LOAD": "載入",
    "START": "開始", "STOP": "停止", "PAUSE": "暫停", "RESUME": "繼續",
    "LOGIN": "登入", "LOGOUT": "登出", "REGISTER": "註冊", "LAUNCH": "啟動",
    "SETTINGS": "設定", "PORTFOLIO": "投資組合", "WATCHLIST": "觀察清單",
    "WATCHLISTS": "觀察清單", "DASHBOARD": "儀表板", "MARKETPLACE": "市集",
    "COMMUNITY": "社群", "DOCUMENTATION": "文件", "ROADMAP": "路線圖",
    "HELP CENTER": "幫助中心", "CONTACT US": "聯繫我們", "TERMS OF SERVICE": "服務條款",
    "FILE MANAGER": "檔案管理器", "AGENT STUDIO": "代理工作室", "AGENT CHAT": "代理對話",
    "AGENT MEMORY": "代理記憶", "DATA SERVICES": "資料服務", "DATA MONITORS": "資料監控",
    "BROKER TEMPLATES": "經紀商範本", "QUICK STATS": "快速統計",
    "RETIREMENT CALCULATOR": "退休計算器", "GOAL-BASED PLANNING": "目標導向規劃",
    "EFFICIENT FRONTIER": "效率前緣", "CORPORATE INTELLIGENCE MAP": "企業情報地圖",
    "VIX FEAR GAUGE": "VIX 恐懼指標", "HIGH-BETA STOCKS": "高 Beta 股票",
    "ASIA MARKETS": "亞洲市場", "ASIA MARKETS TERMINAL": "亞洲市場終端",
    "SOVEREIGN PORTALS": "主權入口", "FINCEPT MARKETS": "Fincept 市場",
    "PORTFOLIO TERMINAL": "投資組合終端", "ALPHA ARENA": "Alpha 競技場",
    "FFN ANALYTICS": "FFN 分析", "QUANTLIB SUITE": "QuantLib 套件",
    "PARSER ENGINES": "解析引擎", "MCP SERVERS": "MCP 伺服器",
    "SCHEDULED QUERIES": "排程查詢", "OPTIMIZATION STRESS SCENARIOS": "最佳化壓力情境",
    "SKILL LEVELS": "技能等級", "WIZARD STEPS": "精靈步驟",
    "WORKFLOW NAME": "工作流名稱", "WORKFLOWS": "工作流", "DISCUSSIONS": "討論區",
    "CONVERSATIONS": "對話", "INPUT PARAMETERS": "輸入參數",
    "SYSTEM CAPABILITIES": "系統能力", "ENCRYPTION": "加密", "SECURITY": "安全性",
    "TICKERS": "股票代碼", "TEMPLATES": "範本", "CONNECTORS": "連接器",
    "PUBLISHERS": "發布者", "CHANNELS": "頻道", "AUCTIONS": "拍賣",
    "PAST COMPETITIONS": "過去競賽", "COMPETITION NAME": "競賽名稱",
    "TEAM QUERY": "團隊查詢", "LOADING": "載入中", "ANALYZING": "分析中",
    "GENERATING": "產生中", "EXECUTING": "執行中", "COMPUTING": "計算中",
    "CONFIGURED": "已設定", "REGISTERED": "已註冊", "COMPLETED": "已完成",
    "IDLE": "閒置", "COPIED": "已複製", "NOT SET": "未設定", "LIVE": "即時",
    "AVAILABLE": "可用", "HIDDEN": "隱藏的", "TRENDING": "趨勢",
    "HOT": "熱門", "ADDED": "已加入", "VOTED": "已投票", "SAVED": "已儲存",
    "WAITING": "等候中", "STREAMING": "串流中", "FAILED": "失敗",
    "SUCCESS": "成功", "PENDING": "待處理", "ACTIVE": "啟用中", "INACTIVE": "未啟用",
    "ENABLED": "已啟用", "DISABLED": "已停用", "CONNECTED": "已連線",
    "DISCONNECTED": "已斷線", "ONLINE": "線上", "OFFLINE": "離線",
    "RISK": "風險", "YIELD": "收益率", "DIVIDEND": "股息", "SPREAD": "價差",
    "MARGIN": "保證金", "LEVERAGE": "槓桿", "LIQUIDITY": "流動性",
    "VOLATILITY": "波動率", "MOMENTUM": "動量", "BENCHMARK": "基準",
    "DRAWDOWN": "回撤", "BACKTEST": "回測", "ALLOCATION": "配置",
    "SECTOR": "類股", "EQUITY": "權益", "BOND": "債券", "BONDS": "債券",
    "BILLS": "票券", "COMMODITY": "商品", "COMMODITIES": "商品",
    "FUTURES": "期貨", "OPTIONS": "選擇權", "STAKING": "質押",
    "GOVERNANCE": "治理", "TOKENOMICS": "代幣經濟", "SWAP": "交換",
    "ARBITRAGE": "套利", "HEDGE": "避險", "PREMIUM": "溢價", "OUTCOME": "結果",
    "OUTCOMES": "結果", "RESULT": "結果", "RESULTS": "結果", "PRICES": "價格",
    "PRESET": "預設", "OUTPUT": "輸出", "PROPERTIES": "屬性", "PRODUCT": "產品",
    "CATEGORY": "分類", "REGION": "地區", "COUNTRY": "國家", "MODE": "模式",
    "PERIOD": "期間", "SOURCE": "來源", "FILTER": "篩選", "FILTERS": "篩選",
    "SORT": "排序", "QUERY": "查詢", "CORE": "核心", "RADIAL": "放射狀",
    "NODES": "節點", "OTHER": "其它", "MODULE": "模組", "MODULES": "模組",
    "INSTRUMENT": "工具", "VIEW": "檢視", "MONITOR": "監控", "TEAM": "團隊",
    "TIPS": "提示", "TRADEMARKS": "商標", "END": "結束", "FORCE": "強制",
    "FRAMEWORK": "框架", "AUTO-LOCK": "自動鎖定", "AUTO-ROUTE": "自動路由",
    "AUTO RUN": "自動執行", "CLEAR CACHE": "清除快取",
    "CLEAR SELECTION": "清除選取", "SKIP & CONTINUE": "跳過並繼續",
    "READ FULL ARTICLE": "閱讀完整文章", "PUBLISH POST": "發布文章",
    "MARK ALL READ": "全部標為已讀", "MAP HOLDINGS TO SECTORS": "將持股對應至類股",
    "EXECUTE COMPUTATION": "執行計算", "SEND REPLY": "傳送回覆",
    "SUBMIT TICKET": "提交工單", "SWITCH PROFILE": "切換設定檔",
    "ACCOUNT": "帳戶", "ACCOUNTS": "帳戶", "ACTIVITY": "活動", "ACTIONS": "操作",
    "AGENT": "代理", "AGENTS": "代理", "AI": "AI", "API": "API", "BANK": "銀行",
    "BALANCE": "餘額", "BASE": "基礎", "BID": "買價", "ASK": "賣價",
    "BOARD": "看板", "BROWSER": "瀏覽器", "CACHE": "快取", "CELL": "儲存格",
    "CELLS": "儲存格", "CHART": "圖表", "CODE": "程式碼", "COLUMN": "欄",
    "COLUMNS": "欄位", "CREDENTIALS": "認證資訊", "DATA": "資料",
    "DATASETS": "資料集", "DATE": "日期", "DESCRIPTION": "說明", "DETAILS": "詳細資訊",
    "ERROR": "錯誤", "ERRORS": "錯誤", "EVENT": "事件", "EVENTS": "事件",
    "EXPIRES": "到期", "FAV": "收藏", "FEE": "費用", "FEES": "費用",
    "FIELD": "欄位", "FIELDS": "欄位", "FILE": "檔案", "FILES": "檔案",
    "FORMAT": "格式", "FUNDS": "基金", "GO": "前往", "HEADER": "標頭",
    "HOLDERS": "持有者", "HOLDINGS": "持股", "IMPORTS": "匯入", "INSPECTOR": "檢視器",
    "INTERVAL": "間隔", "ITEM": "項目", "ITEMS": "項目", "KEY": "金鑰",
    "LEADERBOARD": "排行榜", "LOAD MORE": "載入更多", "LOGGING": "日誌記錄",
    "MARKET": "市場", "MARKETS": "市場", "MEMORY": "記憶", "MESSAGE": "訊息",
    "MESSAGES": "訊息", "MODEL": "模型", "MODELS": "模型", "NAME": "名稱",
    "NEW": "新", "NORMALITY": "常態性", "ORDER": "訂單", "ORDERS": "訂單",
    "OVERVIEW": "總覽", "PARAMETERS": "參數", "PASSWORD": "密碼",
    "PEERS": "同業", "PIPELINE": "管線", "PORTAL": "入口", "POSITION": "部位",
    "POSITIONS": "部位", "POST": "文章", "POSTS": "文章", "PROFILE": "設定檔",
    "PROMPT": "提示詞", "QTY": "數量", "QUICK": "快速", "RATE": "利率",
    "REPLIES": "回覆", "REQUEST": "請求", "RESPONSE": "回應", "RETRY": "重試",
    "ROW": "列", "ROWS": "列", "SCHEDULE": "排程", "SCHEMA": "結構描述",
    "SCHEMAS": "結構描述", "SCRIPT": "腳本", "SERVER": "伺服器", "SERVERS": "伺服器",
    "SESSION": "工作階段", "SESSIONS": "工作階段", "SIGNAL": "訊號",
    "SIGNALS": "訊號", "SIGNATURE": "簽章", "SLOT": "插槽", "SNAPSHOT": "快照",
    "STATS": "統計", "STATUS": "狀態", "STRATEGY": "策略", "SYMBOL": "代碼",
    "SYMBOLS": "代碼", "SYSTEM": "系統", "TABLE": "表格", "TAG": "標籤",
    "TAGS": "標籤", "TASK": "任務", "TICKET": "工單", "TITLE": "標題",
    "TOKEN": "代幣", "TOKENS": "代幣", "TOOL": "工具", "TOOLS": "工具",
    "TOTAL": "總計", "TRADE": "交易", "TRADES": "交易", "TRANSACTION": "交易",
    "TRANSACTIONS": "交易", "TYPE": "類型", "TYPES": "類型", "URL": "URL",
    "USAGE": "用量", "VALUE": "值", "VARIABLES": "變數", "VESSEL": "船舶",
    "VESSELS": "船舶", "VOICE": "語音", "WALLET": "錢包", "WIDGET": "小工具",
    "WIDGETS": "小工具", "WINDOW": "視窗", "WINDOWS": "視窗", "WORKSPACE": "工作區",
    "YEAR": "年", "YEARS": "年", "ANNUAL": "年度", "MONTHLY": "每月",
    "WEEKLY": "每週", "DAILY": "每日", "HOURLY": "每小時", "QUARTERLY": "每季",
    "SCIENCE": "科學", "TECH": "科技", "CULTURE": "文化", "EDUCATION": "教育",
    "GOVT": "政府", "CONGRESS": "國會", "BILATERAL": "雙邊", "MULTILATERAL": "多邊",
    "AGREEMENT": "協議", "AUCTION": "拍賣", "COMPETITION": "競賽",
}


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def build_dictionary() -> dict[str, str]:
    words = {}
    for key, value in SEED_WORDS.items():
        words[key] = value
        words[key.title()] = value
        words[key.lower()] = value
    words.update(EXACT_TRANSLATIONS)
    for key, value in EXACT_TRANSLATIONS.items():
        words[normalized(key)] = value
    return words


DICT = build_dictionary()


SKIP_EXACT = {
    "Polymarket", "Kalshi", "Zerodha", "Polymarket + Kalshi", "Polymarket Gnosis Safe",
    "AAPL", "MSFT", "GOOG", "AMZN", "SPY,AAPL,MSFT", "AAPL,MSFT,GOOG,AMZN",
    "AAPL, MSFT, ...", "AAPL, MSFT, TSLA...", "AAPL, MSFT, ^GSPC, BTC-USD ...",
    "US", "USA", "NSE", "REST", "MCP", "PY", "AI", "API", "RFC 8628",
    "linux-arm64", "linux-x64", "macos-arm64", "macos-x64", "windows-arm64", "windows-x64",
    "v%1", "sha256", "utf-8", "download-url", "open-url", "latest-version",
    "user@domain.com", "YYYY-MM-DD", "yyyy-MM-dd", "XXXX-XXXX", "0x", "sk-...",
}

SKIP_PATTERNS = [
    re.compile(r"\\[bdws]|\[\^?>?|\(\.\*\?\)|\^\(|\(\?P?<|<\([^>]+\)>"),
    re.compile(r"^[A-Za-z-]+:\s*[^ ]+\\r\\n$"),
    re.compile(r"^(Content-Type|Cache-Control|Connection|Access-Control-|Referrer-Policy|X-Content-Type-Options):", re.I),
    re.compile(r".*\.(db|py|json|csv|pem|sqlite|log|txt|md|html?|qml|cpp|h|ts)$", re.I),
    re.compile(r"(^|/)[\w.-]+/[\w./{}%-]+$"),
    re.compile(r"^[A-Z]{1,6}(,[A-Z]{1,6})+(\.\.\.)?$"),
    re.compile(r"^[A-Z]{1,6}(, ?[A-Z]{1,6})+.*$"),
    re.compile(r"^v%\d+$"),
    re.compile(r"^[a-z]+-(arm64|x64)$"),
    re.compile(r"^(QListWidget|QPlainTextEdit|Q[A-Za-z]+[{:]).*"),
    re.compile(r"^[{}()[\]<>|/\\:;.,+\-*=#@$%^&~!?·•…\s]+$"),
    re.compile(r"^[-+]?\$?%?\d+([.,:/]\d+)*[A-Za-z%/]*$"),
    re.compile(r"^[A-Z]:--$|^[HLABS]:%\d+$"),
    re.compile(r"^(account|broker|window|root|array)\b[.\[\]_%\w/-]*$"),
    re.compile(r"^[-\w]+@\w+\.\w+$"),
    re.compile(r"^-----BEGIN .* KEY-----"),
]


def has_chinese(text: str) -> bool:
    return bool(ZH_RE.search(text))


def should_skip(text: str) -> bool:
    s = normalized(text)
    if not s or has_chinese(s):
        return True
    if s in SKIP_EXACT:
        return True
    if "<" in s and ">" in s and "<span" not in s:
        return True
    if re.search(r"\b(Polymarket|Kalshi|Zerodha)\b", s) and s not in EXACT_TRANSLATIONS:
        return True
    return any(pattern.search(s) for pattern in SKIP_PATTERNS)


def lookup(text: str) -> str | None:
    s = normalized(text)
    if s in DICT:
        return DICT[s]
    if s.upper() in DICT:
        return DICT[s.upper()]
    return None


def translate_html_span(text: str) -> str | None:
    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        translated = translate_text(inner)
        return f">{translated or inner}<"

    translated = re.sub(r">([^<>]+)<", replace, text)
    return translated if translated != text and has_chinese(translated) else None


def translate_words(text: str) -> str:
    tokens = re.split(r"([A-Za-z][A-Za-z0-9'/-]*|\s+|%\d+)", text)
    out: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token:
            i += 1
            continue

        matched = False
        for span in (5, 4, 3, 2, 1):
            phrase_tokens = tokens[i : i + span * 2 - 1]
            phrase = "".join(phrase_tokens)
            if not phrase_tokens or not re.fullmatch(r"[A-Za-z0-9'/-]+(?:\s+[A-Za-z0-9'/-]+)*", phrase):
                continue
            translated = lookup(phrase)
            if translated:
                out.append(translated)
                i += len(phrase_tokens)
                matched = True
                break
        if matched:
            continue

        translated = lookup(token)
        out.append(translated if translated else token)
        i += 1

    return "".join(out)


def safe_fallback(text: str) -> bool:
    """Fallback word replacement is only safe for UI labels, not prose/logs."""
    letters = re.findall(r"[A-Za-z]+", text)
    if not letters:
        return False
    if any(word != word.upper() for word in letters):
        return False
    return not re.search(r"\b(cache|only|failed|returned|running|opened|requested)\b", text, re.I)


def translate_text(text: str) -> str | None:
    lead = re.match(r"^\s*", text).group(0)
    trail = re.search(r"\s*$", text).group(0)
    core = text[len(lead) : len(text) - len(trail)]
    s = normalized(core)
    if not s:
        return None

    exact = lookup(s)
    if exact:
        return f"{lead}{exact}{trail}"

    if "<span" in s:
        html = translate_html_span(core)
        return f"{lead}{html}{trail}" if html else None

    if should_skip(s):
        return None

    if not safe_fallback(core):
        return None

    replaced = translate_words(core)
    if replaced != core and has_chinese(replaced):
        return f"{lead}{replaced}{trail}"
    return None


def main() -> None:
    tree = ET.parse(TS_PATH)
    root = tree.getroot()

    candidates = translated = skipped = unchanged = 0
    for msg in root.iter("message"):
        source = msg.find("source")
        translation = msg.find("translation")
        if source is None or translation is None:
            continue

        source_text = source.text or ""
        translation_text = translation.text or ""
        if translation_text != source_text or has_chinese(source_text):
            continue

        candidates += 1
        new_text = translate_text(source_text)
        if new_text and new_text != translation_text:
            translation.text = new_text
            translation.attrib.pop("type", None)
            translated += 1
        elif should_skip(source_text):
            skipped += 1
        else:
            unchanged += 1

    tree.write(TS_PATH, encoding="utf-8", xml_declaration=True)
    print("batch_translate_v4 complete")
    print(f"dictionary entries: {len(DICT)}")
    print(f"candidate unchanged English entries: {candidates}")
    print(f"translated: {translated}")
    print(f"skipped: {skipped}")
    print(f"unchanged/no dictionary hit: {unchanged}")


if __name__ == "__main__":
    main()
