#!/usr/bin/env python3
"""
翻譯 Settings 相關頁面的所有字串。
涵蓋：SettingsScreen, LlmConfigSection, KeybindingsSection, PythonEnvSection, McpServersSection
"""

import xml.etree.ElementTree as ET
import sys
import copy

TS_FILE = "/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts"

# ── 翻譯對照表 ──────────────────────────────────────────────────────
# 格式：(context_name, source_text) -> translation
TRANSLATIONS = {
    # ═══════════════════════════════════════════════════════════
    # SettingsScreen — 側欄 + 各分區
    # ═══════════════════════════════════════════════════════════
    ("SettingsScreen", "SETTINGS"): "設定",
    ("SettingsScreen", "Credentials"): "憑證",
    ("SettingsScreen", "Appearance"): "外觀",
    ("SettingsScreen", "Notifications"): "通知",
    ("SettingsScreen", "Storage Cache"): "儲存空間",
    ("SettingsScreen", "Data Sources"): "資料來源",
    ("SettingsScreen", "LLM Config"): "LLM 設定",
    ("SettingsScreen", "MCP Servers"): "MCP 伺服器",
    ("SettingsScreen", "Logging"): "日誌紀錄",
    ("SettingsScreen", "Security"): "安全性",
    ("SettingsScreen", "Profiles"): "設定檔",
    ("SettingsScreen", "Keybindings"): "快捷鍵",
    ("SettingsScreen", "Python Env"): "Python 環境",
    ("SettingsScreen", "Developer"): "開發者",
    ("SettingsScreen", "Voice"): "語音",

    # Credentials 分區
    ("SettingsScreen", "API CREDENTIALS"): "API 憑證",
    ("SettingsScreen", "Store API keys securely in the OS keychain. Keys are never written to disk in plain text."): "將 API 金鑰安全存放在作業系統的鑰匙圈中。金鑰絕不會以明文寫入磁碟。",
    ("SettingsScreen", "Not set"): "未設定",
    ("SettingsScreen", "Not configured"): "未設定",
    ("SettingsScreen", "Save"): "儲存",
    ("SettingsScreen", "Cleared"): "已清除",
    ("SettingsScreen", "Saved \u2713"): "已儲存 ✓",
    ("SettingsScreen", "Save failed"): "儲存失敗",
    ("SettingsScreen", "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022 (saved)"): "•••••••• (已儲存)",

    # Appearance 分區
    ("SettingsScreen", "TYPOGRAPHY"): "字型排版",
    ("SettingsScreen", "THEME"): "主題",
    ("SettingsScreen", "INTERFACE"): "介面",
    ("SettingsScreen", "Save Settings"): "儲存設定",

    # Notifications 分區
    ("SettingsScreen", "NOTIFICATION PROVIDERS"): "通知供應商",
    ("SettingsScreen", "Test Send"): "測試發送",
    ("SettingsScreen", "Sending..."): "發送中...",
    ("SettingsScreen", "\u2713 Sent successfully"): "✓ 發送成功",
    ("SettingsScreen", "\u2717 "): "✗ ",
    ("SettingsScreen", "ALERT TRIGGERS"): "警報觸發條件",
    ("SettingsScreen", "Save All Providers"): "儲存所有供應商",

    # Storage 分區
    ("SettingsScreen", "STORAGE & DATA MANAGEMENT"): "儲存與資料管理",
    ("SettingsScreen", "REFRESH"): "重新整理",
    ("SettingsScreen", "Refresh"): "重新整理",
    ("SettingsScreen", "CATEGORY"): "分類",
    ("SettingsScreen", "ENTRIES"): "項目數",
    ("SettingsScreen", "ACTION"): "操作",
    ("SettingsScreen", "CLR"): "清除",
    ("SettingsScreen", "STORE"): "儲存區",
    ("SettingsScreen", "SIZE"): "大小",
    ("SettingsScreen", "Registry"): "註冊表",
    ("SettingsScreen", "Cache:"): "快取：",
    ("SettingsScreen", "fincept.db"): "fincept.db",
    ("SettingsScreen", "cache.db"): "cache.db",
    ("SettingsScreen", "EXEC"): "執行",
    ("SettingsScreen", "Ready"): "就緒",
    ("SettingsScreen", "Quick:"): "快速：",
    ("SettingsScreen", "Cancelled"): "已取消",
    ("SettingsScreen", "Error: "): "錯誤：",
    ("SettingsScreen", "OK \u2014 no columns returned"): "成功 — 無欄位回傳",

    # Danger Zone
    ("SettingsScreen", "DANGER ZONE"): "危險區域",
    ("SettingsScreen", "Clear All Cache"): "清除所有快取",
    ("SettingsScreen", "Delete all temporary cached data. Will be re-fetched on next access."): "刪除所有暫存資料。下次存取時將重新擷取。",
    ("SettingsScreen", "CLEAR CACHE"): "清除快取",
    ("SettingsScreen", "Clear ALL User Data"): "清除所有使用者資料",
    ("SettingsScreen", "Permanently delete all databases, files, cache, and UI state. OS keychain is preserved."): "永久刪除所有資料庫、檔案、快取及介面狀態。作業系統鑰匙圈將被保留。",
    ("SettingsScreen", "DELETE ALL"): "全部刪除",

    # Data Sources 分區
    ("SettingsScreen", "DATA SOURCES"): "資料來源",
    ("SettingsScreen", "OPEN FULL SCREEN"): "開啟全螢幕",
    ("SettingsScreen", "No data sources configured. Open the full Data Sources screen to browse and add connectors."): "尚未設定任何資料來源。請開啟完整的資料來源頁面以瀏覽並新增連接器。",
    ("SettingsScreen", "X"): "X",
    ("SettingsScreen", "ENABLE ALL"): "全部啟用",
    ("SettingsScreen", "DISABLE ALL"): "全部停用",

    # ═══════════════════════════════════════════════════════════
    # LlmConfigSection
    # ═══════════════════════════════════════════════════════════
    ("LlmConfigSection", "LLM CONFIGURATION"): "LLM 設定",
    ("LlmConfigSection", "PROVIDERS"): "供應商",
    ("LlmConfigSection", "PROFILES"): "設定檔",
    ("LlmConfigSection", "Providers"): "供應商",
    ("LlmConfigSection", "+ Add"): "+ 新增",
    ("LlmConfigSection", "Remove"): "移除",
    ("LlmConfigSection", "Provider Configuration"): "供應商設定",
    ("LlmConfigSection", "Provider"): "供應商",
    ("LlmConfigSection", "e.g. openai"): "例如 openai",
    ("LlmConfigSection", "API Key"): "API 金鑰",
    ("LlmConfigSection", "sk-..."): "sk-...",
    ("LlmConfigSection", "Model"): "模型",
    ("LlmConfigSection", "Select or type model..."): "選擇或輸入模型...",
    ("LlmConfigSection", "Fetch"): "擷取",
    ("LlmConfigSection", "Base URL"): "基礎網址",
    ("LlmConfigSection", "Optional \u2014 leave empty for default"): "選填 — 留空則使用預設值",
    ("LlmConfigSection", "When enabled, the AI can interact with the terminal: navigate screens, fetch market "
     "data, manage portfolios, run tools, etc."): "啟用後，AI 可與終端互動：切換畫面、擷取市場資料、管理投資組合、執行工具等。",
    ("LlmConfigSection", "Save & Set Active"): "儲存並啟用",
    ("LlmConfigSection", "Test Connection"): "測試連線",

    # LLM Global Settings
    ("LlmConfigSection", "GLOBAL SETTINGS"): "全域設定",
    ("LlmConfigSection", "Temperature"): "溫度",
    ("LlmConfigSection", "Max Tokens"): "最大 Token 數",
    ("LlmConfigSection", "System Prompt"): "系統提示詞",
    ("LlmConfigSection", "Optional system prompt for the LLM..."): "選填 LLM 系統提示詞...",
    ("LlmConfigSection", "Save Global Settings"): "儲存全域設定",

    # LLM Provider placeholders
    ("LlmConfigSection", "Linked to your Fincept account: "): "已連結您的 Fincept 帳戶：",
    ("LlmConfigSection", "Login to your Fincept account to enable"): "登入您的 Fincept 帳戶以啟用",

    # LLM Profiles
    ("LlmConfigSection", "A profile = named LLM config you can assign to any agent or team."): "設定檔 = 可指派給任何代理或團隊的具名 LLM 設定。",
    ("LlmConfigSection", "+ New"): "+ 新增",
    ("LlmConfigSection", "Delete"): "刪除",
    ("LlmConfigSection", "e.g. Fast Groq, Careful Claude, Coding minimax"): "例如 Fast Groq、Careful Claude、Coding minimax",
    ("LlmConfigSection", "Leave blank to inherit from provider"): "留空則繼承供應商設定",
    ("LlmConfigSection", "Leave blank to use provider default"): "留空則使用供應商預設值",
    ("LlmConfigSection", "Leave blank to use global system prompt"): "留空則使用全域系統提示詞",
    ("LlmConfigSection", "SAVE PROFILE"): "儲存設定檔",
    ("LlmConfigSection", "SET AS DEFAULT"): "設為預設",

    # MCP Tools checkbox（在 LlmConfigSection 中）
    ("LlmConfigSection", "Enable MCP Tools (navigation, market data, portfolio, etc.)"): "啟用 MCP 工具（導航、市場資料、投資組合等）",

    # ═══════════════════════════════════════════════════════════
    # KeybindingsSection
    # ═══════════════════════════════════════════════════════════
    ("KeybindingsSection", "Rebind: "): "重新綁定：",
    ("KeybindingsSection", "Press new key combination..."): "請按下新的按鍵組合...",
    ("KeybindingsSection", "Warning: already used by "): "警告：已被以下功能使用 — ",
    ("KeybindingsSection", "Search actions..."): "搜尋操作...",
    ("KeybindingsSection", "Reset All to Defaults"): "全部重設為預設",
    ("KeybindingsSection", "Reset"): "重設",

    # ═══════════════════════════════════════════════════════════
    # PythonEnvSection
    # ═══════════════════════════════════════════════════════════
    ("PythonEnvSection", "PYTHON ENVIRONMENTS"): "Python 環境",
    ("PythonEnvSection", "Filter packages..."): "篩選套件...",
    ("PythonEnvSection", "Refresh"): "重新整理",
    ("PythonEnvSection", "Install Missing"): "安裝缺失套件",
    ("PythonEnvSection", "Upgrade All"): "全部升級",
    ("PythonEnvSection", "Install / Upgrade Selected"): "安裝 / 升級選取項目",
    ("PythonEnvSection", "Starting..."): "啟動中...",

    # ═══════════════════════════════════════════════════════════
    # McpServersSection
    # ═══════════════════════════════════════════════════════════
    ("McpServersSection", "MCP SERVERS"): "MCP 伺服器",
    ("McpServersSection", "External Servers"): "外部伺服器",
    ("McpServersSection", "+ Add"): "+ 新增",
    ("McpServersSection", "Remove"): "移除",
    ("McpServersSection", "Select a server to view details."): "選取伺服器以檢視詳細資訊。",
    ("McpServersSection", "\u25b6  Start"): "▶  啟動",
    ("McpServersSection", "\u25a0  Stop"): "■  停止",
    ("McpServersSection", "All registered MCP tools \u2014 both internal (built-in) and external (from connected servers)."): "所有已註冊的 MCP 工具 — 包含內建及外部（來自已連線伺服器）。",
    ("McpServersSection", "Add MCP Server"): "新增 MCP 伺服器",
    ("McpServersSection", "Add External MCP Server"): "新增外部 MCP 伺服器",
    ("McpServersSection", "Auto-start on launch"): "啟動時自動執行",
    ("McpServersSection", "No external servers configured.\nClick '+ Add' to add one."): "尚未設定外部伺服器。\n點擊「+ 新增」以新增。",
}

# 額外：從截圖中看到的導航列側邊欄項目（可能在 SettingsScreen 中）
# 這些也許是用 addItem / addTab 方式加入的

def main():
    tree = ET.parse(TS_FILE)
    root = tree.getroot()

    filled = 0
    skipped = 0
    not_found = []

    for ctx in root.findall('context'):
        ctx_name = ctx.find('name').text
        for msg in ctx.findall('message'):
            src = msg.find('source')
            trans = msg.find('translation')
            if src is None or trans is None:
                continue

            key = (ctx_name, src.text)
            if key in TRANSLATIONS:
                # 檢查是否已翻譯
                if trans.get('type') == 'unfinished':
                    trans.text = TRANSLATIONS[key]
                    trans.attrib.pop('type', None)
                    filled += 1
                    print(f"  ✅ [{ctx_name}] {src.text[:50]}...")
                else:
                    skipped += 1

    # 檢查哪些翻譯沒有找到對應的 source
    found_keys = set()
    for ctx in root.findall('context'):
        ctx_name = ctx.find('name').text
        for msg in ctx.findall('message'):
            src = msg.find('source')
            if src is not None:
                found_keys.add((ctx_name, src.text))

    for key in TRANSLATIONS:
        if key not in found_keys:
            not_found.append(key)

    print(f"\n📊 結果：{filled} 個字串已填入翻譯，{skipped} 個已跳過（已翻譯）")
    if not_found:
        print(f"⚠️  {len(not_found)} 個翻譯找不到對應的 source（可能 context 名稱不同）：")
        for k in not_found[:10]:
            print(f"   - [{k[0]}] {k[1][:60]}")

    # 寫回檔案
    tree.write(TS_FILE, encoding='utf-8', xml_declaration=True)
    print(f"\n💾 已寫入：{TS_FILE}")

    # 統計最終狀態
    tree2 = ET.parse(TS_FILE)
    root2 = tree2.getroot()
    for ctx in root2.findall('context'):
        name = ctx.find('name').text
        if name in ('SettingsScreen', 'LlmConfigSection', 'KeybindingsSection', 'PythonEnvSection', 'McpServersSection'):
            msgs = ctx.findall('message')
            finished = sum(1 for m in msgs if m.find('translation').get('type') != 'unfinished')
            total = len(msgs)
            print(f"  {name}: {finished}/{total} 已翻譯 ({finished*100//total}%)")


if __name__ == "__main__":
    main()
