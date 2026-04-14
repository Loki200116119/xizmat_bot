"""
📋  Barcha DB so'rovlari — queries.py
"""

from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc
from database.models import User, Service, Order, OrderStatus


# ══════════════════════════════════════════════════════════════
#                        👤  USER
# ══════════════════════════════════════════════════════════════

class UserQueries:

    @staticmethod
    async def get_or_create(session: AsyncSession, telegram_id: int, full_name: str, username: str = None) -> User:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.full_name = full_name
            user.username  = username
            user.last_seen = datetime.utcnow()
        else:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession, limit: int = 50) -> list[User]:
        result = await session.execute(
            select(User).order_by(desc(User.created_at)).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def ban_user(session: AsyncSession, telegram_id: int, ban: bool = True):
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_banned=ban)
        )
        await session.commit()

    @staticmethod
    async def count(session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(User))
        return result.scalar()

    @staticmethod
    async def count_today(session: AsyncSession) -> int:
        today = date.today()
        result = await session.execute(
            select(func.count()).select_from(User)
            .where(func.date(User.created_at) == today)
        )
        return result.scalar()

    @staticmethod
    async def get_all_ids(session: AsyncSession) -> list[int]:
        result = await session.execute(select(User.telegram_id).where(User.is_banned == False))
        return [row[0] for row in result.all()]

    @staticmethod
    async def save_phone(session: AsyncSession, telegram_id: int, phone: str):
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(phone=phone)
        )
        await session.commit()


# ══════════════════════════════════════════════════════════════
#                        🛠️  SERVICE
# ══════════════════════════════════════════════════════════════

class ServiceQueries:

    @staticmethod
    async def get_all(session: AsyncSession, active_only: bool = True) -> list[Service]:
        q = select(Service)
        if active_only:
            q = q.where(Service.is_active == True)
        q = q.order_by(Service.id)
        result = await session.execute(q)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, service_id: int) -> Service | None:
        result = await session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, name: str, description: str, price: str) -> Service:
        svc = Service(name=name, description=description, price=price)
        session.add(svc)
        await session.commit()
        await session.refresh(svc)
        return svc

    @staticmethod
    async def update(session: AsyncSession, service_id: int, **kwargs):
        await session.execute(
            update(Service).where(Service.id == service_id).values(**kwargs)
        )
        await session.commit()

    @staticmethod
    async def toggle_active(session: AsyncSession, service_id: int) -> bool:
        svc = await ServiceQueries.get_by_id(session, service_id)
        if svc:
            new_val = not svc.is_active
            await ServiceQueries.update(session, service_id, is_active=new_val)
            return new_val
        return False

    @staticmethod
    async def delete(session: AsyncSession, service_id: int):
        svc = await ServiceQueries.get_by_id(session, service_id)
        if svc:
            await session.delete(svc)
            await session.commit()

    @staticmethod
    async def count(session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(Service))
        return result.scalar()


# ══════════════════════════════════════════════════════════════
#                        📦  ORDER
# ══════════════════════════════════════════════════════════════

class OrderQueries:

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        service_id: int | None,
        client_name: str,
        phone: str,
        comment: str = None,
        file_id: str = None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            service_id=service_id,
            client_name=client_name,
            phone=phone,
            comment=comment,
            file_id=file_id,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Order | None:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Order)
            .options(joinedload(Order.user), joinedload(Order.service))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int) -> list[Order]:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Order)
            .options(joinedload(Order.service))
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
        )
        return result.scalars().all()

    @staticmethod
    async def get_all(session: AsyncSession, limit: int = 30) -> list[Order]:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Order)
            .options(joinedload(Order.user), joinedload(Order.service))
            .order_by(desc(Order.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_status(session: AsyncSession, status: OrderStatus) -> list[Order]:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Order)
            .options(joinedload(Order.user), joinedload(Order.service))
            .where(Order.status == status)
            .order_by(desc(Order.created_at))
        )
        return result.scalars().all()

    @staticmethod
    async def update_status(session: AsyncSession, order_id: int, status: OrderStatus):
        await session.execute(
            update(Order).where(Order.id == order_id)
            .values(status=status, updated_at=datetime.utcnow())
        )
        await session.commit()

    @staticmethod
    async def count(session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(Order))
        return result.scalar()

    @staticmethod
    async def count_today(session: AsyncSession) -> int:
        today = date.today()
        result = await session.execute(
            select(func.count()).select_from(Order)
            .where(func.date(Order.created_at) == today)
        )
        return result.scalar()

    @staticmethod
    async def count_by_status(session: AsyncSession) -> dict:
        result = await session.execute(
            select(Order.status, func.count()).group_by(Order.status)
        )
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def popular_service(session: AsyncSession) -> str:
        result = await session.execute(
            select(Service.name, func.count(Order.id).label("cnt"))
            .join(Order, Order.service_id == Service.id)
            .group_by(Service.name)
            .order_by(desc("cnt"))
            .limit(1)
        )
        row = result.first()
        return row[0] if row else "—"
