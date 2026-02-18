"""Logout all sessions use case - revokes all refresh tokens for user."""

from uuid import UUID

from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.domain.errors.domain_errors import UserNotFoundError


class LogoutAllUseCase:
    """Use case for logging out all user sessions."""

    def __init__(
        self,
        uow: UnitOfWork,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, user_id: UUID) -> None:
        """
        Logout all sessions for user.
        
        Revokes all refresh tokens and increments token_version to invalidate
        all issued access tokens.
        
        Raises:
            UserNotFoundError: If user not found
        """
        async with self.uow:
            # Get user
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            now = self.clock.now()

            # Revoke all refresh tokens
            await self.uow.refresh_tokens.revoke_all_for_user(user_id, now)

            # Increment token version to invalidate all access tokens
            updated_user = user.with_token_version_incremented(now)
            await self.uow.users.update(updated_user)

            await self.uow.commit()

            # Audit
            await self.audit_log.log_event(
                event_type="user.logout_all",
                user_id=user_id,
                details={"new_token_version": updated_user.token_version},
            )
