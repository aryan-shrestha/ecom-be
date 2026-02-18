"""Token refresh use case with rotation and reuse detection."""

import secrets
import uuid
from datetime import timedelta

from app.application.dto.auth_dto import RefreshRequest, RefreshResponse
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import TokenHasherPort
from app.application.ports.jwt_port import JwtPort
from app.domain.entities.refresh_token import RefreshToken
from app.domain.errors.domain_errors import (
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenReuseDetectedError,
    RefreshTokenRevokedError,
    UserNotActiveError,
    UserNotFoundError,
)


class RefreshUseCase:
    """
    Use case for refreshing access tokens.
    
    Implements token rotation and reuse detection for security.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        token_hasher: TokenHasherPort,
        jwt_service: JwtPort,
        clock: ClockPort,
        audit_log: AuditLogPort,
        refresh_token_ttl_days: int = 14,
    ) -> None:
        self.uow = uow
        self.token_hasher = token_hasher
        self.jwt_service = jwt_service
        self.clock = clock
        self.audit_log = audit_log
        self.refresh_token_ttl_days = refresh_token_ttl_days

    async def execute(self, request: RefreshRequest) -> RefreshResponse:
        """
        Refresh access token using refresh token.
        
        Implements rotation: old token is marked as replaced, new token issued.
        Detects reuse: if old token already replaced, revokes entire family.
        
        Raises:
            RefreshTokenNotFoundError: If token not found
            RefreshTokenExpiredError: If token expired
            RefreshTokenRevokedError: If token revoked
            RefreshTokenReuseDetectedError: If token reuse detected
        """
        # Hash provided token
        token_hash = self.token_hasher.hash_token(request.refresh_token)

        async with self.uow:
            # Get refresh token
            old_token = await self.uow.refresh_tokens.get_by_token_hash(token_hash)
            if not old_token:
                raise RefreshTokenNotFoundError("Refresh token not found")

            now = self.clock.now()

            # Check if token is expired
            if old_token.is_expired(now):
                raise RefreshTokenExpiredError("Refresh token has expired")

            # Check if token is revoked
            if old_token.is_revoked():
                raise RefreshTokenRevokedError("Refresh token has been revoked")

            # REUSE DETECTION: Check if token has been replaced
            if old_token.is_replaced():
                # TOKEN REUSE DETECTED! This is a security threat
                # Revoke entire token family and bump user token version
                await self.uow.refresh_tokens.revoke_family(old_token.family_id, now)

                # Get user and increment token version
                user = await self.uow.users.get_by_id(old_token.user_id)
                if user:
                    updated_user = user.with_token_version_incremented(now)
                    await self.uow.users.update(updated_user)

                await self.uow.commit()

                # Audit
                await self.audit_log.log_event(
                    event_type="security.token_reuse_detected",
                    user_id=old_token.user_id,
                    details={
                        "family_id": str(old_token.family_id),
                        "action": "revoked_family_and_bumped_token_version",
                    },
                    ip=request.ip,
                )

                raise RefreshTokenReuseDetectedError(
                    "Token reuse detected. All sessions revoked."
                )

            # Get user
            user = await self.uow.users.get_by_id(old_token.user_id)
            if not user:
                raise UserNotFoundError("User not found")

            if not user.is_active:
                raise UserNotActiveError("User account is not active")

            # Get user roles
            roles = await self.uow.auth.get_user_roles(user.id)

            # Issue new access token
            access_token = self.jwt_service.issue_access_token(
                user_id=user.id, roles=roles, token_version=user.token_version
            )

            # Generate new refresh token (rotation)
            new_refresh_token_raw = self.token_hasher.generate_token()
            new_refresh_token_hash = self.token_hasher.hash_token(new_refresh_token_raw)

            # Create new refresh token entity (same family)
            new_refresh_token_entity = RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=new_refresh_token_hash,
                family_id=old_token.family_id,  # Keep same family
                issued_at=now,
                expires_at=now + timedelta(days=self.refresh_token_ttl_days),
                revoked_at=None,
                replaced_by_token_id=None,
                ip=request.ip,
                user_agent=request.user_agent,
            )

            # Save new token
            await self.uow.refresh_tokens.save(new_refresh_token_entity)

            # Mark old token as replaced
            updated_old_token = old_token.mark_as_replaced(new_refresh_token_entity.id)
            await self.uow.refresh_tokens.update(updated_old_token)

            await self.uow.commit()

            # Generate new CSRF token
            csrf_token = secrets.token_urlsafe(32)

            # Audit
            await self.audit_log.log_event(
                event_type="user.token_refreshed",
                user_id=user.id,
                details={"family_id": str(old_token.family_id)},
                ip=request.ip,
            )

            return RefreshResponse(
                access_token=access_token,
                refresh_token=new_refresh_token_raw,
                csrf_token=csrf_token,
                token_type="Bearer",
            )
