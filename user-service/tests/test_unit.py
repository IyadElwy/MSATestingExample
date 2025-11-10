"""
Unit Tests for User Service
Tests individual functions and endpoints in isolation
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, users_db


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the database before each test"""
    users_db.clear()
    users_db.update({
        1: {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "active": True},
        2: {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "active": True},
        3: {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "active": False}
    })


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
        assert data['service'] == 'user-service'
        assert 'timestamp' in data


class TestGetAllUsers:
    """Test get all users endpoint"""

    def test_get_all_users_returns_200(self, client):
        """GET /api/users should return 200 OK"""
        response = client.get('/api/users')
        assert response.status_code == 200

    def test_get_all_users_returns_user_list(self, client):
        """GET /api/users should return list of users"""
        response = client.get('/api/users')
        data = response.get_json()
        assert 'users' in data
        assert len(data['users']) == 3


class TestGetUser:
    """Test get user by ID endpoint"""

    def test_get_existing_user_returns_200(self, client):
        """GET /api/users/1 should return 200 OK for existing user"""
        response = client.get('/api/users/1')
        assert response.status_code == 200

    def test_get_existing_user_returns_correct_data(self, client):
        """GET /api/users/1 should return correct user data"""
        response = client.get('/api/users/1')
        data = response.get_json()
        assert data['id'] == 1
        assert data['name'] == 'Alice Smith'
        assert data['email'] == 'alice@example.com'

    def test_get_nonexistent_user_returns_404(self, client):
        """GET /api/users/999 should return 404 for non-existent user"""
        response = client.get('/api/users/999')
        assert response.status_code == 404

    def test_get_nonexistent_user_returns_error_message(self, client):
        """GET /api/users/999 should return error message"""
        response = client.get('/api/users/999')
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'User not found'


class TestCreateUser:
    """Test create user endpoint"""

    def test_create_user_with_valid_data_returns_201(self, client):
        """POST /api/users with valid data should return 201 Created"""
        new_user = {
            'name': 'David Wilson',
            'email': 'david@example.com'
        }
        response = client.post('/api/users', json=new_user)
        assert response.status_code == 201

    def test_create_user_adds_user_to_database(self, client):
        """POST /api/users should add user to database"""
        new_user = {
            'name': 'David Wilson',
            'email': 'david@example.com'
        }
        response = client.post('/api/users', json=new_user)
        data = response.get_json()
        assert data['id'] == 4  # Next available ID
        assert data['name'] == 'David Wilson'
        assert data['email'] == 'david@example.com'
        assert data['active'] is True  # Default value

    def test_create_user_without_name_returns_400(self, client):
        """POST /api/users without name should return 400 Bad Request"""
        invalid_user = {'email': 'test@example.com'}
        response = client.post('/api/users', json=invalid_user)
        assert response.status_code == 400

    def test_create_user_without_email_returns_400(self, client):
        """POST /api/users without email should return 400 Bad Request"""
        invalid_user = {'name': 'Test User'}
        response = client.post('/api/users', json=invalid_user)
        assert response.status_code == 400


class TestValidateUser:
    """Test user validation endpoint"""

    def test_validate_active_user_returns_200(self, client):
        """Validating an active user should return 200 OK"""
        response = client.get('/api/users/1/validate')
        assert response.status_code == 200

    def test_validate_active_user_returns_valid_true(self, client):
        """Validating an active user should return valid: true"""
        response = client.get('/api/users/1/validate')
        data = response.get_json()
        assert data['valid'] is True
        assert 'user' in data

    def test_validate_inactive_user_returns_200(self, client):
        """Validating an inactive user should return 200 OK"""
        response = client.get('/api/users/3/validate')
        assert response.status_code == 200

    def test_validate_inactive_user_returns_valid_false(self, client):
        """Validating an inactive user should return valid: false"""
        response = client.get('/api/users/3/validate')
        data = response.get_json()
        assert data['valid'] is False
        assert data['reason'] == 'User is inactive'

    def test_validate_nonexistent_user_returns_404(self, client):
        """Validating a non-existent user should return 404"""
        response = client.get('/api/users/999/validate')
        assert response.status_code == 404

    def test_validate_nonexistent_user_returns_valid_false(self, client):
        """Validating a non-existent user should return valid: false"""
        response = client.get('/api/users/999/validate')
        data = response.get_json()
        assert data['valid'] is False
        assert data['reason'] == 'User not found'
