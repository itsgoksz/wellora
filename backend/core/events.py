import asyncio
from typing import Callable, Dict, List, Any
import inspect

class EventBus:
    """
    Asynchronous Event Bus for Wellora's Cognitive Architecture.
    Allows agents to subscribe to topics and publish events asynchronously.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str):
        def decorator(func):
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(func)
            return func
        return decorator

    async def publish(self, topic: str, **kwargs):
        if topic not in self._subscribers:
            return
            
        tasks = []
        for callback in self._subscribers[topic]:
            if inspect.iscoroutinefunction(callback):
                tasks.append(asyncio.create_task(callback(**kwargs)))
            else:
                # Run sync functions in a threadpool to not block the async event loop
                tasks.append(asyncio.to_thread(callback, **kwargs))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global singleton event bus
bus = EventBus()
