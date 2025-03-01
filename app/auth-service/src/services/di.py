from fastapi import Depends
from functools import lru_cache


from src.services.login import LoginService

from src.db.redis import get_redis_session
from src.db.database import get_db_session


@lru_cache()
def get_login_service(
        db_session = Depends(get_db_session),
        redis = Depends(get_redis_session)
) -> LoginService:
    return LoginService(db_session=db_session, redis=redis)
