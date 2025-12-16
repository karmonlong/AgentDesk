"""
速率限制器 - 防止触发 API 配额限制
"""
import time
from functools import wraps
from typing import Callable, Any
import asyncio

class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_calls: int = 360, period: float = 60.0):
        """
        Args:
            max_calls: 时间窗口内最大调用次数（默认360=Pro版配额）
            period: 时间窗口（秒，默认60秒=1分钟）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        
    def __call__(self, func: Callable) -> Callable:
        """装饰器"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            await self._wait_if_needed()
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            self._wait_if_needed_sync()
            return func(*args, **kwargs)
        
        # 判断是否是异步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def _wait_if_needed(self):
        """异步等待"""
        now = time.time()
        # 移除过期的调用记录
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
        
        if len(self.calls) >= self.max_calls:
            # 需要等待
            oldest_call = min(self.calls)
            wait_time = self.period - (now - oldest_call) + 0.1  # 多等0.1秒确保安全
            print(f"[RateLimiter] 达到速率限制，等待 {wait_time:.1f} 秒...")
            await asyncio.sleep(wait_time)
            now = time.time()
            self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
        
        self.calls.append(now)
    
    def _wait_if_needed_sync(self):
        """同步等待"""
        now = time.time()
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
        
        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            wait_time = self.period - (now - oldest_call) + 0.1
            print(f"[RateLimiter] 达到速率限制，等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
            now = time.time()
            self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
        
        self.calls.append(now)

# 全局速率限制器实例（Pro版配额：360 RPM）
gemini_limiter = RateLimiter(max_calls=350, period=60.0)  # 留10个buffer
