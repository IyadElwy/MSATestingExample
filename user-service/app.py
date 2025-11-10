from flask import Flask, jsonify, request
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory user database (simplified for demo)
users_db = {
    1: {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "active": True},
    2: {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "active": True},
    3: {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "active": False}
}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy", "service": "user-service", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Get all users"""
    logger.info("Fetching all users")
    return jsonify({"users": list(users_db.values())}), 200


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    logger.info(f"Fetching user with ID: {user_id}")

    user = users_db.get(user_id)
    if user:
        return jsonify(user), 200
    else:
        logger.warning(f"User not found: {user_id}")
        return jsonify({"error": "User not found"}), 404


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Missing required fields: name, email"}), 400

    new_id = max(users_db.keys()) + 1 if users_db else 1
    new_user = {
        "id": new_id,
        "name": data['name'],
        "email": data['email'],
        "active": data.get('active', True)
    }

    users_db[new_id] = new_user
    logger.info(f"Created new user: {new_user}")

    return jsonify(new_user), 201


@app.route('/api/users/<int:user_id>/validate', methods=['GET'])
def validate_user(user_id):
    """Validate if user exists and is active"""
    logger.info(f"Validating user: {user_id}")

    user = users_db.get(user_id)
    if not user:
        return jsonify({"valid": False, "reason": "User not found"}), 404

    if not user.get('active', False):
        return jsonify({"valid": False, "reason": "User is inactive"}), 200

    return jsonify({"valid": True, "user": user}), 200


# ============================================================================
# DEMO FUNCTIONS: For demonstrating test failures
# ============================================================================

def calculate_user_discount(user_age, is_member):
    """
    Calculate discount percentage based on user age and membership status
    WORKING VERSION: Returns correct discount logic
    """
    if user_age < 18:
        return 10  # Youth discount
    elif user_age >= 65:
        return 15  # Senior discount
    elif is_member:
        return 20  # Member discount
    else:
        return 0  # No discount


# BROKEN VERSION (commented out):
# Uncomment this function to see tests fail during presentation
# This demonstrates what happens when buggy code is pushed to CI/CD
#
# def calculate_user_discount(user_age, is_member):
#     """
#     BROKEN VERSION: Has incorrect logic that will fail tests
#     """
#     if user_age < 18:
#         return "10%"  # BUG: Returns string instead of number
#     elif user_age >= 65:
#         return -15  # BUG: Returns negative discount
#     elif is_member:
#         return 25  # BUG: Wrong discount amount (should be 20)
#     else:
#         return None  # BUG: Returns None instead of 0


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
