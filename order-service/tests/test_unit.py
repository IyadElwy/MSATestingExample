"""
Unit Tests for Order Service
Tests individual functions in isolation using mocks for external dependencies
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, orders_db, calculate_order_total
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the orders database before each test"""
    orders_db.clear()


class TestBusinessLogic:
    """Test pure business logic functions (no HTTP dependencies)
    This demonstrates UNIT TESTING - testing isolated functions
    """

    def test_calculate_order_total_basic(self):
        """Calculate total: 2 * 50.00 = 100.00"""
        total = calculate_order_total(2, 50.00)
        assert total == 100.00

    def test_calculate_order_total_with_decimal(self):
        """Calculate total with decimal prices"""
        total = calculate_order_total(3, 29.99)
        assert total == pytest.approx(89.97)

    def test_calculate_order_total_single_item(self):
        """Calculate total for single item"""
        total = calculate_order_total(1, 999.99)
        assert total == 999.99

    def test_calculate_order_total_large_quantity(self):
        """Calculate total for large quantity"""
        total = calculate_order_total(100, 10.50)
        assert total == 1050.00


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check_returns_200(self, client):
        """Health check should return 200 OK"""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_check_returns_correct_data(self, client):
        """Health check should return service status"""
        response = client.get('/health')
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'order-service'


class TestGetOrders:
    """Test get orders endpoints"""

    def test_get_all_orders_returns_200(self, client):
        """GET /api/orders should return 200 OK"""
        response = client.get('/api/orders')
        assert response.status_code == 200

    def test_get_all_orders_returns_empty_list(self, client):
        """GET /api/orders should return empty list initially"""
        response = client.get('/api/orders')
        data = response.get_json()
        assert 'orders' in data
        assert len(data['orders']) == 0

    def test_get_nonexistent_order_returns_404(self, client):
        """GET /api/orders/999 should return 404"""
        response = client.get('/api/orders/999')
        assert response.status_code == 404


class TestCreateOrderWithMocks:
    """Test order creation with mocked external services
    This demonstrates MOCKING - isolating the service under test
    """

    @patch('app.requests.get')
    @patch('app.requests.put')
    def test_create_order_with_valid_data_returns_201(self, mock_put, mock_get, client):
        """Creating order with valid data should return 201 Created"""
        # Mock User Service validation response
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            'valid': True,
            'user': {'id': 1, 'name': 'Alice Smith', 'email': 'alice@example.com'}
        }

        # Mock Product Service stock check response
        mock_stock_response = MagicMock()
        mock_stock_response.status_code = 200
        mock_stock_response.json.return_value = {
            'available': True,
            'product_id': 1,
            'current_stock': 10
        }

        # Mock Product Service get product response
        mock_product_response = MagicMock()
        mock_product_response.status_code = 200
        mock_product_response.json.return_value = {
            'id': 1,
            'name': 'Laptop',
            'price': 999.99,
            'stock': 10
        }

        # Mock Product Service reserve response
        mock_reserve_response = MagicMock()
        mock_reserve_response.status_code = 200
        mock_reserve_response.json.return_value = {
            'status': 'RESERVED',
            'product_id': 1,
            'reserved_qty': 2
        }

        # Configure mock responses in order
        mock_get.side_effect = [mock_user_response, mock_stock_response, mock_product_response]
        mock_put.return_value = mock_reserve_response

        # Create order
        order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 2
        }
        response = client.post('/api/orders', json=order_data)

        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'CONFIRMED'
        assert data['total'] == pytest.approx(1999.98)

    @patch('app.requests.get')
    def test_create_order_with_invalid_user_returns_400(self, mock_get, client):
        """Creating order with invalid user should return 400"""
        # Mock User Service validation response (user not found)
        mock_user_response = MagicMock()
        mock_user_response.status_code = 404
        mock_user_response.json.return_value = {
            'valid': False,
            'reason': 'User not found'
        }
        mock_get.return_value = mock_user_response

        order_data = {
            'user_id': 999,
            'product_id': 1,
            'quantity': 2
        }
        response = client.post('/api/orders', json=order_data)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('app.requests.get')
    def test_create_order_with_insufficient_stock_returns_400(self, mock_get, client):
        """Creating order with insufficient stock should return 400"""
        # Mock User Service validation (valid)
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            'valid': True,
            'user': {'id': 1, 'name': 'Alice'}
        }

        # Mock Product Service stock check (insufficient)
        mock_stock_response = MagicMock()
        mock_stock_response.status_code = 200
        mock_stock_response.json.return_value = {
            'available': False,
            'product_id': 1,
            'current_stock': 1
        }

        mock_get.side_effect = [mock_user_response, mock_stock_response]

        order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 100
        }
        response = client.post('/api/orders', json=order_data)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_create_order_without_required_fields_returns_400(self, client):
        """Creating order without required fields should return 400"""
        invalid_data = {'user_id': 1}  # Missing product_id and quantity
        response = client.post('/api/orders', json=invalid_data)
        assert response.status_code == 400
