from functools import wraps
from fastapi import Request
from src.core.container import Container


def public_endpoint(func):
    """Decorator to pass public endpoints"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print('!!!!!!')
        request = kwargs.get('request')
        print(kwargs, args)
        if request:
            middleware = args[0].app.middleware_stack[0]
            middleware.public_routes.add(request.url.path)
        return await func(*args, **kwargs)
    return wrapper