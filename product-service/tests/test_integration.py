"""
Integration Tests for Product Service
Tests the service behavior with real HTTP calls and state management
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, products_db


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the database before each test"""
    products_db.clear()
    products_db.update({
        1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
        2: {"id": 2, "name": "Mouse", "price": 29.99, "stock": 50},
        3: {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 25},
        4: {"id": 4, "name": "Monitor", "price": 299.99, "stock": 0}
    })


class TestProductWorkflow:
    """Test complete product management workflows"""

    def test_check_stock_and_reserve_workflow(self, client):
        """Integration test: Check stock availability then reserve product"""
        product_id = 1
        quantity = 5

        # Step 1: Check stock availability
        check_response = client.get(f'/api/products/{product_id}/check-stock?quantity={quantity}')
        assert check_response.status_code == 200
        check_data = check_response.get_json()
        assert check_data['available'] is True
        initial_stock = check_data['current_stock']

        # Step 2: Reserve the product
        reserve_response = client.put(f'/api/products/{product_id}/reserve', json={'quantity': quantity})
        assert reserve_response.status_code == 200
        reserve_data = reserve_response.get_json()

        # Step 3: Verify reservation
        assert reserve_data['status'] == 'RESERVED'
        assert reserve_data['reserved_qty'] == quantity
        assert reserve_data['remaining_stock'] == initial_stock - quantity

        # Step 4: Verify stock was actually reduced
        get_response = client.get(f'/api/products/{product_id}')
        product = get_response.get_json()
        assert product['stock'] == initial_stock - quantity

    def test_insufficient_stock_workflow(self, client):
        """Integration test: Try to reserve more than available stock"""
        product_id = 1
        excessive_quantity = 100  # More than available

        # Step 1: Check stock - should show not available
        check_response = client.get(f'/api/products/{product_id}/check-stock?quantity={excessive_quantity}')
        assert check_response.status_code == 200
        check_data = check_response.get_json()
        assert check_data['available'] is False

        # Step 2: Try to reserve anyway - should fail
        reserve_response = client.put(f'/api/products/{product_id}/reserve', json={'quantity': excessive_quantity})
        assert reserve_response.status_code == 400
        error_data = reserve_response.get_json()
        assert 'error' in error_data
        assert 'Insufficient stock' in error_data['error']

    def test_out_of_stock_product_workflow(self, client):
        """Integration test: Handle out of stock product"""
        product_id = 4  # Monitor with 0 stock

        # Step 1: Check product exists
        get_response = client.get(f'/api/products/{product_id}')
        assert get_response.status_code == 200
        product = get_response.get_json()
        assert product['stock'] == 0

        # Step 2: Check stock availability
        check_response = client.get(f'/api/products/{product_id}/check-stock?quantity=1')
        assert check_response.status_code == 200
        check_data = check_response.get_json()
        assert check_data['available'] is False

        # Step 3: Try to reserve - should fail
        reserve_response = client.put(f'/api/products/{product_id}/reserve', json={'quantity': 1})
        assert reserve_response.status_code == 400

    def test_create_and_reserve_new_product_workflow(self, client):
        """Integration test: Create a product and immediately reserve it"""
        # Step 1: Create a new product
        new_product = {
            'name': 'Webcam',
            'price': 89.99,
            'stock': 15
        }
        create_response = client.post('/api/products', json=new_product)
        assert create_response.status_code == 201
        product_id = create_response.get_json()['id']

        # Step 2: Check stock of new product
        check_response = client.get(f'/api/products/{product_id}/check-stock?quantity=3')
        assert check_response.status_code == 200
        assert check_response.get_json()['available'] is True

        # Step 3: Reserve from new product
        reserve_response = client.put(f'/api/products/{product_id}/reserve', json={'quantity': 3})
        assert reserve_response.status_code == 200
        assert reserve_response.get_json()['remaining_stock'] == 12

    def test_multiple_reservations_workflow(self, client):
        """Integration test: Multiple sequential reservations reduce stock correctly"""
        product_id = 2  # Mouse with 50 stock

        # Get initial stock
        get_response = client.get(f'/api/products/{product_id}')
        initial_stock = get_response.get_json()['stock']

        # Make multiple reservations
        reservations = [5, 10, 8]
        for quantity in reservations:
            reserve_response = client.put(f'/api/products/{product_id}/reserve', json={'quantity': quantity})
            assert reserve_response.status_code == 200

        # Verify final stock
        final_response = client.get(f'/api/products/{product_id}')
        final_stock = final_response.get_json()['stock']
        assert final_stock == initial_stock - sum(reservations)
