from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(11), unique=True, index=True, nullable=False)
    password_hash = Column(String(255))
    name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False, default="elderly")
    avatar = Column(String(255))
    birth_date = Column(Date)
    address = Column(String(255))
    dietary_preferences = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    orders = relationship("Order", foreign_keys="Order.user_id", back_populates="user")
    elderly_orders = relationship("Order", foreign_keys="Order.elderly_user_id", back_populates="elderly_user")
    family_binds_as_family = relationship("FamilyBind", foreign_keys="FamilyBind.family_user_id", back_populates="family_user")
    family_binds_as_elderly = relationship("FamilyBind", foreign_keys="FamilyBind.elderly_user_id", back_populates="elderly_user")


class FamilyBind(Base):
    __tablename__ = "family_binds"

    id = Column(Integer, primary_key=True, index=True)
    family_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    elderly_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relation = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))

    family_user = relationship("User", foreign_keys=[family_user_id], back_populates="family_binds_as_family")
    elderly_user = relationship("User", foreign_keys=[elderly_user_id], back_populates="family_binds_as_elderly")


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    image = Column(String(255))
    description = Column(Text)
    nutrition_info = Column(JSON)
    suitable_for = Column(JSON)
    stock = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="on")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order_items = relationship("OrderItem", back_populates="dish")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    elderly_user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Numeric(10, 2), nullable=False)
    meal_period = Column(String(20), nullable=False)
    meal_date = Column(Date, nullable=False, index=True)
    dining_type = Column(String(20), nullable=False, default="dinein")
    pickup_code = Column(String(10))
    status = Column(String(20), nullable=False, default="pending")
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="orders")
    elderly_user = relationship("User", foreign_keys=[elderly_user_id], back_populates="elderly_orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    dish = relationship("Dish", back_populates="order_items")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    prediction_date = Column(Date, unique=True, nullable=False, index=True)
    prediction_data = Column(JSON, nullable=False)
    actual_data = Column(JSON)
    accuracy = Column(Integer)
    features_used = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SmsCode(Base):
    __tablename__ = "sms_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(11), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
