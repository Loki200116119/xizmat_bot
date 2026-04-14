"""
🗄️  SQLAlchemy modellari
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text,
    Boolean, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


# ── Enums ──────────────────────────────────────────────────────

class OrderStatus(str, enum.Enum):
    NEW        = "new"
    ACCEPTED   = "accepted"
    IN_PROCESS = "in_process"
    DONE       = "done"
    CANCELLED  = "cancelled"


STATUS_LABELS = {
    OrderStatus.NEW:        "🆕 Yangi",
    OrderStatus.ACCEPTED:   "✅ Qabul qilindi",
    OrderStatus.IN_PROCESS: "⚙️ Jarayonda",
    OrderStatus.DONE:       "🏁 Tugallandi",
    OrderStatus.CANCELLED:  "❌ Bekor qilindi",
}


# ── Jadvallar ─────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name   = Column(String(150))
    username    = Column(String(100), nullable=True)
    phone       = Column(String(20), nullable=True)
    is_banned   = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    last_seen   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders      = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User {self.telegram_id} — {self.full_name}>"


class Service(Base):
    __tablename__ = "services"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price       = Column(String(100), nullable=True)   # "100 000 so'm" yoki "Kelishiladi"
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    orders      = relationship("Order", back_populates="service")

    def __repr__(self):
        return f"<Service {self.id}: {self.name}>"


class Order(Base):
    __tablename__ = "orders"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id  = Column(Integer, ForeignKey("services.id"), nullable=True)
    client_name = Column(String(150))
    phone       = Column(String(20))
    comment     = Column(Text, nullable=True)
    file_id     = Column(String(300), nullable=True)   # Telegram file_id
    status      = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user        = relationship("User", back_populates="orders")
    service     = relationship("Service", back_populates="orders")

    def __repr__(self):
        return f"<Order #{self.id} — {self.status}>"
