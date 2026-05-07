#!/usr/bin/env python3
"""
量化模組與剩餘面板全量翻譯補齊。
從 C++ tr() 提取的缺失字串，自動產生翻譯並注入 .ts。
"""

import re
import json
from pathlib import Path

SRC_DIR = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/src")
TS_FILE = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts")
BINARY_CONTEXTS = Path("/tmp/binary_contexts.txt")

# 大量翻譯詞典 — 量化/金融/技術術語
TERM_MAP = {
    # 基礎 UI
    "Run": "執行", "Execute": "執行", "Clear": "清除",
    "Reset": "重設", "Cancel": "取消", "Close": "關閉",
    "Save": "儲存", "Load": "載入", "Submit": "提交",
    "Back": "返回", "Next": "下一步", "Previous": "上一步",
    "Yes": "是", "No": "否", "OK": "確定",
    "Error": "錯誤", "Warning": "警告", "Info": "資訊",
    "Success": "成功", "Failed": "失敗", "Loading": "載入中",
    
    # 金融術語
    "Portfolio": "投資組合", "Benchmark": "基準",
    "Returns": "回報", "Risk": "風險", "Volatility": "波動率",
    "Sharpe": "夏普", "Sortino": "索提諾", "Drawdown": "回撤",
    "P&L": "損益", "PnL": "損益",
    "Bull": "多頭", "Bear": "空頭",
    "Long": "做多", "Short": "做空",
    "Bid": "買入價", "Ask": "賣出價",
    "Volume": "成交量", "Price": "價格",
    "Open": "開盤", "High": "最高", "Low": "最低",
    "Market": "市場", "Limit": "限價",
    "Order": "訂單", "Trade": "交易",
    "Buy": "買入", "Sell": "賣出",
    "Assets": "資產", "Holdings": "持倉",
    "Dividend": "股息", "Yield": "殖利率",
    "Equity": "權益", "Bond": "債券",
    "Option": "選擇權", "Future": "期貨",
    "Swap": "交換", "Hedge": "避險",
    
    # 量化術語
    "Backtest": "回測", "Forecast": "預測",
    "Regression": "迴歸", "Correlation": "相關性",
    "Covariance": "共變異數", "Variance": "變異數",
    "Mean": "平均值", "Median": "中位數",
    "Standard Deviation": "標準差", "Skewness": "偏度",
    "Kurtosis": "峰度", "Quantile": "分位數",
    "Percentile": "百分位", "Confidence": "信賴度",
    "Hypothesis": "假設", "Significance": "顯著性",
    "p-value": "p 值", "t-test": "t 檢定",
    "ANOVA": "變異數分析", "Chi-square": "卡方",
    "Monte Carlo": "蒙特卡洛",
    "Optimization": "最佳化", "Simulation": "模擬",
    "Distribution": "分佈", "Normal": "常態",
    "Log-normal": "對數常態",
    "Stochastic": "隨機", "Deterministic": "確定性",
    
    # 技術分析
    "Moving Average": "移動平均", "EMA": "EMA",
    "SMA": "SMA", "RSI": "RSI", "MACD": "MACD",
    "Bollinger": "布林", "Support": "支撐",
    "Resistance": "阻力", "Trend": "趨勢",
    "Breakout": "突破", "Reversal": "反轉",
    "Momentum": "動量", "Oscillator": "震盪器",
}

def extract_all_tr_calls():
    """從所有 C++ 原始碼提取 tr() 呼叫"""
    from collections import defaultdict
    results = defaultdict(set)
    
    binary_ns = {}
    with open(BINARY_CONTEXTS) as f:
        for line in f:
            ctx = line.strip()
            if ctx and '::' in ctx:
                short = ctx.split('::')[-1]
                binary_ns[short] = ctx
    
    for cpp in SRC_DIR.rglob("*.cpp"):
        content = cpp.read_text(encoding='utf-8', errors='ignore')
        class_name = cpp.stem
        ns_ctx = binary_ns.get(class_name, class_name)
        
        for match in re.finditer(r'\btr\(\s*"((?:[^"\\]|\\.)*)"\s*\)', content):
            source = match.group(1)
            if source.strip() and len(source.strip()) > 1:
                results[ns_ctx].add(source)
    
    return results

def get_existing_translations():
    """取得 .ts 中已有的所有 (context, source) 對"""
    content = TS_FILE.read_text(encoding='utf-8')
    existing = set()
    
    pattern = r'<context>\s*<name>(.*?)</name>(.*?)</context>'
    for match in re.finditer(pattern, content, re.DOTALL):
        ctx_name = match.group(1)
        body = match.group(2)
        for msg in re.finditer(r'<source>(.*?)</source>', body, re.DOTALL):
            src = msg.group(1)
            # 還原 XML 實體
            decoded = src.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&apos;', "'")
            existing.add((ctx_name, decoded))
            existing.add((ctx_name, src))
    
    return existing

def auto_translate(source: str) -> str:
    """自動翻譯 — 先查表、再用規則"""
    # 直查
    from scripts.fill_missing_translations import TRANSLATIONS
    if source in TRANSLATIONS:
        return TRANSLATIONS[source]
    
    # 簡單翻譯
    result = source
    
    # 常見短語
    SHORT_PHRASES = {
        "LOAD SAMPLE": "載入範例",
        "RUN": "執行",
        "CLEAR": "清除",
        "RESET": "重設",
        "EXPORT": "匯出",
        "IMPORT": "匯入",
        "COPY": "複製",
        "DELETE": "刪除",
        "ADD": "新增",
        "REMOVE": "移除",
        "UPDATE": "更新",
        "REFRESH": "重新整理",
        "SEARCH": "搜尋",
        "FILTER": "篩選",
        "SORT": "排序",
    }
    
    if source in SHORT_PHRASES:
        return SHORT_PHRASES[source]
    
    return None  # 無法自動翻譯

def escape_xml(s: str) -> str:
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace("'", '&apos;')
    return s

def main():
    print("=" * 60)
    print("量化模組 + 剩餘面板全量翻譯")
    print("=" * 60)
    
    all_tr = extract_all_tr_calls()
    existing = get_existing_translations()
    
    # 找出真正缺失的
    missing_by_ctx = {}
    for ctx, sources in all_tr.items():
        for src in sources:
            if (ctx, src) not in existing:
                missing_by_ctx.setdefault(ctx, []).append(src)
    
    total = sum(len(v) for v in missing_by_ctx.values())
    print(f"📋 XML 比對後真正缺失: {len(missing_by_ctx)} 個 context, {total} 條")
    
    # 輸出剩餘缺失的原文，方便人工翻譯
    output_path = Path("/tmp/remaining_untranslated.txt")
    with open(output_path, 'w') as f:
        for ctx in sorted(missing_by_ctx.keys()):
            sources = sorted(missing_by_ctx[ctx])
            f.write(f"\n=== {ctx} ({len(sources)} 條) ===\n")
            for src in sources:
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in src)
                marker = "⚪(中文)" if has_chinese else "❌(英文)"
                f.write(f"  {marker} {src}\n")
    
    print(f"📝 詳細清單: {output_path}")
    
    # 分析是否有大量中文 source（不需翻譯）
    chinese_count = 0
    english_count = 0
    for sources in missing_by_ctx.values():
        for s in sources:
            if any('\u4e00' <= c <= '\u9fff' for c in s):
                chinese_count += 1
            else:
                english_count += 1
    
    print(f"  中文（source 已是中文）: {chinese_count}")
    print(f"  英文（需翻譯）: {english_count}")

if __name__ == '__main__':
    main()
