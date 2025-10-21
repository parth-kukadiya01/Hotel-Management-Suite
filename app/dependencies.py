from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, require_role
from app.models import User, UserRole


async def get_manager_user(
    current_user: User = Depends(require_role(UserRole.MANAGER))
) -> User:
    return current_user


async def get_authenticated_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user