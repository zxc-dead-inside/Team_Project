import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import redis
from core.logging import get_logger
from core.settings import settings
from models.url import URL, URLClick
from schemas.url import URLCreateRequest, URLResponse, URLStats
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from utils.short_code import ShortCodeGenerator, is_valid_url


logger = get_logger(__name__)


class URLService:
    def __init__(
        self,
        session_factory: sessionmaker,
        redis_client: redis.Redis | None,
        short_code_generator: ShortCodeGenerator,
    ):
        self.session_factory = session_factory
        self.redis_client = redis_client
        self.short_code_generator = short_code_generator

    @contextmanager
    def get_db_session(self):
        """Context manager for database session"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def create_short_url(self, request: URLCreateRequest) -> URLResponse:
        """Create a shortened URL"""
        logger.info("Creating short URL", original_url=str(request.url))

        # Validate URL
        if not is_valid_url(str(request.url)):
            logger.warning("Invalid URL provided", url=str(request.url))
            raise ValueError("Invalid URL")

        # Calculate expiration
        expires_at = None
        if request.expires_in_hours:
            expires_at = datetime.now(UTC) + timedelta(hours=request.expires_in_hours)

        # Generate short code
        with self.get_db_session() as db:
            for attempt in range(settings.max_generation_attempts):
                short_code = request.custom_code or self.short_code_generator.generate_random()

                # Create URL record
                url_record = URL(
                    short_code=short_code, original_url=str(request.url), expires_at=expires_at
                )

                try:
                    db.add(url_record)
                    db.flush()

                    logger.info("Short URL created", short_code=short_code, url_id=url_record.id)
                    break

                except IntegrityError:
                    db.rollback()
                    if request.custom_code:
                        logger.warning(
                            "Custom code already exists", custom_code=request.custom_code
                        )
                        raise ValueError("Custom code already exists")
                    if attempt == settings.max_generation_attempts - 1:
                        logger.error("Failed to generate unique code after max attempts")
                        raise RuntimeError("Failed to generate unique code")

            # Cache in Redis
            self._cache_url(short_code, str(request.url), expires_at)

            return URLResponse(
                short_code=short_code,
                short_url=f"{settings.base_url}/{short_code}",
                original_url=str(request.url),
                expires_at=expires_at,
                created_at=url_record.created_at,
            )

    async def get_original_url(self, short_code: str, client_info: dict[str, Any] = None) -> str:
        """Get original URL and log analytics"""
        logger.info("Resolving short code", short_code=short_code)

        # Try cache first
        cached_url = self._get_cached_url(short_code)
        if cached_url:
            logger.info("URL found in cache", short_code=short_code)
            return cached_url

        # Database lookup
        with self.get_db_session() as db:
            url_record = (
                db.query(URL).filter(URL.short_code == short_code, URL.is_active == True).first()
            )

            if not url_record:
                logger.warning("URL not found", short_code=short_code)
                raise ValueError("URL not found")

            # Check expiration
            if url_record.expires_at and datetime.now(UTC) > url_record.expires_at:
                logger.warning(
                    "URL expired", short_code=short_code, expires_at=url_record.expires_at
                )
                raise ValueError("URL expired")

            # Update click count
            url_record.click_count += 1

            # Log analytics
            if client_info:
                click_record = URLClick(
                    url_id=url_record.id,
                    ip_address=client_info.get("ip_address"),
                    user_agent=client_info.get("user_agent"),
                    referer=client_info.get("referer"),
                )
                db.add(click_record)

            # Update cache
            self._cache_url(short_code, url_record.original_url, url_record.expires_at)

            logger.info("URL resolved", short_code=short_code, clicks=url_record.click_count)
            return url_record.original_url

    async def get_url_stats(self, short_code: str) -> URLStats:
        """Get URL statistics"""
        with self.get_db_session() as db:
            url_record = db.query(URL).filter(URL.short_code == short_code).first()
            if not url_record:
                raise ValueError("URL not found")

            return URLStats(
                short_code=url_record.short_code,
                original_url=url_record.original_url,
                click_count=url_record.click_count,
                created_at=url_record.created_at,
                is_active=url_record.is_active,
                expires_at=url_record.expires_at,
            )

    async def deactivate_url(self, short_code: str) -> bool:
        """Deactivate a shortened URL"""
        logger.info("Deactivating URL", short_code=short_code)

        with self.get_db_session() as db:
            url_record = db.query(URL).filter(URL.short_code == short_code).first()
            if not url_record:
                return False

            url_record.is_active = False

            # Remove from cache
            self._remove_cached_url(short_code)

            logger.info("URL deactivated", short_code=short_code)
            return True

    def _cache_url(self, short_code: str, original_url: str, expires_at: datetime | None):
        """Cache URL in Redis (synchronous)"""
        if not self.redis_client:
            return

        try:
            cache_data = {
                "original_url": original_url,
                "expires_at": expires_at.isoformat() if expires_at else None,
            }
            self.redis_client.setex(
                f"url:{short_code}", settings.redis_cache_ttl, json.dumps(cache_data)
            )
        except Exception as e:
            logger.warning("Failed to cache URL", short_code=short_code, error=str(e))

    def _get_cached_url(self, short_code: str) -> str | None:
        """Get URL from Redis cache (synchronous)"""
        if not self.redis_client:
            return None

        try:
            cached_data = self.redis_client.get(f"url:{short_code}")
            if cached_data:
                data = json.loads(cached_data)

                # Check expiration
                if data.get("expires_at"):
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    if datetime.now(UTC) > expires_at:
                        self._remove_cached_url(short_code)
                        return None

                return data["original_url"]
        except Exception as e:
            logger.warning("Failed to get cached URL", short_code=short_code, error=str(e))

        return None

    def _remove_cached_url(self, short_code: str):
        """Remove URL from Redis cache (synchronous)"""
        if not self.redis_client:
            return

        try:
            self.redis_client.delete(f"url:{short_code}")
        except Exception as e:
            logger.warning("Failed to remove cached URL", short_code=short_code, error=str(e))
