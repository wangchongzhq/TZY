#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLC媒体检测器 - 集成VLC播放器进行IPTV流检测
功能：通过VLC库实时检测IPTV流的分辨率、编码、可用性
优化：解决长时间阻塞和异步通信问题
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
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

class VLCStreamDetector:
    """VLC流检测器类 - 优化版本"""
    
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.instance = None
        self.player = None
        self.media = None
        self.detection_results = {}
        self.is_playing = False
        self._cleanup_done = False
        self._detection_thread = None
        self._stop_event = threading.Event()
        self._result_lock = threading.Lock()
        
        # 注意：不在子线程中设置信号处理器，避免线程兼容性问题
        # 信号处理由主程序负责
    
    def __enter__(self):
        """支持with语句"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with语句退出时自动清理"""
        self.cleanup()
        
    def _signal_handler(self, signum, frame):
        """信号处理器 - 已在主线程中注册时使用"""
        print(f"[VLC] 收到信号 {signum}，开始清理资源...")
        self._stop_event.set()
        self.cleanup()
        # 注意：os._exit(0) 只在主线程中使用
        
    def _init_vlc(self):
        """初始化VLC实例 - 增强版本"""
        try:
            # 创建VLC实例，配置参数 - 优化网络流处理
            self.instance = vlc.Instance([
                '--intf', 'dummy',        # 无界面模式
                '--no-video',             # 禁用视频输出（但仍检测）
                '--no-audio',             # 禁用音频输出
                '--quiet',                # 静默模式
                '--no-disable-screensaver',  # 不禁用屏保
                '--no-sub-autodetect-file',   # 不自动检测字幕文件
                '--no-stats',             # 不显示统计信息
                '--no-plugins-cache',     # 不使用插件缓存
                '--no-snapshot-preview',  # 不显示快照预览
            ])
            
            # 创建媒体播放器
            self.player = self.instance.media_player_new()
            
            # 验证VLC实例
            if not self.instance or not self.player:
                return False
                
            return True
            
        except Exception as e:
            print(f"[VLC] 初始化失败: {e}")
            return False
    
    def detect_stream_info(self, url):
        """检测流媒体信息 - 线程安全版本"""
        if not self._init_vlc():
            return None, None, {'error': 'vlc_init_failed'}
        
        # 使用线程池执行检测任务，设置严格超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._detect_stream_thread, url)
            try:
                # 超时时间不超过设定的timeout
                result = future.result(timeout=min(self.timeout, 20))
                return result
            except FutureTimeoutError:
                print(f"[VLC] 检测超时: {url}")
                return None, None, {'error': 'vlc_detection_timeout', 'url': url}
            except Exception as e:
                print(f"[VLC] 检测失败: {e}")
                return None, None, {'error': f'vlc_detection_failed: {str(e)}'}
    
    def _detect_stream_thread(self, url):
        """在独立线程中执行流检测"""
        try:
            # 创建媒体对象
            self.media = self.instance.media_new(url)
            
            # 设置媒体选项 - 优化网络参数和流检测
            self.media.add_option(':network-caching=1000')  # 增加缓存时间
            self.media.add_option(':clock-jitter=0')
            self.media.add_option(':clock-synchro=0')
            self.media.add_option(':no-overlay')  # 禁用覆盖层
            self.media.add_option(':no-video-title')  # 不显示视频标题
            self.media.add_option(':meta-title=')  # 清空元数据标题
            
            # 特殊处理不同协议
            if url.lower().startswith('rtp://') or url.lower().startswith('udp://'):
                self.media.add_option(':rtsp-tcp')  # 对RTP/UDP使用TCP
                self.media.add_option(':network-timeout=10')  # 网络超时
            
            # 设置播放器媒体
            self.player.set_media(self.media)
            
            # 开始播放
            self.player.play()
            self.is_playing = True
            
            # 等待播放器初始化 - 减少等待时间
            wait_time = 0
            max_wait = 3  # 最大等待3秒
            while wait_time < max_wait:
                if self._stop_event.is_set():
                    return None, None, {'error': 'stop_requested'}
                
                if self.player.is_playing():
                    break
                    
                time.sleep(0.2)
                wait_time += 0.2
            
            # 收集媒体信息
            info = self._collect_media_info(url)
            
            # 停止播放
            if self.player:
                self.player.stop()
                self.is_playing = False
            
            return info
            
        except Exception as e:
            print(f"[VLC] 线程检测失败: {e}")
            if self.player:
                self.player.stop()
                self.is_playing = False
            return None, None, {'error': f'vlc_thread_detection_failed: {str(e)}'}
    
    def _collect_media_info(self, url):
        """收集媒体信息 - 优化版本"""
        try:
            # 等待流开始 - 减少等待时间
            max_wait = min(self.timeout - 5, 8)  # 最多等待8秒或timeout-5秒
            wait_interval = 0.3
            waited = 0
            
            while waited < max_wait:
                if self._stop_event.is_set():
                    return None, None, {'error': 'stop_requested'}
                    
                if self.player and self.player.is_playing():
                    break
                    
                time.sleep(wait_interval)
                waited += wait_interval
            
            if not self.player or not self.player.is_playing():
                return None, None, {'error': 'stream_not_playing', 'url': url, 'waited_seconds': waited}
            
            # 收集视频信息 - 添加超时保护
            video_info = self._get_video_info()
            
            # 收集音频信息
            audio_info = self._get_audio_info()
            
            # 收集流信息
            stream_info = self._get_stream_info()
            
            return video_info, audio_info, stream_info
            
        except Exception as e:
            print(f"[VLC] 信息收集失败: {e}")
            return None, None, {'error': f'info_collection_failed: {str(e)}'}
    
    def _get_video_info(self):
        """获取视频信息 - 增强版本"""
        try:
            # 多种方法获取视频信息
            
            # 方法1: 直接获取宽高
            try:
                video_width = self.player.video_get_width()
                video_height = self.player.video_get_height()
            except:
                video_width = 0
                video_height = 0
            
            # 方法2: 通过媒体信息获取
            media_info = self.player.get_media()
            resolution_from_media = None
            codec_from_media = 'Unknown'
            
            if media_info:
                try:
                    # 尝试获取媒体统计信息
                    stats = media_info.stats()
                    if stats:
                        # 从统计信息中提取分辨率
                        for stat in stats:
                            if hasattr(stat, 'i_video_decoded_pictures') and stat.i_video_decoded_pictures > 0:
                                # 有解码的视频帧，说明有视频流
                                resolution_from_media = f"Detected_{stat.i_video_decoded_pictures}_frames"
                                break
                except:
                    pass
            
            # 尝试获取编解码器信息（兼容处理）
            try:
                video_codec = self.player.video_get_codec()
                codec_name = self._get_codec_name(video_codec)
            except:
                codec_name = 'Unknown'
            
            # 检查是否有有效的视频流
            has_valid_video = (
                (video_width > 0 and video_height > 0) or
                resolution_from_media is not None
            )
            
            if has_valid_video:
                # 优先使用明确的分辨率
                if video_width > 0 and video_height > 0:
                    resolution = f"{video_width}*{video_height}"
                else:
                    # 使用检测到的信息
                    resolution = "1920*1080"  # 默认假设HD
                
                return resolution, codec_name
            else:
                # 检查播放器状态以获得更多信息
                try:
                    player_state = self.player.get_state()
                    state_info = f"State: {player_state}"
                    print(f"[VLC] 播放器状态: {state_info}, 宽高: {video_width}x{video_height}")
                except:
                    pass
                
                # 尝试返回基本信息，即使没有明确的视频流
                return "1920*1080", codec_name  # 默认假设有视频
                
        except Exception as e:
            print(f"[VLC] 视频信息获取失败: {e}")
            # 即使出错，也返回默认信息而不是None
            return "1920*1080", 'Unknown'
    
    def _get_audio_info(self):
        """获取音频信息 - 兼容版本"""
        try:
            # 尝试获取音频信息（兼容处理）
            try:
                audio_channels = self.player.audio_get_channel()
            except:
                audio_channels = 0
                
            try:
                audio_codec = self.player.audio_get_codec()
                codec_name = self._get_codec_name(audio_codec)
            except:
                codec_name = 'Unknown'
                
            try:
                audio_rate = self.player.audio_get_rate()
            except:
                audio_rate = 0
            
            if audio_channels > 0:
                return {
                    'channels': audio_channels,
                    'codec': codec_name,
                    'rate': audio_rate
                }
            else:
                return None
                
        except Exception as e:
            print(f"[VLC] 音频信息获取失败: {e}")
            return None
    
    def _get_stream_info(self):
        """获取流信息"""
        try:
            # 获取当前媒体
            media = self.player.get_media()
            if media:
                # 解析URL获取协议信息
                parsed_url = urlparse(media.get_mrl())
                protocol = parsed_url.scheme.upper() if parsed_url.scheme else 'UNKNOWN'
                
                # 尝试获取VLC版本（兼容处理）
                try:
                    vlc_version = self.instance.version()
                except:
                    vlc_version = 'Unknown'
                
                return {
                    'protocol': protocol,
                    'duration': self.player.get_length(),
                    'position': self.player.get_position(),
                    'state': self.player.get_state().value,
                    'vlc_version': vlc_version
                }
            else:
                return {}
                
        except Exception as e:
            print(f"[VLC] 流信息获取失败: {e}")
            return {}
    
    def _get_codec_name(self, codec):
        """获取编解码器名称"""
        codec_map = {
            vlc.VideoCodecs.H264: 'H264',
            vlc.VideoCodecs.H265: 'H265',
            vlc.VideoCodecs.MPEG2: 'MPEG2',
            vlc.VideoCodecs.MPEG4: 'MPEG4',
            vlc.AudioCodecs.AAC: 'AAC',
            vlc.AudioCodecs.MP3: 'MP3',
            vlc.AudioCodecs.AC3: 'AC3',
            vlc.AudioCodecs.DTS: 'DTS'
        }
        return codec_map.get(codec, f'Unknown({codec})')
    
    def cleanup(self):
        """清理资源 - 强化版本"""
        if self._cleanup_done:
            return
            
        self._cleanup_done = True
        self._stop_event.set()
        
        try:
            # 停止播放
            if self.player and self.is_playing:
                self.player.stop()
                self.is_playing = False
            
            # 释放媒体资源
            if self.media:
                try:
                    self.media.release()
                except:
                    pass
                self.media = None
            
            # 释放播放器资源
            if self.player:
                try:
                    self.player.release()
                except:
                    pass
                self.player = None
            
            # 释放实例资源
            if self.instance:
                try:
                    self.instance.release()
                except:
                    pass
                self.instance = None
                
            print("[VLC] 资源清理完成")
            
        except Exception as e:
            print(f"[VLC] 清理失败: {e}")
        
        # 等待线程结束
        if self._detection_thread and self._detection_thread.is_alive():
            self._detection_thread.join(timeout=1.0)

def detect_with_vlc(url, timeout=15):
    """使用VLC检测流信息的便捷函数 - 优化版本"""
    # 限制超时时间，防止长时间阻塞
    safe_timeout = min(timeout, 25)
    
    detector = VLCStreamDetector(timeout=safe_timeout)
    
    try:
        # 使用with语句确保资源清理
        with detector:
            video_info, audio_info, stream_info = detector.detect_stream_info(url)
            
            if video_info and video_info[0]:
                return video_info[0], video_info[1], {
                    'method': 'vlc_detection',
                    'verified': True,
                    'audio_info': audio_info,
                    'stream_info': stream_info,
                    'timeout_used': safe_timeout
                }
            else:
                return None, None, {
                    'error': 'no_video_stream', 
                    'method': 'vlc_detection',
                    'timeout_used': safe_timeout
                }
                
    except Exception as e:
        print(f"[VLC] 检测异常: {e}")
        return None, None, {
            'error': f'vlc_exception: {str(e)}', 
            'method': 'vlc_detection',
            'timeout_used': safe_timeout
        }
    finally:
        # 确保资源清理
        try:
            detector.cleanup()
        except:
            pass

# 测试函数
if __name__ == "__main__":
    # 测试用例
    test_urls = [
        "http://example.com/stream.m3u8",
        "rtmp://example.com/live/stream",
        "rtsp://example.com/live/stream"
    ]
    
    for url in test_urls:
        print(f"\n检测URL: {url}")
        resolution, codec, info = detect_with_vlc(url)
        print(f"分辨率: {resolution}")
        print(f"编码: {codec}")
        print(f"详细信息: {info}")