#!/usr/bin/env python3
"""
修復 Qt 翻譯檔的 context namespace 不匹配問題。

問題：.ts 檔案裡翻譯放在短名 context（如 SettingsScreen），
但 Qt 執行時使用完整 namespace（如 fincept::screens::SettingsScreen），
導致翻譯查找失敗，UI 顯示英文。

解法：
1. 掃描所有帶 namespace 的 context
2. 提取其短名（最後一個 :: 後的名稱）
3. 從短名 context 複製翻譯到帶 namespace 的 context
4. 將帶 namespace context 裡 vanished 的條目改為 active
"""

import xml.etree.ElementTree as ET
import copy
import sys

TS_FILE = "fincept-qt/translations/fincept_zh_TW.ts"

def main():
    tree = ET.parse(TS_FILE)
    root = tree.getroot()

    # 第一步：建立 context name → context element 的映射
    contexts = {}
    for ctx in root.findall("context"):
        name = ctx.find("name").text or ""
        contexts[name] = ctx

    # 第二步：建立短名 → source → translation 的查找表
    short_name_translations = {}
    for name, ctx in contexts.items():
        if "::" in name:
            continue  # 跳過帶 namespace 的
        trans_map = {}
        for msg in ctx.findall("message"):
            src = msg.find("source")
            tr = msg.find("translation")
            if src is None or tr is None:
                continue
            source_text = src.text or ""
            trans_text = tr.text or ""
            typ = tr.get("type", "")
            if typ not in ("vanished", "obsolete") and trans_text.strip():
                trans_map[source_text] = trans_text
        short_name_translations[name] = trans_map

    # 第三步：修復帶 namespace 的 context
    fixed_count = 0
    activated_count = 0
    created_count = 0

    for name, ctx in contexts.items():
        if "::" not in name:
            continue  # 只處理帶 namespace 的

        # 提取短名
        short_name = name.split("::")[-1]

        # 查找短名 context 的翻譯
        if short_name not in short_name_translations:
            continue

        trans_map = short_name_translations[short_name]
        if not trans_map:
            continue

        # 收集已有的 source text（帶 namespace context 裡的）
        existing_sources = set()
        for msg in ctx.findall("message"):
            src = msg.find("source")
            tr = msg.find("translation")
            if src is None or tr is None:
                continue
            source_text = src.text or ""
            existing_sources.add(source_text)
            typ = tr.get("type", "")

            # 如果是 vanished 且短名有翻譯 → 激活並填入翻譯
            if typ in ("vanished", "obsolete") and source_text in trans_map:
                tr.text = trans_map[source_text]
                if "type" in tr.attrib:
                    del tr.attrib["type"]
                activated_count += 1
                fixed_count += 1
            # 如果是活躍但空白 → 填入翻譯
            elif typ not in ("vanished", "obsolete") and not (tr.text or "").strip():
                if source_text in trans_map:
                    tr.text = trans_map[source_text]
                    fixed_count += 1

        # 如果短名有翻譯但帶 namespace context 裡完全沒有 → 新增 message
        for source_text, trans_text in trans_map.items():
            if source_text not in existing_sources:
                msg_elem = ET.SubElement(ctx, "message")
                src_elem = ET.SubElement(msg_elem, "source")
                src_elem.text = source_text
                tr_elem = ET.SubElement(msg_elem, "translation")
                tr_elem.text = trans_text
                created_count += 1
                fixed_count += 1

    # 第四步：統計結果
    print(f"=== Context Namespace 修復完成 ===")
    print(f"  激活 vanished 條目: {activated_count}")
    print(f"  新增缺失條目:      {created_count}")
    print(f"  總修復數:          {fixed_count}")

    if fixed_count == 0:
        print("沒有需要修復的項目。")
        return

    # 第五步：寫回檔案
    tree.write(TS_FILE, encoding="utf-8", xml_declaration=True)

    # 第六步：驗證
    tree2 = ET.parse(TS_FILE)
    root2 = tree2.getroot()
    ns_active = 0
    ns_empty = 0
    for ctx in root2.findall("context"):
        name = ctx.find("name").text or ""
        if "::" not in name:
            continue
        for msg in ctx.findall("message"):
            tr = msg.find("translation")
            if tr is None:
                continue
            typ = tr.get("type", "")
            if typ in ("vanished", "obsolete"):
                continue
            ns_active += 1
            if not (tr.text or "").strip():
                ns_empty += 1

    print(f"\n=== 修復後驗證 ===")
    print(f"  帶 namespace 的活躍翻譯: {ns_active}")
    print(f"  其中空白:              {ns_empty}")

if __name__ == "__main__":
    main()
