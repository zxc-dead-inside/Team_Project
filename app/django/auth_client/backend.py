import logging

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from .client import AuthServiceClient
from .models import UserProfile


logger = logging.getLogger(__name__)


class AuthServiceBackend(BaseBackend):
    """Authentication backend that uses the Auth service."""

    def authenticate(self, request, username=None, password=None, token=None, **kwargs):
        """Authenticate a user via the Auth service."""
        client = AuthServiceClient()

        if token:
            is_valid, user_data = client.validate_token(token)
            if is_valid and user_data:
                return self._get_or_create_user(user_data)
            return None

        if username and password:
            auth_response = client.login(username, password)
            if auth_response:
                if request and hasattr(request, "session"):
                    request.session["access_token"] = auth_response.get("access_token")
                    request.session["refresh_token"] = auth_response.get(
                        "refresh_token"
                    )

                is_valid, user_data = client.validate_token(
                    auth_response.get("access_token")
                )

                if is_valid and user_data:
                    return self._get_or_create_user(user_data)

        return None

    def _get_or_create_user(self, user_data):
        """Get or create a Django user from Auth service user data."""
        try:
            id = user_data.get("id") or user_data.get("sub")
            username = user_data.get("username")
            email = user_data.get("email", "")
            roles = user_data.get("roles", [])
            is_superuser = user_data.get("is_superuser", False)

            # If user has admin role or is_superuser, they should be staff in Django
            is_staff = is_superuser or "admin" in roles

            try:
                profile = UserProfile.objects.get(id=id)
                user = profile.user
                user.username = username
                user.email = email
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()
                return user
            except UserProfile.DoesNotExist:
                pass

            try:
                user = User.objects.get(username=username)
                user.email = email
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()

                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.id = id
                profile.save()

                return user
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username, email=email, password=None
                )
                user.is_active = True
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()

                UserProfile.objects.create(user=user, id=id)

                return user

        except Exception as e:
            logger.error(f"Error creating/getting user: {e}", exc_info=True)
            return None

    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
