"""Change password use case."""

from app.application.dto.auth_dto import ChangePasswordRequest
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import PasswordHasherPort
from app.domain.errors.domain_errors import InvalidCredentialsError, UserNotFoundError
from app.domain.services.password_policy import PasswordPolicy


class ChangePasswordUseCase:
    """Use case for changing user password."""

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasherPort,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.password_hasher = password_hasher
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: ChangePasswordRequest) -> None:
        """
        Change user password.
        
        Verifies old password, validates new password, and revokes all sessions.
        
        Raises:
            UserNotFoundError: If user not found
            InvalidCredentialsError: If old password is incorrect
            ValueError: If new password doesn't meet policy
        """
        # Validate new password
        PasswordPolicy.validate(request.new_password)

        async with self.uow:
            # Get user
            user = await self.uow.users.get_by_id(request.user_id)
            if not user:
                raise UserNotFoundError(f"User {request.user_id} not found")

            # Verify old password
            if not self.password_hasher.verify_password(
                request.old_password, user.password_hash
            ):
                raise InvalidCredentialsError("Current password is incorrect")

            # Hash new password
            new_password_hash = self.password_hasher.hash_password(request.new_password)

            # Update user with new password (increments token_version)
            now = self.clock.now()
            updated_user = user.with_new_password(new_password_hash, now)
            await self.uow.users.update(updated_user)

            # Revoke all refresh tokens
            await self.uow.refresh_tokens.revoke_all_for_user(user.id, now)

            await self.uow.commit()

            # Audit
            await self.audit_log.log_event(
                event_type="user.password_changed",
                user_id=user.id,
                details={
                    "new_token_version": updated_user.token_version,
                    "sessions_revoked": True,
                },
            )
