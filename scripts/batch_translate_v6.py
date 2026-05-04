#!/usr/bin/env python3
"""Apply exact zh_TW translations for unchanged non-Chinese TS entries."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "fincept-qt" / "translations" / "fincept_zh_TW.ts"
ZH_RE = re.compile(r"[\u4e00-\u9fff]")


TRANSLATIONS: dict[str, str] = {
    "Country…": "國家…",
    "Country (e.g. USA, GBR, IND)": "國家（如 USA, GBR, IND）",
    "Description (optional)": "說明（選填）",
    "Developed Economy": "已開發經濟體",
    "Developing Economy": "開發中經濟體",
    "Middle Income": "中等收入",
    "Bilateral Agreement": "雙邊協定",
    "Regional Agreement": "區域協定",
    "Unilateral Liberalization": "單邊自由化",
    "Multilateral (WTO Round)": "多邊（WTO 回合）",
    "Customs Union (e.g. EU, Mercosur)": "關稅同盟（如 EU, Mercosur）",
    "House Bill": "眾議院法案",
    "Senate Bill": "參議院法案",
    "H. Con. Res.": "眾議院共同決議",
    "H. Joint Res.": "眾議院聯合決議",
    "H. Simple Res.": "眾議院簡單決議",
    "S. Con. Res.": "參議院共同決議",
    "S. Joint Res.": "參議院聯合決議",
    "S. Simple Res.": "參議院簡單決議",
    "Science & Tech": "科學與技術",
    "Re-exports": "再出口",
    "Re-imports": "再進口",
    "Periodicity": "週期性",
    "Quarterly": "每季",
    "Author:": "作者：",
    "Title:": "標題：",
    "Report:": "報告：",
    "Status:": "狀態：",
    "Company:": "公司：",
    "Leader:": "負責人：",
    "Error:": "錯誤：",
    "Schema:": "結構：",
    "Quick:": "快速：",
    "Fields:": "欄位：",
    "CATEGORY:": "分類：",
    "SOURCE:": "來源：",
    "REGION:": "地區：",
    "MODULE:": "模組：",
    "INSTRUMENT:": "工具：",
    "INTERVAL:": "間隔：",
    "Change...": "變更...",
    "Current Age:": "目前年齡：",
    "Retire Age:": "退休年齡：",
    "Inflation:": "通膨率：",
    "Withdrawal Rate:": "提領率：",
    "Exp. Return:": "預期報酬率：",
    "Funder Address:": "出資者地址：",
    "Private Key:": "私鑰：",
    "Signature Type:": "簽名類型：",
    "API Key ID:": "API 金鑰 ID：",
    "Token / API Key value": "Token / API 金鑰值",
    "INITIAL CAPITAL ($)": "初始資本（$）",
    "IMF INDICATOR": "IMF 指標",
    "FINCEPT MACRO — COMING SOON": "FINCEPT 總經 — 即將推出",
    "FINCEPT TERMINAL v4.0.0": "FINCEPT 終端 v4.0.0",
    "FREE API": "免費 API",
    "JSON EDITOR": "JSON 編輯器",
    "PER-ASSET MOMENTS": "各資產動差",
    "PEERS (comma-separated):": "同業（逗號分隔）：",
    "PROJECTED SAVINGS  ·  reference $%1 SKU": "預估節省 · 參考 $%1 SKU",
    "Short-Term Outlook (STEO)": "短期展望（STEO）",
    "Key terms": "關鍵詞",
    "Unconfigured": "未設定",
    "Isolated": "隔離",
    "LAYERED": "分層",
    "hidden": "隱藏",
    "Rebind:": "重新綁定：",
    "Saved: 0": "已儲存: 0",
    "Schemas: 7": "結構: 7",
    "Fields: --": "欄位: --",
    "SOURCE: --": "來源: --",
    "Net: —": "淨額: —",
    "Usage: —": "用量: —",
    "Vol:--": "波動率:--",
    "MKT: --": "市值: --",
    "Est: --": "預估: --",
    "20 Years": "20 年",
    "50 Years": "50 年",
    "24h VOL": "24 小時成交量",
    "Years (e.g. 2015-2023)": "年份（如 2015-2023）",
    "Showing %1 data": "顯示 %1 資料",
    "Clear Kalshi credentials?": "清除 Kalshi 認證資訊？",
    "Clear Polymarket credentials?": "清除 Polymarket 認證資訊？",
    "Cleared. Public RPC will be used.": "已清除。將使用公共 RPC。",
    "No key stored. Public RPC will be used.": "未儲存金鑰。將使用公共 RPC。",
    "Could not find request_token in pasted text": "在貼上的文字中找不到 request_token",
    "This connector does not support connectivity testing.": "此連接器不支援連線測試。",
    "Related markets are Polymarket-only": "相關市場僅限 Polymarket",
    "Opening your browser to complete the handshake…": "正在開啟瀏覽器以完成交握…",
    "Opening your browser to relay the transaction…": "正在開啟瀏覽器以轉發交易…",
    "Validating with RPC…": "使用 RPC 驗證中…",
    "Re-checking freshness…": "重新檢查新鮮度…",
    "Storage: 0 B / 500 MB": "儲存空間: 0 B / 500 MB",
    "Tickers (comma-separated, >= 2). Returns fetched via Yahoo Finance.": "股票代碼（逗號分隔，≥ 2）。報酬率透過 Yahoo Finance 擷取。",
    "Two sandboxed environments to keep library versions conflict-free": "兩個沙箱環境以避免程式庫版本衝突",
    "Total cost basis — the dashed horizontal line on the chart.": "總成本基礎 — 圖表上的虛線水平線。",
    "Numeric values (>= 30). Fits normal, student-t, lognormal (positive only), skewnormal.": "數值（≥ 30）。擬合常態、Student-t、對數常態（僅正值）、偏態常態分布。",
    "Numeric values (>= 8). Includes Jarque-Bera + Shapiro-Wilk normality tests.": "數值（≥ 8）。包含 Jarque-Bera + Shapiro-Wilk 常態性檢定。",
    "Numeric values (e.g. 10.5, 11.2, 9.8, 12.1, ...). Need at least 2.": "數值（如 10.5, 11.2, 9.8, 12.1, ...）。至少需要 2 個。",
    "Predicted values (same length as actual)": "預測值（與實際值等長）",
    "Realized actuals (>= 5 values)": "已實現實際值（≥ 5 個值）",
    "Realized returns (decimals, same length as predictions)": "已實現報酬率（小數，與預測等長）",
    "Realized returns (same length as factor)": "已實現報酬率（與因子等長）",
    "Realized returns (same length as predictions)": "已實現報酬率（與預測等長）",
    "Dependent variable y (>= 10 values)": "因變數 y（≥ 10 個值）",
    "Lower band (optional, same length as actuals)": "下界（選填，與實際值等長）",
    "Upper band (optional, same length as actuals)": "上界（選填，與實際值等長）",
    "Regressor x (single column, same length as y). For multi-feature use the JSON 2D form.": "自變數 x（單欄，與 y 等長）。多特徵請使用 JSON 2D 格式。",
    "Target value (e.g. 0.02)": "目標值（如 0.02）",
    "Quantiles in (0, 1) — e.g. 0.05, 0.5, 0.95": "分位數（0 到 1）— 如 0.05, 0.5, 0.95",
    "View confidences (e.g. 0.8,0.6)": "信心度（如 0.8,0.6）",
    "Comparable deals JSON array...": "可比較交易 JSON 陣列...",
    "Covariance matrix JSON: [[0.04,0.01],[0.01,0.09]]": "共變異數矩陣 JSON: [[0.04,0.01],[0.01,0.09]]",
    "Deals JSON with cash_pct and stock_pct fields...": "含 cash_pct 和 stock_pct 欄位的交易 JSON...",
    "Same JSON array format as Compare tab...": "與比較標籤頁相同的 JSON 陣列格式...",
    "Auto-login (TOTP)": "自動登入（TOTP）",
    "Auto-generated from\nHeading components.": "從標題元件自動產生。",
    "Tip: re-select component after\nediting data to re-render.": "提示：編輯資料後重新選取元件以重新渲染。",
    "ACS 5-year estimates, state level": "ACS 5 年估計，州級",
    "ISO-2 code…": "ISO-2 代碼…",
    "ISO-2 country code, e.g. USA, GBR, DEU\n": "ISO-2 國家代碼，如 USA, GBR, DEU\n",
    "Member code (e.g. US, CN)": "成員代碼（如 US, CN）",
    "Reporter (e.g. US, CN, DE)": "報告國（如 US, CN, DE）",
    "Pipeline ID (e.g. my_pipeline)": "Pipeline ID（如 my_pipeline）",
    "e.g. AAPL — fetched from Yahoo Finance": "如 AAPL — 透過 Yahoo Finance 擷取",
    "Ticker (AAPL, ^GSPC, BTC-USD) or comma-separated values": "股票代碼（AAPL, ^GSPC, BTC-USD）或逗號分隔值",
    "One per line:\nAuthorization: Bearer abc\nX-API-Key: xyz": "每行一個：\nAuthorization: Bearer abc\nX-API-Key: xyz",
    "comma-separated: bootstrap,jackknife,permutation": "逗號分隔: bootstrap,jackknife,permutation",
    "comma-separated: pca,kmeans,agglomerative": "逗號分隔: pca,kmeans,agglomerative",
    "comma-separated: ridge,lasso,random_forest,svr,knn": "逗號分隔: ridge,lasso,random_forest,svr,knn",
    "analytics library list": "分析程式庫清單",
    "trading library list": "交易程式庫清單",
    "basic API quota": "基本 API 配額",
    "restored from storage": "已從儲存空間還原",
    "set by PumpSwap; capped by slippage": "由 PumpSwap 設定；受滑點限制",
    "label: kw1, kw2": "標籤: kw1, kw2",
    "tag1, tag2, ...": "標籤1, 標籤2, ...",
    "enter password": "輸入密碼",
    "all-posts": "所有文章",
    "NORMALITY  (H₀: data is normally distributed; p > 0.05 ⇒ cannot reject normal)": "常態性檢定（H₀: 資料為常態分布；p > 0.05 ⇒ 無法拒絕常態）",
    "ADF (H₀: unit root → non-stationary)": "ADF 檢定（H₀: 存在單根 → 非定態）",
    "KPSS (H₀: stationary)": "KPSS 檢定（H₀: 定態）",
    "© 2024-2026 Fincept Corporation. All rights reserved.": "© 2024-2026 Fincept Corporation. 保留所有權利。",
    "Center (use {page})": "置中（使用 {page}）",
    "Extend flow lands with the Anchor program.": "使用 Anchor 程式延伸資金流。",
    "Withdraw flow lands with the Anchor program.": "使用 Anchor 程式提領資金流。",
    "L2 API credentials: derived (%1…)": "L2 API 認證資訊：已衍生（%1…）",
    "L2 API credentials: not derived": "L2 API 認證資訊：未衍生",
    "Loaded PEM from %1.": "已從 %1 載入 PEM。",
    "Unverified mint: %1": "未驗證代幣: %1",
    "used %1": "已使用 %1",
    "FLASH: %1": "快訊: %1",
    "LON %1": "經度 %1",
    "TOK %1": "代幣 %1",
    "VOL: %1": "成交量: %1",
    "● Agent: %1": "● 代理: %1",
    "Deepgram (API key required)": "Deepgram（需要 API 金鑰）",
    "Google (free, default)": "Google（免費，預設）",
    "Multilingual (nova-3 only)": "多語言（僅 nova-3）",
    "Requires BEA_API_KEY": "需要 BEA_API_KEY",
    "Requires EIA_API_KEY": "需要 EIA_API_KEY",
    "Requires WTO_API_KEY": "需要 WTO_API_KEY",
    "All Fincept Terminal features unlocked.": "所有 Fincept 終端功能已解鎖。",
    "Qt Multimedia not available.\nBuild with Qt6 Multimedia for inline playback.": "Qt Multimedia 不可用。\n使用 Qt6 Multimedia 建構以支援內嵌播放。",
    "QR Members (free)": "QR 會員（免費）",
    "•••••••• (saved)": "•••••••• （已儲存）",
    "—  data points  |  TALIpp Engine": "—  資料點  |  TALIpp 引擎",
}


def contains_chinese(text: str) -> bool:
    return bool(ZH_RE.search(text))


def main() -> None:
    tree = ET.parse(TS_PATH)
    root = tree.getroot()

    candidates = 0
    dictionary_hits = 0
    translated = 0

    for message in root.iter("message"):
        source = message.find("source")
        translation = message.find("translation")
        if source is None or translation is None:
            continue

        source_text = source.text or ""
        translation_text = translation.text or ""
        if source_text != translation_text or contains_chinese(source_text):
            continue

        candidates += 1
        new_text = TRANSLATIONS.get(source_text)
        if new_text is None:
            continue

        dictionary_hits += 1
        translation.text = new_text
        translation.attrib.pop("type", None)
        translated += 1

    if translated:
        tree.write(TS_PATH, encoding="utf-8", xml_declaration=True)

    print("batch_translate_v6 complete")
    print(f"dictionary entries: {len(TRANSLATIONS)}")
    print(f"candidate unchanged non-Chinese entries: {candidates}")
    print(f"dictionary hits: {dictionary_hits}")
    print(f"translated: {translated}")
    print(f"翻譯了 {translated} 條")


if __name__ == "__main__":
    main()
