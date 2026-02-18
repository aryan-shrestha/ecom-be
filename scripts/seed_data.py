#!/usr/bin/env python3
"""Script to seed initial database with roles, permissions, and admin user."""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.infrastructure.db.sqlalchemy.models.permission_model import PermissionModel
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel
from app.infrastructure.db.sqlalchemy.models.role_permission_model import RolePermissionModel
from app.infrastructure.db.sqlalchemy.models.user_model import UserModel
from app.infrastructure.db.sqlalchemy.models.user_role_model import UserRoleModel
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from config.settings import settings


async def seed_data():
    """Seed initial data."""
    engine = create_async_engine(str(settings.database_url), echo=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        # Check if data already exists
        result = await session.execute(select(RoleModel))
        if result.scalars().first():
            print("⚠️  Data already exists, skipping seed")
            return

        print("🌱 Seeding database...")

        # Create roles
        admin_role = RoleModel(id=uuid.uuid4(), name="admin")
        user_role = RoleModel(id=uuid.uuid4(), name="user")
        session.add_all([admin_role, user_role])

        # Create permissions
        rbac_assign_perm = PermissionModel(id=uuid.uuid4(), code="rbac:assign")
        rbac_view_perm = PermissionModel(id=uuid.uuid4(), code="rbac:view")
        users_read_perm = PermissionModel(id=uuid.uuid4(), code="users:read")
        users_write_perm = PermissionModel(id=uuid.uuid4(), code="users:write")

        session.add_all([rbac_assign_perm, rbac_view_perm, users_read_perm, users_write_perm])
        await session.flush()

        # Assign permissions to admin role
        admin_perms = [
            RolePermissionModel(role_id=admin_role.id, permission_id=rbac_assign_perm.id),
            RolePermissionModel(role_id=admin_role.id, permission_id=rbac_view_perm.id),
            RolePermissionModel(role_id=admin_role.id, permission_id=users_read_perm.id),
            RolePermissionModel(role_id=admin_role.id, permission_id=users_write_perm.id),
        ]
        session.add_all(admin_perms)

        # Assign permissions to user role
        user_perms = [
            RolePermissionModel(role_id=user_role.id, permission_id=users_read_perm.id),
        ]
        session.add_all(user_perms)

        # Create admin user
        hasher = Argon2PasswordHasher()
        admin_user_id = uuid.uuid4()
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        admin_user = UserModel(
            id=admin_user_id,
            email="admin@example.com",
            password_hash=hasher.hash_password("Admin123!"),
            is_active=True,
            is_verified=True,
            token_version=0,
            created_at=now,
            updated_at=now,
        )
        session.add(admin_user)
        await session.flush()

        # Assign admin role to admin user
        admin_user_role = UserRoleModel(user_id=admin_user_id, role_id=admin_role.id)
        session.add(admin_user_role)

        await session.commit()

        print("\n✓ Database seeded successfully!")
        print("\n📋 Created:")
        print("  - Roles: admin, user")
        print("  - Permissions: rbac:assign, rbac:view, users:read, users:write")
        print("  - Admin user:")
        print("      Email: admin@example.com")
        print("      Password: Admin123!")
        print("\n⚠️  Change admin password after first login!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
