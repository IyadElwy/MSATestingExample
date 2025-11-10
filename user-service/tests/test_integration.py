"""
Integration Tests for User Service
Tests the service behavior with real HTTP calls (but still isolated service)
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


class TestUserWorkflow:
    """Test complete user management workflows"""

    def test_create_and_retrieve_user_workflow(self, client):
        """Integration test: Create a user and then retrieve it"""
        # Step 1: Create a new user
        new_user = {
            'name': 'Emma Davis',
            'email': 'emma@example.com',
            'active': True
        }
        create_response = client.post('/api/users', json=new_user)
        assert create_response.status_code == 201
        created_user = create_response.get_json()
        user_id = created_user['id']

        # Step 2: Retrieve the created user
        get_response = client.get(f'/api/users/{user_id}')
        assert get_response.status_code == 200
        retrieved_user = get_response.get_json()

        # Step 3: Verify data consistency
        assert retrieved_user['id'] == user_id
        assert retrieved_user['name'] == new_user['name']
        assert retrieved_user['email'] == new_user['email']
        assert retrieved_user['active'] == new_user['active']

    def test_create_and_validate_user_workflow(self, client):
        """Integration test: Create a user and validate it"""
        # Step 1: Create a new active user
        new_user = {
            'name': 'Frank Miller',
            'email': 'frank@example.com',
            'active': True
        }
        create_response = client.post('/api/users', json=new_user)
        assert create_response.status_code == 201
        user_id = create_response.get_json()['id']

        # Step 2: Validate the user
        validate_response = client.get(f'/api/users/{user_id}/validate')
        assert validate_response.status_code == 200
        validation_data = validate_response.get_json()

        # Step 3: Verify validation result
        assert validation_data['valid'] is True
        assert validation_data['user']['name'] == new_user['name']

    def test_inactive_user_validation_workflow(self, client):
        """Integration test: Create inactive user and verify validation fails"""
        # Step 1: Create an inactive user
        new_user = {
            'name': 'Grace Lee',
            'email': 'grace@example.com',
            'active': False
        }
        create_response = client.post('/api/users', json=new_user)
        assert create_response.status_code == 201
        user_id = create_response.get_json()['id']

        # Step 2: Validate the inactive user
        validate_response = client.get(f'/api/users/{user_id}/validate')
        assert validate_response.status_code == 200
        validation_data = validate_response.get_json()

        # Step 3: Verify validation fails for inactive user
        assert validation_data['valid'] is False
        assert validation_data['reason'] == 'User is inactive'

    def test_bulk_user_creation_and_retrieval(self, client):
        """Integration test: Create multiple users and retrieve all"""
        # Step 1: Create multiple users
        users_to_create = [
            {'name': 'User 1', 'email': 'user1@example.com'},
            {'name': 'User 2', 'email': 'user2@example.com'},
            {'name': 'User 3', 'email': 'user3@example.com'}
        ]

        created_ids = []
        for user in users_to_create:
            response = client.post('/api/users', json=user)
            assert response.status_code == 201
            created_ids.append(response.get_json()['id'])

        # Step 2: Retrieve all users
        get_all_response = client.get('/api/users')
        assert get_all_response.status_code == 200
        all_users = get_all_response.get_json()['users']

        # Step 3: Verify all created users are present
        assert len(all_users) >= len(users_to_create)
        created_user_ids = [u['id'] for u in all_users if u['id'] in created_ids]
        assert len(created_user_ids) == len(users_to_create)
