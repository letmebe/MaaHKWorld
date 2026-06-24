#!/usr/bin/env python3
"""
Agent 启动脚本
"""
import sys
# 导入并启动 Agent
from agent_server import start_agent_server

if __name__ == "__main__":
    # 从命令行参数获取 socket_id
    if len(sys.argv) > 1:
        socket_id = sys.argv[1]
    else:
        socket_id = "maa-hkworld-agent"
    
    start_agent_server(socket_id)
