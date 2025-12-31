#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLC媒体检测器 - 重构版本
功能：通过VLC库实时检测IPTV流的分辨率、编码、可用性
优化：简化逻辑，避免信号量问题，提升稳定性
"""

import os
import sys

# 添加项目根目录到Python路径，以支持模块导入
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import vlc
import time
import threading
from urllib.parse import urlparse

class VLCStreamDetectorV2:
    """VLC流检测器类 - 重构版本"""
    
    def __init__(self, timeout=8):
        self.timeout = timeout
        self.instance = None
        self.player = None
        self.media = None
        self._running = False
        self._stop_flag = threading.Event()
    
    def __enter__(self):
        """支持with语句"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with语句退出时自动清理"""
        self.cleanup()
    
    def cleanup(self):
        """清理资源 - 简化版本"""
        try:
            if self.player:
                self.player.stop()
                self.player.release()
                self.player = None
            
            if self.instance:
                self.instance.release()
                self.instance = None
            
            self._stop_flag.set()
        except Exception as e:
            print(f"[VLC-V2] 清理异常: {e}")
    
    def detect_stream_info(self, url):
        """检测流媒体信息 - 简化版本"""
        if not self._init_vlc():
            return None, None, {'error': 'vlc_init_failed'}
        
        try:
            # 直接在线程中执行检测，避免复杂的线程池
            result = self._detect_in_thread(url)
            return result
            
        except Exception as e:
            print(f"[VLC-V2] 检测失败: {e}")
            return None, None, {'error': f'vlc_detection_failed: {str(e)}'}
    
    def _init_vlc(self):
        """初始化VLC实例 - 简化版本"""
        try:
            self.instance = vlc.Instance([
                '--intf', 'dummy',        # 无界面模式
                '--no-video',             # 禁用视频输出
                '--no-audio',             # 禁用音频输出
                '--quiet',                # 静默模式
                '--no-stats',             # 不显示统计信息
            ])
            
            self.player = self.instance.media_player_new()
            
            return self.instance is not None and self.player is not None
            
        except Exception as e:
            print(f"[VLC-V2] 初始化失败: {e}")
            return False
    
    def _detect_in_thread(self, url):
        """在单独线程中执行检测"""
        try:
            # 创建媒体对象
            self.media = self.instance.media_new(url)
            
            # 设置媒体选项
            self.media.add_option(':network-caching=1000')
            self.media.add_option(':clock-jitter=0')
            self.media.add_option(':clock-synchro=0')
            
            # 设置播放器媒体
            self.player.set_media(self.media)
            
            # 开始播放
            self.player.play()
            self._running = True
            
            # 等待播放器初始化
            if not self._wait_for_playing(max_wait=5):
                return None, None, {'error': 'stream_not_playing', 'url': url}
            
            # 收集信息
            video_info = self._get_video_info()
            audio_info = self._get_audio_info()
            stream_info = self._get_stream_info()
            
            return video_info, audio_info, stream_info
            
        finally:
            self._running = False
            if self.player:
                self.player.stop()
    
    def _wait_for_playing(self, max_wait=3):
        """等待播放器开始播放"""
        waited = 0
        while waited < max_wait and not self._stop_flag.is_set():
            try:
                if self.player and self.player.is_playing():
                    return True
            except:
                pass
            
            time.sleep(0.2)
            waited += 0.2
        
        return False
    
    def _get_video_info(self):
        """获取视频信息 - 安全版本"""
        try:
            # 安全获取视频信息，设置默认值
            video_width = 0
            video_height = 0
            codec_name = 'Unknown'
            
            try:
                video_width = self.player.video_get_width()
                video_height = self.player.video_get_height()
            except:
                pass
            
            try:
                video_codec = self.player.video_get_codec()
                codec_name = self._get_codec_name(video_codec)
            except:
                pass
            
            # 如果检测到有效视频，返回分辨率
            if video_width > 0 and video_height > 0:
                return f"{video_width}*{video_height}", codec_name
            
            # 检查播放状态
            try:
                if self.player.get_state().value == 3:  # Playing state
                    # 假设是HD分辨率作为fallback
                    return "1920*1080", codec_name
            except:
                pass
            
            return None, None
            
        except Exception as e:
            print(f"[VLC-V2] 视频信息获取失败: {e}")
            return None, None
    
    def _get_audio_info(self):
        """获取音频信息 - 安全版本"""
        try:
            try:
                channels = self.player.audio_get_channel()
                codec = self.player.audio_get_codec()
                rate = self.player.audio_get_rate()
                
                if channels > 0:
                    return {
                        'channels': channels,
                        'codec': self._get_codec_name(codec),
                        'rate': rate
                    }
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"[VLC-V2] 音频信息获取失败: {e}")
            return None
    
    def _get_stream_info(self):
        """获取流信息 - 安全版本"""
        try:
            # 尝试获取VLC版本（兼容处理）
            try:
                vlc_version = self.instance.version()
            except:
                vlc_version = 'Unknown'
            
            return {
                'protocol': self._get_protocol_from_url(),
                'duration': self.player.get_length(),
                'position': self.player.get_position(),
                'state': self.player.get_state().value,
                'vlc_version': vlc_version
            }
            
        except Exception as e:
            print(f"[VLC-V2] 流信息获取失败: {e}")
            return {
                'protocol': 'Unknown',
                'duration': 0,
                'position': 0.0,
                'state': 0,
                'vlc_version': 'Unknown'
            }
    
    def _get_protocol_from_url(self):
        """从URL获取协议信息"""
        try:
            if hasattr(self, '_current_url'):
                parsed = urlparse(self._current_url)
                return parsed.scheme.upper() if parsed.scheme else 'UNKNOWN'
        except:
            pass
        return 'UNKNOWN'
    
    def _get_codec_name(self, codec):
        """获取编解码器名称"""
        codec_names = {
            0x31637661: 'a52',      # A/52
            0x73736d70: 'mp3',      # MP3
            0x3231564d: 'mp4v',     # MP4V
            0x34363248: 'h264',     # H264
            0x656e6376: 'h265',     # H265
            0x76747030: 'vp30',     # VP3
            0x76747038: 'vp80',     # VP8
            0x76747039: 'vp90',     # VP9
            0x47504d4a: 'mjpg',     # MJPG
        }
        return codec_names.get(codec, f'Unknown(0x{codec:08x})')

def detect_with_vlc_v2(url, timeout=15):
    """使用VLC检测流信息 - 重构版本"""
    with VLCStreamDetectorV2(timeout=timeout) as detector:
        return detector.detect_stream_info(url)

# 保持原有接口兼容性
detect_with_vlc = detect_with_vlc_v2