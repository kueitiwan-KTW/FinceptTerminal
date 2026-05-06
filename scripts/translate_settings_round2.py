#!/usr/bin/env python3
"""
第二輪翻譯：補上剛修改為 tr() 的新字串。
這些字串在 .ts 檔中可能還不存在（因為無法執行 lupdate），
需要手動插入 XML entry。
"""

import xml.etree.ElementTree as ET
import sys

TS_FILE = "/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts"

# 新增或翻譯的字串（(context, source) -> (translation, location_file, location_line)）
NEW_TRANSLATIONS = {
    # 側欄按鈕（新增 tr()）
    ("SettingsScreen", "Credentials"): ("憑證", "SettingsScreen.cpp", 202),
    ("SettingsScreen", "Appearance"): ("外觀", "SettingsScreen.cpp", 203),
    ("SettingsScreen", "Notifications"): ("通知", "SettingsScreen.cpp", 204),
    ("SettingsScreen", "Storage & Cache"): ("儲存與快取", "SettingsScreen.cpp", 205),
    ("SettingsScreen", "Data Sources"): ("資料來源", "SettingsScreen.cpp", 206),
    ("SettingsScreen", "LLM Config"): ("LLM 設定", "SettingsScreen.cpp", 207),
    ("SettingsScreen", "MCP Servers"): ("MCP 伺服器", "SettingsScreen.cpp", 208),
    ("SettingsScreen", "Logging"): ("日誌紀錄", "SettingsScreen.cpp", 209),
    ("SettingsScreen", "Security"): ("安全性", "SettingsScreen.cpp", 210),
    ("SettingsScreen", "Profiles"): ("設定檔", "SettingsScreen.cpp", 211),
    ("SettingsScreen", "Keybindings"): ("快捷鍵", "SettingsScreen.cpp", 212),
    ("SettingsScreen", "Python Env"): ("Python 環境", "SettingsScreen.cpp", 213),
    ("SettingsScreen", "Developer"): ("開發者", "SettingsScreen.cpp", 214),
    ("SettingsScreen", "Voice"): ("語音", "SettingsScreen.cpp", 215),

    # Appearance 新增 tr()
    ("SettingsScreen", "Font Size"): ("字型大小", "SettingsScreen.cpp", 540),
    ("SettingsScreen", "Font Family"): ("字型", "SettingsScreen.cpp", 546),
    ("SettingsScreen", "Content Density"): ("內容密度", "SettingsScreen.cpp", 578),
    ("SettingsScreen", "Controls padding and spacing throughout the UI."): ("控制整個介面的間距與留白。", "SettingsScreen.cpp", 578),
    ("SettingsScreen", "Show AI Chat Bubble"): ("顯示 AI 聊天氣泡", "SettingsScreen.cpp", 592),
    ("SettingsScreen", "AI Chat Bubble"): ("AI 聊天氣泡", "SettingsScreen.cpp", 596),
    ("SettingsScreen", "Floating chat assistant in the bottom-right corner."): ("懸浮在右下角的聊天助手。", "SettingsScreen.cpp", 596),
    ("SettingsScreen", "Show Ticker Bar"): ("顯示行情跑馬燈", "SettingsScreen.cpp", 598),
    ("SettingsScreen", "Ticker Bar"): ("行情跑馬燈", "SettingsScreen.cpp", 601),
    ("SettingsScreen", "Live price ticker at the bottom of the screen."): ("畫面底部的即時行情跑馬燈。", "SettingsScreen.cpp", 601),
    ("SettingsScreen", "Enable Animations"): ("啟用動畫效果", "SettingsScreen.cpp", 603),
    ("SettingsScreen", "Animations"): ("動畫效果", "SettingsScreen.cpp", 606),
    ("SettingsScreen", "Fade and transition effects throughout the UI."): ("整個介面的淡入淡出與轉場效果。", "SettingsScreen.cpp", 606),

    # Notification triggers
    ("SettingsScreen", "In-App Alerts (toast + bell)"): ("應用內通知（提示 + 鈴鐺）", "SettingsScreen.cpp", 993),
    ("SettingsScreen", "Show slide-in toasts and update bell badge."): ("顯示滑入提示並更新鈴鐺標記。", "SettingsScreen.cpp", 993),
    ("SettingsScreen", "Price Alerts"): ("價格警報", "SettingsScreen.cpp", 994),
    ("SettingsScreen", "Notify when price alert thresholds are crossed."): ("當價格超過警報門檻時發送通知。", "SettingsScreen.cpp", 994),
    ("SettingsScreen", "News Alerts"): ("新聞警報", "SettingsScreen.cpp", 995),
    ("SettingsScreen", "Enable news notifications (configure which types below)."): ("啟用新聞通知（在下方設定接收類型）。", "SettingsScreen.cpp", 995),
    ("SettingsScreen", "Breaking News"): ("突發新聞", "SettingsScreen.cpp", 1016),
    ("SettingsScreen", "Notify on FLASH/BREAKING/URGENT priority clusters."): ("快訊/突發/緊急優先級叢集發生時通知。", "SettingsScreen.cpp", 1016),
    ("SettingsScreen", "Monitor Keyword Matches"): ("關鍵字監控匹配", "SettingsScreen.cpp", 1018),
    ("SettingsScreen", "Notify when a news monitor watch list gets new matches."): ("新聞監控的追蹤清單有新匹配時通知。", "SettingsScreen.cpp", 1018),
    ("SettingsScreen", "Category Volume Spikes"): ("分類流量異常飆升", "SettingsScreen.cpp", 1019),
    ("SettingsScreen", "Notify when a category has abnormally high article volume (z-score \u2265 3)."): ("當某分類的文章數量異常偏高（z-score ≥ 3）時通知。", "SettingsScreen.cpp", 1019),
    ("SettingsScreen", "FLASH + High-Impact Articles"): ("快訊 + 高影響力文章", "SettingsScreen.cpp", 1021),
    ("SettingsScreen", "Notify on individual articles that are both FLASH priority and high market impact."): ("同時具備快訊優先級和高市場影響力的個別文章時通知。", "SettingsScreen.cpp", 1021),
    ("SettingsScreen", "Order Fill Alerts"): ("訂單成交警報", "SettingsScreen.cpp", 1029),
    ("SettingsScreen", "Notify when orders are filled or rejected."): ("訂單成交或被拒絕時通知。", "SettingsScreen.cpp", 1029),

    # Storage 說明文字
    ("SettingsScreen", "Manage all persistent data, databases, and files. Execute SQL queries directly against terminal databases."): ("管理所有持久化資料、資料庫和檔案。直接對終端資料庫執行 SQL 查詢。", "SettingsScreen.cpp", 1303),
}

def main():
    tree = ET.parse(TS_FILE)
    root = tree.getroot()

    # 建立 context -> element 映射
    ctx_map = {}
    for ctx in root.findall('context'):
        ctx_map[ctx.find('name').text] = ctx

    # 建立已存在的 (context, source) 集合
    existing = set()
    for ctx in root.findall('context'):
        ctx_name = ctx.find('name').text
        for msg in ctx.findall('message'):
            src = msg.find('source')
            if src is not None:
                existing.add((ctx_name, src.text))

    added = 0
    updated = 0

    for (ctx_name, source), (translation, loc_file, loc_line) in NEW_TRANSLATIONS.items():
        if (ctx_name, source) in existing:
            # 已存在，嘗試更新翻譯
            ctx_elem = ctx_map[ctx_name]
            for msg in ctx_elem.findall('message'):
                src = msg.find('source')
                trans = msg.find('translation')
                if src is not None and src.text == source and trans is not None:
                    if trans.get('type') == 'unfinished':
                        trans.text = translation
                        trans.attrib.pop('type', None)
                        updated += 1
                        print(f"  📝 [{ctx_name}] {source[:50]}...")
                    break
        else:
            # 不存在，需要新增 entry
            ctx_elem = ctx_map.get(ctx_name)
            if ctx_elem is None:
                # 建立新 context
                ctx_elem = ET.SubElement(root, 'context')
                name_elem = ET.SubElement(ctx_elem, 'name')
                name_elem.text = ctx_name
                ctx_map[ctx_name] = ctx_elem

            msg = ET.SubElement(ctx_elem, 'message')
            loc = ET.SubElement(msg, 'location')
            loc.set('filename', f'../src/screens/settings/{loc_file}')
            loc.set('line', str(loc_line))
            src = ET.SubElement(msg, 'source')
            src.text = source
            trans = ET.SubElement(msg, 'translation')
            trans.text = translation
            added += 1
            print(f"  ✅ [NEW] [{ctx_name}] {source[:50]}...")

    print(f"\n📊 結果：{added} 個新字串已加入，{updated} 個已更新")

    # 寫回
    tree.write(TS_FILE, encoding='utf-8', xml_declaration=True)
    print(f"💾 已寫入：{TS_FILE}")

    # 最終統計
    tree2 = ET.parse(TS_FILE)
    root2 = tree2.getroot()
    total_all = 0
    finished_all = 0
    for ctx in root2.findall('context'):
        name = ctx.find('name').text
        if name in ('SettingsScreen', 'LlmConfigSection', 'KeybindingsSection', 'PythonEnvSection', 'McpServersSection'):
            msgs = ctx.findall('message')
            finished = sum(1 for m in msgs if m.find('translation').get('type') != 'unfinished')
            total = len(msgs)
            total_all += total
            finished_all += finished
            print(f"  {name}: {finished}/{total} ({finished*100//total}%)")
    print(f"\n  📊 Settings 總計：{finished_all}/{total_all} ({finished_all*100//total_all}%)")

if __name__ == "__main__":
    main()
