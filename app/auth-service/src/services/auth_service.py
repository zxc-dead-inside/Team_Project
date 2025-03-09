"""Authentication service for user authentication and authorization."""

from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
import jwt
from passlib.context import CryptContext
import uuid
from uuid import UUID

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
        secret_key: str,
        public_key: str,
        private_key: str,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        email_service: EmailService | None = None,
    ):
        """Initialize the auth service."""
        self.user_repository = user_repository
        self.secret_key = secret_key
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
            self, plain_password: str, password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain password
            hashed_password: Hashed password
            
        Returns:
            bool: True if the password is correct, False otherwise
        """
        return self.password_context.verify(plain_password, password)

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
            self, user_id: UUID, token_version: datetime) -> str:

        """
        Create an access token for a user.
        
        Args:
            user_id: User ID
            user_token_version: User token version
            
        Returns:
            str: JWT access token
        """
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.now(UTC) + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "token_version": str(token_version)
        }
        
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
        print(token)
        if not token:
            raise HTTPException(
                status_code=401, detail="Authentication required")
        try:
            payload = jwt.decode(token, self.public_key, algorithms=["RS256"])
            user_id = payload.get("sub")
            if payload.get('type') != type: raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        user: User = await self.user_repository.get_by_id(user_id)
        if payload.get('token_version') != str(user.token_version):
            raise HTTPException(status_code=401, detail="Invalid token")

        return user

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
