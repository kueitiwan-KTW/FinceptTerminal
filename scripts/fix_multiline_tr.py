#!/usr/bin/env python3
"""
修復 tr() 多行字串拼接問題 — 正確版本。

問題模式：
  someFunc(tr("line1\n")
              "line2\n"
              "line3");

修正為：
  someFunc(tr("line1\n"
              "line2\n"
              "line3"));

策略：
1. 找到 tr("...\n") 行尾模式
2. 確認下一行是裸字串續行
3. 把 tr() 的 ) 從第一行移到最後一個字串行
"""
import re
import os
import sys

def fix_file(filepath, base_dir):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 偵測：行尾有 tr("...\n") 且下一行是裸字串
        # 也包含 QCoreApplication::translate("ctx", "...\n") 的情況
        stripped = line.rstrip('\n').rstrip()
        
        # 匹配 tr("...") 結尾的行
        tr_end_match = re.search(r'\btr\(".*?"\)\s*$', stripped)
        translate_end_match = re.search(r'translate\("[^"]*",\s*".*?"\)\s*$', stripped)
        
        end_match = tr_end_match or translate_end_match
        
        if end_match and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            # 下一行是裸字串開頭（不是新語句）
            if next_stripped.startswith('"'):
                # 這是多行字串拼接！
                # 移除行尾的 ) — 就在 " 和 ) 之間
                # tr("...\n") → tr("...\n"
                fixed = stripped
                if tr_end_match:
                    # 找到最後的 ") 並移除 )
                    fixed = re.sub(r'"\)\s*$', '"', stripped)
                elif translate_end_match:
                    fixed = re.sub(r'"\)\s*$', '"', stripped)
                
                result.append(fixed + '\n')
                i += 1
                
                # 收集續行，找到最後一行字串
                while i < len(lines):
                    cont = lines[i]
                    cont_stripped = cont.strip()
                    
                    if cont_stripped.startswith('"'):
                        # 檢查是否是最後一行（後面不再接字串）
                        is_last = (i + 1 >= len(lines) or 
                                   not lines[i + 1].strip().startswith('"'))
                        
                        if is_last:
                            # 在最後一個 " 後面加 )
                            indent = cont[:len(cont) - len(cont.lstrip())]
                            # 找到行尾的 "); 或 "); 或 " 然後加 )
                            if cont_stripped.endswith('");'):
                                # 已經有 "); — 改成 "));
                                new_cont = cont_stripped[:-2] + '));'
                                result.append(indent + new_cont + '\n')
                            elif cont_stripped.endswith('");'):
                                new_cont = cont_stripped[:-2] + '));'
                                result.append(indent + new_cont + '\n')
                            else:
                                # 不確定格式，保留原樣
                                result.append(cont)
                            modified = True
                            i += 1
                            break
                        else:
                            result.append(cont)
                            i += 1
                    else:
                        # 不是字串行了，把 ) 加到上一行
                        # 回退修改上一行
                        if result:
                            prev = result[-1].rstrip('\n').rstrip()
                            if prev.endswith('";'):
                                result[-1] = prev[:-1] + ');\n'
                            elif prev.endswith('"'):
                                result[-1] = prev + ')\n'
                            modified = True
                        result.append(cont)
                        i += 1
                        break
                continue
        
        result.append(line)
        i += 1
    
    if modified:
        with open(filepath, 'w') as f:
            f.writelines(result)
        print(f"✅ 修復: {os.path.relpath(filepath, base_dir)}")
    
    return modified

def main():
    base_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    src_dir = os.path.join(base_dir, 'fincept-qt', 'src')
    fixed = 0
    
    for root, dirs, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith('.cpp'):
                continue
            filepath = os.path.join(root, fname)
            if fix_file(filepath, base_dir):
                fixed += 1
    
    print(f"\n修復完成: {fixed} 個檔案")

if __name__ == '__main__':
    main()
