import time
import uuid
from django.utils.deprecation import MiddlewareMixin

from example.logging_config import SecurityEventLogger, get_django_logger


logger = get_django_logger(__name__)
security_logger = SecurityEventLogger()


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log all HTTP requests and responses
    """

    def process_request(self, request):
        """Log incoming requests"""
        # Generate unique request ID for tracking
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()

        # Log the incoming request
        logger.info(
            "HTTP request started",
            request=request,
            request_id=request.request_id,
            method=request.method,
            path=request.path,
            query_params=dict(request.GET),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            content_type=request.META.get("CONTENT_TYPE", ""),
            content_length=request.META.get("CONTENT_LENGTH", 0),
        )

        # Log POST data (be careful with sensitive data)
        if request.method == "POST" and request.content_type == "application/json":
            try:
                # Only log if content is small to avoid performance issues
                if int(request.META.get("CONTENT_LENGTH", 0)) < 1024:
                    logger.debug(
                        "POST request body",
                        request=request,
                        request_id=request.request_id,
                        body_preview=request.body.decode("utf-8")[:500],
                    )
            except Exception:
                pass  # Don't fail the request if logging fails

    def process_response(self, request, response):
        """Log outgoing responses"""
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time

            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = "error"
            elif response.status_code >= 400:
                log_level = "warning"
            else:
                log_level = "info"

            # Log the response
            getattr(logger, log_level)(
                "HTTP request completed",
                request=request,
                request_id=getattr(request, "request_id", "unknown"),
                status_code=response.status_code,
                content_type=response.get("Content-Type", ""),
                duration=duration,
            )

            # Log performance metrics
            logger.performance(
                "HTTP request performance",
                duration=duration,
                request=request,
                status_code=response.status_code,
                path=request.path,
                method=request.method,
            )

            # Log slow requests
            if duration > 1.0:  # Requests taking more than 1 second
                logger.warning(
                    "Slow HTTP request detected",
                    request=request,
                    duration=duration,
                    path=request.path,
                    method=request.method,
                )

            # Log security events for suspicious patterns
            if response.status_code == 404 and hasattr(request, "request_id"):
                user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
                if any(bot in user_agent for bot in ("bot", "crawler", "spider")):
                    security_logger.log_suspicious_activity(
                        f"Bot accessing non-existent resource: {request.path}",
                        request=request,
                    )

        return response

    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time

            logger.error(
                "Unhandled exception in request",
                error=exception,
                request=request,
                request_id=getattr(request, "request_id", "unknown"),
                duration=duration,
                exception_type=type(exception).__name__,
            )

        return None  # Let Django handle the exception normally


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware specifically for security-related logging
    """

    def process_request(self, request):
        """Check for security-related patterns"""

        # Log authentication attempts
        if request.path.startswith("/admin/login/") or "login" in request.path:
            logger.security(
                "Authentication page accessed", request=request, path=request.path
            )

        # Log potential attack patterns
        suspicious_patterns = [
            "wp-admin",
            "wp-login",
            ".php",
            ".asp",
            ".jsp",
            "admin",
            "phpmyadmin",
            "xmlrpc.php",
        ]

        if any(pattern in request.path.lower() for pattern in suspicious_patterns):
            security_logger.log_suspicious_activity(
                f"Suspicious path accessed: {request.path}",
                request=request,
                pattern_matched=True,
            )

        # Log excessive requests from same IP
        client_ip = self.get_client_ip(request)
        if self.is_rate_limited(client_ip):
            security_logger.log_suspicious_activity(
                "Potential rate limit violation", request=request, client_ip=client_ip
            )

    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def is_rate_limited(self, ip):
        """Simple rate limiting check (implement with Redis/cache)"""
        return False


class PerformanceLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for detailed performance monitoring
    """

    def process_request(self, request):
        """Initialize performance tracking"""
        request.perf_start = time.time()
        request.db_queries = 0

    def process_response(self, request, response):
        """Log performance metrics"""
        if hasattr(request, "perf_start"):
            total_time = time.time() - request.perf_start

            logger.performance(
                "Request performance details",
                request=request,
                total_time=total_time,
                status_code=response.status_code,
                path=request.path,
                method=request.method,
                response_size=len(response.content)
                if hasattr(response, "content")
                else 0,
            )

            # Alert on performance issues
            if total_time > 2.0:
                logger.warning(
                    "Very slow request detected",
                    request=request,
                    duration=total_time,
                    path=request.path,
                )

        return response
