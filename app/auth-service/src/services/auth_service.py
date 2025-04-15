"""Authentication service for user authentication and authorization."""

import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext

from src.db.models.token_blacklist import TokenBlacklist
from src.db.models.user import User
from src.db.repositories.user_repository import UserRepository
from src.services.email_verification_service import EmailService


class AuthService:
    """Service for authentication operations."""
    
    password_context = CryptContext(
        schemes=["argon2", "bcrypt"], deprecated="auto")

    def __init__(
        self,
        user_repository: UserRepository,
        public_key: str,
        private_key: str,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        email_service: EmailService | None = None,
    ):
        """Initialize the auth service."""
        self.user_repository = user_repository
        self.public_key = public_key
        self.private_key = private_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.email_service = email_service
        

    async def identificate_user(self, username: str) -> User | None:
        """
        Identificate a user with username/email.
        
        Args:
            username: Username or email
            
        Returns:
            Optional[User]: User if identification is successful, None otherwise
        """
        user = await self.user_repository.get_by_username(username)

        if not user:
            # Try with email
            user = await self.user_repository.get_by_email(username)

        if not user:
            return None
        
        return user

    async def authenticate_user(
            self, user: User, password: str) -> User | None:
        """
        Authenticate a user with password.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Optional[User]: User if authentication is successful, None otherwise
        """
        if not self.verify_password(password, user.password):

            return None

        return user

    def verify_password(
              self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain password
            hashed_password: Hashed password

        Returns:
            bool: True if the password is correct, False otherwise
        """
        return self.password_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """
        Hash a password.

        Args:
            password: Plain password

        Returns:
            str: Hashed password
        """
        return self.password_context.hash(password)

    def create_access_token(
            self, to_encode: dict, token_version: datetime) -> str:

        """
        Create an access token for a user.

        Args:
            user_id: User ID
            token_version: User token version
            
        Returns:
            str: JWT access token
        """

        if not to_encode.get('exp', None):
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
            expire = datetime.now(UTC) + expires_delta
            to_encode["exp"] = expire

        to_encode["type"] = "access"
        to_encode["token_version"] = str(token_version)
        
        return jwt.encode(to_encode, self.private_key, algorithm="RS256")

    def create_refresh_token(
            self, user_id: UUID, token_version: datetime) -> str:
        """
        Create a refresh token for a user.

        Args:
            user_id: User ID
            user_token_version: User token version

        Returns:
            str: JWT refresh token
        """
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.now(UTC) + expires_delta
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "token_version": str(token_version),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(to_encode, self.private_key, algorithm="RS256")

    async def update_token_blacklist(self, token_blacklist) -> None:
        payload = jwt.decode(
            token_blacklist, self.public_key, algorithms=["RS256"])

        await self.user_repository.update_token_blacklist(
            TokenBlacklist(
                user_id = payload.get('sub'),
                expires_at = datetime.fromtimestamp(payload.get('exp')),
                jti = payload.get('jti')
            )
        )

        return None

    async def validate_token(self, token: str, type: str) -> User | None:

        """
        Validate a JWT token and return the associated user.

        Args:
            token: JWT token

        Returns:
            Optional[User]: User if the token is valid, None otherwise
        """

        if not token:
            raise HTTPException(
                status_code=401, detail="Authentication required")

        try:
            payload = await self.decode_token(token)
            user_id = payload.get("sub")
            if payload.get('type') != type: raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has been expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        user: User = await self.user_repository.get_by_id(user_id)
        if not user: raise HTTPException(
            status_code=401, detail="Invalid token")
        
        if payload.get('token_version') != str(user.token_version):
            raise HTTPException(status_code=401, detail="Invalid token")

        return user
    
    async def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.public_key, algorithms=["RS256"])

    async def check_refresh_token_blacklist(self, token: str) -> None:
        payload = jwt.decode(token, self.public_key, algorithms=["RS256"])
        if await self.user_repository.get_token_from_blacklist(
            payload.get('jti')):
            raise HTTPException(status_code=401, detail="Token has expired")
        
        return None

    async def register_user(
        self, username: str, email: str, password: str
    ) -> tuple[bool, str, User | None]:
        """
        Register a new user.

        Args:
            username: Username
            email: Email address
            password: Password

        Returns:
            tuple[bool, str, Optional[User]]: (success, message, user)
        """
        existing_user = await self.user_repository.get_by_username(username)
        if existing_user:
            return False, "Username already exists", None

        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            return False, "Email already exists", None

        hashed_password = self.hash_password(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            is_active=False,
        )

        created_user = await self.user_repository.create(user)

        return True, "User created successfully", created_user

    async def confirm_email(self, token: str) -> tuple[bool, str]:
        """
        Confirm a user's email address.

        Args:
            token: Email confirmation token

        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.email_service:
            return False, "Email service not configured"

        is_valid, payload = self.email_service.validate_confirmation_token(token)

        if not is_valid or not payload:
            return False, "Invalid or expired token"

        user_id = payload.get("sub")
        email = payload.get("email")

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return False, "User not found"

        if user.email != email:
            return False, "Email mismatch"

        if user.is_active:
            return True, "Email already confirmed"

        user.is_active = True
        await self.user_repository.update(user)

        return True, "Email confirmed successfully"

    async def refresh_tokens_for_user(self, user: User) -> dict:
        """
        Generate new access and refresh tokens for a user.
        Used when user roles or permissions change.

        Args:
            user: The user to generate tokens for

        Returns:
            dict: The new access and refresh tokens
        """
        access_token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "is_superuser": user.is_superuser,
            "roles": [role.name for role in user.roles],
            "permissions": list(
                set(
                    permission.name
                    for role in user.roles
                    for permission in role.permissions
                )
            ),
        }
        access_token = self.create_access_token(
            to_encode=access_token_data,
            token_version=user.token_version
        )
        refresh_token = self.create_refresh_token(
            user_id=user.id,
            token_version=user.token_version
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
        }

    async def get_or_create_oauth_user(
            self, provider: str, user_info: dict) -> User | None:
        """
        Auxiliary method to work with Yandex users.
        
        Args:
            user_info: dict of user info received from yandex
        
        Returns:
           Optional[User]
        """

        user = await self.user_repository.get_by_yandex_id(
            user_info["id"]
        )
        if user:
            return user

        if email := user_info.get("default_email"):
            user = await self.user_repository.get_by_email(email)
            if user:
                user.yandex_id = user_info["id"]
                await self.user_repository.update(user)
                return user

        username = self.generate_user_name("yandex", user_info["login"])
        while not username:
            username = self.generate_user_name("yandex", user_info["login"])

        user = User(
            username=username,
            password=self.hash_password(self.generate_password()),
            email=user_info.get("default_email"),
            yandex_id=user_info["id"],
            is_active=True,
            roles=[],
        )
        return await self.user_repository.create(user)

    
    async def check_unique_username(self, username) -> bool:
        """Retruns true if username is unique."""

        return (
            True if self.user_repository.get_by_username(username) is None
            else False
        )

    @staticmethod
    def generate_user_name(prefix: str, login: str, length: int = 4) -> str:
        """
        Auxiliary method to generate unique user name.
        """

        return f"{prefix}_{login}_{secrets.token_hex(length)}"
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """
        Auxiliary method to generate password.
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(length))
