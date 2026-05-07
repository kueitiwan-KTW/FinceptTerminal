#!/usr/bin/env python3
"""
全量 Context Namespace 修復 v3

策略簡化：不解析 C++ namespace（太容易出錯），
改用 binary strings 輸出的 context 列表作為 ground truth。
"""

import re
import sys
from pathlib import Path

TS_FILE = Path(__file__).parent.parent / "fincept-qt" / "translations" / "fincept_zh_TW.ts"
BINARY_CONTEXTS = Path("/tmp/binary_contexts.txt")

def main():
    print("=" * 60)
    print("全量 Context Namespace 修復 v3")
    print("=" * 60)
    
    # 1. 讀取 binary 中的 namespace contexts（ground truth）
    binary_ns = set()
    with open(BINARY_CONTEXTS) as f:
        for line in f:
            ctx = line.strip()
            if ctx and '::' in ctx:
                binary_ns.add(ctx)
    print(f"📦 Binary namespace contexts: {len(binary_ns)}")
    
    # 2. 解析 .ts 檔案
    content = TS_FILE.read_text(encoding='utf-8')
    
    # 提取所有 context 及其完整 XML block
    ctx_pattern = r'(<context>\s*<name>(.*?)</name>.*?</context>)'
    all_contexts = {}
    for match in re.finditer(ctx_pattern, content, re.DOTALL):
        full_block = match.group(1)
        ctx_name = match.group(2)
        
        # 提取 messages
        messages = {}
        msg_pattern = r'<source>(.*?)</source>\s*<translation(?:\s+type="[^"]*")?>(.*?)</translation>'
        for msg in re.finditer(msg_pattern, full_block, re.DOTALL):
            messages[msg.group(1)] = msg.group(2)
        
        all_contexts[ctx_name] = messages
    
    print(f"📝 .ts contexts: {len(all_contexts)}")
    
    short_names = {k: v for k, v in all_contexts.items() if '::' not in k and v}
    print(f"📋 短名 contexts（有翻譯）: {len(short_names)}")
    
    # 3. 對每個 binary namespace context，檢查是否需要建立/補齊
    new_blocks = []
    updated = 0
    created = 0
    
    for ns_ctx in sorted(binary_ns):
        # 取 class 短名
        short = ns_ctx.split('::')[-1]
        
        if short not in short_names:
            continue  # 短名版本沒翻譯，跳過
        
        short_msgs = short_names[short]
        
        if ns_ctx in all_contexts:
            # namespace 版本已存在，檢查是否需要補翻譯
            ns_msgs = all_contexts[ns_ctx]
            missing = {s: t for s, t in short_msgs.items() if s not in ns_msgs and t}
            if missing:
                # 合併
                merged = {**ns_msgs, **missing}
                all_contexts[ns_ctx] = merged
                updated += 1
                print(f"  📝 {ns_ctx}: +{len(missing)} 條")
        else:
            # 需要新建
            translated = {s: t for s, t in short_msgs.items() if t}
            if translated:
                all_contexts[ns_ctx] = translated
                created += 1
                print(f"  ✨ {ns_ctx}: {len(translated)} 條")
    
    print(f"\n📊 新增: {created}, 補齊: {updated}")
    
    if created == 0 and updated == 0:
        print("✅ 無需修改")
        return
    
    # 4. 重建 .ts 檔案
    # 保留原始 header
    header_match = re.match(r'(.*?)<context>', content, re.DOTALL)
    header = header_match.group(1) if header_match else '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n<TS version="2.1" language="zh_TW">\n'
    
    # 建構所有 context blocks
    lines = [header.rstrip()]
    for ctx_name in sorted(all_contexts.keys()):
        msgs = all_contexts[ctx_name]
        if not msgs:
            continue
        lines.append('<context>')
        lines.append(f'    <name>{ctx_name}</name>')
        for source, translation in sorted(msgs.items()):
            lines.append('    <message>')
            # 處理 XML 特殊字符（source 可能包含 & < > 等）
            lines.append(f'        <source>{source}</source>')
            if translation:
                lines.append(f'        <translation>{translation}</translation>')
            else:
                lines.append('        <translation type="unfinished"></translation>')
            lines.append('    </message>')
        lines.append('</context>')
    lines.append('</TS>')
    lines.append('')
    
    new_content = '\n'.join(lines)
    TS_FILE.write_text(new_content, encoding='utf-8')
    
    # 5. 統計
    total_msgs = sum(len(v) for v in all_contexts.values())
    total_translated = sum(sum(1 for t in v.values() if t) for v in all_contexts.values())
    print(f"\n✅ 完成！")
    print(f"  總 context: {len([k for k, v in all_contexts.items() if v])}")
    print(f"  總 messages: {total_msgs}")
    print(f"  已翻譯: {total_translated}")

if __name__ == '__main__':
    main()
