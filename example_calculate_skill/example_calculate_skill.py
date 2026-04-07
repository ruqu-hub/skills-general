#!/usr/bin/env python3
import sys
import os

# --- 自动加载本地依赖 (libs/ 或 libs.bin) ---
import sys, os
_p = os.path.dirname(os.path.abspath(__file__))
for _d in ["libs", "libs.bin"]:
    if os.path.exists(os.path.join(_p, _d)): sys.path.insert(0, os.path.join(_p, _d))
# ---------------------------------------

import argparse
import json
import logging
from cloud_client import TaskClient, load_global_env, set_shared_api_token, get_base_url, ensure_api_token

# Skill 版本定义
SKILL_VERSION = "0.1.0"

# 加载全局环境变量
load_global_env()

# 设置日志文件路径
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "skill.log")

def main():
    parser = argparse.ArgumentParser(description="Call the example_calculate_skill via Cloud Backend.")
    parser.add_argument("operation", choices=["add", "subtract", "multiply", "divide", "set-token"], help="The operation to perform. Use 'set-token' to configure API_TOKEN.")
    parser.add_argument("x", type=str, help="The first number, or the API_TOKEN string if operation is 'set-token'.")
    parser.add_argument("y", type=float, nargs='?', default=0.0, help="The second number.")
    
    args = parser.parse_args()

    # 处理配置 Token 的特殊命令
    if args.operation == "set-token":
        set_shared_api_token(args.x)
        sys.exit(0)

    # 逻辑：默认云端地址，本地可通过 .env 修改
    base_url = get_base_url()
    
    # 获取并校验 API_TOKEN
    api_token = ensure_api_token()

    client = TaskClient(base_url=base_url, api_token=api_token, skill_version=SKILL_VERSION, log_file=log_file)

    logging.info(f"--- Starting Example Calculate Skill Operation: {args.operation} ---")

    try:
        x_val = float(args.x)
    except ValueError:
        logging.error("Error: 'x' must be a number for arithmetic operations.")
        sys.exit(1)

    parameters = {
        "operation": args.operation,
        "x": x_val,
        "y": args.y
    }

    try:
        # 使用封装好的 run_task 方法：创建并等待完成
        logging.info(f"Submitting task to {base_url}...")
        result = client.run_task(
            task_name="example_calculate", 
            app_name="example_calculate_skill",
            app_version=SKILL_VERSION,
            parameters=parameters, 
            poll_interval=2.0, 
            timeout=60.0
        )
        
        if result.get("code") != 1:
            logging.error(f"Error: {result.get('message')}")
            sys.exit(1)
            
        status_data = result.get("data", {})
        status = status_data.get("status")
        
        if status == "completed":
            logging.info("Task completed successfully!")
            logging.info(f"Result: {json.dumps(status_data.get('result', {}), indent=2)}")
        elif status == "failed":
            logging.error("Task failed!")
            logging.error(f"Error Message: {status_data.get('error_message')}")
            sys.exit(1)
        elif status == "timeout":
            logging.error("Task timed out on the server.")
            sys.exit(1)
            
    except Exception as e:
        logging.exception(f"Exception occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
