#!/usr/bin/env python3
"""
完整修復 Qt 翻譯 Context Namespace 不匹配問題

核心邏輯：
1. 從 binary 的 strings 輸出讀取所有 fincept:: namespace context
2. 從 .ts 檔讀取所有翻譯的 context
3. 對於每個 namespace context（如 fincept::screens::SettingsScreen），
   如果 .ts 中有對應的短名 context（如 SettingsScreen），
   就複製整個 <context> block，改名為 namespace 版本
4. 對於已經有 namespace context 但翻譯不完整的，
   從短名版本補齊缺少的翻譯
"""

import re
import sys
from pathlib import Path

# 路徑設定
TS_FILE = Path(__file__).parent.parent / "fincept-qt" / "translations" / "fincept_zh_TW.ts"
BINARY_CONTEXTS_FILE = Path("/tmp/binary_contexts.txt")

def parse_contexts(ts_content: str) -> dict[str, list[tuple[str, str]]]:
    """解析 .ts 檔案，返回 {context_name: [(source, translation), ...]}"""
    contexts = {}
    # 找所有 <context> blocks
    pattern = r'<context>\s*<name>(.*?)</name>(.*?)</context>'
    for match in re.finditer(pattern, ts_content, re.DOTALL):
        ctx_name = match.group(1)
        ctx_body = match.group(2)
        
        # 解析 messages
        messages = []
        msg_pattern = r'<message[^>]*>\s*<source>(.*?)</source>\s*<translation(?:\s+type="[^"]*")?>(.*?)</translation>'
        for msg_match in re.finditer(msg_pattern, ctx_body, re.DOTALL):
            source = msg_match.group(1)
            translation = msg_match.group(2)
            messages.append((source, translation))
        
        contexts[ctx_name] = messages
    
    return contexts

def build_context_block(name: str, messages: list[tuple[str, str]]) -> str:
    """建構 context XML block"""
    lines = [f'<context>', f'    <name>{name}</name>']
    for source, translation in messages:
        lines.append('    <message>')
        lines.append(f'        <source>{source}</source>')
        if translation:
            lines.append(f'        <translation>{translation}</translation>')
        else:
            lines.append('        <translation type="unfinished"></translation>')
        lines.append('    </message>')
    lines.append('</context>')
    return '\n'.join(lines)

def main():
    print("=" * 60)
    print("Qt 翻譯 Context Namespace 完整修復")
    print("=" * 60)
    
    # 讀取 binary contexts
    if not BINARY_CONTEXTS_FILE.exists():
        print(f"❌ 找不到 {BINARY_CONTEXTS_FILE}")
        print("請先執行: ssh pg-server 'docker exec fincept-6 strings /opt/fincept/bin/FinceptTerminal | grep \"^fincept::\"' > /tmp/binary_contexts.txt")
        sys.exit(1)
    
    binary_contexts = set()
    with open(BINARY_CONTEXTS_FILE) as f:
        for line in f:
            ctx = line.strip()
            if ctx:
                binary_contexts.add(ctx)
    
    print(f"📦 Binary namespace contexts: {len(binary_contexts)}")
    
    # 讀取 .ts
    ts_content = TS_FILE.read_text(encoding='utf-8')
    ts_contexts = parse_contexts(ts_content)
    print(f"📝 .ts 中已有 contexts: {len(ts_contexts)}")
    
    # 建立短名 → namespace 映射
    mappings = {}  # {namespace_ctx: short_ctx}
    for ns_ctx in sorted(binary_contexts):
        short_name = ns_ctx.split('::')[-1]
        if short_name in ts_contexts and ns_ctx not in ts_contexts:
            mappings[ns_ctx] = short_name
    
    print(f"🔗 需要建立的 namespace 映射: {len(mappings)}")
    
    if not mappings:
        print("✅ 所有映射已完成，無需修改")
        return
    
    # 顯示要建立的映射
    print("\n📋 將建立以下 namespace context:")
    for ns, short in sorted(mappings.items()):
        msg_count = len(ts_contexts[short])
        translated = sum(1 for _, t in ts_contexts[short] if t)
        print(f"  {short} → {ns} ({translated}/{msg_count} 已翻譯)")
    
    # 建構新的 context blocks
    new_blocks = []
    for ns_ctx, short_ctx in sorted(mappings.items()):
        messages = ts_contexts[short_ctx]
        block = build_context_block(ns_ctx, messages)
        new_blocks.append(block)
    
    # 插入到 </TS> 之前
    insert_point = ts_content.rfind('</TS>')
    if insert_point == -1:
        print("❌ 找不到 </TS> 標記")
        sys.exit(1)
    
    new_content = (
        ts_content[:insert_point] + 
        '\n' + '\n'.join(new_blocks) + '\n' +
        ts_content[insert_point:]
    )
    
    # 寫入
    TS_FILE.write_text(new_content, encoding='utf-8')
    
    # 統計
    total_messages = sum(len(ts_contexts[short]) for short in mappings.values())
    total_translated = sum(
        sum(1 for _, t in ts_contexts[short] if t) 
        for short in mappings.values()
    )
    
    print(f"\n✅ 完成！")
    print(f"  新增 context blocks: {len(new_blocks)}")
    print(f"  涵蓋翻譯 messages: {total_messages}")
    print(f"  其中已翻譯: {total_translated}")
    print(f"  檔案: {TS_FILE}")

    # 同時處理已存在的 namespace context 但翻譯不完整的情況
    print("\n" + "=" * 60)
    print("檢查已有 namespace context 的翻譯完整度...")
    
    incomplete = 0
    for ns_ctx in sorted(binary_contexts):
        if ns_ctx in ts_contexts:
            short_name = ns_ctx.split('::')[-1]
            if short_name in ts_contexts and short_name != ns_ctx:
                # 兩邊都存在，檢查 namespace 版本是否少了某些翻譯
                ns_sources = set(s for s, _ in ts_contexts[ns_ctx])
                short_sources = set(s for s, _ in ts_contexts[short_name])
                missing = short_sources - ns_sources
                if missing:
                    incomplete += 1
                    print(f"  ⚠️ {ns_ctx}: 缺少 {len(missing)} 條翻譯")
    
    if incomplete == 0:
        print("  ✅ 所有已有 namespace context 翻譯完整")

if __name__ == '__main__':
    main()
