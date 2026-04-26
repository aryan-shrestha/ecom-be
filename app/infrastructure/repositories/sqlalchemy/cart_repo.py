"""SQLAlchemy implementation of CartRepository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.cart import Cart, CartItem
from app.domain.repositories.cart_repository import CartRepository
from app.infrastructure.db.sqlalchemy.models.cart_item_model import CartItemModel
from app.infrastructure.db.sqlalchemy.models.cart_model import CartModel
from app.infrastructure.mappers.cart_mapper import CartItemMapper, CartMapper


class SqlAlchemyCartRepository(CartRepository):
    """SQLAlchemy implementation of CartRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_items(self, cart_id: UUID) -> tuple[CartItem, ...]:
        stmt = select(CartItemModel).where(CartItemModel.cart_id == cart_id)
        result = await self.session.execute(stmt)
        return tuple(CartItemMapper.to_entity(m) for m in result.scalars().all())

    async def get_by_id(self, cart_id: UUID) -> Optional[Cart]:
        stmt = select(CartModel).where(CartModel.id == cart_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._load_items(cart_id)
        return CartMapper.to_entity(model, items)

    async def get_active_by_user_id(self, user_id: UUID) -> Optional[Cart]:
        stmt = (
            select(CartModel)
            .where(CartModel.user_id == user_id, CartModel.status == "ACTIVE")
            .order_by(CartModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._load_items(model.id)
        return CartMapper.to_entity(model, items)

    async def get_active_by_guest_token(self, guest_token: str) -> Optional[Cart]:
        stmt = (
            select(CartModel)
            .where(CartModel.guest_token == guest_token, CartModel.status == "ACTIVE")
            .order_by(CartModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._load_items(model.id)
        return CartMapper.to_entity(model, items)

    async def save(self, cart: Cart) -> Cart:
        model = CartMapper.to_model(cart)
        self.session.add(model)
        await self.session.flush()
        return CartMapper.to_entity(model, cart.items)

    async def update(self, cart: Cart) -> Cart:
        stmt = select(CartModel).where(CartModel.id == cart.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        CartMapper.update_model(model, cart)
        await self.session.flush()
        return CartMapper.to_entity(model, cart.items)

    async def save_item(self, item: CartItem) -> CartItem:
        model = CartItemMapper.to_model(item)
        self.session.add(model)
        await self.session.flush()
        return CartItemMapper.to_entity(model)

    async def update_item(self, item: CartItem) -> CartItem:
        stmt = select(CartItemModel).where(CartItemModel.id == item.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        CartItemMapper.update_model(model, item)
        await self.session.flush()
        return CartItemMapper.to_entity(model)

    async def delete_item(self, item_id: UUID) -> None:
        stmt = delete(CartItemModel).where(CartItemModel.id == item_id)
        await self.session.execute(stmt)
        await self.session.flush()

    async def delete_all_items(self, cart_id: UUID) -> None:
        stmt = delete(CartItemModel).where(CartItemModel.cart_id == cart_id)
        await self.session.execute(stmt)
        await self.session.flush()
