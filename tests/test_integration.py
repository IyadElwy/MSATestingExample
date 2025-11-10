"""
Integration Tests for Microservices
Tests communication between services (Order Service -> Product/User Services)

Run these tests with all services running:
docker-compose up -d
pytest tests/test_integration.py
"""
import pytest
import requests
import time

# Service URLs
USER_SERVICE_URL = "http://localhost:5001"
PRODUCT_SERVICE_URL = "http://localhost:5002"
ORDER_SERVICE_URL = "http://localhost:5003"


@pytest.fixture(scope="module")
def wait_for_services():
    """Wait for all services to be healthy before running tests"""
    services = [
        (USER_SERVICE_URL, "user-service"),
        (PRODUCT_SERVICE_URL, "product-service"),
        (ORDER_SERVICE_URL, "order-service")
    ]

    for url, name in services:
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ {name} is healthy")
                    break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    pytest.fail(f"{name} did not become healthy in time")
                time.sleep(1)


class TestOrderServiceIntegration:
    """Integration tests for Order Service with real service calls"""

    def test_order_service_calls_user_service_successfully(self, wait_for_services):
        """Order Service should successfully validate user via User Service
        This demonstrates INTEGRATION TESTING - testing service-to-service communication
        """
        # First, verify user exists in User Service
        user_response = requests.get(f"{USER_SERVICE_URL}/api/users/1")
        assert user_response.status_code == 200

        # Create an order that will trigger Order Service to call User Service
        order_data = {
            'user_id': 1,
            'product_id': 1,
            'quantity': 2
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        # Should succeed because user exists
        assert order_response.status_code == 201
        order = order_response.json()
        assert order['user_id'] == 1

    def test_order_service_calls_product_service_successfully(self, wait_for_services):
        """Order Service should successfully check inventory via Product Service"""
        # First, verify product exists
        product_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/2")
        assert product_response.status_code == 200
        product = product_response.json()
        initial_stock = product['stock']

        # Create an order that will trigger Order Service to call Product Service
        order_data = {
            'user_id': 1,
            'product_id': 2,
            'quantity': 3
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        assert order_response.status_code == 201

        # Verify that Product Service stock was actually reduced
        updated_product_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/2")
        updated_product = updated_product_response.json()
        assert updated_product['stock'] == initial_stock - 3

    def test_order_service_handles_invalid_user_from_user_service(self, wait_for_services):
        """Order Service should handle invalid user response from User Service"""
        # Try to create order with non-existent user
        order_data = {
            'user_id': 999,
            'product_id': 1,
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        # Should fail with 400 because user doesn't exist
        assert order_response.status_code == 400
        error = order_response.json()
        assert 'error' in error

    def test_order_service_handles_insufficient_stock_from_product_service(self, wait_for_services):
        """Order Service should handle insufficient stock response from Product Service"""
        # Try to order product with 0 stock
        order_data = {
            'user_id': 1,
            'product_id': 4,  # Monitor with 0 stock
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        # Should fail with 400 because insufficient stock
        assert order_response.status_code == 400

    def test_order_service_handles_inactive_user(self, wait_for_services):
        """Order Service should reject order from inactive user"""
        # User 3 is inactive
        order_data = {
            'user_id': 3,
            'product_id': 1,
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        assert order_response.status_code == 400
        error = order_response.json()
        assert 'inactive' in error['error'].lower()


class TestProductServiceIntegration:
    """Integration tests for Product Service"""

    def test_reserve_product_reduces_inventory(self, wait_for_services):
        """Reserving a product should reduce its inventory count"""
        # Get initial stock
        product_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/3")
        initial_stock = product_response.json()['stock']

        # Reserve some quantity
        reserve_data = {'quantity': 5}
        reserve_response = requests.put(
            f"{PRODUCT_SERVICE_URL}/api/products/3/reserve",
            json=reserve_data
        )

        assert reserve_response.status_code == 200
        reservation = reserve_response.json()
        assert reservation['status'] == 'RESERVED'

        # Verify stock was reduced
        updated_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/3")
        new_stock = updated_response.json()['stock']
        assert new_stock == initial_stock - 5


class TestUserServiceIntegration:
    """Integration tests for User Service"""

    def test_validate_user_endpoint_integration(self, wait_for_services):
        """User validation endpoint should work correctly"""
        # Test active user
        response = requests.get(f"{USER_SERVICE_URL}/api/users/1/validate")
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is True

        # Test inactive user
        response = requests.get(f"{USER_SERVICE_URL}/api/users/3/validate")
        assert response.status_code == 200
        data = response.json()
        assert data['valid'] is False
