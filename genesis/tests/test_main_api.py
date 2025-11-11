"""
Comprehensive FastAPI Test Suite for E-commerce Order Management API
Tests all CRUD operations, validation, and error handling
"""
import os
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

# Import the FastAPI app and models
from main import (
    Base,
    Customer,
    Order,
    OrderItem,
    Product,
    app,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_ecommerce.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
from main import get_db

app.dependency_overrides[get_db] = override_get_db


class TestEcommerceAPI(unittest.TestCase):
    """Test suite for E-commerce API endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test database and client"""
        # Create tables using test engine
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        Base.metadata.drop_all(bind=test_engine)
        if os.path.exists("test_ecommerce.db"):
            os.remove("test_ecommerce.db")

    def setUp(self):
        """Set up test data before each test"""
        # Clear all tables
        db = TestingSessionLocal()
        try:
            db.query(OrderItem).delete()
            db.query(Order).delete()
            db.query(Product).delete()
            db.query(Customer).delete()
            db.commit()
        finally:
            db.close()

        # Test data that matches actual schemas
        self.customer_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }

        self.product_data = {
            "name": "Test Product",
            "description": "A test product for testing",
            "price": 29.99,
            "stock_quantity": 100,
            "sku": "TEST-SKU-001"
        }

    def test_root_endpoint(self):
        """Test root API endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "E-commerce Order Management API")
        self.assertEqual(data["version"], "1.0.0")

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

    def test_create_customer_success(self):
        """Test successful customer creation"""
        response = self.client.post("/customers/", json=self.customer_data)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["email"], self.customer_data["email"])
        self.assertEqual(data["first_name"], self.customer_data["first_name"])
        self.assertEqual(data["last_name"], self.customer_data["last_name"])
        self.assertIn("id", data)
        self.assertIn("created_at", data)

    def test_create_customer_duplicate_email(self):
        """Test customer creation with duplicate email"""
        # Create first customer
        self.client.post("/customers/", json=self.customer_data)

        # Try to create duplicate
        response = self.client.post("/customers/", json=self.customer_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already registered", response.json()["detail"])

    def test_get_customers(self):
        """Test getting list of customers"""
        # Create test customers
        customer1 = self.customer_data.copy()
        customer2 = self.customer_data.copy()
        customer2["email"] = "jane@example.com"
        customer2["first_name"] = "Jane"

        self.client.post("/customers/", json=customer1)
        self.client.post("/customers/", json=customer2)

        response = self.client.get("/customers/")
        self.assertEqual(response.status_code, 200)

        customers = response.json()
        self.assertEqual(len(customers), 2)

    def test_get_customer_by_id(self):
        """Test getting customer by ID"""
        # Create customer
        create_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = create_response.json()["id"]

        # Get customer by ID
        response = self.client.get(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], customer_id)
        self.assertEqual(data["email"], self.customer_data["email"])

    def test_get_customer_not_found(self):
        """Test getting non-existent customer"""
        fake_id = str(uuid4())
        response = self.client.get(f"/customers/{fake_id}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Customer not found", response.json()["detail"])

    def test_create_product_success(self):
        """Test successful product creation"""
        response = self.client.post("/products/", json=self.product_data)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["name"], self.product_data["name"])
        self.assertEqual(data["sku"], self.product_data["sku"])
        self.assertEqual(float(data["price"]), self.product_data["price"])
        self.assertEqual(data["stock_quantity"], self.product_data["stock_quantity"])

    def test_create_product_duplicate_sku(self):
        """Test product creation with duplicate SKU"""
        # Create first product
        self.client.post("/products/", json=self.product_data)

        # Try to create duplicate
        response = self.client.post("/products/", json=self.product_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("SKU already exists", response.json()["detail"])

    def test_get_products(self):
        """Test getting list of products"""
        # Create test products
        product1 = self.product_data.copy()
        product2 = self.product_data.copy()
        product2["sku"] = "TEST-SKU-002"
        product2["name"] = "Test Product 2"

        self.client.post("/products/", json=product1)
        self.client.post("/products/", json=product2)

        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)

        products = response.json()
        self.assertEqual(len(products), 2)

    def test_get_product_by_id(self):
        """Test getting product by ID"""
        # Create product
        create_response = self.client.post("/products/", json=self.product_data)
        product_id = create_response.json()["id"]

        # Get product by ID
        response = self.client.get(f"/products/{product_id}")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["id"], product_id)
        self.assertEqual(data["name"], self.product_data["name"])

    def test_update_product(self):
        """Test updating product"""
        # Create product
        create_response = self.client.post("/products/", json=self.product_data)
        product_id = create_response.json()["id"]

        # Update product
        updated_data = self.product_data.copy()
        updated_data["price"] = 39.99
        updated_data["stock_quantity"] = 150

        response = self.client.put(f"/products/{product_id}", json=updated_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(float(data["price"]), 39.99)
        self.assertEqual(data["stock_quantity"], 150)

    def test_create_order_success(self):
        """Test successful order creation"""
        # Create customer and product first
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        product_response = self.client.post("/products/", json=self.product_data)
        product_id = product_response.json()["id"]

        # Create order
        order_data = {
            "customer_id": customer_id,
            "status": "pending",
            "shipping_address": "123 Test St, Test City, TC 12345",
            "order_items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "unit_price": 29.99
                }
            ]
        }

        response = self.client.post("/orders/", json=order_data)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["customer_id"], customer_id)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(float(data["total_amount"]), 59.98)  # 2 * 29.99
        self.assertEqual(len(data["order_items"]), 1)

    def test_create_order_invalid_customer(self):
        """Test order creation with invalid customer"""
        fake_customer_id = str(uuid4())
        fake_product_id = str(uuid4())

        order_data = {
            "customer_id": fake_customer_id,
            "order_items": [
                {
                    "product_id": fake_product_id,
                    "quantity": 1,
                    "unit_price": 29.99
                }
            ]
        }

        response = self.client.post("/orders/", json=order_data)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Customer not found", response.json()["detail"])

    def test_create_order_invalid_product(self):
        """Test order creation with invalid product"""
        # Create customer
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        fake_product_id = str(uuid4())
        order_data = {
            "customer_id": customer_id,
            "order_items": [
                {
                    "product_id": fake_product_id,
                    "quantity": 1,
                    "unit_price": 29.99
                }
            ]
        }

        response = self.client.post("/orders/", json=order_data)
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    def test_create_order_insufficient_stock(self):
        """Test order creation with insufficient stock"""
        # Create customer and product with limited stock
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        limited_product = self.product_data.copy()
        limited_product["stock_quantity"] = 1  # Only 1 in stock
        product_response = self.client.post("/products/", json=limited_product)
        product_id = product_response.json()["id"]

        # Try to order more than available
        order_data = {
            "customer_id": customer_id,
            "order_items": [
                {
                    "product_id": product_id,
                    "quantity": 5,  # More than stock
                    "unit_price": 29.99
                }
            ]
        }

        response = self.client.post("/orders/", json=order_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient stock", response.json()["detail"])

    def test_get_orders(self):
        """Test getting list of orders"""
        # Create customer, product, and order
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        product_response = self.client.post("/products/", json=self.product_data)
        product_id = product_response.json()["id"]

        order_data = {
            "customer_id": customer_id,
            "order_items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": 29.99
                }
            ]
        }

        self.client.post("/orders/", json=order_data)

        response = self.client.get("/orders/")
        self.assertEqual(response.status_code, 200)

        orders = response.json()
        self.assertEqual(len(orders), 1)

    def test_update_order_status(self):
        """Test updating order status"""
        # Create customer, product, and order
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        product_response = self.client.post("/products/", json=self.product_data)
        product_id = product_response.json()["id"]

        order_data = {
            "customer_id": customer_id,
            "order_items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": 29.99
                }
            ]
        }

        order_response = self.client.post("/orders/", json=order_data)
        order_id = order_response.json()["id"]

        # Update status
        status_update = {"status": "confirmed"}
        response = self.client.put(f"/orders/{order_id}/status", json=status_update)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["new_status"], "confirmed")

    def test_update_order_status_invalid(self):
        """Test updating order with invalid status"""
        # Create customer, product, and order
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        product_response = self.client.post("/products/", json=self.product_data)
        product_id = product_response.json()["id"]

        order_data = {
            "customer_id": customer_id,
            "order_items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": 29.99
                }
            ]
        }

        order_response = self.client.post("/orders/", json=order_data)
        order_id = order_response.json()["id"]

        # Try invalid status
        status_update = {"status": "invalid_status"}
        response = self.client.put(f"/orders/{order_id}/status", json=status_update)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid status", response.json()["detail"])

    def test_get_customer_orders(self):
        """Test getting orders for specific customer"""
        # Create customer and product
        customer_response = self.client.post("/customers/", json=self.customer_data)
        customer_id = customer_response.json()["id"]

        product_response = self.client.post("/products/", json=self.product_data)
        product_id = product_response.json()["id"]

        # Create multiple orders
        order_data = {
            "customer_id": customer_id,
            "order_items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": 29.99
                }
            ]
        }

        self.client.post("/orders/", json=order_data)
        self.client.post("/orders/", json=order_data)

        response = self.client.get(f"/customers/{customer_id}/orders")
        self.assertEqual(response.status_code, 200)

        orders = response.json()
        self.assertEqual(len(orders), 2)
        for order in orders:
            self.assertEqual(order["customer_id"], customer_id)


if __name__ == "__main__":
    unittest.main()
