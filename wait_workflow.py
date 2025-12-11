#!/usr/bin/env python3
"""
等待GitHub Actions工作流完成的脚本
"""
import subprocess
import time
import sys

def main():
    max_attempts = 10
    wait_time = 60  # 秒
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n第 {attempt} 次检查工作流状态...")
        
        # 运行check_workflow_status.py脚本
        result = subprocess.run([sys.executable, "check_workflow_status.py"])
        
        if result.returncode == 0:
            print("\n✅ 工作流执行成功！")
            sys.exit(0)
        else:
            print(f"❌ 工作流仍在运行或执行失败，{wait_time}秒后再次检查...")
            time.sleep(wait_time)
    
    print("\n❌ 超过最大检查次数，工作流可能执行失败。")
    sys.exit(1)

if __name__ == "__main__":
    main()