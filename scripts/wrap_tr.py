#!/usr/bin/env python3
"""
自動將 C++ 原始碼中硬編碼的英文 UI 字串包裝為 tr() 呼叫。

規則：
1. 將 new QLabel("英文") 改為 new QLabel(tr("英文"))
2. 將 QPushButton("英文") 改為 QPushButton(tr("英文"))
3. 將 setPlaceholderText("英文") 改為 setPlaceholderText(tr("英文"))
4. 將 setWindowTitle("英文") 改為 setWindowTitle(tr("英文"))
5. 將 setToolTip("英文") 改為 setToolTip(tr("英文"))
6. 將 addTab(widget, "英文") 改為 addTab(widget, tr("英文"))
7. 將 setText("英文") 改為 setText(tr("英文")) （僅含字母的字串）

排除：
- 已經用 tr() 包裝的
- 空字串 ""
- 純符號 "—", "•", " ", "|", "●", "⌄", ">", "$", "...", "--", "0"
- 技術字串（如 SQL、CSS、日期格式、路徑等）
- 在匿名 namespace 或非 QObject 成員函式中的（需要用 QObject::tr()）
"""

import re
import os
import sys
from pathlib import Path

# 不需要翻譯的字串模式
SKIP_PATTERNS = [
    r'^$',                          # 空字串
    r'^[\s—•|●⌄>$…\-\.]+$',       # 純符號
    r'^\d+$',                       # 純數字
    r'^0$',                         # 零
    r'^\.\.\.$',                    # 省略號
    r'^--$',                        # 雙破折號
    r'^OK$',                        # 狀態
    r'^CSV$',                       # 檔案格式
    r'^\$',                         # 美元符號開頭
    r'^@',                          # @ 開頭（用戶名）
    r'^\d{4}-\d{2}-\d{2}',         # 日期格式
    r'^SELECT\s',                   # SQL
    r'^https?://',                  # URL
    r'^#[0-9a-fA-F]',              # 顏色碼
    r'^[A-Z]+\s*v\d',              # 版本號如 ALGO v1.0
    r'^%\d',                        # printf 格式
    r'^\{',                         # JSON/模板
    r'^<',                          # HTML
    r'font-',                       # CSS
    r'color:',                      # CSS
    r'background',                  # CSS
    r'border',                      # CSS
    r'padding',                     # CSS
    r'margin',                      # CSS
    r'style=',                      # HTML style
    r'^QSS:',                       # QSS
    r'\.png$',                      # 圖檔
    r'\.svg$',                      # 圖檔
    r'\.jpg$',                      # 圖檔
    r'\.json$',                     # JSON 檔
    r'\.csv$',                      # CSV 檔
    r'\.py$',                       # Python 檔
    r'^application/',               # MIME type
    r'^text/',                      # MIME type
    r'^Content-',                   # HTTP header
    r'^Bearer\s',                   # Auth header
    r'^Authorization',              # Auth header
    r'^GET\s|^POST\s|^PUT\s',      # HTTP method
    r'api\.fincept',               # API URL
    r'^fincept_',                   # 內部 ID
    r'^FINCEPT$',                   # 品牌名（保留英文）
]

# 編譯跳過模式
SKIP_RE = [re.compile(p) for p in SKIP_PATTERNS]

def should_skip(s: str) -> bool:
    """判斷字串是否應跳過（不需要翻譯）"""
    s_stripped = s.strip()
    if not s_stripped:
        return True
    # 純 ASCII 符號（無字母）
    if not re.search(r'[a-zA-Z]', s_stripped):
        return True
    for pat in SKIP_RE:
        if pat.search(s_stripped):
            return True
    return False

# 需要處理的模式
# pattern_name: (搜尋 regex, 替換函式)
PATTERNS = [
    # new QLabel("text") → new QLabel(tr("text"))
    # new QLabel("text", parent) → new QLabel(tr("text"), parent)
    (
        r'new\s+QLabel\(\s*"([^"]+)"\s*([,\)])',
        lambda m: f'new QLabel(tr("{m.group(1)}"){m.group(2)}' if not should_skip(m.group(1)) else m.group(0)
    ),
    # new QPushButton("text") → new QPushButton(tr("text"))
    (
        r'new\s+QPushButton\(\s*"([^"]+)"\s*([,\)])',
        lambda m: f'new QPushButton(tr("{m.group(1)}"){m.group(2)}' if not should_skip(m.group(1)) else m.group(0)
    ),
    # setPlaceholderText("text") → setPlaceholderText(tr("text"))
    (
        r'setPlaceholderText\(\s*"([^"]+)"\s*\)',
        lambda m: f'setPlaceholderText(tr("{m.group(1)}"))' if not should_skip(m.group(1)) else m.group(0)
    ),
    # setWindowTitle("text") → setWindowTitle(tr("text"))
    (
        r'setWindowTitle\(\s*"([^"]+)"\s*\)',
        lambda m: f'setWindowTitle(tr("{m.group(1)}"))' if not should_skip(m.group(1)) else m.group(0)
    ),
    # setToolTip("text") → setToolTip(tr("text"))
    (
        r'setToolTip\(\s*"([^"]+)"\s*\)',
        lambda m: f'setToolTip(tr("{m.group(1)}"))' if not should_skip(m.group(1)) else m.group(0)
    ),
    # setHeaderLabel("text") → setHeaderLabel(tr("text"))
    (
        r'setHeaderLabel\(\s*"([^"]+)"\s*\)',
        lambda m: f'setHeaderLabel(tr("{m.group(1)}"))' if not should_skip(m.group(1)) else m.group(0)
    ),
    # setTitle("text") → setTitle(tr("text"))
    (
        r'setTitle\(\s*"([^"]+)"\s*\)',
        lambda m: f'setTitle(tr("{m.group(1)}"))' if not should_skip(m.group(1)) else m.group(0)
    ),
]

# addTab 較特殊，第二個參數才是文字
ADDTAB_PATTERN = (
    r'addTab\(([^,]+),\s*"([^"]+)"\s*\)',
    lambda m: f'addTab({m.group(1)}, tr("{m.group(2)}"))' if not should_skip(m.group(2)) else m.group(0)
)

# setText("純英文字串") → setText(tr("...")) 
# 只處理看起來像 UI 文字的（含空格或全大寫）
SETTEXT_PATTERN = (
    r'->setText\(\s*"([^"]+)"\s*\)',
    lambda m: f'->setText(tr("{m.group(1)}"))' if not should_skip(m.group(1)) and is_ui_text(m.group(1)) else m.group(0)
)

def is_ui_text(s: str) -> bool:
    """判斷字串是否為 UI 可見文字（需翻譯）"""
    s = s.strip()
    # 已包含 %1 等格式化的，也需翻譯但要小心
    # 純大寫短詞（如 IDLE, LIVE, OK）→ 翻譯
    if re.match(r'^[A-Z][A-Z\s]+$', s) and len(s) <= 30:
        return True
    # 含空格的英文短語
    if ' ' in s and re.match(r'^[A-Za-z\s\d\-\.\,\:\;\(\)\/\&]+$', s):
        return True
    # 短單詞如 "Name", "Type" 等
    if re.match(r'^[A-Z][a-z]+$', s):
        return True
    return False

def is_in_anonymous_namespace(lines: list, line_idx: int) -> bool:
    """檢查是否在匿名 namespace 中"""
    for i in range(line_idx, -1, -1):
        line = lines[i].strip()
        if 'namespace {' in line or line == 'namespace':
            return True
        if line.startswith('class ') or '::' in line:
            break
    return False

def process_file(filepath: str, dry_run: bool = False) -> tuple:
    """處理單一檔案，回傳 (修改數, 修改列表)"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # 跳過已完全翻譯的檔案
    if 'tr(' not in content and 'QObject::tr(' not in content:
        # 檔案完全沒用 tr()，可能是非 UI 檔案
        pass
    
    # 檢查是否有行已包含 tr( — 避免重複包裝
    lines = content.split('\n')
    
    # 逐行處理，避免跨行替換問題
    new_lines = []
    for i, line in enumerate(lines):
        original_line = line
        
        # 已有 tr( 的行跳過
        if 'tr(' in line and (
            'tr("' in line or 
            'QObject::tr(' in line or 
            'QCoreApplication::translate(' in line
        ):
            new_lines.append(line)
            continue
        
        # 套用所有模式
        for pattern, replacer in PATTERNS:
            line = re.sub(pattern, replacer, line)
        
        # addTab
        pattern, replacer = ADDTAB_PATTERN
        line = re.sub(pattern, replacer, line)
        
        # setText — 更保守
        pattern, replacer = SETTEXT_PATTERN
        line = re.sub(pattern, replacer, line)
        
        if line != original_line:
            changes.append((i + 1, original_line.strip(), line.strip()))
        
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return len(changes), changes

def main():
    import argparse
    parser = argparse.ArgumentParser(description='將 C++ UI 字串包裝為 tr() 呼叫')
    parser.add_argument('path', help='掃描的目錄路徑')
    parser.add_argument('--dry-run', action='store_true', help='只顯示會修改的內容，不實際修改')
    parser.add_argument('--verbose', action='store_true', help='顯示每一行修改')
    args = parser.parse_args()
    
    scan_path = Path(args.path)
    if not scan_path.exists():
        print(f"❌ 路徑不存在: {scan_path}")
        sys.exit(1)
    
    total_changes = 0
    total_files = 0
    modified_files = 0
    
    for cpp_file in sorted(scan_path.rglob('*.cpp')):
        total_files += 1
        n_changes, changes = process_file(str(cpp_file), dry_run=args.dry_run)
        
        if n_changes > 0:
            modified_files += 1
            total_changes += n_changes
            rel_path = cpp_file.relative_to(scan_path)
            print(f"\n📝 {rel_path} ({n_changes} 處修改)")
            if args.verbose:
                for line_no, old, new in changes:
                    print(f"   L{line_no}: {old}")
                    print(f"       → {new}")
    
    mode = "模擬" if args.dry_run else "實際"
    print(f"\n{'='*60}")
    print(f"✅ {mode}完成：掃描 {total_files} 個檔案")
    print(f"   修改 {modified_files} 個檔案，共 {total_changes} 處")
    if args.dry_run:
        print(f"   （使用 --verbose 查看每行修改詳情）")
        print(f"   （移除 --dry-run 以實際修改檔案）")

if __name__ == '__main__':
    main()
