"""
SQLAlchemy Models for Genesis E-commerce Application
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    inventory = Column(Integer, default=0)  # TDD expects 'inventory' field
    stock_quantity = Column(Integer, default=0)  # Keep existing for backward compatibility
    sku = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order_items = relationship("OrderItem", back_populates="product")

class Order(Base):
    __tablename__ = "orders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), default="pending")
    total_amount = Column(Numeric(10, 2), nullable=False)
    shipping_address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
