#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性使用的调试输出文件
用于临时记录调试信息，不会影响项目正常运行
"""

import time
import os

class DebugLogger:
    """简单的调试日志记录器"""
    
    def __init__(self, log_file="debug_output.log", enabled=True, level="DEBUG"):
        """
        初始化调试日志器
        
        Args:
            log_file: 日志文件路径
            enabled: 是否启用日志记录
            level: 日志级别，可选值：DEBUG, INFO, WARNING, ERROR
        """
        self.log_file = log_file
        self.enabled = enabled
        self.level = level.upper()
        
        # 日志级别优先级
        self._level_priority = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3
        }
        
        # 清空之前的日志文件
        if self.enabled and os.path.exists(self.log_file):
            os.remove(self.log_file)
        
        if self.enabled:
            self.info(f"调试日志已启动，日志文件：{self.log_file}")
    
    def _should_log(self, message_level):
        """检查是否应该记录该级别的日志"""
        message_priority = self._level_priority.get(message_level.upper(), 0)
        current_priority = self._level_priority.get(self.level, 0)
        return message_priority >= current_priority
    
    def _write_log(self, level, message):
        """写入日志到文件"""
        if not self.enabled or not self._should_log(level):
            return
            
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"调试日志写入失败: {e}")
    
    def debug(self, message):
        """记录DEBUG级别的日志"""
        self._write_log("DEBUG", message)
    
    def info(self, message):
        """记录INFO级别的日志"""
        self._write_log("INFO", message)
    
    def warning(self, message):
        """记录WARNING级别的日志"""
        self._write_log("WARNING", message)
    
    def error(self, message):
        """记录ERROR级别的日志"""
        self._write_log("ERROR", message)
    
    def log_variable(self, name, value):
        """记录变量值"""
        self.debug(f"变量 {name} = {value} (类型: {type(value).__name__})")
    
    def log_function_call(self, func_name, *args, **kwargs):
        """记录函数调用"""
        args_str = ", ".join(map(str, args))
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        params_str = ", ".join(filter(None, [args_str, kwargs_str]))
        self.debug(f"调用函数: {func_name}({params_str})")
    
    def get_log_content(self):
        """获取日志文件内容"""
        if not os.path.exists(self.log_file):
            return ""
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"读取调试日志失败: {e}")
            return ""
    
    def print_log(self):
        """打印日志文件内容到控制台"""
        content = self.get_log_content()
        if content:
            print("=== 调试日志内容 ===")
            print(content)
        else:
            print("调试日志文件为空或不存在")
    
    def cleanup(self):
        """清理日志文件"""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            print(f"调试日志文件 {self.log_file} 已删除")


# 使用示例
if __name__ == "__main__":
    # 创建调试日志器实例
    logger = DebugLogger(log_file="debug_output.log", enabled=True, level="DEBUG")
    
    # 记录不同级别的日志
    logger.debug("这是一个调试信息")
    logger.info("这是一个普通信息")
    logger.warning("这是一个警告信息")
    logger.error("这是一个错误信息")
    
    # 记录变量值
    test_var = "Hello, Debug!"
    test_num = 42
    logger.log_variable("test_var", test_var)
    logger.log_variable("test_num", test_num)
    
    # 记录函数调用
    logger.log_function_call("my_function", "param1", 123, option=True)
    
    # 打印日志内容
    logger.print_log()
    
    # 可以选择清理日志文件
    # logger.cleanup()