"""User login use case."""

import secrets
import uuid
from datetime import timedelta

from app.application.dto.auth_dto import LoginRequest, LoginResponse
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import PasswordHasherPort, TokenHasherPort
from app.application.ports.jwt_port import JwtPort
from app.domain.entities.refresh_token import RefreshToken
from app.domain.errors.domain_errors import (
    InvalidCredentialsError,
    UserNotActiveError,
    UserNotFoundError,
)
from app.domain.value_objects.email import Email


class LoginUseCase:
    """Use case for user login."""

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasherPort,
        token_hasher: TokenHasherPort,
        jwt_service: JwtPort,
        clock: ClockPort,
        audit_log: AuditLogPort,
        refresh_token_ttl_days: int = 14,
    ) -> None:
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_hasher = token_hasher
        self.jwt_service = jwt_service
        self.clock = clock
        self.audit_log = audit_log
        self.refresh_token_ttl_days = refresh_token_ttl_days

    async def execute(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate user and issue tokens.
        
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserNotActiveError: If user account is not active
        """
        email = Email(request.email).normalize()

        async with self.uow:
            # Get user
            user = await self.uow.users.get_by_email(email)
            if not user:
                # Generic error to prevent user enumeration
                raise InvalidCredentialsError("Invalid email or password")

            # Verify password
            if not self.password_hasher.verify_password(request.password, user.password_hash):
                # Audit failed login
                await self.audit_log.log_event(
                    event_type="user.login_failed",
                    user_id=user.id,
                    details={"reason": "invalid_password", "email": str(user.email)},
                    ip=request.ip,
                )
                raise InvalidCredentialsError("Invalid email or password")

            # Check if user is active
            if not user.is_active:
                await self.audit_log.log_event(
                    event_type="user.login_failed",
                    user_id=user.id,
                    details={"reason": "account_inactive", "email": str(user.email)},
                    ip=request.ip,
                )
                raise UserNotActiveError("User account is not active")

            # Get user roles
            roles = await self.uow.auth.get_user_roles(user.id)

            # Issue access token
            access_token = self.jwt_service.issue_access_token(
                user_id=user.id, roles=roles, token_version=user.token_version
            )

            # Generate refresh token
            refresh_token_raw = self.token_hasher.generate_token()
            refresh_token_hash = self.token_hasher.hash_token(refresh_token_raw)

            # Create refresh token entity
            now = self.clock.now()
            family_id = uuid.uuid4()  # New token family
            refresh_token_entity = RefreshToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=refresh_token_hash,
                family_id=family_id,
                issued_at=now,
                expires_at=now + timedelta(days=self.refresh_token_ttl_days),
                revoked_at=None,
                replaced_by_token_id=None,
                ip=request.ip,
                user_agent=request.user_agent,
            )

            # Save refresh token
            await self.uow.refresh_tokens.save(refresh_token_entity)
            await self.uow.commit()

            # Generate CSRF token
            csrf_token = secrets.token_urlsafe(32)

            # Audit successful login
            await self.audit_log.log_event(
                event_type="user.login_success",
                user_id=user.id,
                details={"email": str(user.email), "roles": roles},
                ip=request.ip,
            )

            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token_raw,
                csrf_token=csrf_token,
                token_type="Bearer",
            )
