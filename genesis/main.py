"""
FastAPI E-commerce Order Management System
Main application with PostgreSQL integration and comprehensive CRUD operations
"""
import os
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import uvicorn
from genesis.app.tenant_middleware import (
    TenantMiddleware,
    create_tenant_database_dependency,
    create_tenant_schema,
    drop_tenant_schema,
    list_tenant_schemas,
)
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ecommerce")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models
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
    stock_quantity = Column(Integer, default=0)
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

# Create tables function (called when needed, not at import)
def create_tables():
    Base.metadata.create_all(bind=engine)

# Only create tables if running directly
if __name__ == "__main__":
    create_tables()

# Pydantic Schemas
class CustomerBase(BaseModel):
    email: str = Field(..., description="Customer email address")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None

    model_config = {'from_attributes': True}

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    sku: str = Field(..., min_length=1, max_length=100)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None

    model_config = {'from_attributes': True}

class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: UUID
    product: ProductResponse

    model_config = {'from_attributes': True}

class OrderBase(BaseModel):
    customer_id: UUID
    status: str = Field(default="pending")
    shipping_address: str | None = None

class OrderCreate(OrderBase):
    order_items: list[OrderItemCreate] = Field(..., min_length=1)

class OrderResponse(OrderBase):
    id: UUID
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime | None
    customer: CustomerResponse
    order_items: list[OrderItemResponse]

    model_config = {'from_attributes': True}

# FastAPI App
app = FastAPI(
    title="E-commerce Order Management API",
    description="Comprehensive order management system with FastAPI and PostgreSQL",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy support
app.add_middleware(TenantMiddleware, tenant_schema_prefix="tenant_")

# Database Dependencies
def get_db():
    """Standard database dependency (public schema)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Tenant-aware database dependency
get_tenant_db = create_tenant_database_dependency(SessionLocal)

# Customer Endpoints
@app.post("/customers/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_tenant_db)):
    """Create a new customer"""
    db_customer = db.query(Customer).filter(Customer.email == customer.email).first()
    if db_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/customers/", response_model=list[CustomerResponse])
def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_tenant_db)):
    """Get list of customers"""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: UUID, db: Session = Depends(get_tenant_db)):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer

# Product Endpoints
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_tenant_db)):
    """Create a new product"""
    db_product = db.query(Product).filter(Product.sku == product.sku).first()
    if db_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SKU already exists"
        )

    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=list[ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_tenant_db)):
    """Get list of products"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_tenant_db)):
    """Get product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, product: ProductCreate, db: Session = Depends(get_tenant_db)):
    """Update product"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    for key, value in product.model_dump().items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

# Order Endpoints
@app.post("/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_tenant_db)):
    """Create a new order with order items"""
    # Validate customer exists
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Calculate total amount and validate products
    total_amount = Decimal('0.00')
    validated_items = []

    for item in order.order_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )

        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}"
            )

        item_total = item.unit_price * item.quantity
        total_amount += item_total
        validated_items.append((item, product))

    # Create order
    db_order = Order(
        customer_id=order.customer_id,
        status=order.status,
        total_amount=total_amount,
        shipping_address=order.shipping_address
    )
    db.add(db_order)
    db.flush()  # Get the order ID without committing

    # Create order items and update stock
    for item, product in validated_items:
        db_order_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(db_order_item)

        # Update product stock
        product.stock_quantity -= item.quantity

    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders/", response_model=list[OrderResponse])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_tenant_db)):
    """Get list of orders"""
    orders = db.query(Order).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: UUID, db: Session = Depends(get_tenant_db)):
    """Get order by ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order

@app.put("/orders/{order_id}/status")
def update_order_status(order_id: UUID, status_update: dict, db: Session = Depends(get_tenant_db)):
    """Update order status"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    new_status = status_update.get("status")

    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    order.status = new_status
    db.commit()
    return {"message": "Order status updated successfully", "new_status": new_status}

@app.get("/customers/{customer_id}/orders", response_model=list[OrderResponse])
def get_customer_orders(customer_id: UUID, db: Session = Depends(get_tenant_db)):
    """Get all orders for a specific customer"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    orders = db.query(Order).filter(Order.customer_id == customer_id).all()
    return orders

# Health Check
# Tenant Management Endpoints
@app.post("/tenants/{tenant_slug}", status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant_slug: str):
    """Create a new tenant schema"""
    try:
        await create_tenant_schema(tenant_slug, DATABASE_URL)
        return {"message": f"Tenant '{tenant_slug}' created successfully", "tenant_slug": tenant_slug}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tenant: {str(e)}"
        )

@app.delete("/tenants/{tenant_slug}")
async def delete_tenant(tenant_slug: str):
    """Delete a tenant schema (use with caution!)"""
    try:
        await drop_tenant_schema(tenant_slug, DATABASE_URL)
        return {"message": f"Tenant '{tenant_slug}' deleted successfully", "tenant_slug": tenant_slug}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete tenant: {str(e)}"
        )

@app.get("/tenants/")
async def list_tenants():
    """List all tenant schemas"""
    try:
        schemas = await list_tenant_schemas(DATABASE_URL)
        tenants = [schema.replace('tenant_', '') for schema in schemas]
        return {"tenants": tenants}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Root endpoint
@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "E-commerce Order Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    create_tables()
    uvicorn.run(app, host="0.0.0.0", port=8000)
