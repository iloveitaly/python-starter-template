import asyncio


async def merge_iterables(*iterables):
    """
    Iterates over a list of iterables in parallel, yielding results as they become available.
    This is helpful when running chunks of a capture in parallel and delivering documents to Estuary as soon as they
    are available.
    """

    pending = {asyncio.create_task(it.__aiter__().__anext__()): it for it in iterables}

    while pending:
        # FIRST_COMPLETED will also return a task if it raised an exception
        done, _ = await asyncio.wait(
            pending.keys(), return_when=asyncio.FIRST_COMPLETED
        )

        for task in done:
            it = pending.pop(task)
            try:
                # `result()` will raise an exception, cancel any future async consumption, *not* stop the async
                # processes immediately, but will return a non-zero exit code to estuary. Therefore when a async process
                # fails the log output does not immediately stop.
                result = task.result()

                yield result
                pending[asyncio.create_task(it.__anext__())] = it
            except StopAsyncIteration:
                pass


def hash_function_code(func):
    import hashlib
    import inspect

    source = inspect.getsource(func)
    return hashlib.sha256(source.encode()).hexdigest()
