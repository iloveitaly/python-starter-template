"""
This should go in server.py

it's to avoid this error. I am sure if this is going to work, needs more investigation, and probably better postgres timeouts

se exc.TimeoutError(\n    ...<4 lines>...\n    )\nsqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00 (
"""
# from anyio.to_thread import current_default_thread_limiter
# SHOW max_connections
# engine.pool.size() + engine.pool._max_overflow
# async def startup():
#     limiter = current_default_thread_limiter()
#     limiter.total_tokens = YOUR_POOL_SIZE  # e.g., 10
