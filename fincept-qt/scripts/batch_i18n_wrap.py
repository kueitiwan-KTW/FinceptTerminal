#!/usr/bin/env python3
"""
批量 i18n 包裝工具 — 掃描 C++ 原始碼並將硬編碼英文字串包裝為 tr()
只處理 UI 相關字串（setText, QLabel, setTitle, setPlaceholderText 等）
不觸碰已經有 tr() 的行、log 呼叫、stylesheet、技術常量等
"""
import re
import sys
import os
from pathlib import Path

# 需要被 tr() 包裝的函式模式（這些函式的字串參數是顯示給用戶看的）
UI_FUNCTIONS = [
    'setText', 'setTitle', 'setPlaceholderText', 'setToolTip',
    'setStatusTip', 'setWhatsThis', 'setWindowTitle',
    'setTabText', 'setTabToolTip', 'addTab', 'addItem',
    'setLabelText', 'setItemText', 'setHeaderLabel',
    'setSectionLabel', 'setInformativeText', 'setDetailedText',
    'append', 'addAction', 'setAccessibleName',
    'setAccessibleDescription', 'setHeaderData',
]

# QLabel 建構函式中的字串
QLABEL_PATTERN = re.compile(
    r'new\s+QLabel\s*\(\s*"([^"]+)"\s*\)',
)

# UI 函式呼叫中的字串
UI_FUNC_PATTERN = re.compile(
    r'(?:' + '|'.join(UI_FUNCTIONS) + r')\s*\(\s*"([^"]+)"',
)

# QPushButton / QAction 建構式
QBUTTON_PATTERN = re.compile(
    r'new\s+Q(?:Push|Tool|Radio|Check)Button\s*\(\s*"([^"]+)"\s*\)',
)

QACTION_PATTERN = re.compile(
    r'new\s+QAction\s*\(\s*"([^"]+)"\s*[,)]',
)

QGROUPBOX_PATTERN = re.compile(
    r'new\s+QGroupBox\s*\(\s*"([^"]+)"\s*\)',
)

QMENU_PATTERN = re.compile(
    r'(?:addMenu|addSection)\s*\(\s*"([^"]+)"\s*\)',
)

# 要排除的行模式
EXCLUDE_PATTERNS = [
    re.compile(r'tr\s*\('),          # 已經有 tr()
    re.compile(r'LOG_'),             # 日誌
    re.compile(r'qDebug|qWarning'), # Qt 日誌
    re.compile(r'setStyleSheet'),    # CSS
    re.compile(r'setObjectName'),    # 物件名
    re.compile(r'//'),               # 被註解的行（簡單檢測）
    re.compile(r'Q_OBJECT'),         # 巨集
    re.compile(r'#include'),         # 引入
    re.compile(r'#define'),          # 定義
    re.compile(r'\.arg\s*\('),       # arg 鏈（通常在 tr 裡面）
    re.compile(r'connect\s*\('),     # signal/slot 連接
    re.compile(r'setProperty\s*\('), # 屬性設定
    re.compile(r'QUrl'),             # URL
    re.compile(r'QRegularExpression'), # 正則
    re.compile(r'http[s]?://'),      # URL 字串
]

# 要排除的字串值（技術常量、品牌名等）
EXCLUDE_STRINGS = {
    '', '--', '—', '-', '|', ':', ';', ',', '.', '...',
    '0', '0.0', '0%', 'N/A', 'n/a', 'OK', 'ok',
    'FINCEPT', 'TERMINAL', 'FINCEPT TERMINAL',
    'FinceptTerminal', 'fincept-terminal',
    'QLabel', 'QPushButton', 'QWidget',
    'true', 'false', 'null', 'none',
    'px', 'pt', 'em', 'rem', '%',
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
    'JSON', 'CSV', 'XML', 'HTML', 'SQL',
    'USD', 'EUR', 'GBP', 'JPY', 'CNY',
    'UTC', 'GMT',
}

# 正則排除模式（技術字串）
EXCLUDE_STRING_PATTERNS = [
    re.compile(r'^[\d\.\-\+\%\$\#\@\!\*\&\^\~\`]+$'),  # 純數字/符號
    re.compile(r'^#[0-9a-fA-F]{3,8}$'),                  # 顏色碼
    re.compile(r'^rgba?\('),                              # CSS 色彩
    re.compile(r'^[\w\-]+\.(png|jpg|svg|ico|gif|qss|css|js|py|cpp|h)$'),  # 檔案名
    re.compile(r'^\w+://'),                               # 協議 URL
    re.compile(r'^font-'),                                # CSS 屬性
    re.compile(r'^background'),                           # CSS 屬性
    re.compile(r'^border'),                               # CSS 屬性
    re.compile(r'^margin'),                               # CSS 屬性
    re.compile(r'^padding'),                              # CSS 屬性
    re.compile(r'^color:'),                               # CSS 屬性
    re.compile(r'^\{'),                                   # JSON/CSS 區塊
    re.compile(r'^Q\w+\s*\{'),                           # QSS
    re.compile(r'^[a-z_]+$'),                             # 純小寫識別符
    re.compile(r'^SELECT|^INSERT|^UPDATE|^DELETE|^CREATE'), # SQL
    re.compile(r'^application/'),                         # MIME
    re.compile(r'^\d+\s*(ms|s|px|pt|%|MB|GB|KB)$'),      # 度量值
]


def should_exclude_string(s: str) -> bool:
    """判斷是否應排除此字串（非 UI 文字）"""
    s_stripped = s.strip()
    if s_stripped in EXCLUDE_STRINGS:
        return True
    if len(s_stripped) <= 1:
        return True
    for pat in EXCLUDE_STRING_PATTERNS:
        if pat.search(s_stripped):
            return True
    return False


def should_exclude_line(line: str) -> bool:
    """判斷是否應排除此行"""
    stripped = line.strip()
    if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
        return True
    for pat in EXCLUDE_PATTERNS:
        if pat.search(line):
            return True
    return False


def find_replacements(line: str, line_num: int) -> list:
    """找出一行中需要替換的字串"""
    if should_exclude_line(line):
        return []
    
    replacements = []
    all_patterns = [
        QLABEL_PATTERN,
        UI_FUNC_PATTERN,
        QBUTTON_PATTERN,
        QACTION_PATTERN,
        QGROUPBOX_PATTERN,
        QMENU_PATTERN,
    ]
    
    for pat in all_patterns:
        for match in pat.finditer(line):
            full_match = match.group(0)
            string_val = match.group(1)
            
            # 排除非 UI 字串
            if should_exclude_string(string_val):
                continue
            
            # 確認此處尚未被 tr() 包裝
            # 尋找 match 位置前面是否有 tr(
            start = match.start()
            before = line[:start]
            if 'tr(' in before[-10:]:  # 簡單向前搜尋
                continue
            
            # 建立替換：將 "string" 替換為 tr("string")
            old = f'"{string_val}"'
            new = f'tr("{string_val}")'
            replacements.append({
                'line': line_num,
                'old': old,
                'new': new,
                'string': string_val,
                'context': full_match,
            })
    
    return replacements


def process_file(filepath: str, dry_run: bool = True) -> list:
    """處理單一檔案"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    all_replacements = []
    modified_lines = list(lines)
    
    for i, line in enumerate(lines):
        repls = find_replacements(line, i + 1)
        if repls:
            all_replacements.extend(repls)
            if not dry_run:
                new_line = line
                for r in repls:
                    # 只替換第一個出現（避免重複替換）
                    new_line = new_line.replace(r['old'], r['new'], 1)
                modified_lines[i] = new_line
    
    if not dry_run and all_replacements:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
    
    return all_replacements


def main():
    import argparse
    parser = argparse.ArgumentParser(description='批量 i18n 包裝工具')
    parser.add_argument('path', help='要掃描的目錄或檔案')
    parser.add_argument('--apply', action='store_true', help='實際修改檔案（預設為 dry-run）')
    parser.add_argument('--summary', action='store_true', help='只顯示摘要統計')
    args = parser.parse_args()
    
    target = Path(args.path)
    if target.is_file():
        files = [target]
    else:
        files = sorted(target.rglob('*.cpp'))
    
    total_strings = 0
    file_count = 0
    unique_strings = set()
    
    for f in files:
        repls = process_file(str(f), dry_run=not args.apply)
        if repls:
            file_count += 1
            total_strings += len(repls)
            for r in repls:
                unique_strings.add(r['string'])
            if not args.summary:
                print(f"\n{'[已修改]' if args.apply else '[將修改]'} {f} ({len(repls)} 處)")
                for r in repls:
                    print(f"  L{r['line']}: {r['old']} → {r['new']}")
    
    print(f"\n{'='*60}")
    print(f"{'已修改' if args.apply else '待修改'}: {file_count} 個檔案, {total_strings} 處字串")
    print(f"唯一字串數: {len(unique_strings)}")
    
    if not args.apply and total_strings > 0:
        print(f"\n執行 --apply 來實際修改檔案")
    
    # 輸出唯一字串到 stdout（用於 add_translations.py）
    if args.summary:
        print("\n--- 唯一英文字串清單 ---")
        for s in sorted(unique_strings):
            print(s)


if __name__ == '__main__':
    main()
