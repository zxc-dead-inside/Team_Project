"""Authentication and authorization models."""

from enum import Enum

from pydantic import BaseModel, Field


class RoleEnum(str, Enum):
    """Enum representing available user roles"""

    ADMIN = "admin"
    MODERATOR = "moderator"
    SUBSCRIBER = "subscriber"
    USER = "user"
    ANONYMOUS = "anonymous"


class RoleModel(BaseModel):
    """Model representing a user role"""

    name: str
    description: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "subscriber",
                    "description": "Paid subscriber with premium access",
                }
            ]
        }
    }


class UserData(BaseModel):
    """
    Model representing authenticated user data from JWT claims.

    Attributes:
        id: User identifier
        username: User's username
        email: User's email address
        is_superuser: Whether user has superuser privileges
        roles: List of user roles with their details
    """

    id: str
    username: str
    email: str
    is_superuser: bool
    roles: list[RoleModel] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "user123",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "is_superuser": False,
                    "roles": [{"name": "subscriber", "description": "Paid subscriber"}],
                }
            ]
        }
    }


class Roles:
    """Role definitions and hierarchy management"""

    # Use enum instead of string constants
    ADMIN = RoleEnum.ADMIN
    MODERATOR = RoleEnum.MODERATOR
    SUBSCRIBER = RoleEnum.SUBSCRIBER
    USER = RoleEnum.USER
    ANONYMOUS = RoleEnum.ANONYMOUS

    # Define roles hierarchy (higher roles inherit permissions of lower roles)
    HIERARCHY = {
        ADMIN: [MODERATOR, SUBSCRIBER, USER, ANONYMOUS],
        MODERATOR: [USER, ANONYMOUS],
        SUBSCRIBER: [USER, ANONYMOUS],
        USER: [ANONYMOUS],
        ANONYMOUS: [],
    }

    @classmethod
    def get_roles(cls) -> dict[str, RoleModel]:
        """Get all defined roles"""
        return {
            cls.ADMIN: RoleModel(
                name=cls.ADMIN, description="Administrator with full access"
            ),
            cls.MODERATOR: RoleModel(
                name=cls.MODERATOR, description="Content moderator"
            ),
            cls.SUBSCRIBER: RoleModel(
                name=cls.SUBSCRIBER, description="Paid subscriber"
            ),
            cls.USER: RoleModel(name=cls.USER, description="Regular user"),
            cls.ANONYMOUS: RoleModel(
                name=cls.ANONYMOUS,
                description="Role for unauthenticated users with limited access",
            ),
        }

    @classmethod
    def has_role(cls, user_roles: list[str], required_role: str) -> bool:
        """
        Check if user has the required role or a higher role

        Args:
            user_roles: List of role names the user has
            required_role: Role name that is required

        Returns:
            True if user has the required role or a higher role
        """
        if not user_roles:
            return required_role == cls.ANONYMOUS

        # Direct match
        if required_role in user_roles:
            return True

        # Check if user has a higher role that includes the required role
        for user_role in user_roles:
            if user_role in cls.HIERARCHY and required_role in cls.HIERARCHY[user_role]:
                return True

        return False

    @classmethod
    def get_effective_roles(cls, user_roles: list[str]) -> set[str]:
        """
        Get all effective roles for a user based on the hierarchy

        Args:
            user_roles: List of role names the user has

        Returns:
            Set of all effective role names
        """
        effective_roles = set(user_roles)

        for role in user_roles:
            if role in cls.HIERARCHY:
                effective_roles.update(cls.HIERARCHY[role])

        return effective_roles