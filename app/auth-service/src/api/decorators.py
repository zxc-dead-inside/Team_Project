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
from functools import wraps
import logging
from fastapi.routing import APIRoute
from fastapi import Request
from src.core.logger import setup_logging

setup_logging()

# class PermissionAwareRoute(APIRoute):
#     def get_route_handler(self):
#         original_handler = super().get_route_handler()
        
#         async def wrapped_handler(request: Request):
#             # Сохраняем required_permissions в request.state
#             request.state.required_permissions = getattr(self.endpoint, "required_permissions", None)
#             return await original_handler(request)
        
#         return wrapped_handler

# class PermissionAwareRoute(APIRoute):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     logging.info(f"Route created for path: {self.path}")  # Проверка, что роут приме
    
    # def get_route_handler(self):
    #     original_handler = super().get_route_handler()
    #     endpoint = self.dependant.call  # Правильный способ получить эндпоинт
    #     logging.info(f"decorator endpoint: {endpoint}")

    #     async def wrapper(request: Request):
    #         # Сохраняем required_permissions из эндпоинта
    #         logging.info(f"endpoint: {dir(endpoint)}")
    #         request.state.required_permissions = getattr(endpoint, "required_permissions", [])
    #         logging.info(f"request.state.required_permissions: {request.state.required_permissions}")
    #         return await original_handler(request)
        
    #     return wrapper


# class PermissionAwareRoute(APIRoute):
#     def get_route_handler(self):
#         original_handler = super().get_route_handler()
#         endpoint = self.dependant.call  # Получаем эндпоинт
#         logging.info(f"decorator endpoint: {endpoint}")
#         logging.info(f"Wrapping handler for {self.path}")
        
#         async def wrapper(request: Request):
#             # Передаем required_permissions в request.state
#             logging.info(f"Executing wrapped handler for {self.path}")  # Логируем вызов
#             request.state.required_permissions = getattr(self.endpoint, "required_permissions", [])
#             logging.info(f"request.state.required_permissions: {request.state.required_permissions}")
#             return await original_handler(request)
        
#         return wrapper


class PermissionAwareRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()
        endpoint = self.dependant.call  # Получаем эндпоинт
        
        async def wrapper(request: Request):
            # Сохраняем required_permissions из декоратора в request.state
            request.state.required_permissions = getattr(endpoint, "required_permissions", [])
            return await original_handler(request)
        
        return wrapper


def requires_permissions(permissions: list[str]):
    def decorator(func):
        @wraps(func)  # Сохраняем метаданные исходной функции
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        wrapper.required_permissions = permissions  # Добавляем атрибут
        return wrapper
    return decorator