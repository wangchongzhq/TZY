# -*- coding: utf-8 -*-
"""
简繁体中文转换工具
"""
from opencc import OpenCC
from typing import Dict, Any, List, Set

# 初始化简繁体转换对象
s2t_converter = OpenCC('s2t')  # 简体转繁体
t2s_converter = OpenCC('t2s')  # 繁体转简体

# 默认转换配置
DEFAULT_CONVERSION_CONFIG = {
    'opencc_config': 't2s.json',  # 繁体到简体
    'excluded_channels': ['翡翠台', '明珠台', '本港台'],  # 不转换的频道
    'excluded_groups': ['港澳频道'],  # 不转换的分组
    'fields_to_convert': ['name', 'group']  # 需要转换的字段
}

class ChineseConversionPipeline:
    """
    简繁体转换流水线，用于处理直播源的繁简转换
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化转换流水线
        
        Args:
            config: 转换配置，包括需要转换的字段、例外列表等
        """
        self.config = config or DEFAULT_CONVERSION_CONFIG
        self.converter = t2s_converter  # 默认使用繁体转简体
        self.excluded_channels = set(self.config.get('excluded_channels', []))
        self.excluded_groups = set(self.config.get('excluded_groups', []))
        self.fields_to_convert = self.config.get('fields_to_convert', ['name', 'group'])
    
    def should_convert_channel(self, channel_name: str, group_name: str = None) -> bool:
        """
        判断频道是否应该进行转换
        
        Args:
            channel_name: 频道名称
            group_name: 分组名称
        
        Returns:
            bool: 是否应该转换
        """
        if not channel_name:
            return False
        
        # 检查是否在例外频道列表中
        if channel_name in self.excluded_channels:
            print(f"例外频道: {channel_name}")
            return False
        
        # 检查是否在例外分组中
        if group_name and group_name in self.excluded_groups:
            print(f"例外分组: {group_name} 中的频道: {channel_name}")
            return False
        
        return True
    
    def convert_channel(self, channel_name: str, group_name: str = None) -> str:
        """
        转换频道名称
        
        Args:
            channel_name: 频道名称
            group_name: 分组名称
        
        Returns:
            str: 转换后的频道名称
        """
        if self.should_convert_channel(channel_name, group_name):
            converted = self.converter.convert(channel_name)
            if converted != channel_name:
                print(f"转换频道: {channel_name} -> {converted} (分组: {group_name})")
            return converted
        return channel_name
    
    def convert_group(self, group_name: str) -> str:
        """
        转换分组名称
        
        Args:
            group_name: 分组名称
        
        Returns:
            str: 转换后的分组名称
        """
        if group_name in self.excluded_groups:
            return group_name
        return self.converter.convert(group_name)
    
    def process_channel_data(self, channels: Dict[str, List[tuple]]) -> Dict[str, List[tuple]]:
        """
        处理完整的频道数据，转换所有需要转换的字段
        
        Args:
            channels: 频道数据，格式为 {group_name: [(channel_name, url), ...]}
        
        Returns:
            Dict[str, List[tuple]]: 转换后的频道数据
        """
        processed_channels = {}
        
        for group_name, channel_list in channels.items():
            # 转换分组名称
            converted_group = self.convert_group(group_name)
            
            # 转换该分组下的所有频道
            converted_channels = []
            for channel_name, url in channel_list:
                converted_channel = self.convert_channel(channel_name, converted_group)
                converted_channels.append((converted_channel, url))
            
            processed_channels[converted_group] = converted_channels
        
        return processed_channels

def simplify_chinese(text):
    """
    将繁体中文转换为简体中文（兼容旧版本）
    
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
    将简体中文转换为繁体中文（兼容旧版本）
    
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

# 创建全局转换流水线实例
conversion_pipeline = ChineseConversionPipeline()

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
    
    # 测试转换流水线
    test_channels = {
        "新聞": ["無線新聞台", "http://example.com/news"],
        "娛樂": ["翡翠台", "http://example.com/ctv"],  # 应该被排除
        "港澳頻道": ["明珠台", "http://example.com/atv"]  # 应该被排除
    }
    
    print(f"\n原始频道数据: {test_channels}")
    processed = conversion_pipeline.process_channel_data(test_channels)
    print(f"转换后频道数据: {processed}")
