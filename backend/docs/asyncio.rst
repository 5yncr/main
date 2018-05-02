.. _asyncio:

asyncio description
===================

Conceptually, asyncio allows Python to run multiple functions at a time on a
single thread, using `cooperative
multitasking <https://en.wikipedia.org/wiki/Cooperative_multitasking>`_.
async functions are defined with ``async def``, and called with ``await
funcall()``.  When running ``await ...``, Python may switch to a different async
function which is currently running.  A single async function is called a
"coroutine", and it is run in the "event loop".

As a concrete example, look at ``listen_requests`` in ``network/listen_requests``.
Here, it defines a coroutine of a tcp server.  On each new request, it calls
``async_handle_request`` with a Reader and Writer.  Whenever that function (or
any function it calls) calls a function with the ``await`` keyword, the function
may block, and another incoming request may be handled.  For example, when
reading a chunk from disk, another request may come in and be quickly handled.


How does this work?  Any function defined with ``async def ...`` actually returns
a coroutine when called.  If called from another coroutine, this coroutine may
be scheduled (conceptually run) by calling it with the ``await`` keyword (ie,
``await function()``).  How about running a coroutine from a non-coroutine?  You
have a couple options.  Most popular is probably
``asyncio.get_event_loop().run_until_complete(coroutine)`` (where ``coroutine`` is
returned by calling an async function), which blocks until ``coroutine`` finishes
and returns its result.


There are also options for calling coroutines from other coroutines that don't
involve using ``await`` (and waiting for it to finish).
``asyncio.ensure_future(coroutine)`` schedules ``coroutine`` to be run, but returns
immediately.  It returns a ``task``, which can be later checked for completion.
There are several other functions that do similar things, which are described
in the `Python documentation
<https://docs.python.org/3.5/library/asyncio.html>`_.

async_util
----------
``async_util`` has a few functions for doing more complex things with coroutines
and tasks.

Fist is ``limit_gather``.  This takes a list of tasks and a number ``n`` and will
run up ``n`` of the tasks at a time.  If a task finishes within ``task_timeout``
seconds it just finishes, but if it takes longer ``limit_gather`` will schedule
another, unless ``n`` or more tasks are already pending (ie not done).  It will
return a list of the results of the tasks, probably in the order of the input
list.

``process_queue_with_limit`` is a more complicated version of ``limit_gather``.  It
takes an input and an output queue and a number ``n``.  It will process the tasks
from ``queue`` and put the results in ``done_queue``, with the same limit
constraint as ``limit_gather``.  This function will *not* return, and must be
canceled with ``.cancel()`` when the input and output queues have been processed.
(You can wait on the input queue with ``await queue.join()``, which will return
when all the items have been processed).

Finally, ``async_cache`` is a simple function cache, that will cache the last
``maxsize`` recently returned objects from calling the cached function.  It
defaults to an LRU cache, but may take different cache objects to instantiate.

How is this used?
-----------------
``limit_gather`` is used to download up to ``MAX_CONCURRENT_FILE_DOWNLOADS``
(currently 4) files at a time.

``process_queue_with_limit`` is used to download up to
``MAX_CONCURRENT_CHUNK_DOWNLOADS`` (currently 8) chunks at a time per file.

``async_cache`` is used as a cache on reading file and drop metadata (with an LRU
cache) and getting chunk lists from peers (with a TTL cache).
