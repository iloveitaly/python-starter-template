"""
Let's make working with async utils fun
"""

import asyncio


async def merge_iterables(*iterables):
    """
    Iterates over a list of iterables in parallel, yielding results as they become available.
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
