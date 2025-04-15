import logging

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

from .client import AuthServiceClient


logger = logging.getLogger(__name__)

class JWTAuthMiddleware(MiddlewareMixin):
    """Middleware to authenticate users with JWT tokens."""
    
    def process_request(self, request):
        """Process request to authenticate using JWT."""
        for exempt_path in settings.AUTH_EXEMPT_PATHS:
            if request.path.startswith(exempt_path):
                return None
                
        if not hasattr(request, 'user'):
            request.user = AnonymousUser()
            
        if request.user.is_authenticated:
            return None
            
        token = self._get_token_from_request(request)
        if not token:
            return None
            
        user = authenticate(request=request, token=token)
        if user:
            login(request, user)
            
        return None
        
    def _get_token_from_request(self, request):
        """Extract token from request."""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
            
        if hasattr(request, 'session'):
            return request.session.get('access_token')
            
        return None
        
    def process_response(self, request, response):
        """Check if token needs refresh."""
        if not hasattr(request, 'session'):
            return response
            
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')
        
        if not access_token or not refresh_token:
            return response
            
        client = AuthServiceClient()
        try:
            is_valid, user_data = client.validate_token(access_token)
            if not is_valid:
                tokens = client.refresh_token(refresh_token)
                if tokens:
                    request.session['access_token'] = tokens.get('access_token')
                    request.session['refresh_token'] = tokens.get('refresh_token')
        except Exception as e:
            logger.warning(f"Failed to refresh token: {e}")
            
        return response
