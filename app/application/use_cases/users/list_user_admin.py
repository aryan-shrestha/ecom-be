from typing import Optional
from uuid import UUID

from app.domain.entities.user import User
from app.application.interfaces.uow import UnitOfWork
from app.application.dto.user_dto import UserDTO, UserListResponse

class ListUsersAdminUseCase:
    """Use case for listing users with pagination - admin only."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, offset: int = 0, limit: int = 20) -> UserListResponse:
        """List users with pagination."""
        async with self.uow:
            users, total = await self.uow.users.list_paginated(offset=offset, limit=limit)

            user_dtos = [
                UserDTO(
                    id=u.id,
                    email=str(u.email),
                    first_name=u.first_name,
                    last_name=u.last_name,
                    is_active=u.is_active,
                    is_verified=u.is_verified,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                ) for u in users
            ]

            return UserListResponse(
                users=user_dtos,
                total=total,
                offset=offset,
                limit=limit,
            )