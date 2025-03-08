"""Authentication service for user authentication and authorization."""

from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
import uuid
import jwt
from passlib.context import CryptContext

from src.db.repositories.user_repository import UserRepository
from src.db.models.user import User
from src.db.models.token_blacklist import TokenBlacklist


class AuthService:
    """Service for authentication operations."""
    
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def __init__(
        self,
        user_repository: UserRepository,
        secret_key: str,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        """Initialize the auth service."""
        self.user_repository = user_repository
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.uuid = uuid.uuid4()
    
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

    async def authenticate_user(self, user: User, password: str) -> User | None:
        """
        Authenticate a user with password.
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Optional[User]: User if authentication is successful, None otherwise
        """
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
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
    
    def create_access_token(self, user_id: int, token_version: datetime) -> str:
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
        
        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
    
    def create_refresh_token(self, user_id: int, token_version: datetime) -> str:
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
            "jti": str(self.uuid)
        }

        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
    
    async def update_token_blacklist(self, token_blacklist) -> None:
        payload = jwt.decode(
            token_blacklist, self.secret_key, algorithms=["HS256"])

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
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
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
        payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

        if await self.user_repository.get_token_from_blacklist(
            payload.get('jti')):
            raise HTTPException(status_code=401, detail="Token has expired")
        
        return None
