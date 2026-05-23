"""
统一日志模块 - 按日期轮转，自动清理旧日志
"""
import threading
import queue
import time
from datetime import datetime, timedelta
from pathlib import Path

LOG_QUEUE: queue.Queue = queue.Queue()
LOG_DIR = Path(__file__).parent / 'logs'
_log_thread = None
_log_running = False
_current_date = None
_log_file_handle = None
RETENTION_DAYS = 1  # 保留最近1天的日志

def _get_log_file_path(date: datetime) -> Path:
    """获取指定日期的日志文件路径"""
    return LOG_DIR / f"agent-{date.strftime('%Y%m%d')}.log"

def _cleanup_old_logs():
    """清理超过保留天数的旧日志"""
    try:
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        for log_file in LOG_DIR.glob("agent-*.log"):
            try:
                date_str = log_file.stem.replace("agent-", "")
                file_date = datetime.strptime(date_str, "%Y%m%d")
                if file_date < cutoff_date:
                    log_file.unlink()
            except (ValueError, OSError):
                continue
    except Exception:
        pass

def _log_writer():
    """后台线程：从队列取日志写入文件"""
    global _current_date, _log_file_handle
    
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 启动时清理旧日志
    _cleanup_old_logs()
    
    while _log_running:
        try:
            # 检查日期是否变更
            today = datetime.now().date()
            if _current_date != today:
                # 日期变更，关闭旧文件，打开新文件
                if _log_file_handle:
                    _log_file_handle.close()
                _current_date = today
                log_file = _get_log_file_path(datetime.now())
                _log_file_handle = open(log_file, 'a', encoding='utf-8', buffering=8192)
                # 清理旧日志
                _cleanup_old_logs()
            
            # 获取日志消息
            msg = LOG_QUEUE.get(timeout=0.1)
            if _log_file_handle:
                _log_file_handle.write(msg)
                _log_file_handle.flush()
                
        except queue.Empty:
            continue
        except Exception:
            continue
    
    # 线程退出时关闭文件
    if _log_file_handle:
        _log_file_handle.close()
        _log_file_handle = None

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
