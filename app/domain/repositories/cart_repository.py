"""Cart repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities.cart import Cart, CartItem


class CartRepository(ABC):
    """Repository interface for Cart aggregate."""

    @abstractmethod
    async def get_by_id(self, cart_id: UUID) -> Optional[Cart]:
        """Retrieve cart by ID (includes items)."""
        ...

    @abstractmethod
    async def get_active_by_user_id(self, user_id: UUID) -> Optional[Cart]:
        """Retrieve active cart for authenticated user."""
        ...

    @abstractmethod
    async def get_active_by_guest_token(self, guest_token: str) -> Optional[Cart]:
        """Retrieve active cart for guest session token."""
        ...

    @abstractmethod
    async def save(self, cart: Cart) -> Cart:
        """Persist a new cart (without items)."""
        ...

    @abstractmethod
    async def update(self, cart: Cart) -> Cart:
        """Update an existing cart header (status, updated_at)."""
        ...

    @abstractmethod
    async def save_item(self, item: CartItem) -> CartItem:
        """Insert a new cart item."""
        ...

    @abstractmethod
    async def update_item(self, item: CartItem) -> CartItem:
        """Update an existing cart item (quantity)."""
        ...

    @abstractmethod
    async def delete_item(self, item_id: UUID) -> None:
        """Remove a single cart item."""
        ...

    @abstractmethod
    async def delete_all_items(self, cart_id: UUID) -> None:
        """Remove all items from a cart."""
        ...
