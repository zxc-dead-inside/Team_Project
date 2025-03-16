import logging
from fastapi import Request, HTTPException
from functools import wraps

from src.core.logger import setup_logging


setup_logging()


def required(
        permissions: list = None,
        roles: list = None,
        anonymous_allowed: bool = False
    ):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                user = getattr(request.state, "user", None)
                if user:
                    # Проверяем наличие ролей
                    if roles:
                        if not any(
                            role in user.get("roles", []) for role in roles):
                            raise HTTPException(
                                status_code=403,
                                detail="Forbidden: Insufficient roles"
                            )

                    # Проверяем наличие разрешений
                    if permissions:
                        if not any(
                            permission in user.get("permissions", [])
                                for permission in permissions):
                            raise HTTPException(
                                status_code=403,
                                detail="Forbidden: Insufficient permissions"
                            )
                else:
                    if anonymous_allowed:
                        """
                        Если анонимный доступ разрешен и 
                        пользователь не аутентифицрован
                        """
                        request.state.user = 'anonym'
                    else:
                        raise HTTPException(
                            status_code=401,
                            detail="User identification is required"
                        )

            except HTTPException as exc:
                """
                Если пользователь аутентифицрован, но прав недостаточно
                """
                if anonymous_allowed:
                    request.state.user = 'anonym'
                else:
                    raise exc
            except Exception:
                logging.error(exc_info=True)
                raise HTTPException(status_code=500)

            # Если все проверки пройдены, вызываем исходную функцию
            return await func(request, *args, **kwargs)

        return wrapper
    return decorator
