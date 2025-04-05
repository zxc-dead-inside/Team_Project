"""Authentication and authorization dependencies."""

from typing import Annotated

from models.auth import RoleEnum, Roles, UserData

from fastapi import Depends, HTTPException, status

from .jwt_bearer import JWTBearer


# Always returns a user (either authenticated or anonymous)
jwt_auth = JWTBearer(require_auth=False)

# Type annotation for dependency injection
User = Annotated[UserData, Depends(jwt_auth)]


async def get_current_user(user_data: User) -> UserData:
    """
    Get current user data (either authenticated or anonymous).

    Args:
        user_data: JWT user data from token or anonymous user data

    Returns:
        UserData: Validated user model
    """
    return user_data


def has_role(required_role: RoleEnum | str):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Role name required to access the endpoint

    Returns:
        Dependency function that checks if user has the required role
    """

    async def role_dependency(user_data: User) -> UserData:
        if isinstance(required_role, RoleEnum):
            required_role_str = required_role.value
        else:
            required_role_str = required_role

        # If anonymous role is required, any user (including anonymous) can access
        if required_role_str == Roles.ANONYMOUS:
            return user_data

        # For other roles, check if the user is anonymous only
        user_role_names = [role.name for role in user_data.roles]

        # If user is anonymous only and we require a higher role, reject
        if (
            len(user_role_names) == 1
            and user_role_names[0] == Roles.ANONYMOUS
            and required_role_str != Roles.ANONYMOUS
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not Roles.has_role(user_role_names, required_role_str):
            effective_roles = Roles.get_effective_roles(user_role_names)
            available_roles = ", ".join(effective_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Access denied",
                    "required_role": required_role_str,
                    "user_roles": available_roles,
                    "message": f"Role '{required_role_str}' required. User has: {available_roles}",
                },
            )

        return user_data

    return role_dependency


# Shortcuts for common roles
admin_required = has_role(Roles.ADMIN)
moderator_required = has_role(Roles.MODERATOR)
subscriber_required = has_role(Roles.SUBSCRIBER)
user_required = has_role(Roles.USER)
anonymous_required = has_role(Roles.ANONYMOUS)
