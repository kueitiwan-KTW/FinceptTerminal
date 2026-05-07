#!/usr/bin/env python3
"""
全面掃描 C++ 原始碼中的所有 tr() 呼叫，
對照 .ts 翻譯檔，找出所有缺失的翻譯。
同時處理硬編碼（非 tr()）的使用者可見字串。
"""

import re
import os
from pathlib import Path
from collections import defaultdict

SRC_DIR = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/src")
TS_FILE = Path("/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts")
BINARY_CONTEXTS = Path("/tmp/binary_contexts.txt")

def extract_tr_calls(src_dir: Path) -> dict[str, set[str]]:
    """從 C++ 原始碼提取所有 tr() 呼叫及其所在檔案/類別"""
    # 以檔名推斷 class，再用 binary context 映射完整 namespace
    file_tr = defaultdict(set)
    
    for cpp_file in src_dir.rglob("*.cpp"):
        content = cpp_file.read_text(encoding='utf-8', errors='ignore')
        # 提取所有 tr("...") 字串
        for match in re.finditer(r'\btr\(\s*"((?:[^"\\]|\\.)*)"\s*\)', content):
            source = match.group(1)
            # 跳過空字串和純符號
            if not source.strip() or len(source.strip()) <= 1:
                continue
            # 用檔名推斷 class
            class_name = cpp_file.stem
            file_tr[class_name].add(source)
    
    return file_tr

def parse_ts_contexts(ts_file: Path) -> dict[str, set[str]]:
    """解析 .ts 取得 {context: {sources}}"""
    content = ts_file.read_text(encoding='utf-8')
    contexts = {}
    
    pattern = r'<context>\s*<name>(.*?)</name>(.*?)</context>'
    for match in re.finditer(pattern, content, re.DOTALL):
        ctx_name = match.group(1)
        body = match.group(2)
        sources = set()
        for msg in re.finditer(r'<source>(.*?)</source>', body, re.DOTALL):
            sources.add(msg.group(1))
        contexts[ctx_name] = sources
    
    return contexts

def load_binary_contexts(path: Path) -> dict[str, str]:
    """載入 binary context → {short_name: full_namespace}"""
    mapping = {}
    with open(path) as f:
        for line in f:
            ctx = line.strip()
            if ctx and '::' in ctx:
                short = ctx.split('::')[-1]
                mapping[short] = ctx
    return mapping

def main():
    print("=" * 60)
    print("全面翻譯缺失掃描")
    print("=" * 60)
    
    # 1. 提取 C++ tr() 呼叫
    print("\n📂 掃描 C++ tr() 呼叫...")
    file_tr = extract_tr_calls(SRC_DIR)
    total_tr = sum(len(v) for v in file_tr.values())
    print(f"  {len(file_tr)} 個類別, {total_tr} 個唯一 tr() 字串")
    
    # 2. 解析 .ts
    print("\n📝 解析 .ts...")
    ts_contexts = parse_ts_contexts(TS_FILE)
    
    # 3. 載入 binary contexts
    binary_ns = load_binary_contexts(BINARY_CONTEXTS)
    
    # 4. 比對缺失
    print("\n🔍 缺失分析:")
    missing_by_ctx = defaultdict(list)
    found_count = 0
    missing_count = 0
    
    for class_name, sources in sorted(file_tr.items()):
        # 找到 namespace context
        ns_ctx = binary_ns.get(class_name)
        
        # 檢查所有可能的 context
        check_contexts = [class_name]
        if ns_ctx:
            check_contexts.append(ns_ctx)
        
        for source in sorted(sources):
            found = False
            for ctx in check_contexts:
                if ctx in ts_contexts and source in ts_contexts[ctx]:
                    found = True
                    break
            
            if found:
                found_count += 1
            else:
                missing_count += 1
                target_ctx = ns_ctx or class_name
                missing_by_ctx[target_ctx].append(source)
    
    print(f"  已有翻譯: {found_count}")
    print(f"  缺失翻譯: {missing_count}")
    
    # 5. 輸出缺失清單
    if missing_by_ctx:
        print(f"\n📋 缺失翻譯詳情 ({len(missing_by_ctx)} 個 context):")
        for ctx in sorted(missing_by_ctx.keys()):
            sources = missing_by_ctx[ctx]
            print(f"\n  【{ctx}】({len(sources)} 條)")
            for src in sources[:10]:
                # 判斷是否需要翻譯（中文 source 不需要）
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in src)
                marker = "⚪" if has_chinese else "❌"
                print(f"    {marker} {src}")
            if len(sources) > 10:
                print(f"    ... +{len(sources)-10} more")
    
    # 輸出為 JSON 以供後續自動修復
    import json
    output = {}
    for ctx, sources in missing_by_ctx.items():
        english_sources = [s for s in sources if not any('\u4e00' <= c <= '\u9fff' for c in s)]
        if english_sources:
            output[ctx] = english_sources
    
    out_path = Path("/tmp/missing_translations.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 缺失清單已輸出: {out_path}")
    print(f"   需翻譯的 context: {len(output)}")
    print(f"   需翻譯的字串: {sum(len(v) for v in output.values())}")

if __name__ == '__main__':
    main()
