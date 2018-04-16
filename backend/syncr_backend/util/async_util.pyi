from typing import Callable, Awaitable, Any, Generic, TypeVar, Dict, List, NamedTuple, Optional
from asyncio import Queue
from mypy_extensions import VarArg, KwArg
from collections import MutableMapping


_T = TypeVar("_T")

FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)

class CacheInfo(NamedTuple('CacheInfo', [
    ('hits', int),
    ('misses', int),
    ('maxsize', int),
    ('currsize', int)
])): ...

class _cache_wrapper(Generic[_T]):
    __wrapped__ = ...  # type: Callable[..., Awaitable[_T]]
    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[_T]: ...
    def cache_info(self) -> CacheInfo: ...
    def cache_clear(self) -> None: ...

class async_cache():
    def __init__(self, maxsize: int=..., cache_obj:Optional[Callable[..., MutableMapping]]=..., cache_none: bool=..., **kwargs: Any) -> None: ...
    def __call__(self, f: F) -> F: ...

async def limit_gather(fs: List[Awaitable[_T]], n: int, task_timeout: int=...) -> List[_T]: ...

async def process_queue_with_limit(queue: Queue[Awaitable[_T]], n: int, done_queue: Queue[_T], task_timeout: int=...) -> None: ...
