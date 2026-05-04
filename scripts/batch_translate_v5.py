#!/usr/bin/env python3
"""Translate remaining unchanged English entries in fincept_zh_TW.ts.

The script is intentionally conservative:
- only touches entries whose translation equals source;
- skips code-like strings, regexes, HTML/QSS, headers, ticker examples, and brands;
- prefers exact format-string translations, then falls back to word replacement.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "fincept-qt" / "translations" / "fincept_zh_TW.ts"
REMAINING_PATH = Path("/tmp/remaining.txt")

ZH_RE = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_RE = re.compile(r"[A-Za-z]{3,}")
PLACEHOLDER_RE = re.compile(r"%\d+")


FORMAT_TRANSLATIONS: dict[str, str] = {
    "%1 LOADING": "%1 載入中",
    "%1 FETCHING DATA...": "%1 擷取資料中...",
    "%1 LOADING OBSERVATIONS...": "%1 載入觀察資料中...",
    "%1d ago": "%1 天前",
    "%1h ago": "%1 小時前",
    "%1m ago": "%1 分鐘前",
    "%1s ago": "%1 秒前",
    "%1 ATTEMPT%2 REMAINING": "%1 次嘗試%2剩餘",
    "%1 WATCHES %2 HIT": "%1 觀察 %2 命中",
    "%1 WATCHES  %2 HIT": "%1 觀察  %2 命中",
    "%1 / %2 windows": "%1 / %2 視窗",
    "%1 (%2 shares)": "%1（%2 股）",
    "%1 returned empty output": "%1 回傳空輸出",
    "%1 returned malformed JSON": "%1 回傳格式錯誤的 JSON",
    "%1 connection %2": "%1 連線 %2",
    "%1 deployment(s)": "%1 個部署",
    "%1 tools (%2 internal · %3 external)": "%1 個工具（%2 內部 · %3 外部）",
    "%1 tools  (%2 internal · %3 external)": "%1 個工具（%2 內部 · %3 外部）",
    "+%1 more": "+%1 更多",
    "+%1 src": "+%1 來源",
    "· %1 likes": "· %1 個讚",
    "[MEMBER] %1": "[成員] %1",
    "%1 bps": "%1 基點",
    "%1 mkts": "%1 個市場",
    "DONE (%1ms)": "完成 (%1ms)",
    "DONE %1": "完成 %1",
    "FAILED: %1": "失敗：%1",
    "FAILED %1": "失敗 %1",
    "ERROR [%1]: %2": "錯誤 [%1]：%2",
    "%1: bad JSON: %2": "%1：錯誤的 JSON：%2",
    "%1 triggered on %2": "%1 在 %2 觸發",
    "%1 cache incomplete (only %2 NSE equities) — re-downloading": "%1 快取不完整（僅 %2 檔 NSE 股票）— 重新下載中",
    "%1 | %2 %3 | Conf: %4%\n%5": "%1 | %2 %3 | 信心度：%4%\n%5",
    "%1\n  %2 | %3 tools": "%1\n  %2 | %3 個工具",
    "%1\n\n%2\n\nSent: %3": "%1\n\n%2\n\n傳送：%3",
    "%1\nsectors": "%1\n類股",
    "%1  ·  %2  ·  Opened %3": "%1  ·  %2  ·  已開啟 %3",
    "%1 %2 BEAR": "%1 %2 空方",
    "%1 %2 BULL": "%1 %2 多方",
    "%1 %2 x%3 via %4": "%1 %2 x%3 透過 %4",
    "%1  fwd %2": "%1  遠期 %2",
    "%1#dup%2": "%1#複製%2",
    "%1%  %2d cvr": "%1%  %2天覆蓋率",
    "%1: TODO": "%1：待辦",
    "Active profile:  <b>%1</b>": "啟用設定檔：<b>%1</b>",
    "Adding MCP server: %1": "新增 MCP 伺服器：%1",
    "Agent chat [%1]: \\": "代理對話 [%1]：\\",
    "Analysts (%1)": "分析師 (%1)",
    "Ann. vol %1% > max %2%": "年化波動率 %1% > 最大值 %2%",
    "Applying migration v%1: %2": "套用遷移 v%1：%2",
    "Available Models (%1)\n\n": "可用模型 (%1)\n\n",
    "Backtest requested: %1 on %2": "已請求回測：%1 於 %2",
    "Best: %1": "最佳：%1",
    "Board (%1/%2)": "看板 (%1/%2)",
    "Built panel: %1": "已建立面板：%1",
    "Bulk-deleted %1 connections": "已批次刪除 %1 個連線",
    "Bulk-disabled %1 connections": "已批次停用 %1 個連線",
    "Bulk-enabled %1 connections": "已批次啟用 %1 個連線",
    "COST %1 %2": "成本 %1 %2",
    "CSV exported to: %1": "CSV 已匯出至：%1",
    "Cache hit [%1]": "快取命中 [%1]",
    "Calmar: %1": "Calmar：%1",
    "Cell %1": "儲存格 %1",
    "Clone  %1": "複製  %1",
    "Col %1": "欄 %1",
    "Comparison slot added. Total slots: %1": "已新增比較插槽。插槽總數：%1",
    "Creating monitor: %1": "建立監控：%1",
    "Creating plan for: %1": "為 %1 建立計畫",
    "DAY  %1%2%": "日  %1%2%",
    "Delivered pending state on navigate: %1": "導覽時已送達待處理狀態：%1",
    "Delivered pending state to: %1": "已送達待處理狀態至：%1",
    "Delivered via %1": "已透過 %1 送達",
    "Dock layout corrupt: %1 open areas — resetting": "停駐佈局損壞：%1 個開啟區域 — 正在重設",
    "Dock layout version mismatch (saved %1, expected %2) — resetting": "停駐佈局版本不符（已儲存 %1，預期 %2）— 正在重設",
    "Download progress: %1 / %2 bytes": "下載進度：%1 / %2 位元組",
    "Downloaded AngelOne master contract: %1 bytes": "已下載 AngelOne 主合約：%1 位元組",
    "Downloaded Groww instrument CSV: %1 bytes": "已下載 Groww 工具 CSV：%1 位元組",
    "Duplicated '%1' → '%2'": "已複製 '%1' → '%2'",
    "Edit  %1": "編輯  %1",
    "Elapsed: %1m %2s": "已耗時：%1 分 %2 秒",
    "Elapsed: %1s": "已耗時：%1 秒",
    "Ensemble: %1  [%2]\nModels: %3": "集成：%1  [%2]\n模型：%3",
    "Est: $%1": "估計：$%1",
    "Est: %1%2": "估計：%1%2",
    "Events (%1/%2)": "事件 (%1/%2)",
    "Exchange changed: %1 → %2": "交易所已變更：%1 → %2",
    "Execute routed query: %1": "執行已路由查詢：%1",
    "Fee: %1": "手續費：%1",
    "Feed vote result: ok=%1": "動態投票結果：ok=%1",
    "Fees: %1": "手續費：%1",
    "Final: $%1": "最終：$%1",
    "Fincept Terminal [%1]": "Fincept 終端 [%1]",
    "Fincept async poll %1 status=%2": "Fincept 非同步輪詢 %1 狀態=%2",
    "Flow clean — score: %1 — %2": "流程乾淨 — 分數：%1 — %2",
    "Freq: %1  |  Window: %2 days  |  Next: %3  |  Last: %4": "頻率：%1  |  視窗：%2 天  |  下次：%3  |  上次：%4",
    "Funds (%1/%2)": "基金 (%1/%2)",
    "Getting session: %1": "取得工作階段：%1",
    "Gr %1%  Net %2%": "總 %1%  淨 %2%",
    "Header %1": "標頭 %1",
    "Holders (%1/%2)": "持有者 (%1/%2)",
    "ID: %1\nQuery: %2\nStatus: %3\n": "ID：%1\n查詢：%2\n狀態：%3\n",
    "Initialized focused account: %1": "已初始化聚焦帳戶：%1",
    "Insiders (%1/%2)": "內部人 (%1/%2)",
    "Installing %1/%2: %3": "安裝中 %1/%2：%3",
    "Kalshi bridge: non-JSON response — ": "Kalshi 橋接：非 JSON 回應 — ",
    "Kalshi lifecycle: %1 → %2": "Kalshi 生命週期：%1 → %2",
    "LAT: %1ms": "延遲：%1ms",
    "LLM requested %1 tool calls": "LLM 請求了 %1 次工具呼叫",
    "Last run %1  •  %2ms": "上次執行 %1  •  %2ms",
    "Listed %1 sessions": "已列出 %1 個工作階段",
    "Listening on 127.0.0.1:%1": "正在監聽 127.0.0.1:%1",
    "MCP tool server running at %1\n\nAvailable tools:\n  %2\n\n": "MCP 工具伺服器執行於 %1\n\n可用工具：\n  %2\n\n",
    "MKT: $%1": "市值：$%1",
    "MKT: %1%2": "市值：%1%2",
    "Max %1": "最大 %1",
    "Migration v%1 applied successfully": "遷移 v%1 已成功套用",
    "Model list populated: %1 entries": "模型清單已填充：%1 個條目",
    "Multi vessel: %1 found": "多船舶：找到 %1 個",
    "Multi-query: %1": "多重查詢：%1",
    "NAME: %1\n\n": "名稱：%1\n\n",
    "Net: %1%2": "淨值：%1%2",
    "OK — %1 row(s) affected": "OK — %1 列受影響",
    "OK — %1 row(s) returned%2": "OK — 回傳 %1 列%2",
    "OUT [%1]": "輸出 [%1]",
    "Optimized Models: %1\n\n": "已最佳化模型：%1\n\n",
    "Optimizing prompt (%1): \\": "最佳化提示詞 (%1)：\\",
    "PRI: %1": "優先級：%1",
    "Paper order filled: %1 @ %2": "模擬訂單已成交：%1 @ %2",
    "Paper order queued: %1": "模擬訂單已佇列：%1",
    "Paper order: %1 %2 x%3 account=%4": "模擬訂單：%1 %2 x%3 帳戶=%4",
    "Paper trade: %1 %2 %3": "模擬交易：%1 %2 %3",
    "Peers (%1/%2)": "同業 (%1/%2)",
    "Port 5010 busy - use manual paste fallback": "連接埠 5010 忙碌 - 使用手動貼上備援",
    "Price feed started (interval=%1s)": "價格資料流已啟動（間隔=%1 秒）",
    "Price: %1   Chg: %2%": "價格：%1   漲跌：%2%",
    "Prompt optimized: %1 chars -> %2 chars": "提示詞已最佳化：%1 字元 -> %2 字元",
    "Python check: path=%1  exists=%2": "Python 檢查：path=%1  exists=%2",
    "QUALITY: %1%": "品質：%1%",
    "QUOTE: %1": "報價：%1",
    "QuantStats: %1": "QuantStats：%1",
    "RUN OK — %1 fields extracted": "執行成功 — 已擷取 %1 個欄位",
    "Refreshed tool cache: %1 total (%2 internal, %3 external)": "已重新整理工具快取：共 %1 個（%2 內部，%3 外部）",
    "Rejected stale filter gen %1": "已拒絕過期篩選產生 %1",
    "Requesting: %1 (risk=%2)": "請求中：%1（風險=%2）",
    "Resolved [%1/%2] → profile '%3'": "已解析 [%1/%2] → 設定檔 '%3'",
    "Resolved [%1] via legacy active provider fallback": "已透過舊版啟用供應商備援解析 [%1]",
    "Retraining %1 — 0/%2 windows": "重新訓練 %1 — 0/%2 視窗",
    "Retraining %1...": "重新訓練 %1...",
    "Routed → %1 (intent: %2, confidence: %3%)": "已路由 → %1（意圖：%2，信心度：%3%）",
    "Routing query: %1": "路由查詢：%1",
    "Row %1: only %2 columns, skipping": "第 %1 列：只有 %2 欄，已跳過",
    "Run %1 %2 [%3]": "執行 %1 %2 [%3]",
    "SENT: %1": "已傳送：%1",
    "STT fatal: %1": "STT 嚴重錯誤：%1",
    "STT status: %1": "STT 狀態：%1",
    "Saving strategy: %1": "儲存策略：%1",
    "Schema at version %1": "結構版本 %1",
    "Send [%1]: \\": "傳送 [%1]：\\",
    "Series: %1": "序列：%1",
    "Set active agent: %1": "設定啟用代理：%1",
    "Setup file missing: %1 — reinstall the application": "安裝檔缺失：%1 — 請重新安裝應用程式",
    "Sha256 mismatch — expected=%1, actual=%2": "Sha256 不匹配 — 預期=%1，實際=%2",
    "Sha256 verified: %1": "Sha256 已驗證：%1",
    "Slot %1 removed. Remaining: %2": "插槽 %1 已移除。剩餘：%2",
    "Slot removed. %1 slot(s) remaining": "插槽已移除。剩餘 %1 個插槽",
    "Starting retrain: %1  |  %2 windows": "開始重新訓練：%1  |  %2 個視窗",
    "Stop requested: %1": "已請求停止：%1",
    "Streaming agent query [%1]: %2": "串流代理查詢 [%1]：%2",
    "Subscribed %1 tokens (mode %2)": "已訂閱 %1 個代幣（模式 %2）",
    "Supply (%1)": "供應量 (%1)",
    "System clock rolled back %1s since last lockout write — ": "系統時鐘自上次鎖定寫入後回撥 %1 秒 — ",
    "Table populated: %1 total, %2 missing": "表格已填充：共 %1 個，缺失 %2 個",
    "Target: %1 (%2)": "目標：%1（%2）",
    "Task %1 — %2% — %3": "任務 %1 — %2% — %3",
    "Test %1: %2 — %3": "測試 %1：%2 — %3",
    "Test: %1": "測試：%1",
    "Text msg: %1": "文字訊息：%1",
    "Ticket #%1": "工單 #%1",
    "Tool '%1' %2": "工具 '%1' %2",
    "Tool '%1' threw exception: %2": "工具 '%1' 擲出例外：%2",
    "Total: %1  |  Fav: %2": "合計：%1  |  收藏：%2",
    "Trigger suppressed by filter: %1": "觸發已被篩選器抑制：%1",
    "UTC %1": "UTC %1",
    "Unsupported platform/arch: %1 / %2": "不支援的平台/架構：%1 / %2",
    "View confidences (e.g. 0.8,0.6)": "檢視信心度（例如 0.8,0.6）",
    "Voice provider '%1' process exited (code=%2, status=%3)": "語音供應商 '%1' 程序已結束（代碼=%2，狀態=%3）",
    "Voice provider '%1' started": "語音供應商 '%1' 已啟動",
    "Voice provider '%1' stopped": "語音供應商 '%1' 已停止",
    "Voice provider selected: %1": "已選取語音供應商：%1",
    "Vol: %1%": "波動率：%1%",
    "Vote result: ok=%1 msg=%2": "投票結果：ok=%1 訊息=%2",
    "What's new:\n%1\n\n": "最新內容：\n%1\n\n",
    "Window %1/%2": "視窗 %1/%2",
    "[%1 items]": "[%1 個項目]",
    "[%1/%2] Cache hit": "[%1/%2] 快取命中",
    "[%1] Installed: %2": "[%1] 已安裝：%2",
    "[%1] Skipped (failed): %2 — %3": "[%1] 已跳過（失敗）：%2 — %3",
    "[%1] WS status: %2": "[%1] WS 狀態：%2",
    "[%1] parsed %2 installed packages": "[%1] 已解析 %2 個已安裝套件",
    "[DONE] %1": "[完成] %1",
    "[Fetching %1...]": "[擷取 %1 中...]",
    "[Fincept] %1": "[Fincept] %1",
    "[Fincept] %1: %2": "[Fincept] %1：%2",
    "[Fincept] %1\n%2": "[Fincept] %1\n%2",
    "[REQ] %1": "[請求] %1",
    "[START] %1": "[開始] %1",
    "\n%1 msg": "\n%1 則訊息",
    "● LIVE": "● 即時",
    "⚠  DELETE PORTFOLIO": "⚠  刪除投資組合",
    "manual paste extracted token: %1": "手動貼上已擷取權杖：%1",
    "manual paste input (%1 chars): %2": "手動貼上輸入（%1 字元）：%2",
    "navigate('%1') suppressed — terminal locked": "navigate('%1') 已抑制 — 終端已鎖定",
    "request(): %1 topic(s) have no producer — likely unregistered ": "request()：%1 個主題沒有 producer — 可能尚未註冊 ",
    "Assessing Process Quality...": "評估程序品質中...",
    "Loading deals...": "載入交易中...",
    "Malformed request": "格式錯誤的請求",
    "Needs intraday data — daily snapshots only.": "需要日內資料 — 僅有每日快照。",
    "OK — no columns returned": "OK — 未回傳欄位",
    "Please describe:\n": "請描述：\n",
    "Python response is not JSON: ": "Python 回應不是 JSON：",
    "Query returned failure": "查詢回傳失敗",
    "RUN FAILED — ": "執行失敗 — ",
    "Script reported failure": "腳本回報失敗",
    "Setup is taking longer than expected — possibly a slow internet connection.\n": "安裝時間比預期更久 — 可能是網路連線較慢。\n",
    "Training ended without result": "訓練結束但沒有結果",
    "Training process exited abnormally (exit=%1) after emitting result": "訓練程序在輸出結果後異常結束（exit=%1）",
    "active is '%1' not '%2'": "啟用值是 '%1'，不是 '%2'",
    "in-flight": "進行中",
    "step %1": "步驟 %1",
}


EXACT_TRANSLATIONS: dict[str, str] = {
    **FORMAT_TRANSLATIONS,
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
    "NO DATA — SELECT A SERIES FROM THE LEFT PANEL": "無資料 — 請從左側面板選擇序列",
    "NO PORTFOLIOS — CREATE ONE": "無投資組合 — 建立一個",
    "NO DISCUSSIONS YET": "尚無討論",
    "NO POSTS YET": "尚無文章",
    "NO REPLIES YET": "尚無回覆",
    "Loading…": "載入中…",
    "Loading...": "載入中...",
    "Aborted.": "已中止。",
    "Cancelled.": "已取消。",
    "Complete": "完成",
    "Failed.": "失敗。",
    "Failed: %1": "失敗：%1",
    "Stale.": "已過期。",
    "Waiting": "等候中",
    "Streaming": "串流中",
    "hidden": "隱藏",
}


WORD_TRANSLATIONS: dict[str, str] = {
    "loading": "載入中",
    "fetching": "擷取中",
    "saving": "儲存中",
    "creating": "建立中",
    "verifying": "驗證中",
    "analyzing": "分析中",
    "generating": "產生中",
    "executing": "執行中",
    "computing": "計算中",
    "connecting": "連線中",
    "downloading": "下載中",
    "installing": "安裝中",
    "retraining": "重新訓練中",
    "streaming": "串流中",
    "requesting": "請求中",
    "routing": "路由中",
    "optimizing": "最佳化中",
    "discovering": "探索中",
    "starting": "啟動中",
    "waiting": "等候中",
    "triggered": "觸發",
    "returned": "回傳",
    "delivered": "已送達",
    "resolved": "已解析",
    "rejected": "已拒絕",
    "subscribed": "已訂閱",
    "initialized": "已初始化",
    "populated": "已填充",
    "installed": "已安裝",
    "skipped": "已跳過",
    "duplicated": "已複製",
    "applied": "已套用",
    "exported": "已匯出",
    "refreshed": "已重新整理",
    "listed": "已列出",
    "confirmed": "已確認",
    "cancelled": "已取消",
    "aborted": "已中止",
    "downloaded": "已下載",
    "verified": "已驗證",
    "elapsed": "已耗時",
    "migration": "遷移",
    "cache": "快取",
    "missing": "缺失",
    "corrupt": "損壞",
    "mismatch": "不匹配",
    "incomplete": "不完整",
    "threshold": "閾值",
    "anomalies": "異常",
    "snapshot": "快照",
    "transactions": "交易",
    "holdings": "持股",
    "portfolio": "投資組合",
    "vessels": "船舶",
    "connectors": "連接器",
    "monitors": "監控",
    "widgets": "小工具",
    "sessions": "工作階段",
    "messages": "訊息",
    "packages": "套件",
    "entries": "條目",
    "schedule": "排程",
    "sources": "來源",
    "agents": "代理",
    "factors": "因子",
    "fields": "欄位",
    "columns": "欄位",
    "windows": "視窗",
    "tools": "工具",
    "servers": "伺服器",
    "models": "模型",
    "internal": "內部",
    "external": "外部",
    "active": "啟用中",
    "available": "可用",
    "remaining": "剩餘",
    "running": "執行中",
    "pending": "待處理",
    "bytes": "位元組",
    "affected": "受影響",
    "selected": "已選取",
    "configured": "已設定",
    "registered": "已註冊",
    "detected": "已偵測",
    "supported": "已支援",
    "required": "必填",
    "enabled": "已啟用",
    "disabled": "已停用",
    "failed": "失敗",
    "success": "成功",
    "error": "錯誤",
    "ready": "就緒",
    "busy": "忙碌",
    "idle": "閒置",
    "live": "即時",
    "stale": "過期",
    "total": "合計",
    "result": "結果",
    "output": "輸出",
    "status": "狀態",
    "version": "版本",
    "progress": "進度",
    "attempt": "嘗試",
    "confidence": "信心度",
    "score": "分數",
    "quality": "品質",
    "interval": "間隔",
    "frequency": "頻率",
    "window": "視窗",
    "column": "欄位",
    "row": "列",
    "cell": "儲存格",
    "sheet": "工作表",
    "header": "標頭",
    "profile": "設定檔",
    "account": "帳戶",
    "member": "成員",
    "connection": "連線",
    "request": "請求",
    "response": "回應",
    "query": "查詢",
    "schema": "結構",
    "parser": "解析器",
    "backend": "後端",
    "process": "程序",
    "worker": "工作程序",
    "kernel": "核心",
    "broker": "經紀商",
    "exchange": "交易所",
    "instrument": "工具",
    "symbol": "代碼",
    "ticker": "股票代碼",
    "price": "價格",
    "spread": "價差",
    "volume": "成交量",
    "balance": "餘額",
    "fee": "手續費",
    "vote": "投票",
    "reply": "回覆",
    "post": "文章",
    "comment": "留言",
    "article": "文章",
    "community": "社群",
    "discussion": "討論",
    "competition": "競賽",
    "team": "團隊",
    "slot": "插槽",
    "panel": "面板",
    "layout": "佈局",
    "template": "範本",
    "monitor": "監控",
    "inspector": "檢視器",
    "explorer": "瀏覽器",
    "navigator": "導覽",
    "filter": "篩選",
    "selector": "選取器",
    "override": "覆寫",
    "fallback": "備援",
    "legacy": "舊版",
    "done": "完成",
    "opened": "已開啟",
    "sent": "已傳送",
    "shares": "股",
    "likes": "個讚",
    "topics": "主題",
    "producer": "producer",
    "chars": "字元",
    "risk": "風險",
    "intent": "意圖",
    "producer": "producer",
}


BRANDS = {
    "Fincept",
    "FinceptTerminal",
    "Kalshi",
    "Polymarket",
    "Zerodha",
    "AngelOne",
    "Groww",
    "QuantStats",
    "TALIpp",
}

SKIP_EXACT = {
    "AAPL",
    "MSFT",
    "GOOG",
    "AMZN",
    "SPY,AAPL,MSFT",
    "AAPL,MSFT,GOOG,AMZN",
    "AAPL, MSFT, ...",
    "AAPL, MSFT, TSLA...",
    "AAPL, MSFT, ^GSPC, BTC-USD ...",
    "MSFT,GOOG,AMZN",
    "SH000300 (CSI300)",
    "^GSPTSE",
    "^STOXX50E",
    "YYYY-MM-DD",
    "yyyy-MM-dd",
    "KEY=value KEY2=value2",
    "-----BEGIN RSA PRIVATE KEY-----\\n…paste PEM contents here…\\n-----END RSA PRIVATE KEY-----",
    "download-url",
    "latest-version",
    "open-url",
    "sha256",
    "linux-arm64",
    "linux-x64",
    "macos-arm64",
    "macos-x64",
    "windows-arm64",
    "windows-x64",
}

SKIP_PATTERNS = [
    re.compile(r"\\[AbBdDsSwWZ]|\[\^|<\([^>]+\)>|\(\.\*\?\)|\(\?P?<|\^\(|\$\)|\|</"),
    re.compile(r"^<[^>]+>.*</[^>]+>$", re.S),
    re.compile(r"^</?[\w:-]+[^>]*>$"),
    re.compile(r"^(Content-Type|Cache-Control|Connection|Access-Control-|Referrer-Policy|X-Content-Type-Options|Authorization|Accept|User-Agent):", re.I),
    re.compile(r"^(QListWidget|QPlainTextEdit|Q[A-Za-z]+)\s*[{:]"),
    re.compile(r"\b(color|background|font-size|border|padding|margin)\s*:"),
    re.compile(r".*\.(db|py|json|csv|pem|sqlite|log|txt|md|html?|qml|cpp|h|ts|zip|exe|dll)$", re.I),
    re.compile(r"(^|/)[\w.-]+/[\w./{}%'-]+$"),
    re.compile(r"^[A-Z]{1,6}(,[A-Z]{1,6})+(\.\.\.)?$"),
    re.compile(r"^[A-Z]{1,6}(, ?[A-Z]{1,6})+.*$"),
    re.compile(r"^\^?[A-Z]{1,6}([.-][A-Z]{1,6})?$"),
    re.compile(r"^[a-z]+-(arm64|x64)$"),
    re.compile(r"^[{}()[\]<>|/\\:;.,+\-*=#@$%^&~!?·•…\s]+$"),
    re.compile(r"^[-+]?\$?%?\d+([.,:/]\d+)*[A-Za-z%/]*$"),
    re.compile(r"^(account|broker|window|root|array)\b[.\[\]_%\w/-]*$"),
    re.compile(r"^[-\w]+@\w+\.\w+$"),
    re.compile(r"^-----BEGIN .* KEY-----"),
    re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\([^)]*\)$"),
    re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*=%\d+"),
]


def normalized(text: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", text.strip())


def has_chinese(text: str) -> bool:
    return bool(ZH_RE.search(text))


def is_candidate(source_text: str, translation_text: str) -> bool:
    return (
        translation_text == source_text
        and not has_chinese(translation_text)
        and len(translation_text) > 5
        and bool(EN_WORD_RE.search(translation_text))
    )


def load_remaining(path: Path = REMAINING_PATH) -> set[str]:
    if not path.exists():
        return set()

    remaining: set[str] = set()
    line_re = re.compile(r"^\[[^\]]+\]\s*(.*)$")
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip("\n")
        match = line_re.match(line)
        text = match.group(1) if match else line
        if text:
            remaining.add(text)
    return remaining


def build_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for key, value in EXACT_TRANSLATIONS.items():
        variants = [(key, value)]
        if "\n" in key or "\n" in value:
            variants.append((key.replace("\n", r"\n"), value.replace("\n", r"\n")))
        if "\r" in key or "\r" in value:
            variants.append((key.replace("\r", r"\r"), value.replace("\r", r"\r")))
        for variant_key, variant_value in variants:
            lookup[variant_key] = variant_value
            lookup[normalized(variant_key)] = variant_value
    return lookup


LOOKUP = build_lookup()


def should_skip(text: str) -> bool:
    s = normalized(text)
    if not s or has_chinese(s):
        return True
    if s in SKIP_EXACT:
        return True
    if "<" in s and ">" in s:
        return True
    if any(re.search(rf"\b{re.escape(brand)}\b", s) for brand in BRANDS) and s not in LOOKUP:
        return True
    return any(pattern.search(s) for pattern in SKIP_PATTERNS)


def exact_translate(text: str) -> str | None:
    s = normalized(text)
    if s in LOOKUP:
        return LOOKUP[s]
    compact = re.sub(r"\s+", " ", s)
    if compact in LOOKUP:
        return LOOKUP[compact]
    return None


def translate_words(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        lower = word.lower()
        return WORD_TRANSLATIONS.get(lower, word)

    return re.sub(r"\b[A-Za-z][A-Za-z'-]*\b", replace, text)


def fallback_allowed(text: str) -> bool:
    if should_skip(text):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    if not words:
        return False
    translated_hits = sum(1 for word in words if word.lower() in WORD_TRANSLATIONS)
    if translated_hits == 0:
        return False

    # Keep prose/examples that need human translation out unless several terms are known.
    if len(words) > 8 and translated_hits < 2 and not PLACEHOLDER_RE.search(text):
        return False
    return True


def translate_text(text: str) -> str | None:
    lead_match = re.match(r"^\s*", text)
    trail_match = re.search(r"\s*$", text)
    lead = lead_match.group(0) if lead_match else ""
    trail = trail_match.group(0) if trail_match else ""
    core = text[len(lead) : len(text) - len(trail)]
    if not core:
        return None

    exact = exact_translate(core)
    if exact is not None:
        return f"{lead}{exact}{trail}"

    if not fallback_allowed(core):
        return None

    replaced = translate_words(core)
    if replaced != core and has_chinese(replaced):
        return f"{lead}{replaced}{trail}"
    return None


def main() -> None:
    if len(FORMAT_TRANSLATIONS) < 200:
        raise RuntimeError(f"FORMAT_TRANSLATIONS must contain at least 200 entries, got {len(FORMAT_TRANSLATIONS)}")

    remaining_hint = load_remaining()
    tree = ET.parse(TS_PATH)
    root = tree.getroot()

    candidates = translated = exact_hits = fallback_hits = skipped = unchanged = hinted = 0

    for message in root.iter("message"):
        source = message.find("source")
        translation = message.find("translation")
        if source is None or translation is None:
            continue

        source_text = source.text or ""
        translation_text = translation.text or ""
        if not is_candidate(source_text, translation_text):
            continue

        candidates += 1
        if source_text in remaining_hint or normalized(source_text) in remaining_hint:
            hinted += 1

        exact = exact_translate(source_text)
        new_text = exact if exact is not None else translate_text(source_text)
        if new_text and new_text != translation_text:
            translation.text = new_text
            translation.attrib.pop("type", None)
            translated += 1
            if exact is not None:
                exact_hits += 1
            else:
                fallback_hits += 1
        elif should_skip(source_text):
            skipped += 1
        else:
            unchanged += 1

    tree.write(TS_PATH, encoding="utf-8", xml_declaration=True)

    print("batch_translate_v5 complete")
    print(f"remaining.txt entries: {len(remaining_hint)}")
    print(f"format dictionary entries: {len(FORMAT_TRANSLATIONS)}")
    print(f"candidate unchanged English entries: {candidates}")
    print(f"candidates also present in remaining.txt: {hinted}")
    print(f"translated: {translated}")
    print(f"  exact: {exact_hits}")
    print(f"  fallback word replacement: {fallback_hits}")
    print(f"skipped: {skipped}")
    print(f"unchanged/no safe dictionary hit: {unchanged}")


if __name__ == "__main__":
    main()
