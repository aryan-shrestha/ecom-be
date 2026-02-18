"""Dependency injection container for FastAPI."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.cache_port import CachePort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import PasswordHasherPort, TokenHasherPort
from app.application.ports.jwt_port import JwtPort
from app.application.use_cases.auth.change_password import ChangePasswordUseCase
from app.application.use_cases.auth.login import LoginUseCase
from app.application.use_cases.auth.logout import LogoutUseCase
from app.application.use_cases.auth.logout_all import LogoutAllUseCase
from app.application.use_cases.auth.refresh import RefreshUseCase
from app.application.use_cases.auth.register import RegisterUseCase
from app.application.use_cases.rbac.assign_role import AssignRoleUseCase
from app.application.use_cases.rbac.check_permission import CheckPermissionUseCase
from app.infrastructure.caching.memory_cache import MemoryCache
from app.infrastructure.caching.system_clock import SystemClock
from app.infrastructure.observability.audit_logger import StructuredAuditLogger
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.token_hasher import HmacTokenHasher
from app.infrastructure.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from config.settings import settings


class Container:
    """Dependency injection container."""

    def __init__(self) -> None:
        # Ports (singletons)
        self._password_hasher: PasswordHasherPort = Argon2PasswordHasher()
        self._token_hasher: TokenHasherPort = HmacTokenHasher(
            settings.refresh_token_hmac_secret
        )
        self._jwt_service: JwtPort = JwtService(
            private_key=settings.get_jwt_private_key(),
            public_key=settings.get_jwt_public_key(),
            algorithm=settings.jwt_algorithm,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            kid=settings.jwt_active_kid,
            access_token_ttl_minutes=settings.jwt_access_token_ttl_minutes,
        )
        self._clock: ClockPort = SystemClock()
        self._audit_log: AuditLogPort = StructuredAuditLogger()
        self._cache: CachePort = MemoryCache()

    def get_password_hasher(self) -> PasswordHasherPort:
        """Get password hasher."""
        return self._password_hasher

    def get_token_hasher(self) -> TokenHasherPort:
        """Get token hasher."""
        return self._token_hasher

    def get_jwt_service(self) -> JwtPort:
        """Get JWT service."""
        return self._jwt_service

    def get_clock(self) -> ClockPort:
        """Get clock."""
        return self._clock

    def get_audit_log(self) -> AuditLogPort:
        """Get audit logger."""
        return self._audit_log

    def get_cache(self) -> CachePort:
        """Get cache."""
        return self._cache

    def get_uow(self, session: AsyncSession) -> UnitOfWork:
        """Get Unit of Work."""
        return SqlAlchemyUnitOfWork(session)

    # Use cases
    def get_register_use_case(self, session: AsyncSession) -> RegisterUseCase:
        """Get RegisterUseCase."""
        return RegisterUseCase(
            uow=self.get_uow(session),
            password_hasher=self._password_hasher,
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_login_use_case(self, session: AsyncSession) -> LoginUseCase:
        """Get LoginUseCase."""
        return LoginUseCase(
            uow=self.get_uow(session),
            password_hasher=self._password_hasher,
            token_hasher=self._token_hasher,
            jwt_service=self._jwt_service,
            clock=self._clock,
            audit_log=self._audit_log,
            refresh_token_ttl_days=settings.refresh_token_ttl_days,
        )

    def get_refresh_use_case(self, session: AsyncSession) -> RefreshUseCase:
        """Get RefreshUseCase."""
        return RefreshUseCase(
            uow=self.get_uow(session),
            token_hasher=self._token_hasher,
            jwt_service=self._jwt_service,
            clock=self._clock,
            audit_log=self._audit_log,
            refresh_token_ttl_days=settings.refresh_token_ttl_days,
        )

    def get_logout_use_case(self, session: AsyncSession) -> LogoutUseCase:
        """Get LogoutUseCase."""
        return LogoutUseCase(
            uow=self.get_uow(session),
            token_hasher=self._token_hasher,
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_logout_all_use_case(self, session: AsyncSession) -> LogoutAllUseCase:
        """Get LogoutAllUseCase."""
        return LogoutAllUseCase(
            uow=self.get_uow(session),
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_change_password_use_case(self, session: AsyncSession) -> ChangePasswordUseCase:
        """Get ChangePasswordUseCase."""
        return ChangePasswordUseCase(
            uow=self.get_uow(session),
            password_hasher=self._password_hasher,
            clock=self._clock,
            audit_log=self._audit_log,
        )

    def get_check_permission_use_case(self, session: AsyncSession) -> CheckPermissionUseCase:
        """Get CheckPermissionUseCase."""
        return CheckPermissionUseCase(
            uow=self.get_uow(session),
            cache=self._cache,
        )

    def get_assign_role_use_case(self, session: AsyncSession) -> AssignRoleUseCase:
        """Get AssignRoleUseCase."""
        return AssignRoleUseCase(
            uow=self.get_uow(session),
            audit_log=self._audit_log,
        )


@lru_cache
def get_container() -> Container:
    """Get singleton container instance."""
    return Container()
