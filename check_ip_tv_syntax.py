import ast
import sys

# 尝试解析IP-TV.py文件，获取更详细的错误信息
try:
    with open('IP-TV.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尝试解析整个文件
    ast.parse(content)
    print('✓ IP-TV.py: 语法正确')
    
except SyntaxError as e:
    print(f'✗ 语法错误: {e}')
    print(f'行号: {e.lineno}, 偏移量: {e.offset}')
    
    # 获取有问题的行
    lines = content.splitlines()
    if 0 <= e.lineno - 1 < len(lines):
        problem_line = lines[e.lineno - 1]
        print(f'问题行内容: {repr(problem_line)}')
        
        # 打印该行的十六进制表示
        print(f'问题行十六进制: {problem_line.encode("utf-8").hex()}')
        
        # 标记错误位置
        if 0 <= e.offset - 1 < len(problem_line):
            print('错误位置: ' + ' ' * (e.offset - 1) + '^')
            
except Exception as e:
    print(f'✗ 其他错误: {type(e).__name__}: {e}')
