# from functools import wraps
# from typing import List

# def requires_permissions(permissions: List[str]):
#     def decorator(func):
#         # Save permition in endpoint's attribute
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             return await func(*args, **kwargs)
#         wrapper.required_permissions = permissions
#         return wrapper
#     return decorator


# from fastapi.routing import APIRoute
# from typing import Callable, List

# def requires_permissions(permissions: List[str]):
#     # Кастомный класс маршрута с метаданными
#     class PermissionAPIRoute(APIRoute):
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, **kwargs)
#             self.permissions = permissions  # Сохраняем разрешения в маршруте

#     return PermissionAPIRoute

from fastapi.routing import APIRoute
from fastapi import Request

class PermissionAwareRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()
        
        async def wrapped_handler(request: Request):
            # Сохраняем required_permissions в request.state
            request.state.required_permissions = getattr(self.endpoint, "required_permissions", None)
            return await original_handler(request)
        
        return wrapped_handler


def requires_permissions(permissions: list[str]):
    def decorator(func):
        func.required_permissions = permissions
        return func
    return decorator