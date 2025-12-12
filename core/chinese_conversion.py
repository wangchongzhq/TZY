# -*- coding: utf-8 -*-
"""
简繁体中文转换工具
"""
from opencc import OpenCC

# 初始化简繁体转换对象
s2t_converter = OpenCC('s2t')  # 简体转繁体
t2s_converter = OpenCC('t2s')  # 繁体转简体

def simplify_chinese(text):
    """
    将繁体中文转换为简体中文
    
    Args:
        text (str): 包含繁体中文的文本
        
    Returns:
        str: 转换后的简体中文文本
    """
    if not text or not isinstance(text, str):
        return text
    return t2s_converter.convert(text)

def traditionalize_chinese(text):
    """
    将简体中文转换为繁体中文
    
    Args:
        text (str): 包含简体中文的文本
        
    Returns:
        str: 转换后的繁体中文文本
    """
    if not text or not isinstance(text, str):
        return text
    return s2t_converter.convert(text)

def add_traditional_aliases(aliases_dict):
    """
    为字典中的简体中文别名添加对应的繁体中文版本
    
    Args:
        aliases_dict (dict): 频道名称到别名列表的映射
        
    Returns:
        dict: 更新后的包含简繁体别名的字典
    """
    updated_dict = {}
    
    for channel_name, aliases in aliases_dict.items():
        # 确保aliases是列表
        if not isinstance(aliases, list):
            aliases = [aliases]
        
        # 转换频道名称为繁体
        traditional_channel_name = traditionalize_chinese(channel_name)
        
        # 创建新的别名列表，包含原始别名和对应的繁体别名
        new_aliases = set(aliases)  # 使用集合避免重复
        
        # 为每个别名添加繁体版本
        for alias in aliases:
            traditional_alias = traditionalize_chinese(alias)
            if traditional_alias != alias:  # 只有当转换后不同时才添加
                new_aliases.add(traditional_alias)
        
        # 如果频道名称本身是简体，也将其繁体版本作为别名添加
        if traditional_channel_name != channel_name:
            new_aliases.add(traditional_channel_name)
        
        # 将集合转换回列表
        updated_dict[channel_name] = list(new_aliases)
    
    return updated_dict

if __name__ == "__main__":
    # 测试简繁体转换功能
    test_text = "CCTV1 央视 湖南卫视"
    print(f"简体: {test_text}")
    print(f"繁体: {traditionalize_chinese(test_text)}")
    
    # 测试添加繁体别名功能
    test_aliases = {
        "CCTV1": ["CCTV-1", "CCTV1综合"],
        "湖南卫视": ["湖南卫视 HD", "湖南台"]
    }
    print(f"\n原始别名: {test_aliases}")
    print(f"添加繁体后: {add_traditional_aliases(test_aliases)}")
