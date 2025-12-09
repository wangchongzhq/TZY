import json
import requests
import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Optional, Any
from core.config import get_config
from core.channel_utils import normalize_channel_name

logger = logging.getLogger(__name__)

class EPGHandler:
    def __init__(self):
        self.epg_data: Dict[str, Any] = {}
        self.channel_logos: Dict[str, str] = {}
        self.epg_sources: List[str] = []
        self.logo_source: str = ""
        self._load_config()
        self._load_channel_logos()
    
    def _load_config(self):
        """加载EPG配置"""
        epg_config = get_config("epg", {})
        self.epg_sources = epg_config.get("sources", [])
        self.logo_source = epg_config.get("logo_source", "epg_data.json")
    
    def _load_channel_logos(self):
        """从epg_data.json加载频道台标信息"""
        try:
            with open("epg_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # 处理epg_data.json的两种可能格式：列表或包含'epgs'键的字典
            if isinstance(data, dict):
                channels = data.get('epgs', [])
            else:
                channels = data
                
            for channel in channels:
                # 使用规范化的频道名称作为键
                normalized_name = normalize_channel_name(channel.get("name", ""))
                # 同时存储原始名称和规范化名称作为键，以提高匹配率
                self.channel_logos[normalized_name] = channel.get("logo", "")
                self.channel_logos[channel.get("name", "")] = channel.get("logo", "")
                # 存储epgid和tvid作为键
                if "epgid" in channel:
                    self.channel_logos[channel["epgid"]] = channel.get("logo", "")
                if "tvid" in channel:
                    self.channel_logos[channel["tvid"]] = channel.get("logo", "")
            logger.info(f"成功加载了 {len(self.channel_logos)} 个频道的台标信息")
        except Exception as e:
            logger.error(f"加载台标信息失败: {e}")
    
    def load_epg_data(self):
        """加载所有EPG源数据"""
        if not self.epg_sources:
            logger.warning("没有配置EPG源")
            return
        
        for source in self.epg_sources:
            try:
                logger.info(f"正在从 {source} 加载EPG数据")
                response = requests.get(source, timeout=30)
                response.raise_for_status()
                
                # 检测内容类型
                if "xml" in response.headers.get("content-type", "") or source.endswith(".xml"):
                    self._parse_xml_epg(response.content, source)
                else:
                    # 尝试按XML解析
                    try:
                        self._parse_xml_epg(response.content, source)
                    except Exception as e:
                        logger.error(f"解析EPG源 {source} 失败，不支持的格式: {e}")
            except Exception as e:
                logger.error(f"加载EPG源 {source} 失败: {e}")
    
    def _parse_xml_epg(self, xml_content: bytes, source: str):
        """解析XML格式的EPG数据"""
        try:
            root = ET.fromstring(xml_content)
            
            # 解析tv元素下的channel和programme元素
            for channel_elem in root.findall("./channel"):
                channel_id = channel_elem.attrib.get("id", "")
                if not channel_id:
                    continue
                
                # 提取频道名称
                display_name_elem = channel_elem.find("./display-name")
                channel_name = display_name_elem.text if display_name_elem is not None else ""
                
                # 提取频道图标
                icon_elem = channel_elem.find("./icon")
                icon_url = icon_elem.attrib.get("src", "") if icon_elem is not None else ""
                
                # 存储频道信息
                if channel_id not in self.epg_data:
                    self.epg_data[channel_id] = {
                        "name": channel_name,
                        "icon": icon_url,
                        "programmes": []
                    }
                else:
                    # 更新已存在频道的信息
                    if not self.epg_data[channel_id]["name"]:
                        self.epg_data[channel_id]["name"] = channel_name
                    if not self.epg_data[channel_id]["icon"]:
                        self.epg_data[channel_id]["icon"] = icon_url
            
            for programme_elem in root.findall("./programme"):
                channel_id = programme_elem.attrib.get("channel", "")
                start_time = programme_elem.attrib.get("start", "")
                stop_time = programme_elem.attrib.get("stop", "")
                
                if not channel_id or not start_time or not stop_time:
                    continue
                
                # 提取节目标题
                title_elem = programme_elem.find("./title")
                title = title_elem.text if title_elem is not None else ""
                
                # 提取节目描述
                desc_elem = programme_elem.find("./desc")
                description = desc_elem.text if desc_elem is not None else ""
                
                # 提取节目分类
                category_elem = programme_elem.find("./category")
                category = category_elem.text if category_elem is not None else ""
                
                # 存储节目信息
                programme = {
                    "start": start_time,
                    "stop": stop_time,
                    "title": title,
                    "description": description,
                    "category": category
                }
                
                if channel_id in self.epg_data:
                    self.epg_data[channel_id]["programmes"].append(programme)
                else:
                    # 创建新的频道条目
                    self.epg_data[channel_id] = {
                        "name": "",
                        "icon": "",
                        "programmes": [programme]
                    }
            
            logger.info(f"成功解析来自 {source} 的EPG数据，包含 {len(self.epg_data)} 个频道")
        except ET.ParseError as e:
            logger.error(f"解析XML格式错误: {e}")
        except Exception as e:
            logger.error(f"解析EPG数据时发生未知错误: {e}")
    
    def get_channel_epg_info(self, channel_identifier: str) -> Optional[Dict[str, Any]]:
        """根据频道标识符获取EPG信息"""
        # 先尝试直接匹配频道标识符
        if channel_identifier in self.epg_data:
            return self.epg_data[channel_identifier]
        
        # 尝试使用规范化的频道名称匹配
        normalized_identifier = normalize_channel_name(channel_identifier)
        for channel_id, info in self.epg_data.items():
            if normalize_channel_name(info["name"]) == normalized_identifier:
                return info
        
        return None
    
    def get_channel_logo(self, channel_identifier: str) -> str:
        """获取频道的台标URL
        
        参数:
            channel_identifier: 频道标识符，可以是原始名称、规范化名称、epgid或tvid
            
        返回:
            str: 台标URL字符串，如果找不到则返回空字符串
            
        匹配逻辑:
            1. 尝试使用规范化后的频道名称从epg_data.json中匹配
            2. 尝试使用原始频道名称从epg_data.json中匹配
            3. 如果在epg_data.json中找不到，再尝试从已加载的EPG数据中获取
        """
        # 先尝试从epg_data.json中获取
        normalized_identifier = normalize_channel_name(channel_identifier)
        if normalized_identifier in self.channel_logos:
            return self.channel_logos[normalized_identifier]
        if channel_identifier in self.channel_logos:
            return self.channel_logos[channel_identifier]
        
        # 再尝试从EPG数据中获取
        epg_info = self.get_channel_epg_info(channel_identifier)
        if epg_info and epg_info.get("icon"):
            return epg_info["icon"]
        
        return ""
    
    def get_all_channels(self) -> Dict[str, Any]:
        """获取所有EPG频道信息"""
        return self.epg_data

# 创建全局EPGHandler实例
epg_handler = EPGHandler()
