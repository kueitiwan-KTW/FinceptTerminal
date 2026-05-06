#!/usr/bin/env python3
"""
重建 .ts 翻譯檔：從原始碼掃描 tr() 呼叫，建立正確的 context + source 結構。
然後把既有翻譯合併進新結構中。

策略：
1. 掃描所有 .cpp/.h，解析 class namespace::ClassName + tr("...") 
2. 用掃到的 context+source 建立新 .ts XML 結構
3. 從舊 .ts 讀取已有翻譯（source → translation 對應表）
4. 合併：新結構 + 舊翻譯
"""
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

SRC_DIR = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/src'
TS_FILE = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts'
TS_OUT  = TS_FILE  # 直接覆寫

def load_existing_translations(ts_path):
    """從現有 .ts 檔載入所有 source → translation 對應"""
    translations = {}
    try:
        tree = ET.parse(ts_path)
        root = tree.getroot()
        for ctx in root.findall('context'):
            for msg in ctx.findall('message'):
                src_el = msg.find('source')
                trans_el = msg.find('translation')
                if src_el is not None and trans_el is not None:
                    src = src_el.text or ''
                    trans = trans_el.text or ''
                    if src and trans and src != trans:
                        translations[src] = trans
    except Exception as e:
        print(f"⚠️ 讀取舊 .ts 失敗: {e}")
    return translations


def find_class_context(filepath):
    """從 .cpp 檔案找出 class context（namespace::ClassName）"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 方法 1：找 namespace + class
    # 例如 namespace fincept::screens { ... class SettingsScreen ...
    # 方法 2：找檔案對應的 .h 中的 class 定義
    # 方法 3：從 .cpp 中的成員函式定義推斷 class
    #   e.g. void SettingsScreen::createUI() → class = SettingsScreen
    
    # 先找 namespace 聲明
    namespaces = []
    ns_matches = re.findall(r'namespace\s+([\w:]+)\s*\{', content)
    for ns in ns_matches:
        namespaces.append(ns)
    
    # 找 class::method 模式推斷 class name
    classes = set()
    method_pattern = re.compile(r'(?:void|bool|int|QString|QWidget\*?|[\w:]+\*?)\s+([\w:]+)::([\w]+)\s*\(')
    for match in method_pattern.finditer(content):
        class_name = match.group(1)
        if class_name not in ('std', 'QObject', 'QWidget', 'QLabel', 'QTimer',
                               'QFile', 'QDir', 'QString', 'QVariant', 'QJsonObject',
                               'QJsonArray', 'QJsonDocument', 'QColor', 'QFont',
                               'QPixmap', 'QIcon', 'QPainter', 'QStyleOption'):
            classes.add(class_name)
    
    # 找 QObject::tr() 的使用 — context 是 "QObject"
    has_qobject_tr = 'QObject::tr(' in content
    
    return classes, has_qobject_tr, namespaces


def extract_tr_strings(filepath):
    """從檔案中提取所有 tr("...") 字串"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    strings = []
    
    # 匹配 tr("...") — 處理跳脫引號
    # 也匹配 QObject::tr("...")
    pattern = re.compile(r'(?:QObject::)?tr\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
    for m in pattern.finditer(content):
        s = m.group(1)
        if s.strip():
            strings.append(s)
    
    # 也匹配 QCoreApplication::translate("Context", "...")
    pattern2 = re.compile(r'QCoreApplication::translate\(\s*"[\w:]+"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\)')
    for m in pattern2.finditer(content):
        s = m.group(1)
        if s.strip():
            strings.append(s)
    
    return list(set(strings))


def build_ts_xml(context_strings, translations):
    """建立 .ts XML"""
    root = ET.Element('TS')
    root.set('version', '2.1')
    root.set('language', 'zh_TW')
    
    translated_count = 0
    total_count = 0
    
    for ctx_name in sorted(context_strings.keys()):
        sources = context_strings[ctx_name]
        if not sources:
            continue
            
        ctx_el = ET.SubElement(root, 'context')
        name_el = ET.SubElement(ctx_el, 'name')
        name_el.text = ctx_name
        
        for src in sorted(set(sources)):
            total_count += 1
            msg_el = ET.SubElement(ctx_el, 'message')
            src_el = ET.SubElement(msg_el, 'source')
            src_el.text = src
            
            trans_el = ET.SubElement(msg_el, 'translation')
            if src in translations:
                trans_el.text = translations[src]
                translated_count += 1
            else:
                trans_el.set('type', 'unfinished')
                trans_el.text = src
    
    return root, total_count, translated_count


def indent_xml(elem, level=0):
    """美化 XML 輸出"""
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
    if not level:
        elem.tail = "\n"


def main():
    print("📖 讀取現有翻譯...")
    translations = load_existing_translations(TS_FILE)
    print(f"   已載入 {len(translations)} 個翻譯對")
    
    print("🔍 掃描原始碼 tr() 呼叫...")
    context_strings = defaultdict(list)
    
    for root_dir, dirs, files in os.walk(SRC_DIR):
        for fname in files:
            if not fname.endswith(('.cpp', '.h')):
                continue
            filepath = os.path.join(root_dir, fname)
            
            tr_strings = extract_tr_strings(filepath)
            if not tr_strings:
                continue
            
            classes, has_qobject_tr, namespaces = find_class_context(filepath)
            
            # 決定 context
            if classes:
                # 使用最長的（最具體的）class name
                ctx = sorted(classes, key=len, reverse=True)[0]
                # 如果 class name 不含 :: 且有 namespace，加上 namespace
                if '::' not in ctx and namespaces:
                    # 用最深的 namespace
                    ns = sorted(namespaces, key=len, reverse=True)[0]
                    ctx = f"{ns}::{ctx}"
            elif has_qobject_tr:
                ctx = "QObject"
            else:
                # 用檔名作為 context
                ctx = os.path.splitext(fname)[0]
            
            context_strings[ctx].extend(tr_strings)
    
    print(f"   找到 {len(context_strings)} 個 context")
    total_strings = sum(len(v) for v in context_strings.values())
    print(f"   找到 {total_strings} 個 tr() 字串")
    
    print("🔨 建立新 .ts 結構...")
    root, total, translated = build_ts_xml(context_strings, translations)
    
    print("💾 寫入 .ts 檔...")
    indent_xml(root)
    tree = ET.ElementTree(root)
    
    # 寫入 XML 宣告
    with open(TS_OUT, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<!DOCTYPE TS>\n')
        tree.write(f, encoding='unicode', xml_declaration=False)
    
    print(f"✅ 完成！")
    print(f"   Context 數：{len(context_strings)}")
    print(f"   總字串數：{total}")
    print(f"   已翻譯：{translated} ({100*translated/max(total,1):.1f}%)")
    print(f"   未翻譯：{total - translated}")


if __name__ == '__main__':
    main()
