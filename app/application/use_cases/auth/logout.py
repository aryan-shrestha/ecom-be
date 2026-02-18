"""Logout use case - revokes current refresh token."""

from app.application.dto.auth_dto import LogoutRequest
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import TokenHasherPort
from app.domain.errors.domain_errors import RefreshTokenNotFoundError


class LogoutUseCase:
    """Use case for logging out (revoking current refresh token)."""

    def __init__(
        self,
        uow: UnitOfWork,
        token_hasher: TokenHasherPort,
        clock: ClockPort,
        audit_log: AuditLogPort,
    ) -> None:
        self.uow = uow
        self.token_hasher = token_hasher
        self.clock = clock
        self.audit_log = audit_log

    async def execute(self, request: LogoutRequest) -> None:
        """
        Logout user by revoking current refresh token.
        
        Raises:
            RefreshTokenNotFoundError: If token not found
        """
        # Hash provided token
        token_hash = self.token_hasher.hash_token(request.refresh_token)

        async with self.uow:
            # Get refresh token
            refresh_token = await self.uow.refresh_tokens.get_by_token_hash(token_hash)
            if not refresh_token:
                # Silently succeed if token not found (already logged out)
                return

            # Revoke token
            now = self.clock.now()
            await self.uow.refresh_tokens.revoke_by_token_hash(token_hash, now)
            await self.uow.commit()

            # Audit
            await self.audit_log.log_event(
                event_type="user.logout",
                user_id=refresh_token.user_id,
                details={"token_id": str(refresh_token.id)},
            )
