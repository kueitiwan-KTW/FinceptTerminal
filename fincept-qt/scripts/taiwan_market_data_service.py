#!/usr/bin/env python3
"""
台灣股市數據 Connector (Taiwan Market Data Service)
透過 yfinance 提供台灣上市/上櫃股票即時與歷史資料。

端點分類：
- TW Realtime：台股即時行情（上市/上櫃）
- TW Historical：台股歷史 K 線
- TW Index：加權指數、櫃買指數
- TW Info：個股基本資訊
"""

import sys
import json
import time

try:
    import yfinance as yf
    import pandas as pd
except ImportError as e:
    print(json.dumps({
        "success": False,
        "error": f"缺少依賴套件: {e}",
        "data": []
    }))
    sys.exit(1)


def safe_call(func, *args, **kwargs):
    """安全呼叫函式，含重試與錯誤處理"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    return {"success": True, "data": [], "count": 0}
                for col in result.columns:
                    if result[col].dtype == 'datetime64[ns]':
                        result[col] = result[col].astype(str)
                result = result.replace([float("inf"), float("-inf")], None)
                result = result.where(pd.notna(result), None)
                data = result.to_dict(orient='records')
                return {"success": True, "data": data, "count": len(data)}
            elif isinstance(result, (list, dict)):
                return {"success": True, "data": result, "count": len(result) if isinstance(result, list) else 1}
            else:
                return {"success": True, "data": str(result), "count": 1}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return {"success": False, "error": str(e), "data": []}
    return {"success": False, "error": "超過最大重試次數", "data": []}


# ==================== 台股藍籌代碼表 ====================

TW_BLUECHIP_SYMBOLS = [
    "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2303.TW",
    "2881.TW", "2882.TW", "2891.TW", "1301.TW", "2412.TW", "3711.TW",
    "2886.TW", "1303.TW", "2884.TW", "3008.TW", "2002.TW", "1326.TW",
    "5880.TW", "2207.TW", "2892.TW", "2885.TW", "6505.TW", "2357.TW",
]

TW_ETF_SYMBOLS = [
    "0050.TW", "0056.TW", "00878.TW", "00919.TW", "00929.TW",
    "006208.TW", "00713.TW", "00940.TW",
]

TW_INDEX_SYMBOLS = [
    "^TWII",  # 台灣加權指數
]

TWO_SYMBOLS = [
    "6547.TWO", "3293.TWO", "8069.TWO", "6803.TWO", "3611.TWO",
    "5871.TWO", "6781.TWO", "3105.TWO",
]


# ==================== 即時行情 ====================

def _batch_quotes(symbols):
    """批次抓取多檔即時報價"""
    records = []
    tickers = yf.Tickers(" ".join(symbols))
    for sym in symbols:
        try:
            t = tickers.tickers.get(sym)
            if t is None:
                continue
            info = t.fast_info
            records.append({
                "symbol": sym,
                "price": info.last_price,
                "open": info.open,
                "high": info.day_high,
                "low": info.day_low,
                "prev_close": info.previous_close,
                "volume": info.last_volume,
                "market_cap": info.market_cap,
                "currency": info.currency,
                "change": round(info.last_price - info.previous_close, 2) if info.last_price and info.previous_close else None,
                "change_pct": round((info.last_price - info.previous_close) / info.previous_close * 100, 2) if info.last_price and info.previous_close else None,
            })
        except Exception:
            continue
    return {"success": True, "data": records, "count": len(records)}


def get_tw_bluechip_realtime():
    """台股上市藍籌即時行情（前 24 大權值股）"""
    return _batch_quotes(TW_BLUECHIP_SYMBOLS)


def get_tw_etf_realtime():
    """台股 ETF 即時行情"""
    return _batch_quotes(TW_ETF_SYMBOLS)


def get_tw_index_realtime():
    """台灣加權指數即時行情"""
    return _batch_quotes(TW_INDEX_SYMBOLS)


def get_two_realtime():
    """上櫃股票即時行情"""
    return _batch_quotes(TWO_SYMBOLS)


def get_tw_individual_quote(symbol="2330"):
    """個別台股即時報價（輸入純數字代碼，自動加 .TW）"""
    if not symbol.endswith(('.TW', '.TWO')):
        symbol = symbol + '.TW'
    return _batch_quotes([symbol])


# ==================== 歷史 K 線 ====================

def _fetch_history(symbols, period="3mo", interval="1d"):
    """批次抓取歷史 K 線"""
    all_records = []
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            hist = t.history(period=period, interval=interval)
            if hist.empty:
                continue
            hist = hist.reset_index()
            for _, row in hist.iterrows():
                all_records.append({
                    "symbol": sym,
                    "date": str(row.get("Date", "")),
                    "open": row.get("Open"),
                    "high": row.get("High"),
                    "low": row.get("Low"),
                    "close": row.get("Close"),
                    "volume": int(row.get("Volume", 0)),
                })
        except Exception:
            continue
    return {"success": True, "data": all_records, "count": len(all_records)}


def get_tw_bluechip_history():
    """台股藍籌 3 個月日 K 線"""
    return _fetch_history(TW_BLUECHIP_SYMBOLS[:12])


def get_tw_individual_history(symbol="2330", period="6mo"):
    """個別台股歷史 K 線"""
    if not symbol.endswith(('.TW', '.TWO')):
        symbol = symbol + '.TW'
    return _fetch_history([symbol], period=period)


def get_tw_index_history():
    """台灣加權指數歷史 K 線"""
    return _fetch_history(TW_INDEX_SYMBOLS, period="1y")


# ==================== 個股基本資訊 ====================

def get_tw_stock_info(symbol="2330"):
    """個別台股基本面資訊"""
    if not symbol.endswith(('.TW', '.TWO')):
        symbol = symbol + '.TW'
    try:
        t = yf.Ticker(symbol)
        info = t.info
        return {
            "success": True,
            "data": [{
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "currency": info.get("currency"),
                "exchange": info.get("exchange"),
                "website": info.get("website"),
            }],
            "count": 1
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


# ==================== 端點註冊表 ====================

ENDPOINTS = {
    # 即時行情
    "tw_bluechip_realtime": {"func": get_tw_bluechip_realtime, "desc": "台股上市藍籌即時行情", "category": "TW Realtime"},
    "tw_etf_realtime": {"func": get_tw_etf_realtime, "desc": "台股 ETF 即時行情", "category": "TW Realtime"},
    "tw_index_realtime": {"func": get_tw_index_realtime, "desc": "台灣加權指數即時行情", "category": "TW Index"},
    "two_realtime": {"func": get_two_realtime, "desc": "上櫃股票即時行情", "category": "TW Realtime"},
    "tw_individual_quote": {"func": get_tw_individual_quote, "desc": "個別台股報價（輸入代碼）", "category": "TW Realtime"},

    # 歷史 K 線
    "tw_bluechip_history": {"func": get_tw_bluechip_history, "desc": "台股藍籌 3 月日 K 線", "category": "TW Historical"},
    "tw_individual_history": {"func": get_tw_individual_history, "desc": "個別台股歷史 K 線", "category": "TW Historical"},
    "tw_index_history": {"func": get_tw_index_history, "desc": "台灣加權指數歷史 K 線", "category": "TW Historical"},

    # 基本資訊
    "tw_stock_info": {"func": get_tw_stock_info, "desc": "個別台股基本面資訊", "category": "TW Info"},
}


def get_all_endpoints():
    """回傳所有可用端點與描述"""
    endpoints = list(ENDPOINTS.keys())
    categories = {}
    for name, info in ENDPOINTS.items():
        cat = info.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)

    return {
        "success": True,
        "data": {
            "available_endpoints": endpoints,
            "total_count": len(endpoints),
            "categories": categories
        },
        "timestamp": int(time.time())
    }


def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "未指定端點", "data": []}))
        sys.exit(1)

    endpoint = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    if endpoint == "get_all_endpoints":
        result = get_all_endpoints()
    elif endpoint in ENDPOINTS:
        func = ENDPOINTS[endpoint]["func"]
        if args:
            result = func(*args)
        else:
            result = func()
    else:
        result = {"success": False, "error": f"未知端點: {endpoint}", "data": []}

    result["timestamp"] = int(time.time())
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
