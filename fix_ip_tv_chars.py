import re

# 读取IP-TV.py文件内容
try:
    with open('IP-TV.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除所有不可打印字符，包括欧元符号和其他特殊字符
    # 保留ASCII可打印字符和常见的中文、日文、韩文等Unicode字符
    cleaned_content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f\u20ac\ue000-\uf8ff]', '', content)
    
    # 将清理后的内容写回文件
    with open('IP-TV.py', 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print('✓ IP-TV.py文件中的不可打印字符已移除')
    
except Exception as e:
    print(f'✗ 处理文件时出错: {type(e).__name__}: {e}')
