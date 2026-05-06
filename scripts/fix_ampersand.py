#!/usr/bin/env python3
"""修復含 & 的字串 + Settings 區域翻譯"""
import re

TS = '/Users/ktw/ktw-projects/fincept-terminal-zh/fincept-qt/translations/fincept_zh_TW.ts'

with open(TS, 'r', encoding='utf-8') as f:
    content = f.read()

# 翻譯表（source → translation）
# 注意 .ts 中 & 已被 XML 轉義為 &amp;，&& 為 &amp;&amp;
FIXES = {
    # 含 &amp; 的
    'Save &amp; Set Active': '儲存並啟用',
    'TEST &amp; SAVE': '測試並儲存',
    'SAVE &amp; CONNECT': '儲存並連線',
    'SKIP &amp; CONTINUE': '跳過並繼續',
    'TIME &amp; SALES': '成交明細',
    'T&amp;S': '成交明細',
    'M&amp;A ANALYTICS': 'M&amp;A 分析',
    'M&amp;A Analytics': 'M&amp;A 分析',
    'Sources &amp; Uses': '資金來源與用途',
    'Science &amp; Tech': '科學與科技',
    'SYMBOLS &amp; PARAMETERS': '代碼與參數',
    'STORAGE &amp; DATA MANAGEMENT': '儲存與資料管理',
    'PROFILE &amp; ACCOUNT': '個人資料與帳戶',
    'Trading &amp; Portfolio': '交易與投資組合',
    'Markets &amp; Data': '市場與資料',
    'Research &amp; Intelligence': '研究與情報',
    'DRAWDOWN &amp; RISK METRICS': '回撤與風險指標',
    'View Plans &amp; Pricing': '查看方案與定價',
    'Create &amp; Switch': '建立並切換',
    # Settings 相關
    'Credentials': '憑證',
    'Appearance': '外觀',
    'Notifications': '通知',
    'Storage Cache': '儲存快取',
    'Data Sources': '資料來源',
    'LLM Config': 'LLM 設定',
    'MCP Servers': 'MCP 伺服器',
    'Logging': '日誌記錄',
    'Security': '安全性',
    'Profiles': '設定檔',
    'Keybindings': '快速鍵',
    'Python Env': 'Python 環境',
    'Developer': '開發者',
    'Voice': '語音',
    'Provider Configuration': '供應商設定',
    'Provider': '供應商',
    'API Key': 'API 金鑰',
    'Base URL': '基礎 URL',
    'Model': '模型',
    'Test Connection': '測試連線',
    'PROVIDERS': '供應商',
    'PROFILES': '設定檔',
    'LLM CONFIGURATION': 'LLM 設定',
    'SETTINGS': '設定',
    'Linked to your Fincept account': '已連結至您的 Fincept 帳戶',
    'Select a deployment to view curve': '選取部署以檢視曲線',
    'Select an article': '選取文章',
    'Session error — please restart.': '工作階段錯誤 — 請重新啟動。',
    'Show Raw JSON': '顯示原始 JSON',
    'Signal Data': '訊號資料',
    'Slippage Estimator': '滑價估算器',
    'Spot: —': '現貨：—',
    'Stationarity': '定態性',
    'Statistics': '統計',
    'Scorecard': '計分卡',
    'Sensitivity': '敏感度',
    'Sentiment': '情緒',
    'Synergies': '綜效',
    'Task Monitor': '任務監控',
    'Technicals': '技術面',
    'Technology': '科技',
    'Train Model': '訓練模型',
    'Upgrade All': '全部升級',
    'Voice mode active': '語音模式啟用中',
    'not configured': '尚未設定',
    'hidden': '已隱藏',
    'datasets': '資料集',
    'market': '市場',
}

fixed = 0
for src, trans in FIXES.items():
    if src == trans:
        continue
    # 精確匹配：<source>SRC</source> 後面跟 <translation...>SRC</translation>
    # 或 <translation type="unfinished">SRC</translation>
    old = f'<source>{src}</source>'
    if old not in content:
        continue

    # 找到所有包含此 source 的位置
    idx = 0
    while True:
        pos = content.find(old, idx)
        if pos == -1:
            break
        
        # 找後面的 <translation
        trans_start = content.find('<translation', pos + len(old))
        if trans_start == -1 or trans_start > pos + len(old) + 50:
            idx = pos + 1
            continue
        
        # 找 > 結束
        gt = content.find('>', trans_start)
        if gt == -1:
            idx = pos + 1
            continue
        
        # 找 </translation>
        trans_end = content.find('</translation>', gt)
        if trans_end == -1:
            idx = pos + 1
            continue
        
        existing_trans = content[gt+1:trans_end]
        
        # 只替換未翻譯的（與 source 相同或有 unfinished 標記）
        if existing_trans == src or 'type="unfinished"' in content[trans_start:gt+1]:
            # 替換翻譯內容，移除 unfinished 標記
            new_tag = f'<translation>{trans}'
            old_tag = content[trans_start:gt+1] + existing_trans
            content = content[:trans_start] + new_tag + content[trans_end:]
            fixed += 1
        
        idx = pos + 1

with open(TS, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 修復 {fixed} 個字串")

# 最終統計
pairs = re.findall(r'<source>(.*?)</source>\s*<translation[^>]*>(.*?)</translation>', content, re.DOTALL)
total = len(pairs)
translated = sum(1 for s, t in pairs if s.strip() != t.strip())
print(f"翻譯覆蓋率：{translated}/{total} ({100*translated/max(total,1):.1f}%)")
