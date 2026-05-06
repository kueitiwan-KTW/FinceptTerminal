#!/usr/bin/env python3
"""
修復 fincept_zh_TW.ts 中品質不佳的翻譯。

三階段修復：
1. 補齊缺失翻譯（擴展 sync_translations.py 掃描範圍）
2. 識別品質不佳的翻譯（中英夾雜機翻）
3. 用整句翻譯替換品質不佳的翻譯

用法：
  python3 scripts/fix_bad_translations.py scan     # 掃描並輸出問題報告
  python3 scripts/fix_bad_translations.py extract   # 提取待翻譯文字到 JSON
  python3 scripts/fix_bad_translations.py apply      # 從 JSON 套用翻譯
  python3 scripts/fix_bad_translations.py sync       # 補齊缺失的 tr() 字串
"""
import xml.etree.ElementTree as ET
import re, sys, json, os
from pathlib import Path

TS_FILE = "translations/fincept_zh_TW.ts"
# 擴展掃描到所有 src 子目錄
SRC_DIRS = ["src"]
EXTRACT_FILE = "translations/bad_translations.json"
FIXED_FILE = "translations/fixed_translations.json"

# 技術術語白名單（這些英文在翻譯中保留是合理的）
TECH_TERMS = {
    'http', 'https', 'url', 'api', 'llm', 'mcp', 'json', 'csv', 'html',
    'xml', 'sql', 'null', 'true', 'false', 'python', 'fincept', 'websocket',
    'sdk', 'oauth', 'jwt', 'ssl', 'tls', 'tcp', 'udp', 'dns', 'ip',
    'etf', 'rsi', 'macd', 'sma', 'ema', 'atr', 'vwap', 'pe', 'eps',
    'aapl', 'msft', 'goog', 'amzn', 'tsla', 'btcusd', 'nifty',
    'openai', 'anthropic', 'gemini', 'groq', 'deepgram', 'whisper',
    'oanda', 'polygon', 'coinbase', 'kraken', 'binance', 'bybit',
    'docker', 'git', 'npm', 'pip', 'cuda', 'gpu', 'cpu', 'ram',
    'widget', 'dock', 'toolbar', 'tab', 'panel',
    'gguf', 'lora', 'qlora', 'bert', 'gpt', 'llama',
    'csv', 'pdf', 'png', 'jpg', 'svg', 'webp',
    'config', 'yaml', 'toml', 'env',
    'alice', 'blue', 'adanos',  # broker 名稱
    'nse', 'bse', 'nyse', 'nasdaq', 'tsx',  # 交易所
    'gdp', 'cpi', 'ppi', 'pce',  # 經濟指標
    'stdin', 'stdout', 'stderr',
}

# sync_translations.py 的 AUTO_TRANSLATE 對照表（重用）
AUTO_TRANSLATE = {
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
    "REFRESH": "重新整理", "Refresh": "重新整理",
    "LOADING": "載入中", "Loading": "載入中",
    "Loading...": "載入中...", "LOADING...": "載入中...",
    "SUBMIT": "送出", "Submit": "送出",
    "COPY": "複製", "Copy": "複製",
    "CLEAR": "清除", "Clear": "清除",
    "SEND": "傳送", "Send": "傳送",
    "BACK": "返回", "Back": "返回",
    "NEXT": "下一步", "Next": "下一步",
    "DONE": "完成", "Done": "完成",
    "YES": "是", "Yes": "是",
    "NO": "否", "No": "否",
    "OK": "確定",
    "Credentials": "憑證",
    "Appearance": "外觀",
    "Notifications": "通知",
    "Storage Cache": "儲存快取",
    "LLM Config": "LLM 設定",
    "Logging": "日誌",
    "Security": "安全性",
    "Keybindings": "快捷鍵",
    "Python Env": "Python 環境",
    "Developer": "開發者",
    "Voice": "語音",
    "PROVIDERS": "供應商",
    "Enable MCP Tools": "啟用 MCP 工具",
    "Save, Set Active": "儲存並啟用",
    "Save & Set Active": "儲存並啟用",
    "Apply & Save": "套用並儲存",
    "Create & Switch": "建立並切換",
    "STORAGE & DATA MANAGEMENT": "儲存與資料管理",
    "No data available": "無可用資料",
    "No results found": "找不到結果",
    "New Chat": "新對話",
    "Test Connection": "測試連線",
}


def is_bad_quality(source: str, translation: str) -> bool:
    """判斷翻譯品質是否不佳"""
    if not source or not translation:
        return False
    if source == translation:
        return False  # 未翻譯的另外處理

    # 有中文但也有大量英文（排除術語）
    if re.search(r'[\u4e00-\u9fff]', translation):
        eng_words = re.findall(r'[a-zA-Z]{3,}', translation)
        non_tech = [w for w in eng_words if w.lower() not in TECH_TERMS]
        if len(non_tech) >= 2:
            return True

    # 特徵模式：把 "to" 換成 "至"、"of" 換成 "的" 但其餘都是英文
    if re.search(r'[a-zA-Z]{3,}\s+至[a-zA-Z]', translation):
        return True
    if re.search(r'[a-zA-Z]{3,}\s+的[A-Z]', translation):
        return True
    if re.search(r'[a-zA-Z]{3,}\s+用於[a-zA-Z]', translation):
        return True
    if re.search(r'[a-zA-Z]{3,}\s+於[a-zA-Z]', translation):
        return True

    return False


def extract_tr_strings_all():
    """從整個 src 目錄提取所有 tr() 字串"""
    strings = set()
    for d in SRC_DIRS:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.rglob("*.cpp"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'tr\("([^"]+)"\)', text):
                strings.add(m.group(1))
        for f in p.rglob("*.h"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'tr\("([^"]+)"\)', text):
                strings.add(m.group(1))
    return strings


def load_ts():
    """載入翻譯檔"""
    tree = ET.parse(TS_FILE)
    root = tree.getroot()
    return tree, root


def get_all_translations(root):
    """取得所有翻譯對"""
    pairs = {}
    for ctx in root.findall("context"):
        for msg in ctx.findall("message"):
            src = msg.find("source")
            trans = msg.find("translation")
            if src is not None and src.text:
                pairs[src.text] = trans.text if trans is not None else None
    return pairs


def cmd_scan():
    """掃描並輸出問題報告"""
    tree, root = load_ts()
    pairs = get_all_translations(root)

    bad = []
    for src, trans in pairs.items():
        if trans and is_bad_quality(src, trans):
            bad.append((src, trans))

    # 也找缺失的
    tr_strings = extract_tr_strings_all()
    missing = tr_strings - set(pairs.keys())

    print(f"翻譯檔總數: {len(pairs)}")
    print(f"品質不佳（中英夾雜）: {len(bad)}")
    print(f"完全缺失（tr() 有但 .ts 無）: {len(missing)}")
    print()

    if bad:
        print("=== 品質不佳範例（前 20 個）===")
        for s, t in bad[:20]:
            print(f"  EN: {s[:60]}")
            print(f"  ZH: {t[:60]}")
            print()

    if missing:
        print(f"=== 缺失翻譯（前 20 個）===")
        for s in sorted(missing)[:20]:
            print(f"  {s[:70]}")


def cmd_extract():
    """提取品質不佳的翻譯到 JSON，供 AI 翻譯"""
    tree, root = load_ts()
    pairs = get_all_translations(root)

    bad_items = []
    for src, trans in pairs.items():
        if trans and is_bad_quality(src, trans):
            bad_items.append({
                "source": src,
                "current_translation": trans,
                "fixed_translation": ""  # 待填入
            })

    # 也加入缺失的
    tr_strings = extract_tr_strings_all()
    missing = tr_strings - set(pairs.keys())
    for s in sorted(missing):
        # 嘗試自動翻譯
        auto = AUTO_TRANSLATE.get(s)
        bad_items.append({
            "source": s,
            "current_translation": "(MISSING)",
            "fixed_translation": auto or ""
        })

    with open(EXTRACT_FILE, "w", encoding="utf-8") as f:
        json.dump(bad_items, f, ensure_ascii=False, indent=2)

    print(f"已提取 {len(bad_items)} 個待修復翻譯到 {EXTRACT_FILE}")
    print(f"  - 品質不佳: {sum(1 for x in bad_items if x['current_translation'] != '(MISSING)')}")
    print(f"  - 缺失: {sum(1 for x in bad_items if x['current_translation'] == '(MISSING)')}")


def cmd_apply():
    """從 fixed_translations.json 套用修正後的翻譯"""
    if not os.path.exists(FIXED_FILE):
        print(f"找不到 {FIXED_FILE}，請先準備好修正後的翻譯")
        return

    with open(FIXED_FILE, "r", encoding="utf-8") as f:
        fixes = json.load(f)

    fix_map = {item["source"]: item["fixed_translation"]
               for item in fixes if item.get("fixed_translation")}

    if not fix_map:
        print("沒有可套用的翻譯")
        return

    tree, root = load_ts()

    updated = 0
    added = 0
    for ctx in root.findall("context"):
        for msg in ctx.findall("message"):
            src_el = msg.find("source")
            trans_el = msg.find("translation")
            if src_el is not None and src_el.text in fix_map:
                new_trans = fix_map[src_el.text]
                if trans_el is not None:
                    trans_el.text = new_trans
                    # 移除 unfinished 標記
                    if "type" in trans_el.attrib:
                        del trans_el.attrib["type"]
                    updated += 1

    # 新增缺失的
    ctx = root.find("context")
    existing = get_all_translations(root)
    for src, trans in fix_map.items():
        if src not in existing:
            msg = ET.SubElement(ctx, "message")
            src_el = ET.SubElement(msg, "source")
            src_el.text = src
            trans_el = ET.SubElement(msg, "translation")
            trans_el.text = trans
            added += 1

    ET.indent(tree, space="    ")
    tree.write(TS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"已套用 {updated} 個更新 + {added} 個新增")


def cmd_sync():
    """補齊缺失的 tr() 字串（擴展版）"""
    tr_strings = extract_tr_strings_all()
    tree, root = load_ts()
    existing = get_all_translations(root)
    ctx = root.find("context")

    missing = tr_strings - set(existing.keys())
    if not missing:
        print("所有 tr() 字串已在翻譯檔中")
        return

    added = 0
    auto_count = 0
    for s in sorted(missing):
        msg = ET.SubElement(ctx, "message")
        src_el = ET.SubElement(msg, "source")
        src_el.text = s
        trans_el = ET.SubElement(msg, "translation")

        auto = AUTO_TRANSLATE.get(s)
        if auto:
            trans_el.text = auto
            auto_count += 1
        else:
            trans_el.set("type", "unfinished")
            trans_el.text = s
        added += 1

    ET.indent(tree, space="    ")
    tree.write(TS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"新增 {added} 筆（自動翻譯 {auto_count}, 待翻譯 {added - auto_count}）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "scan":
        cmd_scan()
    elif cmd == "extract":
        cmd_extract()
    elif cmd == "apply":
        cmd_apply()
    elif cmd == "sync":
        cmd_sync()
    else:
        print(f"未知指令: {cmd}")
        print(__doc__)
        sys.exit(1)
