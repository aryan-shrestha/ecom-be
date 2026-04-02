"Role mapper for converting between domain entities and database models."

from app.domain.entities.role import Role
from app.infrastructure.db.sqlalchemy.models.role_model import RoleModel


class RoleMapper:
    """Mapper for Role entity and RoleModel."""

    @staticmethod
    def to_entity(model: RoleModel) -> Role:
        """Convert ORM model to domain entity."""
        return Role(id=model.id, name=model.name)

    @staticmethod
    def to_model(entity: Role) -> RoleModel:
        """Convert domain entity to ORM model."""
        return RoleModel(id=entity.id, name=entity.name)