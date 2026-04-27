#!/usr/bin/env python3
"""Script to seed initial database with roles, permissions, and admin user."""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

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
        # Create roles
            # Roles (idempotent)
            admin_role = (
                await session.execute(select(RoleModel).where(RoleModel.name == "admin"))
            ).scalar_one_or_none()
            if not admin_role:
                admin_role = RoleModel(id=uuid.uuid4(), name="admin")
                session.add(admin_role)

            user_role = (
                await session.execute(select(RoleModel).where(RoleModel.name == "user"))
            ).scalar_one_or_none()
            if not user_role:
                user_role = RoleModel(id=uuid.uuid4(), name="user")
                session.add(user_role)

            # Permissions (idempotent)
            permission_codes = [
                "rbac:assign",
                "rbac:view",
                "users:read",
                "users:write",
                "products:read",
                "products:write",
                "products:publish",
                "products:archive",
                "products:variant_write",
                "categories:read",
                "categories:write",
                "inventory:read",
                "inventory:adjust",
                "products:media_write",
                "orders:manage",
                "roles:read",
                "roles:write",
                "permissions:read",
                "permissions:write",
            ]

            result = await session.execute(
                select(PermissionModel).where(PermissionModel.code.in_(permission_codes))
            )
            permissions_by_code = {perm.code: perm for perm in result.scalars().all()}
            for code in permission_codes:
                if code not in permissions_by_code:
                    perm = PermissionModel(id=uuid.uuid4(), code=code)
                    session.add(perm)
                    permissions_by_code[code] = perm

            await session.flush()

            # Assign permissions to admin role
            result = await session.execute(
                select(RolePermissionModel.permission_id).where(
                    RolePermissionModel.role_id == admin_role.id
                )
            )
            admin_permission_ids = set(result.scalars().all())
            for code in permission_codes:
                perm_id = permissions_by_code[code].id
                if perm_id not in admin_permission_ids:
                    session.add(RolePermissionModel(role_id=admin_role.id, permission_id=perm_id))

            # Assign permissions to user role (users:read only)
            users_read_id = permissions_by_code["users:read"].id
            result = await session.execute(
                select(RolePermissionModel.permission_id).where(
                    RolePermissionModel.role_id == user_role.id
                )
            )
            user_permission_ids = set(result.scalars().all())
            if users_read_id not in user_permission_ids:
                session.add(RolePermissionModel(role_id=user_role.id, permission_id=users_read_id))

            # Create admin user if missing
            hasher = Argon2PasswordHasher()
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            admin_user = (
                await session.execute(select(UserModel).where(UserModel.email == "admin@example.com"))
            ).scalar_one_or_none()
            if not admin_user:
                admin_user = UserModel(
                    id=uuid.uuid4(),
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
        print("Products: products:read, products:write, products:publish, products:archive")
        print("Products:variant_write, products:media_write")
        print("Categories: categories:read, categories:write")
        print("Inventory: inventory:read, inventory:adjust")
        print("Orders: orders:manage")
        print("Roles: roles:read, roles:write")
        print("Permissions: permissions:read, permissions:write")

        # Assign admin role to admin user
        result = await session.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == admin_user.id,
                UserRoleModel.role_id == admin_role.id,
            )
        )
        if not result.scalar_one_or_none():
            session.add(UserRoleModel(user_id=admin_user.id, role_id=admin_role.id))

        await session.commit()

        print("\nDatabase seeded successfully!")
        print("\nCreated:")
        print("  - Roles: admin, user")
        print("  - Permissions: rbac:assign, rbac:view, users:read, users:write,")
        print("    products:read, products:write, products:publish, products:archive,")
        print("    products:variant_write, products:media_write,")
        print("    categories:read, categories:write,")
        print("    inventory:read, inventory:adjust,")
        print("    orders:manage, roles:read, roles:write, permissions:read, permissions:write")
        print("  - Admin user:")
        print("      Email: admin@example.com")
        print("      Password: Admin123!")
        print("\nChange admin password after first login!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
