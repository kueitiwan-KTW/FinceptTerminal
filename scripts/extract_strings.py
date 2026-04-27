#!/usr/bin/env python3
"""
從 FinceptTerminal C++ 原始碼中提取所有可翻譯字串。
輸出 JSON 格式供翻譯使用。

用法：python3 extract_strings.py > strings_to_translate.json
"""
import re
import json
import os
import sys
from pathlib import Path

# 要掃描的目錄
SRC_DIR = Path(__file__).parent.parent / "fincept-qt" / "src"

# 需要翻譯的 Qt 方法呼叫模式
PATTERNS = [
    # setText("..."), setPlaceholderText("..."), setToolTip("..."), setWindowTitle("...")
    r'(setText|setPlaceholderText|setToolTip|setWindowTitle|setTitle|setHeaderText|setLabelText|setInformativeText)\s*\(\s*(?:QStringLiteral\s*\(\s*)?"([^"]*)"',
    # QStringLiteral("...") — 獨立出現
    r'QStringLiteral\s*\(\s*"([^"]*)"',
    # QString("...")
    r'QString\s*\(\s*"([^"]*)"',
]

# 不翻譯的字串模式（技術性/非使用者可見）
SKIP_PATTERNS = [
    r'^$',                          # 空字串
    r'^[#\.\-\d\s\{\}%:;,/\\]+$',  # 純符號/數字
    r'^(https?://|wss?://|/api/)',  # URL
    r'^(color|background|border|font|padding|margin|width|height)',  # CSS 屬性
    r'^(QWidget|QLabel|QPush|QLine|QCombo|QTable|QScroll|QSplitter|QFrame)',  # Qt 類名
    r'^(GET|POST|PUT|DELETE|PATCH)$',  # HTTP 方法
    r'^[A-Z_]{2,}$',               # 全大寫常量名
    r'^\w+\.\w+$',                 # 檔名或屬性（如 config.json）
    r'^#[0-9a-fA-F]{3,8}$',        # 顏色碼
    r'^[\d\.]+\s*(px|em|rem|%|pt|s|ms)$',  # CSS 尺寸
    r'^\{.*\}$',                   # 大括號模板
    r'^rgba?\(',                    # 顏色函式
    r'^(true|false|null|none)$',   # 布林/空值
    r'^[a-z_]+$',                  # 純 snake_case 標識符
    r'.*\{.*\}.*\{.*\}',          # 多重模板佔位
]

def should_skip(text: str) -> bool:
    """判斷字串是否需要跳過（不翻譯）"""
    if len(text) < 2:
        return True
    for pat in SKIP_PATTERNS:
        if re.match(pat, text, re.IGNORECASE):
            return True
    # 純 CSS/stylesheet 字串
    if any(kw in text.lower() for kw in ['background:', 'color:', 'border:', 'font-size:', 'padding:', 'margin:']):
        return True
    return False

def extract_from_file(filepath: Path) -> list:
    """從單一 C++ 檔案提取字串"""
    results = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return results
    
    lines = content.split('\n')
    
    for line_no, line in enumerate(lines, 1):
        # 跳過註解行
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue
        
        for pattern in PATTERNS:
            for match in re.finditer(pattern, line):
                # 取最後一個 group（字串內容）
                text = match.group(match.lastindex)
                if text and not should_skip(text):
                    rel_path = str(filepath.relative_to(SRC_DIR.parent))
                    results.append({
                        "file": rel_path,
                        "line": line_no,
                        "original": text,
                        "context": stripped[:120],
                    })
    return results

def main():
    if not SRC_DIR.exists():
        print(f"錯誤：找不到原始碼目錄 {SRC_DIR}", file=sys.stderr)
        sys.exit(1)
    
    all_strings = []
    seen = set()  # 去重
    
    for cpp_file in sorted(SRC_DIR.rglob("*.cpp")):
        strings = extract_from_file(cpp_file)
        for s in strings:
            key = s["original"]
            if key not in seen:
                seen.add(key)
                all_strings.append(s)
    
    for h_file in sorted(SRC_DIR.rglob("*.h")):
        strings = extract_from_file(h_file)
        for s in strings:
            key = s["original"]
            if key not in seen:
                seen.add(key)
                all_strings.append(s)
    
    output = {
        "total": len(all_strings),
        "strings": all_strings
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\n// 共提取 {len(all_strings)} 個不重複可翻譯字串", file=sys.stderr)

if __name__ == "__main__":
    main()
