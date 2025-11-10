"""
End-to-End Tests for the Complete E-Commerce System
Tests complete user workflows across all microservices

Run these tests with all services running:
docker-compose up -d
pytest tests/test_e2e.py
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
    """Wait for all services to be healthy"""
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


class TestCompleteOrderWorkflow:
    """End-to-end test of the complete order processing workflow
    This demonstrates E2E TESTING - testing the entire system workflow
    """

    def test_complete_successful_order_workflow(self, wait_for_services):
        """Complete workflow: User places order for product

        Scenario:
        1. Client verifies user exists
        2. Client checks product availability
        3. Client creates order
        4. Order Service validates user (calls User Service)
        5. Order Service checks inventory (calls Product Service)
        6. Order Service reserves product (calls Product Service)
        7. Order Service processes and stores order
        8. Client receives order confirmation
        """
        # Step 1: Verify user exists
        user_id = 1
        user_response = requests.get(f"{USER_SERVICE_URL}/api/users/{user_id}")
        assert user_response.status_code == 200
        user = user_response.json()
        print(f"✓ User found: {user['name']}")

        # Step 2: Check product availability
        product_id = 2  # Mouse
        product_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}")
        assert product_response.status_code == 200
        product = product_response.json()
        initial_stock = product['stock']
        print(f"✓ Product found: {product['name']}, Stock: {initial_stock}")

        # Verify sufficient stock
        quantity = 3
        stock_check = requests.get(
            f"{PRODUCT_SERVICE_URL}/api/products/{product_id}/check-stock",
            params={'quantity': quantity}
        )
        assert stock_check.status_code == 200
        assert stock_check.json()['available'] is True
        print(f"✓ Sufficient stock available for {quantity} units")

        # Step 3: Create order (this triggers all the inter-service calls)
        order_data = {
            'user_id': user_id,
            'product_id': product_id,
            'quantity': quantity
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)
        assert order_response.status_code == 201
        order = order_response.json()
        print(f"✓ Order created: Order ID {order['id']}")

        # Verify order details
        assert order['user_id'] == user_id
        assert order['product_id'] == product_id
        assert order['quantity'] == quantity
        assert order['status'] == 'CONFIRMED'
        assert order['total'] == quantity * product['price']
        print(f"✓ Order total: ${order['total']:.2f}")

        # Step 4: Verify inventory was reduced
        updated_product = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}").json()
        assert updated_product['stock'] == initial_stock - quantity
        print(f"✓ Inventory updated: {initial_stock} → {updated_product['stock']}")

        # Step 5: Verify order can be retrieved
        order_retrieval = requests.get(f"{ORDER_SERVICE_URL}/api/orders/{order['id']}")
        assert order_retrieval.status_code == 200
        retrieved_order = order_retrieval.json()
        assert retrieved_order['id'] == order['id']
        print(f"✓ Order can be retrieved successfully")

        print("\n✅ Complete order workflow test PASSED")

    def test_order_fails_with_inactive_user(self, wait_for_services):
        """E2E Test: Order should fail when user is inactive"""
        # User 3 is inactive
        order_data = {
            'user_id': 3,
            'product_id': 1,
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        # Should fail
        assert order_response.status_code == 400
        error = order_response.json()
        assert 'error' in error
        print(f"✓ Order correctly rejected for inactive user: {error['error']}")

    def test_order_fails_with_insufficient_stock(self, wait_for_services):
        """E2E Test: Order should fail when product has insufficient stock"""
        # Product 4 (Monitor) has 0 stock
        order_data = {
            'user_id': 1,
            'product_id': 4,
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        # Should fail
        assert order_response.status_code == 400
        error = order_response.json()
        assert 'error' in error
        print(f"✓ Order correctly rejected for out-of-stock product: {error['error']}")

    def test_order_fails_with_nonexistent_user(self, wait_for_services):
        """E2E Test: Order should fail when user doesn't exist"""
        order_data = {
            'user_id': 999,
            'product_id': 1,
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        assert order_response.status_code == 400
        print(f"✓ Order correctly rejected for non-existent user")

    def test_order_fails_with_nonexistent_product(self, wait_for_services):
        """E2E Test: Order should fail when product doesn't exist"""
        order_data = {
            'user_id': 1,
            'product_id': 999,
            'quantity': 1
        }
        order_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order_data)

        assert order_response.status_code == 400
        print(f"✓ Order correctly rejected for non-existent product")


class TestMultipleOrdersWorkflow:
    """E2E Test: Multiple orders affect inventory correctly"""

    def test_multiple_orders_reduce_inventory_correctly(self, wait_for_services):
        """Multiple orders should correctly reduce inventory"""
        product_id = 3  # Keyboard with 25 stock

        # Get initial stock
        initial_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}")
        initial_stock = initial_response.json()['stock']

        # Place first order
        order1_data = {'user_id': 1, 'product_id': product_id, 'quantity': 5}
        order1_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order1_data)
        assert order1_response.status_code == 201

        # Place second order
        order2_data = {'user_id': 2, 'product_id': product_id, 'quantity': 3}
        order2_response = requests.post(f"{ORDER_SERVICE_URL}/api/orders", json=order2_data)
        assert order2_response.status_code == 201

        # Verify total reduction
        final_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}")
        final_stock = final_response.json()['stock']

        assert final_stock == initial_stock - 8  # 5 + 3
        print(f"✓ Multiple orders correctly reduced inventory: {initial_stock} → {final_stock}")


class TestSystemHealth:
    """E2E Test: All services should be healthy"""

    def test_all_services_are_healthy(self, wait_for_services):
        """All microservices should report healthy status"""
        services = [
            (USER_SERVICE_URL, "user-service"),
            (PRODUCT_SERVICE_URL, "product-service"),
            (ORDER_SERVICE_URL, "order-service")
        ]

        for url, name in services:
            response = requests.get(f"{url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['service'] == name
            print(f"✓ {name} is healthy")
