import asyncio
import functools
from collections import namedtuple
from concurrent.futures import ALL_COMPLETED
from concurrent.futures import FIRST_COMPLETED
from functools import _make_key  # type: ignore

from cachetools import LRUCache

from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


async def limit_gather(fs, n, task_timeout=0):
    """
    Gathers the tasks in fs, but only allows n at a time to be pending.
    If task_timeout is greater than 0, allows each task that long to complete
    before trying the next.

    Useful a large list of tasks need to be completed, but running too many may
    cause side effects (ie, sockets timing out).

    >>> from syncr_backend.util.async_util import limit_gather
    >>> import asyncio
    >>>
    >>> async def coro(n: int) -> None:
    ...     await asyncio.sleep(n)
    ...     print("done sleeping for %s seconds" % n)
    ...     return n
    >>>
    >>> loop = asyncio.get_event_loop()
    >>> coros = [coro(5), coro(3), coro(1), coro(2), coro(4)]
    >>> results = loop.run_until_complete(limit_gather(coros, 3))
    done sleeping for 1 seconds
    done sleeping for 3 seconds
    done sleeping for 2 seconds
    done sleeping for 5 seconds
    done sleeping for 4 seconds
    >>> print(results)
    [5, 3, 1, 2, 4]


    :param fs: A list of awaitable objects to run
    :param n: The maximum number to allow to be pending at a time
    :param task_timeout: Give each task this long before trying the next
    :return: A list of what is returned by the tasks in fs
    """
    tasks = []

    for f in fs:
        tasks.append(asyncio.ensure_future(f))

        done, pending = await asyncio.wait(
            tasks, timeout=task_timeout, return_when=ALL_COMPLETED,
        )
        while len(pending) >= n:
            done, pending = await asyncio.wait(
                pending, return_when=FIRST_COMPLETED,
            )

    while pending:
        done, pending = await asyncio.wait(tasks, return_when=ALL_COMPLETED)

    return [t.result() for t in tasks]


async def process_queue_with_limit(queue, n, done_queue, task_timeout=0):
    """
    Processses up to n tasks from queue at a time, putting the results in
    done_queue.

    Otherwise similar to limit_gather.

    This function does not return, and should be cancled when queue.join()
    returns, everything from done_queue has been processed, and there is
    nothing left to add.

    >>> from syncr_backend.util.async_util import process_queue_with_limit
    >>> import asyncio
    >>>
    >>> async def coro(n: int) -> None:
    ...     await asyncio.sleep(n)
    ...     return n*n
    >>>
    >>> in_queue = asyncio.Queue()
    >>> out_queue = asyncio.Queue()
    >>>
    >>> loop = asyncio.get_event_loop()
    >>> processor = asyncio.ensure_future(
    ...     process_queue_with_limit(in_queue, 3, out_queue),
    ... )
    >>>
    >>> for n in [1, 2, 3, 4]:
    ...     loop.run_until_complete(in_queue.put(coro(n)))
    >>>
    >>> loop.run_until_complete(in_queue.join())
    >>> r = []
    >>> while not out_queue.empty():
    ...     result = loop.run_until_complete(out_queue.get())
    ...     r.append(result)
    >>>
    >>> r
    [1, 4, 9, 16]
    >>> processor.cancel()
    True

    :param queue: The queue of input tasks
    :param n: The max number of pending tasks at a time
    :param done_queue: Queue to add results to
    :param task_timeout: Allow tasks to take up to this long before running \
    another
    """
    tasks = []
    try:
        while True:
            task = asyncio.ensure_future(await queue.get())
            task.add_done_callback(
                lambda future: done_queue.put_nowait(future.result()),
            )
            task.add_done_callback(
                lambda _: queue.task_done(),
            )
            tasks.append(task)

            done, pending = await asyncio.wait(
                tasks, timeout=task_timeout, return_when=ALL_COMPLETED,
            )
            while len(pending) >= n:
                done, pending = await asyncio.wait(
                    pending, return_when=FIRST_COMPLETED,
                )
    except asyncio.CancelledError:
        return


#: Cache info for async_cache
CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])


def async_cache(maxsize=128, cache_obj=None, cache_none=False, **kwargs):
    """
    Make a decorator that caches async function calls

    :param maxsize: The maximum cache size
    :param cache_obj: Override the default LRU cache
    :param cache_none: Set to True to cache `None` results
    :return: A decorator for a function
    """

    def decorator(fn):
        if cache_obj is None:
            cache = LRUCache(maxsize=maxsize, **kwargs)
        else:
            cache = cache_obj(maxsize=maxsize, **kwargs)
        sentinel = object()
        hits = misses = 0

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            nonlocal hits, misses
            key = _make_key(args, kwargs, typed=False)
            result = cache.get(key, sentinel)
            if result is not sentinel:
                hits += 1
                return result
            result = await fn(*args, **kwargs)
            if cache_none or result is not None:
                cache[key] = result
            misses += 1
            return result

        def cache_info():
            return CacheInfo(hits, misses, maxsize, len(cache))

        def cache_clear():
            nonlocal hits, misses
            cache.clear()
            hits = misses = 0

        def _dump_cache():
            return cache

        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        wrapper._dump_cache = _dump_cache

        return wrapper

    return decorator
