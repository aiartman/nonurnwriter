import time
from functools import wraps, partial

def retry(exception_to_check, tries=3, delay=1, backoff=2):
    def deco_retry(f):
        @wraps(f)
        def wrapper_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except exception_to_check as e:
                    mtries -= 1
                    if mtries == 0:
                        raise
                    time.sleep(mdelay)
                    mdelay *= backoff
            return f(*args, **kwargs)
        return wrapper_retry
    return deco_retry