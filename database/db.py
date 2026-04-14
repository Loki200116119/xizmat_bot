"""
🔌  Database ulanish va sessiya
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import settings
from database.models import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Barcha jadvallarni yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Demo xizmatlar qo'shish (agar bo'sh bo'lsa)
    async with AsyncSessionLocal() as session:
        from database.queries import ServiceQueries
        services = await ServiceQueries.get_all(session)
        if not services:
            await _seed_demo_services(session)


async def _seed_demo_services(session: AsyncSession):
    """Birinchi ishga tushirishda demo xizmatlar"""
    from database.models import Service
    demos = [
        Service(name="Telegram Bot Yasash", description="Professional Telegram bot ishlab chiqish. Aiogram 3 asosida.", price="500 000 – 2 000 000 so'm"),
        Service(name="Logo Dizayn", description="Korporativ uslubdagi original logotip dizayni.", price="200 000 so'm"),
        Service(name="SMM Xizmatlari", description="Ijtimoiy tarmoqlarda sahifa yuritish va kontent yaratish.", price="800 000 so'm/oy"),
        Service(name="Target Reklama", description="Facebook va Instagram maqsadli reklamalari.", price="Kelishiladi"),
        Service(name="Konsultatsiya", description="30 daqiqalik bepul onlayn konsultatsiya.", price="Bepul"),
    ]
    session.add_all(demos)
    await session.commit()


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
