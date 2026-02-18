"""User registration use case."""

import uuid
from datetime import timedelta

from app.application.dto.auth_dto import RegisterRequest, RegisterResponse
from app.application.interfaces.uow import UnitOfWork
from app.application.ports.audit_log_port import AuditLogPort
from app.application.ports.clock_port import ClockPort
from app.application.ports.crypto_port import PasswordHasherPort
from app.domain.entities.user import User
from app.domain.errors.domain_errors import UserAlreadyExistsError
from app.domain.services.password_policy import PasswordPolicy
from app.domain.value_objects.email import Email


class RegisterUseCase:
    """Use case for user registration."""

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

    async def execute(self, request: RegisterRequest) -> RegisterResponse:
        """
        Register a new user.
        
        Raises:
            UserAlreadyExistsError: If email already registered
            ValueError: If password doesn't meet policy
        """
        # Validate password policy
        PasswordPolicy.validate(request.password)

        # Normalize email
        email = Email(request.email).normalize()

        async with self.uow:
            # Check if user already exists
            if await self.uow.users.exists_by_email(email):
                raise UserAlreadyExistsError(f"User with email {email} already exists")

            # Hash password
            password_hash = self.password_hasher.hash_password(request.password)

            # Create user entity
            now = self.clock.now()
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=password_hash,
                is_active=True,
                is_verified=False,  # Could require email verification
                token_version=0,
                created_at=now,
                updated_at=now,
            )

            # Save user
            user = await self.uow.users.save(user)
            await self.uow.commit()

            # Audit log
            await self.audit_log.log_event(
                event_type="user.registered",
                user_id=user.id,
                details={"email": str(user.email)},
            )

            return RegisterResponse(user_id=user.id, email=str(user.email))
