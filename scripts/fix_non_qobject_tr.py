#!/usr/bin/env python3
"""
全面修復所有非 QObject context 中的 tr() 呼叫。
策略：將自由函式、namespace 函式、struct 成員中的 tr() 
替換為 QCoreApplication::translate("FinceptTerminal", ...)
"""
import re
import os
import sys

def is_in_class_method(lines, target_line_idx):
    """
    判斷目標行是否在 QObject 子類別的成員函式中。
    簡單的啟發式：往回找最近的函式定義，看是否屬於有 Q_OBJECT 的類別。
    """
    # 這個太複雜，改用另一個策略：
    # 在 Docker 建構時，讓編譯器告訴我們哪些 tr() 有問題
    return True

def fix_all_tr_in_free_functions(base_dir):
    """
    更暴力但安全的策略：
    1. 收集所有 .cpp 中的 tr() 呼叫
    2. 如果對應的 .h 沒有 Q_OBJECT，或 tr() 在 namespace 自由函式中
       → 替換為 QCoreApplication::translate
    """
    src_dir = os.path.join(base_dir, 'fincept-qt', 'src')
    fixed_count = 0
    
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith('.cpp'):
                continue
            
            filepath = os.path.join(root, fname)
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            if 'tr(' not in content:
                continue
            
            # 檢查對應的 .h 檔是否有 Q_OBJECT
            hpath = filepath.replace('.cpp', '.h')
            has_qobject = False
            if os.path.exists(hpath):
                with open(hpath, 'r') as f:
                    hcontent = f.read()
                has_qobject = 'Q_OBJECT' in hcontent
            
            if not has_qobject:
                # 整個檔案都不是 QObject 子類別
                # 所有 tr() 都需要替換
                original = content
                content = re.sub(
                    r'\btr\(',
                    'QCoreApplication::translate("FinceptTerminal", ',
                    content
                )
                if '#include <QCoreApplication>' not in content:
                    # 在最後一個 #include 之後加入
                    last_include = content.rfind('#include')
                    if last_include >= 0:
                        end_of_line = content.index('\n', last_include)
                        content = (content[:end_of_line+1] + 
                                  '#include <QCoreApplication>\n' + 
                                  content[end_of_line+1:])
                
                if content != original:
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"✅ 全檔修復 (非QObject): {os.path.relpath(filepath, base_dir)}")
                    fixed_count += 1
            else:
                # 有 Q_OBJECT 但可能有自由函式
                # 分析每個 tr() 是否在類別成員函式內
                lines = content.split('\n')
                modified = False
                
                # 追蹤是否在 namespace 作用域（非 class member）
                # 策略：找出類別名稱，然後看 tr() 是否在 ClassName:: 方法中
                
                # 從 .h 取得類別名
                class_names = []
                with open(hpath, 'r') as f:
                    for line in f:
                        m = re.match(r'\s*class\s+(\w+)\s*:', line)
                        if m:
                            class_names.append(m.group(1))
                
                if not class_names:
                    continue
                
                # 掃描 .cpp 找自由函式中的 tr()
                in_class_method = False
                brace_depth = 0
                func_start_depth = 0
                new_lines = []
                
                for i, line in enumerate(lines):
                    # 檢查函式定義行
                    for cname in class_names:
                        if f'{cname}::' in line and '{' in line:
                            in_class_method = True
                            func_start_depth = brace_depth
                    
                    # 非成員函式定義（自由函式）
                    func_def_match = re.match(
                        r'(?:static\s+)?(?:inline\s+)?\w[\w:]*\s+(?:(?!' + 
                        '|'.join(class_names) + r'::)\w+)\s*\(', 
                        line.strip()
                    )
                    
                    brace_depth += line.count('{') - line.count('}')
                    
                    if brace_depth <= func_start_depth and in_class_method:
                        in_class_method = False
                    
                    # 如果不在成員函式中且有 tr()
                    if not in_class_method and 'tr(' in line:
                        # 檢查是不是真的 tr() 呼叫
                        if re.search(r'\btr\(', line) and 'translate' not in line:
                            old_line = line
                            line = re.sub(
                                r'\btr\(',
                                'QCoreApplication::translate("FinceptTerminal", ',
                                line
                            )
                            if line != old_line:
                                modified = True
                    
                    new_lines.append(line)
                
                if modified:
                    content = '\n'.join(new_lines)
                    if '#include <QCoreApplication>' not in content:
                        last_include = content.rfind('#include')
                        if last_include >= 0:
                            end_of_line = content.index('\n', last_include)
                            content = (content[:end_of_line+1] + 
                                      '#include <QCoreApplication>\n' + 
                                      content[end_of_line+1:])
                    
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"✅ 局部修復 (自由函式): {os.path.relpath(filepath, base_dir)}")
                    fixed_count += 1
    
    return fixed_count

def main():
    base_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    fixed = fix_all_tr_in_free_functions(base_dir)
    print(f"\n修復完成: {fixed} 個檔案")

if __name__ == '__main__':
    main()
