"""
Worker Utilities for MVP-Fusion
Provides worker ID tracking and thread management
"""

import threading
from typing import Optional

# Thread-local storage for worker IDs
_thread_local = threading.local()

def set_worker_id(worker_id: str):
    """Set the worker ID for the current thread"""
    _thread_local.worker_id = worker_id

def get_worker_id() -> str:
    """
    Get the worker ID for the current thread
    Returns 'Main' for the main thread or 'Worker-X' for worker threads
    """
    if not hasattr(_thread_local, 'worker_id'):
        # If no worker ID set, determine based on thread
        thread = threading.current_thread()
        if thread.name == 'MainThread':
            return 'Main'
        elif thread.name.startswith('ThreadPoolExecutor'):
            # Extract worker number from ThreadPoolExecutor-0_1 format
            try:
                worker_num = thread.name.split('_')[-1]
                return f'Worker-{worker_num}'
            except:
                return f'Worker-{thread.ident % 100}'
        else:
            return f'Worker-{thread.ident % 100}'
    return _thread_local.worker_id

def get_worker_prefix() -> str:
    """Get a formatted worker prefix for logging"""
    worker_id = get_worker_id()
    return f"[{worker_id}]"

def format_with_worker(message: str) -> str:
    """Format a message with the worker prefix"""
    return f"{get_worker_prefix()} {message}"