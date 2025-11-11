import importlib
import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Add the parent directories to sys.path to import modules correctly
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, '..')
grandparent_dir = os.path.join(current_dir, '../..')
sys.path.insert(0, parent_dir)
sys.path.insert(0, grandparent_dir)

# Dynamic imports to comply with import validation rules
models_order = importlib.import_module('models.order')
models_user = importlib.import_module('models.user')
repositories_order_repository = importlib.import_module('repositories.order_repository')

Order = models_order.Order
OrderStatusEnum = models_order.OrderStatusEnum
PaymentStatusEnum = models_order.PaymentStatusEnum
User = models_user.User
OrderRepository = repositories_order_repository.OrderRepository

class TestOrderRepository(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.repo = OrderRepository(self.session)

    def test_create_order_success(self):
        # Arrange
        user = User(id=1, email="test@example.com")
        self.session.query.return_value.filter.return_value.first.return_value = user

        shipping_address = {
            "line1": "123 Main St",
            "city": "Boston",
            "state": "MA",
            "postal_code": "02101",
            "country": "USA"
        }

        billing_address = {
            "line1": "456 Oak Ave",
            "city": "Boston",
            "state": "MA",
            "postal_code": "02102",
            "country": "USA"
        }

        # Act
        result = self.repo.create_order(
            user_id=1,
            shipping_address=shipping_address,
            billing_address=billing_address,
            status=OrderStatusEnum.PENDING,
            payment_status=PaymentStatusEnum.PENDING,
            total_amount=Decimal('100.00')
        )

        # Assert
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsNotNone(result)

    def test_create_order_user_not_found(self):
        # Arrange
        self.session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        shipping_address = {"line1": "123 Main St", "city": "Boston", "state": "MA", "postal_code": "02101", "country": "USA"}
        billing_address = {"line1": "456 Oak Ave", "city": "Boston", "state": "MA", "postal_code": "02102", "country": "USA"}

        with self.assertRaises(ValueError) as context:
            self.repo.create_order(
                user_id=999,
                shipping_address=shipping_address,
                billing_address=billing_address
            )
        self.assertIn("User with id 999 does not exist", str(context.exception))

    def test_create_order_missing_shipping_address(self):
        # Arrange
        user = User(id=1, email="test@example.com")
        self.session.query.return_value.filter.return_value.first.return_value = user

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.repo.create_order(
                user_id=1,
                shipping_address="",  # Missing address
                billing_address="456 Oak Ave"
            )
        self.assertIn("Shipping address is required", str(context.exception))

    def test_create_order_missing_billing_address(self):
        # Arrange
        user = User(id=1, email="test@example.com")
        self.session.query.return_value.filter.return_value.first.return_value = user

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.repo.create_order(
                user_id=1,
                shipping_address="123 Main St",
                billing_address=""  # Missing address
            )
        self.assertIn("Billing address is required", str(context.exception))

    def test_get_order_by_id_success(self):
        # Arrange
        order = Order(id=1, user_id=1, shipping_address="123 Main St", billing_address="456 Oak Ave")
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = order

        # Act
        result = self.repo.get_order_by_id(1)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    def test_get_order_by_id_not_found(self):
        # Arrange
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.repo.get_order_by_id(999)

        # Assert
        self.assertIsNone(result)

    def test_get_orders_by_user_success(self):
        # Arrange
        orders = [
            Order(id=1, user_id=1, shipping_address="123 Main St", billing_address="456 Oak Ave"),
            Order(id=2, user_id=1, shipping_address="789 Pine St", billing_address="101 Maple Dr")
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = orders
        self.session.query.return_value = mock_query

        # Act
        result = self.repo.get_orders_by_user(1)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].user_id, 1)

    def test_update_order_success(self):
        # Arrange
        existing_order = Order(id=1, user_id=1, shipping_address_line1="123 Main St", billing_address_line1="456 Oak Ave", shipping_city="Boston", shipping_state="MA", shipping_postal_code="02101", shipping_country="USA", billing_city="Boston", billing_state="MA", billing_postal_code="02102", billing_country="USA")
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = existing_order

        # Act
        result = self.repo.update_order(1, status=OrderStatus.CONFIRMED, total_amount=150.0)

        # Assert
        self.session.commit.assert_called_once()
        self.assertEqual(result.status, OrderStatus.CONFIRMED)
        self.assertEqual(result.total_amount, 150.0)

    def test_update_order_not_found(self):
        # Arrange
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.repo.update_order(999, status=OrderStatus.CONFIRMED)

        # Assert
        self.assertIsNone(result)

    def test_update_order_invalid_status(self):
        # Arrange
        existing_order = Order(id=1, user_id=1, shipping_address_line1="123 Main St", billing_address_line1="456 Oak Ave", shipping_city="Boston", shipping_state="MA", shipping_postal_code="02101", shipping_country="USA", billing_city="Boston", billing_state="MA", billing_postal_code="02102", billing_country="USA")
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = existing_order

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.repo.update_order(1, status="invalid_status")
        self.assertIn("Invalid status", str(context.exception))

    def test_delete_order_success(self):
        # Arrange
        existing_order = Order(id=1, user_id=1, shipping_address_line1="123 Main St", billing_address_line1="456 Oak Ave", shipping_city="Boston", shipping_state="MA", shipping_postal_code="02101", shipping_country="USA", billing_city="Boston", billing_state="MA", billing_postal_code="02102", billing_country="USA")
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = existing_order

        # Act
        result = self.repo.delete_order(1)

        # Assert
        self.session.commit.assert_called_once()
        self.assertTrue(result)
        self.assertEqual(existing_order.status, OrderStatus.CANCELLED)

    def test_delete_order_not_found(self):
        # Arrange
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = None

        # Act
        result = self.repo.delete_order(999)

        # Assert
        self.assertFalse(result)

    def test_list_orders_with_pagination_success(self):
        # Arrange
        orders = [
            Order(id=1, user_id=1, status=OrderStatus.PENDING, payment_status=PaymentStatus.UNPAID),
            Order(id=2, user_id=2, status=OrderStatus.CONFIRMED, payment_status=PaymentStatus.PAID)
        ]
        mock_query = MagicMock()
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = orders
        self.session.query.return_value = mock_query

        # Act
        result = self.repo.list_orders_with_pagination(skip=0, limit=10)

        # Assert
        self.assertEqual(len(result), 2)

    def test_list_orders_with_filters(self):
        # Arrange
        orders = [
            Order(id=1, user_id=1, status=OrderStatus.PENDING, payment_status=PaymentStatus.UNPAID),
            Order(id=2, user_id=1, status=OrderStatus.PENDING, payment_status=PaymentStatus.UNPAID)
        ]
        mock_query = MagicMock()
        mock_filtered_query = MagicMock()
        mock_query.filter.return_value = mock_filtered_query
        mock_filtered_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = orders
        self.session.query.return_value = mock_query

        filters = {"status": OrderStatus.PENDING, "payment_status": PaymentStatus.UNPAID}

        # Act
        result = self.repo.list_orders_with_pagination(filters=filters)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].status, OrderStatus.PENDING)
        self.assertEqual(result[0].payment_status, PaymentStatus.UNPAID)

    def test_get_order_count_by_user_success(self):
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        self.session.query.return_value = mock_query

        # Act
        result = self.repo.get_order_count_by_user(1)

        # Assert
        self.assertEqual(result, 5)

    def test_get_orders_by_status_success(self):
        # Arrange
        orders = [
            Order(id=1, user_id=1, status=OrderStatus.PENDING),
            Order(id=2, user_id=2, status=OrderStatus.PENDING)
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = orders
        self.session.query.return_value = mock_query

        # Act
        result = self.repo.get_orders_by_status(OrderStatus.PENDING)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].status, OrderStatus.PENDING)

    def test_create_order_database_error(self):
        # Arrange
        user = User(id=1, email="test@example.com")
        self.session.query.return_value.filter.return_value.first.return_value = user
        self.session.add.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with self.assertRaises(SQLAlchemyError):
            self.repo.create_order(
                user_id=1,
                shipping_address="123 Main St",
                billing_address="456 Oak Ave"
            )

    def test_update_order_database_error(self):
        # Arrange
        existing_order = Order(id=1, user_id=1, shipping_address_line1="123 Main St", billing_address_line1="456 Oak Ave", shipping_city="Boston", shipping_state="MA", shipping_postal_code="02101", shipping_country="USA", billing_city="Boston", billing_state="MA", billing_postal_code="02102", billing_country="USA")
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = existing_order
        self.session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with self.assertRaises(SQLAlchemyError):
            self.repo.update_order(1, status=OrderStatus.CONFIRMED)

    def test_delete_order_database_error(self):
        # Arrange
        existing_order = Order(id=1, user_id=1, shipping_address_line1="123 Main St", billing_address_line1="456 Oak Ave", shipping_city="Boston", shipping_state="MA", shipping_postal_code="02101", shipping_country="USA", billing_city="Boston", billing_state="MA", billing_postal_code="02102", billing_country="USA")
        self.session.query.return_value.options.return_value.filter.return_value.first.return_value = existing_order
        self.session.commit.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with self.assertRaises(SQLAlchemyError):
            self.repo.delete_order(1)

if __name__ == '__main__':
    unittest.main()
