"""
End-to-End Tests for Microservices Architecture
Tests the complete order workflow with all services running together
"""
import pytest
import requests
import time
from multiprocessing import Process
import sys
import os

# Add service directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'user-service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product-service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'order-service'))


# Service URLs
USER_SERVICE_URL = 'http://localhost:5001'
PRODUCT_SERVICE_URL = 'http://localhost:5002'
ORDER_SERVICE_URL = 'http://localhost:5003'


def start_user_service():
    """Start user service on port 5001"""
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'user-service'))
    from app import app
    app.run(host='0.0.0.0', port=5001, debug=False)


def start_product_service():
    """Start product service on port 5002"""
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'product-service'))
    from app import app
    app.run(host='0.0.0.0', port=5002, debug=False)


def start_order_service():
    """Start order service on port 5003"""
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'order-service'))
    os.environ['USER_SERVICE_URL'] = USER_SERVICE_URL
    os.environ['PRODUCT_SERVICE_URL'] = PRODUCT_SERVICE_URL
    from app import app
    app.run(host='0.0.0.0', port=5003, debug=False)


@pytest.fixture(scope='module')
def services():
    """Start all microservices for e2e testing"""
    # Start services in separate processes
    user_process = Process(target=start_user_service)
    product_process = Process(target=start_product_service)
    order_process = Process(target=start_order_service)

    user_process.start()
    product_process.start()
    order_process.start()

    # Wait for services to be ready
    time.sleep(3)

    # Verify services are healthy
    max_retries = 10
    for i in range(max_retries):
        try:
            requests.get(f'{USER_SERVICE_URL}/health', timeout=1)
            requests.get(f'{PRODUCT_SERVICE_URL}/health', timeout=1)
            requests.get(f'{ORDER_SERVICE_URL}/health', timeout=1)
            break
        except:
            if i == max_retries - 1:
                raise Exception("Services failed to start")
            time.sleep(1)

    yield

    # Cleanup
    user_process.terminate()
    product_process.terminate()
    order_process.terminate()
    user_process.join()
    product_process.join()
    order_process.join()


class TestEndToEndOrderFlow:
    """Test complete order flow across all services"""

    def test_complete_successful_order_flow(self, services):
        """E2E: Complete order flow - user validation, stock check, and order creation"""
        # Step 1: Verify user exists and is active
        user_id = 1
        user_response = requests.get(f'{USER_SERVICE_URL}/api/users/{user_id}')
        assert user_response.status_code == 200
        user = user_response.json()
        assert user['active'] is True

        # Step 2: Verify product exists and has stock
        product_id = 1
        product_response = requests.get(f'{PRODUCT_SERVICE_URL}/api/products/{product_id}')
        assert product_response.status_code == 200
        product = product_response.json()
        initial_stock = product['stock']
        assert initial_stock > 0

        # Step 3: Check product stock availability
        quantity = 2
        stock_check_response = requests.get(
            f'{PRODUCT_SERVICE_URL}/api/products/{product_id}/check-stock',
            params={'quantity': quantity}
        )
        assert stock_check_response.status_code == 200
        stock_data = stock_check_response.json()
        assert stock_data['available'] is True

        # Step 4: Create order (this will validate user, check stock, and reserve product)
        order_data = {
            'user_id': user_id,
            'product_id': product_id,
            'quantity': quantity
        }
        order_response = requests.post(f'{ORDER_SERVICE_URL}/api/orders', json=order_data)
        assert order_response.status_code == 201
        order = order_response.json()

        # Step 5: Verify order details
        assert order['user_id'] == user_id
        assert order['product_id'] == product_id
        assert order['quantity'] == quantity
        assert order['status'] == 'CONFIRMED'
        assert order['total'] == quantity * product['price']

        # Step 6: Verify product stock was reduced
        updated_product_response = requests.get(f'{PRODUCT_SERVICE_URL}/api/products/{product_id}')
        updated_product = updated_product_response.json()
        assert updated_product['stock'] == initial_stock - quantity

        # Step 7: Verify order can be retrieved
        order_id = order['id']
        get_order_response = requests.get(f'{ORDER_SERVICE_URL}/api/orders/{order_id}')
        assert get_order_response.status_code == 200
        retrieved_order = get_order_response.json()
        assert retrieved_order['id'] == order_id

    def test_order_fails_with_inactive_user(self, services):
        """E2E: Order should fail when user is inactive"""
        # User ID 3 is inactive
        inactive_user_id = 3

        # Verify user is inactive
        user_response = requests.get(f'{USER_SERVICE_URL}/api/users/{inactive_user_id}/validate')
        assert user_response.status_code == 200
        validation = user_response.json()
        assert validation['valid'] is False

        # Try to create order with inactive user
        order_data = {
            'user_id': inactive_user_id,
            'product_id': 1,
            'quantity': 1
        }
        order_response = requests.post(f'{ORDER_SERVICE_URL}/api/orders', json=order_data)

        # Verify order creation fails
        assert order_response.status_code == 400
        error_data = order_response.json()
        assert 'error' in error_data

    def test_order_fails_with_out_of_stock_product(self, services):
        """E2E: Order should fail when product is out of stock"""
        # Product ID 4 has 0 stock
        out_of_stock_product_id = 4

        # Verify product is out of stock
        product_response = requests.get(f'{PRODUCT_SERVICE_URL}/api/products/{out_of_stock_product_id}')
        product = product_response.json()
        assert product['stock'] == 0

        # Try to create order
        order_data = {
            'user_id': 1,
            'product_id': out_of_stock_product_id,
            'quantity': 1
        }
        order_response = requests.post(f'{ORDER_SERVICE_URL}/api/orders', json=order_data)

        # Verify order creation fails
        assert order_response.status_code == 400
        error_data = order_response.json()
        assert 'error' in error_data

    def test_order_fails_with_insufficient_stock(self, services):
        """E2E: Order should fail when requested quantity exceeds available stock"""
        product_id = 2  # Mouse with 50 stock

        # Get current stock
        product_response = requests.get(f'{PRODUCT_SERVICE_URL}/api/products/{product_id}')
        product = product_response.json()
        available_stock = product['stock']

        # Try to order more than available
        excessive_quantity = available_stock + 10
        order_data = {
            'user_id': 1,
            'product_id': product_id,
            'quantity': excessive_quantity
        }
        order_response = requests.post(f'{ORDER_SERVICE_URL}/api/orders', json=order_data)

        # Verify order creation fails
        assert order_response.status_code == 400

    def test_create_new_user_and_place_order(self, services):
        """E2E: Create a new user and immediately place an order"""
        # Step 1: Create a new user
        new_user = {
            'name': 'Test User',
            'email': 'testuser@example.com',
            'active': True
        }
        user_response = requests.post(f'{USER_SERVICE_URL}/api/users', json=new_user)
        assert user_response.status_code == 201
        user = user_response.json()
        new_user_id = user['id']

        # Step 2: Place an order with the new user
        order_data = {
            'user_id': new_user_id,
            'product_id': 2,
            'quantity': 1
        }
        order_response = requests.post(f'{ORDER_SERVICE_URL}/api/orders', json=order_data)
        assert order_response.status_code == 201
        order = order_response.json()
        assert order['user_id'] == new_user_id
        assert order['status'] == 'CONFIRMED'

    def test_multiple_concurrent_orders_reduce_stock_correctly(self, services):
        """E2E: Multiple orders should correctly reduce product stock"""
        product_id = 3  # Keyboard with 25 stock

        # Get initial stock
        product_response = requests.get(f'{PRODUCT_SERVICE_URL}/api/products/{product_id}')
        initial_stock = product_response.json()['stock']

        # Place multiple orders
        orders_to_place = [
            {'user_id': 1, 'product_id': product_id, 'quantity': 2},
            {'user_id': 2, 'product_id': product_id, 'quantity': 3},
            {'user_id': 1, 'product_id': product_id, 'quantity': 1}
        ]

        total_ordered = 0
        for order_data in orders_to_place:
            order_response = requests.post(f'{ORDER_SERVICE_URL}/api/orders', json=order_data)
            assert order_response.status_code == 201
            total_ordered += order_data['quantity']

        # Verify final stock
        final_product_response = requests.get(f'{PRODUCT_SERVICE_URL}/api/products/{product_id}')
        final_stock = final_product_response.json()['stock']
        assert final_stock == initial_stock - total_ordered


class TestServiceHealth:
    """Test that all services are healthy"""

    def test_all_services_healthy(self, services):
        """E2E: Verify all services respond to health checks"""
        # Check user service
        user_health = requests.get(f'{USER_SERVICE_URL}/health')
        assert user_health.status_code == 200
        assert user_health.json()['status'] == 'healthy'

        # Check product service
        product_health = requests.get(f'{PRODUCT_SERVICE_URL}/health')
        assert product_health.status_code == 200
        assert product_health.json()['status'] == 'healthy'

        # Check order service
        order_health = requests.get(f'{ORDER_SERVICE_URL}/health')
        assert order_health.status_code == 200
        assert order_health.json()['status'] == 'healthy'
