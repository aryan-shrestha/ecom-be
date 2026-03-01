"""Order repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.entities.order import Order, OrderStatus


class OrderRepository(ABC):
    """Repository interface for Order aggregate."""

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Retrieve order by ID (includes items)."""
        ...

    @abstractmethod
    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Retrieve order by order_number."""
        ...

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Persist new order together with its items."""
        ...

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Update order header fields (status, updated_at, etc.)."""
        ...

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Order], int]:
        """List orders for a specific user with pagination."""
        ...

    @abstractmethod
    async def list_admin(
        self,
        offset: int = 0,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
        user_id: Optional[UUID] = None,
        order_number: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> tuple[list[Order], int]:
        """List orders for admin with filters and pagination."""
        ...
