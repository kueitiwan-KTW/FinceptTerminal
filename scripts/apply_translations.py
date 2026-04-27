#!/usr/bin/env python3
"""
將 FinceptTerminal C++ 原始碼中的硬編碼字串包裝為 tr() 呼叫，
並產生 Qt .ts 翻譯檔案。

步驟：
1. 讀取翻譯對照表
2. 掃描所有 .cpp 檔案
3. 將 setText("xxx") 改為 setText(tr("xxx"))
4. 產生 fincept_zh_TW.ts 翻譯檔

用法：python3 apply_translations.py
"""
import re
import json
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime

SRC_DIR = Path(__file__).parent.parent / "fincept-qt" / "src"
TRANSLATIONS_FILE = "/tmp/fincept_all_translations.json"
OUTPUT_TS = Path(__file__).parent.parent / "fincept-qt" / "translations" / "fincept_zh_TW.ts"

# 需要替換的模式
# 匹配 ->setText("...") 等呼叫，但不匹配已經有 tr() 的
REPLACEMENT_METHODS = [
    'setText', 'setPlaceholderText', 'setToolTip', 'setWindowTitle',
    'setTitle', 'setHeaderText', 'setLabelText', 'setInformativeText',
]

def load_translations():
    """載入翻譯對照表"""
    with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('translations', data)

def wrap_tr_in_file(filepath: Path, translations: dict, stats: dict):
    """在單一檔案中將字串包裝為 tr()"""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception:
        return
    
    original = content
    modified = False
    
    for method in REPLACEMENT_METHODS:
        # 匹配 ->method("string") 或 method("string")
        # 但不匹配已經有 tr( 的
        pattern = rf'({method}\s*\(\s*)(?!tr\()("(?:[^"\\]|\\.)*")'
        
        def replacer(match):
            nonlocal modified
            prefix = match.group(1)
            string_literal = match.group(2)
            # 取出字串內容（去掉引號）
            text = string_literal[1:-1]
            
            # 檢查是否需要翻譯（非 SKIP）
            if text in translations and translations[text] != 'SKIP':
                modified = True
                stats['wrapped'] += 1
                return f'{prefix}tr({string_literal})'
            return match.group(0)
        
        content = re.sub(pattern, replacer, content)
    
    # 同時處理 QStringLiteral("...") → tr("...")
    def qsl_replacer(match):
        nonlocal modified
        text = match.group(1)
        if text in translations and translations[text] != 'SKIP':
            modified = True
            stats['qsl_replaced'] += 1
            return f'tr("{text}")'
        return match.group(0)
    
    content = re.sub(r'QStringLiteral\s*\(\s*"([^"]*?)"\s*\)', qsl_replacer, content)
    
    if modified:
        filepath.write_text(content, encoding='utf-8')
        stats['files_modified'] += 1

def generate_ts_file(translations: dict):
    """產生 Qt .ts 翻譯檔案"""
    OUTPUT_TS.parent.mkdir(parents=True, exist_ok=True)
    
    # Qt .ts 檔案的 XML 結構
    ts = ET.Element('TS', version="2.1", language="zh_TW")
    
    # 按檔案分組（使用 context）
    context = ET.SubElement(ts, 'context')
    name = ET.SubElement(context, 'name')
    name.text = 'FinceptTerminal'
    
    count = 0
    for original, translated in sorted(translations.items()):
        if translated == 'SKIP' or not translated:
            continue
        
        msg = ET.SubElement(context, 'message')
        source = ET.SubElement(msg, 'source')
        source.text = original
        translation = ET.SubElement(msg, 'translation')
        translation.text = translated
        count += 1
    
    # 美化輸出
    rough_string = ET.tostring(ts, encoding='unicode')
    dom = minidom.parseString(rough_string)
    pretty = dom.toprettyxml(indent="    ", encoding=None)
    
    # 加入 DOCTYPE
    header = '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n'
    # 移除 minidom 的 <?xml?> 行
    lines = pretty.split('\n')
    body = '\n'.join(lines[1:])
    
    with open(OUTPUT_TS, 'w', encoding='utf-8') as f:
        f.write(header + body)
    
    return count

def add_translator_to_main():
    """修改 main.cpp 以載入翻譯檔"""
    main_cpp = SRC_DIR / "main.cpp"
    if not main_cpp.exists():
        print(f"  ⚠️ 找不到 {main_cpp}")
        return False
    
    content = main_cpp.read_text(encoding='utf-8')
    
    # 檢查是否已經加過
    if 'QTranslator' in content:
        print("  ℹ️ main.cpp 已包含 QTranslator")
        return True
    
    # 加入 #include
    if '#include <QApplication>' in content:
        content = content.replace(
            '#include <QApplication>',
            '#include <QApplication>\n#include <QTranslator>\n#include <QLocale>'
        )
    
    # 在 QApplication 建立後加入翻譯器載入
    # 尋找 QApplication app(argc, argv) 或類似
    app_pattern = r'(QApplication\s+\w+\s*\([^)]*\)\s*;)'
    match = re.search(app_pattern, content)
    if match:
        translator_code = '''
    // 載入繁體中文翻譯
    QTranslator translator;
    QString locale = QLocale::system().name(); // e.g. "zh_TW"
    if (locale.startsWith("zh")) {
        // 嘗試從多個路徑載入翻譯檔
        bool loaded = translator.load("fincept_zh_TW", ":/translations")
                   || translator.load("fincept_zh_TW", QCoreApplication::applicationDirPath() + "/translations")
                   || translator.load("fincept_zh_TW", "/usr/share/fincept/translations");
        if (loaded) {
            QCoreApplication::installTranslator(&translator);
            qInfo() << "[i18n] 已載入繁體中文翻譯";
        } else {
            qWarning() << "[i18n] 找不到繁體中文翻譯檔案";
        }
    }
'''
        content = content.replace(
            match.group(0),
            match.group(0) + '\n' + translator_code
        )
        main_cpp.write_text(content, encoding='utf-8')
        return True
    
    print("  ⚠️ 找不到 QApplication 初始化位置")
    return False

def main():
    print("=" * 60)
    print("FinceptTerminal 繁體中文化腳本")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 載入翻譯
    print("\n[1/4] 載入翻譯對照表...")
    translations = load_translations()
    translated_count = sum(1 for v in translations.values() if v != 'SKIP')
    print(f"  ✅ {len(translations)} 個字串，其中 {translated_count} 個需翻譯")
    
    # 2. 包裝 tr()
    print("\n[2/4] 包裝 tr() 呼叫...")
    stats = {'wrapped': 0, 'qsl_replaced': 0, 'files_modified': 0}
    for cpp_file in sorted(SRC_DIR.rglob("*.cpp")):
        wrap_tr_in_file(cpp_file, translations, stats)
    print(f"  ✅ 修改了 {stats['files_modified']} 個檔案")
    print(f"     setText/etc → tr(): {stats['wrapped']} 處")
    print(f"     QStringLiteral → tr(): {stats['qsl_replaced']} 處")
    
    # 3. 產生 .ts 翻譯檔
    print("\n[3/4] 產生 Qt .ts 翻譯檔...")
    ts_count = generate_ts_file(translations)
    print(f"  ✅ {OUTPUT_TS}")
    print(f"     包含 {ts_count} 個翻譯條目")
    
    # 4. 修改 main.cpp
    print("\n[4/4] 修改 main.cpp 載入翻譯器...")
    success = add_translator_to_main()
    if success:
        print("  ✅ main.cpp 已更新")
    
    print("\n" + "=" * 60)
    print("完成！下一步：")
    print("  1. 用 lrelease 編譯 .ts → .qm")
    print("  2. 修改 CMakeLists.txt 包含翻譯資源")
    print("  3. 重新建構 Docker 映像")
    print("=" * 60)

if __name__ == "__main__":
    main()
