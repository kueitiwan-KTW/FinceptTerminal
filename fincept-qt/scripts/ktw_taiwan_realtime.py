#!/usr/bin/env python3
"""
台股即時行情橋接器 (KTW Taiwan Realtime Bridge)
透過 KTW SaaS Platform 代理存取 Intelligence 的 Fugle 即時行情。

用途：
  - Fincept Terminal 的即時行情 feed
  - 透過 Platform 代理 (/api/fincept/quotes) 存取 Intelligence 內網的行情 API
  - 盤中時段提供即時報價，盤後回退到 yfinance

環境變數：
  KTW_SAAS_URL — Platform 服務的 base URL（例如 https://ktwsmart.com）
  KTW_API_KEY  — SaaS 認證 token（Payload JWT）

端點：
  stream_snapshot    — 取得當前 SSE 快照（一次性查詢）
  stream_status      — 查詢串流狀態
  latest_quotes      — REST 最新行情
  sparkline          — 走勢線數據
"""

import sys
import json
import os
import time

try:
    import requests
except ImportError:
    # 無 requests 套件時 fallback
    requests = None


def get_base_url():
    """取得 Platform 服務的 base URL"""
    url = os.environ.get('KTW_SAAS_URL', '').rstrip('/')
    if not url:
        return None
    return url


def get_auth_headers():
    """取得認證 headers（Bearer token）"""
    api_key = os.environ.get('KTW_API_KEY', '')
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    return headers


def stream_snapshot():
    """
    一次性 SSE 快照 — 連上 /api/quotes/stream 收第一筆 snapshot 後立即斷開。
    適合 Terminal 定時輪詢使用。

    注意：SSE 端點無法透過 Platform 代理（Next.js 不支援長連線），
    此功能保留給未來直連 Intelligence 的場景。
    目前改用 latest_quotes() 作為替代。
    """
    # 由於 SSE 無法走 Platform 代理，改用 latest_quotes 替代
    return latest_quotes()


def stream_status():
    """查詢 Fugle 串流狀態（透過 Platform 代理）"""
    base_url = get_base_url()
    if not base_url:
        return {"success": False, "error": "KTW_SAAS_URL 環境變數未設定", "data": []}

    try:
        resp = requests.get(
            f"{base_url}/api/fincept/quotes",
            params={"action": "stream-status"},
            headers=get_auth_headers(),
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        return {"success": True, "data": [data], "count": 1}
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


def latest_quotes():
    """REST 最新行情（各標的最新一筆，透過 Platform 代理）"""
    base_url = get_base_url()
    if not base_url:
        return {"success": False, "error": "KTW_SAAS_URL 環境變數未設定", "data": []}

    try:
        resp = requests.get(
            f"{base_url}/api/fincept/quotes",
            params={"action": "latest"},
            headers=get_auth_headers(),
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        return {
            "success": True,
            "data": result.get("data", []),
            "count": result.get("count", 0),
            "source": "fugle_rest"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


def sparkline(symbols="", hours="24"):
    """走勢線數據（透過 Platform 代理）"""
    base_url = get_base_url()
    if not base_url:
        return {"success": False, "error": "KTW_SAAS_URL 環境變數未設定", "data": []}

    try:
        params = {"action": "sparkline", "hours": hours}
        if symbols:
            params["symbols"] = symbols
        resp = requests.get(
            f"{base_url}/api/fincept/quotes",
            params=params,
            headers=get_auth_headers(),
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        return {
            "success": True,
            "data": result.get("data", []),
            "count": len(result.get("data", [])),
            "source": "fugle_rest"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


def quotes_list(page="1", limit="20", symbol=""):
    """行情列表（分頁查詢，透過 Platform 代理）"""
    base_url = get_base_url()
    if not base_url:
        return {"success": False, "error": "KTW_SAAS_URL 環境變數未設定", "data": []}

    try:
        params = {"action": "list", "page": page, "limit": limit}
        if symbol:
            params["symbol"] = symbol
        resp = requests.get(
            f"{base_url}/api/fincept/quotes",
            params=params,
            headers=get_auth_headers(),
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        return {
            "success": True,
            "data": result.get("data", []),
            "count": result.get("total", 0),
            "page": result.get("page", 1),
            "source": "fugle_rest"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": []}


# ==================== 端點註冊表 ====================

ENDPOINTS = {
    "stream_snapshot": {"func": stream_snapshot, "desc": "Fugle SSE 即時行情快照（目前走 REST）", "category": "TW Realtime Stream"},
    "stream_status": {"func": stream_status, "desc": "Fugle 串流狀態查詢", "category": "TW Realtime Stream"},
    "latest_quotes": {"func": latest_quotes, "desc": "各標的最新行情（REST）", "category": "TW Realtime REST"},
    "sparkline": {"func": sparkline, "desc": "走勢線數據", "category": "TW Realtime REST"},
    "quotes_list": {"func": quotes_list, "desc": "行情列表（分頁）", "category": "TW Realtime REST"},
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
            "categories": categories,
            "requires": "KTW_SAAS_URL + KTW_API_KEY 環境變數"
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
