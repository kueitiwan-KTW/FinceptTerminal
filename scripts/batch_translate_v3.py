#!/usr/bin/env python3
"""第三輪：智能模式翻譯 + 技術詞保留原文 → 全部移除 unfinished"""
import xml.etree.ElementTree as ET
import re

TS_PATH = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts'

# 單詞翻譯表
WORD_MAP = {
    # 通用
    "LOADING": "載入中", "CATEGORIES": "分類", "CATEGORY": "分類",
    "SETTINGS": "設定", "ACCOUNTS": "帳戶", "ACTIVITY": "活動",
    "AGENCIES": "機構", "AGENTS": "代理", "AGENT": "代理",
    "STUDIO": "工作室", "MEMORY": "記憶體", "CHAT": "對話",
    "MODELS": "模型", "MODEL": "模型", "EXPLORER": "瀏覽器",
    "SERIES": "序列", "TOOLS": "工具", "TOOL": "工具",
    "WEIGHTS": "權重", "ARENA": "競技場",
    "INVESTMENTS": "投資", "ALTERNATIVE": "另類",
    "RESULTS": "結果", "TYPE": "類型", "ANALYZER": "分析工具",
    "CONFIGURATION": "設定", "SCHEMA": "結構",
    "TRANSFORMATION": "轉換", "POWERED": "驅動",
    "SECRET": "密鑰", "APPLY": "套用",
    "BREAKDOWN": "分解", "COMPARISON": "比較",
    "OVERVIEW": "總覽", "SUMMARY": "摘要",
    "INTERVAL": "時間間隔", "ENGINE": "引擎",
    "AVAILABLE": "可用", "SWAP": "交換",
    "PLAN": "方案", "PRICING": "定價",
    "TOPICS": "主題", "SCHEMAS": "結構",
    "ENDPOINTS": "端點", "MODULES": "模組",
    "INDICATORS": "指標", "SOURCES": "來源",
    "GLOBAL": "全球", "CHINESE": "中國",
    "FINANCIAL": "金融", "QUANTITATIVE": "量化",
    "POWERED": "驅動", "BROWSE": "瀏覽",
    "ANALYZERS": "分析工具", "CLASSES": "類別",
    "VIEW": "檢視", "SINGLE": "單一",
    "PROFILE": "設定檔", "PROFILES": "設定檔",
    "MAPPING": "對應", "MAPPINGS": "對應",
    "INTERNAL": "內部", "EXTERNAL": "外部",
    "ENABLE": "啟用", "DISABLE": "停用",
    "CHECK": "檢查", "UNCHECK": "取消勾選",
    "SELECT": "選取", "SELECTED": "已選取",
    "ASSIGN": "指派", "ASSIGNED": "已指派",
    "CONFIG": "設定", "NAMED": "命名的",
    "SAVE": "儲存", "SAVED": "已儲存",
    "CREDENTIALS": "認證資訊",
    "REQUIRED": "必填", "OPTIONAL": "選填",
    "CUSTOM": "自訂", "DEFAULT": "預設",
    "FAILED": "失敗", "SUCCESS": "成功",
    "LOGS": "日誌", "LOG": "日誌",
    "PYTHON": "Python", "SCRIPT": "腳本",
    "RUN": "執行", "RUNNING": "執行中",
    "STOPPED": "已停止", "PAUSED": "已暫停",
    "COMPLETED": "已完成", "PENDING": "待處理",
    "CANCEL": "取消", "CANCELLED": "已取消",
    "CONFIRM": "確認", "CONFIRMED": "已確認",
    "DELETE": "刪除", "DELETED": "已刪除",
    "CREATE": "建立", "CREATED": "已建立",
    "UPDATE": "更新", "UPDATED": "已更新",
    "REMOVE": "移除", "REMOVED": "已移除",
    "RESET": "重設",
    "ENTER": "輸入", "EXIT": "退出",
    "START": "開始", "STOP": "停止",
    "OPEN": "開啟", "CLOSE": "關閉",
    "SHOW": "顯示", "HIDE": "隱藏",
    "EXPAND": "展開", "COLLAPSE": "收合",
    "NEXT": "下一步", "PREV": "上一步", "PREVIOUS": "上一步",
    "BACK": "返回", "FORWARD": "前進",
    "UP": "上", "DOWN": "下", "LEFT": "左", "RIGHT": "右",
    "TOP": "頂部", "BOTTOM": "底部",
    "FIRST": "第一", "LAST": "最後",
    "NEW": "新增", "OLD": "舊",
    "SEARCH": "搜尋", "FILTER": "篩選", "SORT": "排序",
    "COPY": "複製", "PASTE": "貼上", "CUT": "剪下",
    "UNDO": "復原", "REDO": "重做",
    "IMPORT": "匯入", "EXPORT": "匯出",
    "UPLOAD": "上傳", "DOWNLOAD": "下載",
    "CONNECT": "連線", "DISCONNECT": "中斷連線",
    "REFRESH": "重新整理", "RELOAD": "重新載入",
    "SYNC": "同步", "ASYNC": "非同步",
    "PIN": "PIN 碼", "LOCK": "鎖定", "UNLOCK": "解鎖",
    "VERIFY": "驗證", "VALIDATE": "驗證",
    "TEST": "測試", "DEBUG": "除錯",
    "DEPLOY": "部署", "BUILD": "建構",
    "INSTALL": "安裝", "UNINSTALL": "解除安裝",
    "BUY": "買入", "SELL": "賣出", "HOLD": "持有",
    "LONG": "做多", "SHORT": "做空",
    "BULL": "看漲", "BEAR": "看跌",
    "RISK": "風險", "REWARD": "報酬",
    "STOCK": "股票", "BOND": "債券",
    "MARKET": "市場", "EXCHANGE": "交易所",
    "PORTFOLIO": "投資組合", "WATCHLIST": "觀察清單",
    "ORDER": "訂單", "TRADE": "交易",
    "POSITION": "部位", "BALANCE": "餘額",
    "ASSET": "資產", "EQUITY": "權益",
    "SECTOR": "類股", "INDUSTRY": "產業",
    "COUNTRY": "國家", "REGION": "地區",
    "CURRENCY": "貨幣", "CASH": "現金",
    "YIELD": "收益率", "DIVIDEND": "股息",
    "RETURN": "報酬", "PROFIT": "利潤", "LOSS": "虧損",
    "VOLUME": "成交量", "PRICE": "價格",
    "CHANGE": "漲跌", "PERCENT": "百分比",
    "HIGH": "最高", "LOW": "最低",
    "AVERAGE": "平均", "MEDIAN": "中位數",
    "TOTAL": "合計", "NET": "淨",
    "GROSS": "總", "CUMULATIVE": "累積",
    "ANNUAL": "年度", "MONTHLY": "每月", "WEEKLY": "每週",
    "DAILY": "每日", "HOURLY": "每小時",
    "INTRADAY": "盤中",
    "FORECAST": "預測", "PREDICTION": "預測",
    "CORRELATION": "相關性", "VOLATILITY": "波動率",
    "MOMENTUM": "動量", "TREND": "趨勢",
    "SIGNAL": "訊號", "ALERT": "警示",
    "CHART": "圖表", "TABLE": "表格", "GRAPH": "圖形",
    "REPORT": "報告", "ANALYSIS": "分析",
    "METRICS": "指標", "SCORE": "分數",
    "RATING": "評等", "RANK": "排名",
    "WEIGHT": "權重", "ALLOCATION": "配置",
    "STRATEGY": "策略", "BACKTEST": "回測",
    "OPTIMIZE": "最佳化", "SIMULATION": "模擬",
    "CALENDAR": "行事曆", "EVENT": "事件",
    "NEWS": "新聞", "RESEARCH": "研究",
    "ECONOMIC": "經濟", "FUNDAMENTAL": "基本面",
    "TECHNICAL": "技術面",
    "PERFORMANCE": "績效",
    "BENCHMARK": "基準",
    "DRAWDOWN": "回撤",
    "HEDGE": "避險",
    "LEVERAGE": "槓桿",
    "MARGIN": "保證金",
    "LIQUIDITY": "流動性",
    "SPREAD": "價差",
    "PREMIUM": "溢價",
    "DISCOUNT": "折價",
    "FEE": "手續費", "FEES": "手續費",
    "STAKING": "質押",
    "GOVERNANCE": "治理",
    "TOKENOMICS": "代幣經濟學",
    "BLOCKCHAIN": "區塊鏈",
    "WALLET": "錢包", "WALLETS": "錢包",
    "ADDRESS": "地址",
    "NETWORK": "網路",
    "PROTOCOL": "協定",
    "BRIDGE": "橋接",
    "GAS": "Gas",
    "PREDICTION": "預測",
    "MARKET MAKING": "做市",
    "ARBITRAGE": "套利",
    "EXECUTION": "執行",
    "REBALANCE": "再平衡",
    "CONTRIBUTORS": "貢獻者",
    "HISTORY": "歷史",
    "STATUS": "狀態",
    "VALUE": "價值",
    "TARGET": "目標",
    "ACTUAL": "實際",
    "EXPECTED": "預期",
    "VARIANCE": "變異數",
    "DEVIATION": "偏差",
    "MAX": "最大", "MIN": "最小",
    "LIMIT": "限制",
    "THRESHOLD": "閾值",
    "TRIGGER": "觸發",
    "CONDITION": "條件",
    "RULE": "規則",
    "POLICY": "策略",
    "TEMPLATE": "範本",
    "WORKSPACE": "工作區",
    "PANEL": "面板",
    "WIDGET": "小工具",
    "LAYOUT": "佈局",
    "SECTION": "區段",
    "TAB": "標籤頁",
    "MENU": "選單",
    "TOOLBAR": "工具列",
    "SIDEBAR": "側邊欄",
    "HEADER": "標題列",
    "FOOTER": "頁尾",
    "COLUMNS": "欄位",
    "ROWS": "列",
    "ITEMS": "項目",
    "FILES": "檔案",
    "NOTES": "筆記",
    "TAGS": "標籤",
    "LABELS": "標籤",
    "COMMENTS": "留言",
    "MESSAGES": "訊息",
    "NOTIFICATIONS": "通知",
    "UPDATES": "更新",
    "ALERTS": "警示",
    "EVENTS": "事件",
    "TASKS": "任務",
    "JOBS": "工作",
    "QUEUE": "佇列",
    "SERVER": "伺服器",
    "CLIENT": "用戶端",
    "ENDPOINT": "端點",
    "REQUEST": "請求",
    "RESPONSE": "回應",
    "HEALTH": "健康", "HEALTHY": "健康",
    "ERROR": "錯誤", "ERRORS": "錯誤",
    "WARNINGS": "警告",
    "ENABLED": "已啟用", "DISABLED": "已停用",
    "ACTIVE": "活躍", "INACTIVE": "非活躍",
    "ONLINE": "線上", "OFFLINE": "離線",
    "CONNECTED": "已連線", "DISCONNECTED": "已斷線",
    "LIVE": "即時", "DELAYED": "延遲",
    "REAL": "實際", "SIMULATED": "模擬",
    "PAPER": "模擬",
    "DEMO": "示範",
    "PRODUCTION": "正式環境",
    "DEVELOPMENT": "開發環境",
    "STAGING": "預備環境",
}

def smart_translate(source):
    """智能翻譯：嘗試用單詞表組合翻譯"""
    s = source.strip()
    
    # 純數字/符號/代碼 → 保留原文
    if re.match(r'^[\d\s\.,/:;\-\+\*\(\)\[\]\{\}=<>\|&%#@!~^_]+$', s):
        return s
    
    # 技術字串（UUID, hex, API paths）→ 保留原文
    if re.match(r'^[0-9a-f\-]{36}$', s, re.I):  # UUID
        return s
    if re.match(r'^0x', s):  # hex
        return s
    if re.match(r'^/[a-z]', s):  # API path
        return s
    if '-----BEGIN' in s:  # PEM key
        return s
    
    # 時間格式保留
    if re.match(r'^[\d:]+$', s) or s in ('--:--:--',):
        return s
    
    # HTML 內容 → 翻譯內部文字
    if '<span' in s:
        def html_translate(m):
            txt = m.group(1)
            return smart_translate(txt)
        # 簡化：保留 HTML 標籤，翻譯純文字部分
        result = re.sub(r'>([^<]+)<', lambda m: '>' + translate_phrase(m.group(1)) + '<', s)
        return result
    
    # 全大寫句子 → 逐詞翻譯
    if s == s.upper() and re.search(r'[A-Z]', s):
        return translate_phrase(s)
    
    # 混合大小寫句子 → 嘗試整句
    return translate_phrase(s)

def translate_phrase(phrase):
    """嘗試逐詞翻譯一個片語"""
    # 先嘗試整體匹配
    p = phrase.strip()
    if p in WORD_MAP:
        return WORD_MAP[p]
    if p.upper() in WORD_MAP:
        return WORD_MAP[p.upper()]
    
    # 分隔符切分嘗試
    # 常見分隔: 空格, |, ·, —, -, :, /
    parts = re.split(r'(\s+[\|·—\-:\/]+\s+|\s{2,})', p)
    if len(parts) > 1:
        translated_parts = []
        for part in parts:
            if re.match(r'^[\s\|·—\-:\/]+$', part):
                translated_parts.append(part)
            else:
                translated_parts.append(translate_words(part.strip()))
        return ''.join(translated_parts)
    
    return translate_words(p)

def translate_words(text):
    """逐詞翻譯"""
    words = text.split()
    if not words:
        return text
    
    result = []
    i = 0
    while i < len(words):
        # 嘗試 3-word, 2-word, 1-word 匹配
        matched = False
        for n in (3, 2, 1):
            if i + n <= len(words):
                phrase = ' '.join(words[i:i+n])
                if phrase in WORD_MAP:
                    result.append(WORD_MAP[phrase])
                    i += n
                    matched = True
                    break
                if phrase.upper() in WORD_MAP:
                    result.append(WORD_MAP[phrase.upper()])
                    i += n
                    matched = True
                    break
        if not matched:
            # 保留原文（技術術語等）
            result.append(words[i])
            i += 1
    
    return ' '.join(result)

def main():
    tree = ET.parse(TS_PATH)
    root = tree.getroot()
    
    translated = 0
    kept_original = 0
    
    for ctx in root.findall('.//context'):
        for msg in ctx.findall('message'):
            trans = msg.find('translation')
            src = msg.find('source')
            if trans is None or src is None:
                continue
            if trans.get('type') != 'unfinished':
                continue
            
            source = src.text or ''
            result = smart_translate(source)
            
            if result != source.strip():
                translated += 1
            else:
                kept_original += 1
            
            trans.text = result
            if 'type' in trans.attrib:
                del trans.attrib['type']
    
    tree.write(TS_PATH, encoding='unicode', xml_declaration=True)
    
    with open(TS_PATH, 'r') as f:
        remaining = f.read().count('type="unfinished"')
    
    print(f"✅ 第三輪翻譯完成")
    print(f"  翻譯: {translated} 條")
    print(f"  保留原文: {kept_original} 條")
    print(f"  剩餘 unfinished: {remaining} 條")

if __name__ == '__main__':
    main()
