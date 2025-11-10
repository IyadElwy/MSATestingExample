"""
Unit Tests for Product Service
Tests individual functions and endpoints in isolation
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, products_db, calculate_product_total


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


class TestBusinessLogic:
    """Test pure business logic functions (no HTTP dependencies)"""

    def test_calculate_product_total_basic(self):
        """Calculate total: 2 * 50.00 = 100.00"""
        total = calculate_product_total(2, 50.00)
        assert total == 100.00

    def test_calculate_product_total_with_decimal(self):
        """Calculate total with decimal prices"""
        total = calculate_product_total(3, 29.99)
        assert total == pytest.approx(89.97)

    def test_calculate_product_total_single_item(self):
        """Calculate total for single item"""
        total = calculate_product_total(1, 999.99)
        assert total == 999.99


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
        assert data['service'] == 'product-service'


class TestGetAllProducts:
    """Test get all products endpoint"""

    def test_get_all_products_returns_200(self, client):
        """GET /api/products should return 200 OK"""
        response = client.get('/api/products')
        assert response.status_code == 200

    def test_get_all_products_returns_product_list(self, client):
        """GET /api/products should return list of products"""
        response = client.get('/api/products')
        data = response.get_json()
        assert 'products' in data
        assert len(data['products']) == 4


class TestGetProduct:
    """Test get product by ID endpoint"""

    def test_get_existing_product_returns_200(self, client):
        """GET /api/products/1 should return 200 OK"""
        response = client.get('/api/products/1')
        assert response.status_code == 200

    def test_get_existing_product_returns_correct_data(self, client):
        """GET /api/products/1 should return correct product data"""
        response = client.get('/api/products/1')
        data = response.get_json()
        assert data['id'] == 1
        assert data['name'] == 'Laptop'
        assert data['price'] == 999.99
        assert data['stock'] == 10

    def test_get_nonexistent_product_returns_404(self, client):
        """GET /api/products/999 should return 404"""
        response = client.get('/api/products/999')
        assert response.status_code == 404


class TestCheckStock:
    """Test stock checking endpoint"""

    def test_check_stock_sufficient_returns_200(self, client):
        """Checking stock with sufficient quantity should return 200"""
        response = client.get('/api/products/1/check-stock?quantity=5')
        assert response.status_code == 200

    def test_check_stock_sufficient_returns_available_true(self, client):
        """Checking stock with sufficient quantity should return available: true"""
        response = client.get('/api/products/1/check-stock?quantity=5')
        data = response.get_json()
        assert data['available'] is True
        assert data['current_stock'] == 10
        assert data['requested_quantity'] == 5

    def test_check_stock_insufficient_returns_available_false(self, client):
        """Checking stock with insufficient quantity should return available: false"""
        response = client.get('/api/products/1/check-stock?quantity=20')
        data = response.get_json()
        assert data['available'] is False

    def test_check_stock_nonexistent_product_returns_404(self, client):
        """Checking stock for non-existent product should return 404"""
        response = client.get('/api/products/999/check-stock?quantity=1')
        assert response.status_code == 404


class TestReserveProduct:
    """Test product reservation endpoint"""

    def test_reserve_product_with_sufficient_stock_returns_200(self, client):
        """Reserving product with sufficient stock should return 200"""
        response = client.put('/api/products/1/reserve', json={'quantity': 5})
        assert response.status_code == 200

    def test_reserve_product_reduces_stock(self, client):
        """Reserving product should reduce stock"""
        initial_stock = products_db[1]['stock']
        response = client.put('/api/products/1/reserve', json={'quantity': 5})
        data = response.get_json()
        assert data['status'] == 'RESERVED'
        assert data['reserved_qty'] == 5
        assert products_db[1]['stock'] == initial_stock - 5

    def test_reserve_product_with_insufficient_stock_returns_400(self, client):
        """Reserving product with insufficient stock should return 400"""
        response = client.put('/api/products/1/reserve', json={'quantity': 100})
        assert response.status_code == 400

    def test_reserve_product_with_insufficient_stock_returns_error(self, client):
        """Reserving product with insufficient stock should return error"""
        response = client.put('/api/products/1/reserve', json={'quantity': 100})
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Insufficient stock'

    def test_reserve_nonexistent_product_returns_404(self, client):
        """Reserving non-existent product should return 404"""
        response = client.put('/api/products/999/reserve', json={'quantity': 1})
        assert response.status_code == 404
