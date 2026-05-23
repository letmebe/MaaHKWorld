"""
统一日志模块
"""
import threading
import queue
from datetime import datetime
from pathlib import Path

LOG_QUEUE: queue.Queue = queue.Queue()
LOG_FILE = Path(__file__).parent / 'logs' / 'agent.log'
_log_thread = None
_log_running = False

def _log_writer():
    """后台线程：从队列取日志写入文件"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8', buffering=8192) as f:
        while _log_running:
            try:
                msg = LOG_QUEUE.get(timeout=0.1)
                f.write(msg)
                f.flush()
            except queue.Empty:
                continue

def start_log_thread():
    """启动日志线程"""
    global _log_thread, _log_running
    if _log_thread is None:
        _log_running = True
        _log_thread = threading.Thread(target=_log_writer, daemon=True)
        _log_thread.start()

def stop_log_thread():
    """停止日志线程"""
    global _log_running
    _log_running = False

def log(message: str):
    """统一日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_QUEUE.put(f"[{timestamp}] {message}\n")
