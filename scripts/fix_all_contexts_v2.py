#!/usr/bin/env python3
"""
從 C++ 原始碼提取所有 tr() 字串及其 namespace context，
與現有 .ts 翻譯檔對比，找出缺失的翻譯，
然後自動從短名 context 複製到 namespace context。

核心策略：
- 掃描 .cpp/.h 檔案找到每個類別的 namespace
- 確保 .ts 中每個 namespace context 都有完整的翻譯
"""

import re
import os
from pathlib import Path
from collections import defaultdict

SRC_DIR = Path(__file__).parent.parent / "fincept-qt" / "src"
TS_FILE = Path(__file__).parent.parent / "fincept-qt" / "translations" / "fincept_zh_TW.ts"

def find_class_namespaces(src_dir: Path) -> dict[str, str]:
    """掃描 .h 檔案，建立 class_name → full_namespace::class_name 映射"""
    mapping = {}
    
    for h_file in src_dir.rglob("*.h"):
        content = h_file.read_text(encoding='utf-8', errors='ignore')
        
        # 追蹤當前 namespace stack
        namespaces = []
        brace_depth = 0
        ns_depths = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # 匹配 namespace 宣告
            ns_match = re.match(r'namespace\s+([\w:]+)\s*\{', stripped)
            if ns_match:
                ns_name = ns_match.group(1)
                # 處理 fincept::screens 這種合併寫法
                namespaces.extend(ns_name.split('::'))
                ns_depths.append(brace_depth)
            
            # 匹配 class 宣告（含 Q_OBJECT）
            class_match = re.match(r'class\s+(\w+)\s*(?::\s*public|{)', stripped)
            if class_match and namespaces:
                class_name = class_match.group(1)
                full_name = '::'.join(namespaces) + '::' + class_name
                mapping[class_name] = full_name
            
            # 追蹤大括號
            brace_depth += stripped.count('{') - stripped.count('}')
            
            # 彈出已關閉的 namespace
            while ns_depths and brace_depth <= ns_depths[-1]:
                ns_depths.pop()
                if namespaces:
                    namespaces.pop()
    
    return mapping

def parse_ts_file(ts_file: Path) -> dict[str, dict[str, str]]:
    """解析 .ts 檔案，返回 {context_name: {source: translation}}"""
    content = ts_file.read_text(encoding='utf-8')
    contexts = {}
    
    pattern = r'<context>\s*<name>(.*?)</name>(.*?)</context>'
    for match in re.finditer(pattern, content, re.DOTALL):
        ctx_name = match.group(1)
        ctx_body = match.group(2)
        
        messages = {}
        msg_pattern = r'<source>(.*?)</source>\s*<translation(?:\s+type="[^"]*")?>(.*?)</translation>'
        for msg_match in re.finditer(msg_pattern, ctx_body, re.DOTALL):
            source = msg_match.group(1)
            translation = msg_match.group(2)
            messages[source] = translation
        
        contexts[ctx_name] = messages
    
    return contexts

def build_context_xml(name: str, messages: dict[str, str]) -> str:
    """建構 context XML"""
    lines = ['<context>', f'    <name>{name}</name>']
    for source, translation in sorted(messages.items()):
        lines.append('    <message>')
        lines.append(f'        <source>{source}</source>')
        if translation:
            lines.append(f'        <translation>{translation}</translation>')
        else:
            lines.append(f'        <translation type="unfinished"></translation>')
        lines.append('    </message>')
    lines.append('</context>')
    return '\n'.join(lines)

def main():
    print("=" * 60)
    print("全量 Context Namespace 修復 v2")
    print("=" * 60)
    
    # 1. 從原始碼建立 class → namespace 映射
    print("\n📂 掃描 C++ 原始碼...")
    class_ns = find_class_namespaces(SRC_DIR)
    print(f"  找到 {len(class_ns)} 個類別 → namespace 映射")
    
    # 2. 解析 .ts
    print("\n📝 解析 .ts 翻譯檔...")
    ts_contexts = parse_ts_file(TS_FILE)
    print(f"  現有 {len(ts_contexts)} 個 context")
    
    # 3. 找出需要建立/補齊的 namespace context
    new_blocks = []
    updated_count = 0
    
    for short_name, messages in sorted(ts_contexts.items()):
        if '::' in short_name:
            continue  # 已經是 namespace 版本
        if not messages:
            continue  # 沒有翻譯內容
        
        # 從原始碼映射找 namespace
        if short_name in class_ns:
            ns_name = class_ns[short_name]
        else:
            # 沒找到映射，跳過
            continue
        
        if ns_name in ts_contexts:
            # namespace 版本已存在，檢查是否需要補翻譯
            ns_messages = ts_contexts[ns_name]
            missing = {}
            for src, trl in messages.items():
                if src not in ns_messages and trl:
                    missing[src] = trl
            
            if missing:
                print(f"  📝 {ns_name}: 補齊 {len(missing)} 條翻譯")
                # 合併
                merged = {**ns_messages, **missing}
                new_blocks.append(('update', ns_name, merged))
                updated_count += 1
        else:
            # namespace 版本不存在，建立
            translated = {s: t for s, t in messages.items() if t}
            if translated:
                print(f"  ✨ 新增 {ns_name} ({len(translated)} 條翻譯)")
                new_blocks.append(('create', ns_name, translated))
    
    print(f"\n📊 統計:")
    print(f"  需要新增的 namespace context: {sum(1 for t, _, _ in new_blocks if t == 'create')}")
    print(f"  需要補齊的 namespace context: {sum(1 for t, _, _ in new_blocks if t == 'update')}")
    
    if not new_blocks:
        print("✅ 無需修改")
        return
    
    # 4. 修改 .ts 檔案
    content = TS_FILE.read_text(encoding='utf-8')
    
    # 先處理 update（替換已存在的 context block）
    for action, ns_name, messages in new_blocks:
        if action == 'update':
            # 找到舊的 block 並替換
            old_pattern = rf'<context>\s*<name>{re.escape(ns_name)}</name>.*?</context>'
            new_block = build_context_xml(ns_name, messages)
            content = re.sub(old_pattern, new_block, content, flags=re.DOTALL)
    
    # 再處理 create（在 </TS> 前插入）
    creates = [build_context_xml(ns, msgs) for action, ns, msgs in new_blocks if action == 'create']
    if creates:
        insert_point = content.rfind('</TS>')
        content = content[:insert_point] + '\n'.join(creates) + '\n' + content[insert_point:]
    
    TS_FILE.write_text(content, encoding='utf-8')
    
    total_new_translations = sum(len(msgs) for _, _, msgs in new_blocks)
    print(f"\n✅ 完成！共處理 {len(new_blocks)} 個 context，{total_new_translations} 條翻譯")
    print(f"  檔案: {TS_FILE}")

if __name__ == '__main__':
    main()
