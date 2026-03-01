"""SQLAlchemy implementation of OrderRepository."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.order import Order, OrderItem, OrderStatus
from app.domain.repositories.order_repository import OrderRepository
from app.infrastructure.db.sqlalchemy.models.order_item_model import OrderItemModel
from app.infrastructure.db.sqlalchemy.models.order_model import OrderModel
from app.infrastructure.mappers.order_mapper import OrderItemMapper, OrderMapper


class SqlAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_items(self, order_id: UUID) -> tuple[OrderItem, ...]:
        stmt = select(OrderItemModel).where(OrderItemModel.order_id == order_id)
        result = await self.session.execute(stmt)
        return tuple(OrderItemMapper.to_entity(m, order_id) for m in result.scalars().all())

    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._load_items(order_id)
        return OrderMapper.to_entity(model, items)

    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        stmt = select(OrderModel).where(OrderModel.order_number == order_number)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._load_items(model.id)
        return OrderMapper.to_entity(model, items)

    async def save(self, order: Order) -> Order:
        order_model = OrderMapper.to_model(order)
        self.session.add(order_model)
        await self.session.flush()

        # Persist items
        for item in order.items:
            item_model = OrderItemMapper.to_model(item)
            self.session.add(item_model)
        await self.session.flush()

        return OrderMapper.to_entity(order_model, order.items)

    async def update(self, order: Order) -> Order:
        stmt = select(OrderModel).where(OrderModel.id == order.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        OrderMapper.update_model(model, order)
        await self.session.flush()
        items = await self._load_items(order.id)
        return OrderMapper.to_entity(model, items)

    async def list_for_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Order], int]:
        count_stmt = select(func.count()).select_from(OrderModel).where(OrderModel.user_id == user_id)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        orders = []
        for m in models:
            items = await self._load_items(m.id)
            orders.append(OrderMapper.to_entity(m, items))

        return orders, total

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
        filters = []
        if status is not None:
            filters.append(OrderModel.status == status.value)
        if user_id is not None:
            filters.append(OrderModel.user_id == user_id)
        if order_number is not None:
            filters.append(OrderModel.order_number.ilike(f"%{order_number}%"))
        if from_date is not None:
            filters.append(OrderModel.created_at >= from_date)
        if to_date is not None:
            filters.append(OrderModel.created_at <= to_date)

        count_stmt = select(func.count()).select_from(OrderModel)
        if filters:
            count_stmt = count_stmt.where(*filters)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = select(OrderModel).order_by(OrderModel.created_at.desc()).offset(offset).limit(limit)
        if filters:
            stmt = stmt.where(*filters)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        orders = []
        for m in models:
            items = await self._load_items(m.id)
            orders.append(OrderMapper.to_entity(m, items))

        return orders, total
