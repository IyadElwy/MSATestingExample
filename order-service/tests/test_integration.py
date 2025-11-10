"""
Integration Tests for Order Service
Tests interactions with User and Product services using mocked HTTP calls
"""
import pytest
import sys
import os
from unittest.mock import patch, Mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, orders_db, calculate_order_total


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the database before each test"""
    orders_db.clear()


class TestOrderServiceIntegration:
    """Test order service with mocked external service calls"""

    @patch('app.requests.get')
    @patch('app.requests.put')
    def test_successful_order_creation_workflow(self, mock_put, mock_get, client):
        """Integration test: Create order with mocked external services"""
        # Mock user validation
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            'valid': True,
            'user': {'id': 1, 'name': 'Alice', 'active': True}
        }

        # Mock product stock check
        mock_stock_response = Mock()
        mock_stock_response.status_code = 200
        mock_stock_response.json.return_value = {
            'available': True,
            'product_id': 1,
            'current_stock': 10
        }

        # Mock product details
        mock_product_response = Mock()
        mock_product_response.status_code = 200
        mock_product_response.json.return_value = {
            'id': 1,
            'name': 'Laptop',
            'price': 999.99,
            'stock': 10
        }

        # Mock product reservation
        mock_reserve_response = Mock()
        mock_reserve_response.status_code = 200
        mock_reserve_response.json.return_value = {
            'status': 'RESERVED',
            'remaining_stock': 8
        }

        # Configure mock to return different responses for different URLs
        def get_side_effect(url, *args, **kwargs):
            if 'validate' in url:
                return mock_user_response
            elif 'check-stock' in url:
                return mock_stock_response
            else:
                return mock_product_response

        mock_get.side_effect = get_side_effect
        mock_put.return_value = mock_reserve_response

        # Create order
        order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 2
        }
        response = client.post('/api/orders', json=order_data)

        # Verify response
        assert response.status_code == 201
        order = response.get_json()
        assert order['user_id'] == 1
        assert order['product_id'] == 1
        assert order['quantity'] == 2
        assert order['total'] == 1999.98  # 2 * 999.99
        assert order['status'] == 'CONFIRMED'

    @patch('app.requests.get')
    def test_order_fails_with_invalid_user(self, mock_get, client):
        """Integration test: Order creation fails when user is invalid"""
        # Mock user validation failure
        mock_user_response = Mock()
        mock_user_response.status_code = 404
        mock_user_response.json.return_value = {
            'valid': False,
            'reason': 'User not found'
        }
        mock_get.return_value = mock_user_response

        # Try to create order
        order_data = {
            'user_id': 999,
            'product_id': 1,
            'quantity': 1
        }
        response = client.post('/api/orders', json=order_data)

        # Verify failure
        assert response.status_code == 400
        error_data = response.get_json()
        assert 'error' in error_data
        assert 'User validation failed' in error_data['error']

    @patch('app.requests.get')
    def test_order_fails_with_insufficient_stock(self, mock_get, client):
        """Integration test: Order creation fails when product out of stock"""
        # Mock user validation success
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            'valid': True,
            'user': {'id': 1, 'name': 'Alice'}
        }

        # Mock product stock check failure
        mock_stock_response = Mock()
        mock_stock_response.status_code = 200
        mock_stock_response.json.return_value = {
            'available': False,
            'product_id': 1,
            'current_stock': 0
        }

        def get_side_effect(url, *args, **kwargs):
            if 'validate' in url:
                return mock_user_response
            else:
                return mock_stock_response

        mock_get.side_effect = get_side_effect

        # Try to create order
        order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 1
        }
        response = client.post('/api/orders', json=order_data)

        # Verify failure
        assert response.status_code == 400
        error_data = response.get_json()
        assert 'Product check failed' in error_data['error']

    @patch('app.requests.get')
    @patch('app.requests.put')
    def test_order_fails_when_reservation_fails(self, mock_put, mock_get, client):
        """Integration test: Order creation fails when product reservation fails"""
        # Mock successful validation and stock check
        mock_user_response = Mock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {'valid': True, 'user': {'id': 1}}

        mock_stock_response = Mock()
        mock_stock_response.status_code = 200
        mock_stock_response.json.return_value = {'available': True, 'current_stock': 10}

        mock_product_response = Mock()
        mock_product_response.status_code = 200
        mock_product_response.json.return_value = {'id': 1, 'price': 99.99, 'stock': 10}

        def get_side_effect(url, *args, **kwargs):
            if 'validate' in url:
                return mock_user_response
            elif 'check-stock' in url:
                return mock_stock_response
            else:
                return mock_product_response

        mock_get.side_effect = get_side_effect

        # Mock reservation failure
        mock_reserve_response = Mock()
        mock_reserve_response.status_code = 400
        mock_reserve_response.json.return_value = {'error': 'Reservation failed'}
        mock_put.return_value = mock_reserve_response

        # Try to create order
        order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 1
        }
        response = client.post('/api/orders', json=order_data)

        # Verify failure
        assert response.status_code == 500
        error_data = response.get_json()
        assert 'Failed to reserve product' in error_data['error']


class TestOrderCalculations:
    """Test order calculation business logic"""

    def test_calculate_order_total(self):
        """Test order total calculation"""
        assert calculate_order_total(2, 10.50) == 21.00
        assert calculate_order_total(5, 99.99) == 499.95
        assert calculate_order_total(1, 1500.00) == 1500.00
