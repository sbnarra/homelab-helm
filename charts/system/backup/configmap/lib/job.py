from concurrent.futures import as_completed

_executor = None
_futures = []

def init(executor):
    global _executor
    _executor = executor
import traceback
import sys
def queue(ctx, func, *args, **kwargs):
    frame = sys._getframe(1)
    caller_loc = f"{frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}()"
    
    def job():
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ctx.error(f"Job '{func.__name__}' failed ({caller_loc}): {e}", e)
            raise
    future = _executor.submit(job)
    _futures.append(future)
    return future

def wait(ctx):
    completed = 0
    errors = 0

    global _futures
    while _futures:
        batch = list(_futures)
        _futures = []
        for future in as_completed(batch):
            try:
                future.result()
                completed += 1
            except Exception:
                errors += 1
                pass

    msg = f"{completed}/{completed + errors} jobs completed"
    if errors: 
      ctx.error(msg)
      sys.exit(1)
    else: ctx.info(f"{msg} successfully")
    