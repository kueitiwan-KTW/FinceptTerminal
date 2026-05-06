#!/usr/bin/env python3
"""
批量翻譯 bad_translations.json 中的 source 文字為繁體中文。
使用 Google Translate 整句翻譯，加上後處理修正。

用法：python3 scripts/batch_translate.py
"""
import json, re, time, sys

# 保護性佔位符：翻譯前將 %1, %2 等替換為佔位符，翻譯後還原
PLACEHOLDER_MAP = {}
PLACEHOLDER_COUNTER = 0

def protect_placeholders(text: str) -> str:
    """將 %1, %2, \\n 等替換為佔位符"""
    global PLACEHOLDER_COUNTER
    placeholders = {}
    
    # 保護 %1, %2 等 Qt 佔位符
    def replace_ph(m):
        global PLACEHOLDER_COUNTER
        PLACEHOLDER_COUNTER += 1
        key = f"ZZPH{PLACEHOLDER_COUNTER}ZZ"
        placeholders[key] = m.group(0)
        return key
    
    result = re.sub(r'%\d+', replace_ph, text)
    # 保護 \n
    result = result.replace('\\n', 'ZZNEWLINEZZ')
    # 保護 HTML entities
    result = re.sub(r'&[a-z]+;', replace_ph, result)
    
    return result, placeholders


def restore_placeholders(text: str, placeholders: dict) -> str:
    """還原佔位符"""
    result = text
    for key, val in placeholders.items():
        result = result.replace(key, val)
    result = result.replace('ZZNEWLINEZZ', '\\n')
    return result


# 金融術語後處理對照表
TERM_FIXES = {
    '投資組合': '投資組合',
    '代幣': '代幣',
    '區塊鏈': '區塊鏈',
    '虛擬貨幣': '加密貨幣',
    '報酬率': '報酬率',
    '波動性': '波動率',
    '波動率': '波動率',
    '殖利率': '殖利率',
    '經紀人': '券商',
    '資產': '資產',
    '期貨': '期貨',
    '選項': '選擇權',  # Options 在金融語境
    '儀表板': '儀表板',
    '小部件': 'Widget',
    '小工具': 'Widget',
    '工具列': '工具列',
}


def translate_batch(texts: list[str], batch_size=10) -> list[str]:
    """批量翻譯文字"""
    from deep_translator import GoogleTranslator
    
    translator = GoogleTranslator(source='en', target='zh-TW')
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_results = []
        
        for text in batch:
            if not text or len(text.strip()) < 2:
                batch_results.append(text)
                continue
            
            # 如果全是格式字元，不翻譯
            clean = re.sub(r'[%\d\s\n\\<>/&;.,:!?\-\+\(\)\[\]#"\'=|×$@*_{}]', '', text)
            if len(clean) < 3:
                batch_results.append(text)
                continue
            
            # 保護佔位符
            protected, placeholders = protect_placeholders(text)
            
            # 清理可能導致翻譯失敗的字元
            safe_text = protected.replace('—', '-').replace('–', '-').replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
            
            try:
                translated = translator.translate(safe_text)
                if translated:
                    # 還原佔位符
                    translated = restore_placeholders(translated, placeholders)
                    batch_results.append(translated)
                else:
                    batch_results.append(text)  # fallback 保留原文
            except Exception as e:
                print(f"  ⚠ 翻譯失敗: {text[:40]}... ({e})", file=sys.stderr)
                batch_results.append(text)  # fallback
            
            time.sleep(0.1)  # 避免觸發限速
        
        results.extend(batch_results)
        print(f"  進度: {min(i+batch_size, len(texts))}/{len(texts)}", file=sys.stderr)
        time.sleep(0.3)  # 批次間間隔
    
    return results


def main():
    INPUT_FILE = "translations/bad_translations.json"
    OUTPUT_FILE = "translations/fixed_translations.json"
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    print(f"讀取 {len(items)} 個待翻譯項目")
    
    # 提取 source 文字
    sources = [item["source"] for item in items]
    
    # 批量翻譯
    print("開始翻譯...")
    translations = translate_batch(sources)
    
    # 組合結果
    for item, trans in zip(items, translations):
        item["fixed_translation"] = trans
    
    # 寫出
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！結果寫入 {OUTPUT_FILE}")
    
    # 統計
    translated = sum(1 for item in items if item["fixed_translation"] and item["fixed_translation"] != item["source"])
    print(f"成功翻譯: {translated}/{len(items)}")


if __name__ == "__main__":
    main()
