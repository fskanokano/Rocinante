from functools import wraps


def process_view_exempt(func):
    func.process_view_exempt = True

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        return res

    return wrapper
