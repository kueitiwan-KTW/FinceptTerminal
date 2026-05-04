#!/usr/bin/env python3
"""
將新的 tr() 字串的繁體中文翻譯插入 fincept_zh_TW.ts。
只新增尚未存在的 <source> 項目。
"""

import xml.etree.ElementTree as ET
import sys

TS_FILE = "translations/fincept_zh_TW.ts"

# 新增翻譯對照表 — source → translation
NEW_TRANSLATIONS = {
    # ToolBar.cpp
    "  |  PROFESSIONAL RESEARCH DESK": "  |  專業研究桌面",
    " LIVE": " 即時",
    "View Plans & Pricing": "查看方案與價格",
    "⬡ CHAT": "⬡ 對話",
    "Switch to Chat Mode (F9)": "切換至對話模式 (F9)",
    "LOGOUT": "登出",
    "FREE": "免費版",
    "File": "檔案",
    "New Window": "新視窗",
    "Move to Monitor": "移至螢幕",
    "(single monitor)": "（單螢幕）",
    "New Workspace": "新增工作區",
    "Open Workspace": "開啟工作區",
    "Save Workspace": "儲存工作區",
    "Save Workspace As": "另存工作區",
    "Import Workspace": "匯入工作區",
    "Export Workspace": "匯出工作區",
    "File Manager": "檔案管理器",
    "Refresh All": "全部重新整理",
    "Navigate": "導覽",
    "Markets & Data": "市場與資料",
    "Economics": "經濟",
    "GOVT Data": "政府資料",
    "Asia Markets": "亞洲市場",
    "Relationship Map": "關係圖譜",
    "Trading & Portfolio": "交易與投組",
    "Equity Trading": "股票交易",
    "Alpha Arena": "Alpha 競技場",
    "Prediction Markets": "預測市場",
    "Derivatives": "衍生性商品",
    "Watchlist": "自選清單",
    "Research & Intelligence": "研究與情報",
    "Equity Research": "股票研究",
    "M&A Analytics": "併購分析",
    "Alt. Investments": "另類投資",
    "Geopolitics": "地緣政治",
    "Maritime": "海運",
    "Surface Analytics": "表面分析",
    "Tools": "工具",
    "Agent Config": "代理設定",
    "MCP Servers": "MCP 伺服器",
    "Data Mapping": "資料映射",
    "Data Sources": "資料來源",
    "Report Builder": "報表建構器",
    "Trade Viz": "交易視覺化",
    "Notes": "筆記",
    "Forum": "論壇",
    "Docs": "文件",
    "Support": "支援",
    "About": "關於",
    "View": "檢視",
    "Component Browser": "元件瀏覽器",
    "Fullscreen": "全螢幕",
    "Focus Mode": "專注模式",
    "Always on Top": "視窗置頂",
    "Float Panel": "浮動面板",
    "Dashboard": "儀表板",
    "News Feed": "新聞",
    "Portfolio": "投資組合",
    "Markets": "市場",
    "Crypto Trading": "加密貨幣交易",
    "Algo Trading": "演算法交易",
    "AI Chat": "AI 對話",
    "Quick Switch": "快速切換",
    "Trading": "交易",
    "Research": "研究",
    "M&&A Analytics": "併購分析",
    "Portfolio View": "投組檢視",
    "Markets View": "市場檢視",
    "News View": "新聞檢視",
    "Economics && Data": "經濟與資料",
    "Geopolitics View": "地緣政治檢視",
    "AI && Quant": "AI 與量化",
    "Quant Lab": "量化實驗室",
    "Tools View": "工具檢視",
    "Refresh Screen": "重新整理",
    "Take Screenshot": "螢幕截圖",
    "Help": "說明",
    "About Fincept": "關於 Fincept",
    "Help Center": "說明中心",
    "Contact Us": "聯絡我們",
    "Terms of Service": "服務條款",
    "Privacy Policy": "隱私政策",
    "Trademarks": "商標",
    "Check for Updates": "檢查更新",
    "Logout": "登出",
    # DashboardStatusBar.cpp
    "SESSION:": "工作階段：",
    "LAYOUT:": "版面：",
    "ACTIVE": "啟用中",
    "FEEDS:": "資料源：",
    "CONNECTED": "已連線",
    "MEM: OPTIMAL": "記憶體：最佳",
    "LAT: ---": "延遲：---",
    "READY": "就緒",
    "EMPTY": "空白",
    "DISCONNECTED": "已斷線",
    "LAT: ERR": "延遲：錯誤",
    "LAT: %1ms": "延遲：%1ms",
}


def main():
    tree = ET.parse(TS_FILE)
    root = tree.getroot()

    # 找到第一個（也是唯一的）context
    context = root.find("context")
    if context is None:
        print("錯誤：找不到 <context> 節點")
        sys.exit(1)

    # 收集現有的 source 文字
    existing = set()
    for msg in context.findall("message"):
        src = msg.find("source")
        if src is not None and src.text:
            existing.add(src.text)

    added = 0
    for source, translation in sorted(NEW_TRANSLATIONS.items()):
        if source in existing:
            continue
        # 建立新 <message> 節點
        msg = ET.SubElement(context, "message")
        src_el = ET.SubElement(msg, "source")
        src_el.text = source
        trans_el = ET.SubElement(msg, "translation")
        trans_el.text = translation
        added += 1

    if added > 0:
        ET.indent(tree, space="    ")
        tree.write(TS_FILE, encoding="utf-8", xml_declaration=True)
        print(f"已新增 {added} 筆翻譯")
    else:
        print("所有翻譯已存在，無須新增")


if __name__ == "__main__":
    main()
