from flask import Flask, jsonify, request
from datetime import datetime
import logging
import requests
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs from environment variables
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://localhost:5001')
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5002')

# In-memory orders database (simplified for demo)
orders_db = {}
order_counter = 1


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy", "service": "order-service", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    """Get all orders"""
    logger.info("Fetching all orders")
    return jsonify({"orders": list(orders_db.values())}), 200


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order by ID"""
    logger.info(f"Fetching order with ID: {order_id}")

    order = orders_db.get(order_id)
    if order:
        return jsonify(order), 200
    else:
        logger.warning(f"Order not found: {order_id}")
        return jsonify({"error": "Order not found"}), 404


def validate_user_exists(user_id):
    """Call User Service to validate user"""
    try:
        logger.info(f"Validating user {user_id} with User Service")
        response = requests.get(f"{USER_SERVICE_URL}/api/users/{user_id}/validate", timeout=5)

        if response.status_code == 404:
            return False, "User not found"

        data = response.json()
        if not data.get('valid', False):
            return False, data.get('reason', 'User validation failed')

        return True, data.get('user')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling User Service: {e}")
        return False, "User service unavailable"


def check_product_availability(product_id, quantity):
    """Call Product Service to check stock availability"""
    try:
        logger.info(f"Checking product {product_id} availability with Product Service")
        response = requests.get(
            f"{PRODUCT_SERVICE_URL}/api/products/{product_id}/check-stock",
            params={'quantity': quantity},
            timeout=5
        )

        if response.status_code == 404:
            return False, None, "Product not found"

        data = response.json()
        if not data.get('available', False):
            return False, None, "Insufficient stock"

        # Get product details for price
        product_response = requests.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}", timeout=5)
        product = product_response.json()

        return True, product, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Product Service: {e}")
        return False, None, "Product service unavailable"


def reserve_product_inventory(product_id, quantity):
    """Call Product Service to reserve inventory"""
    try:
        logger.info(f"Reserving {quantity} units of product {product_id}")
        response = requests.put(
            f"{PRODUCT_SERVICE_URL}/api/products/{product_id}/reserve",
            json={'quantity': quantity},
            timeout=5
        )

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error reserving product: {e}")
        return False, {"error": "Failed to reserve product"}


def calculate_order_total(quantity, unit_price):
    """Business logic: Calculate order total
    This is a pure function that can be unit tested in isolation
    """
    return quantity * unit_price


# ============================================================================
# DEMO FUNCTIONS: For demonstrating test failures
# ============================================================================

def calculate_shipping_cost(order_total, delivery_speed):
    """
    Calculate shipping cost based on order total and delivery speed
    WORKING VERSION: Returns correct shipping cost
    """
    if order_total >= 100:
        # Free shipping for orders over $100
        return 0.0

    if delivery_speed == "express":
        return 15.99
    elif delivery_speed == "standard":
        return 5.99
    elif delivery_speed == "economy":
        return 2.99
    else:
        return 5.99  # Default to standard


# BROKEN VERSION (commented out):
# Uncomment this function to see tests fail during presentation
# This demonstrates what happens when buggy code is pushed to CI/CD
#
# def calculate_shipping_cost(order_total, delivery_speed):
#     """
#     BROKEN VERSION: Has incorrect logic that will fail tests
#     """
#     if order_total >= 100:
#         return 10.0  # BUG: Charges for free shipping
#
#     if delivery_speed == "express":
#         return "15.99"  # BUG: Returns string instead of number
#     elif delivery_speed == "standard":
#         return -5.99  # BUG: Returns negative cost
#     elif delivery_speed == "economy":
#         return 25.99  # BUG: Economy more expensive than express
#     else:
#         return None  # BUG: Returns None instead of default value


@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order
    This demonstrates the complete workflow:
    1. Validate user
    2. Check product availability
    3. Reserve product
    4. Create order
    """
    global order_counter

    data = request.get_json()

    # Validate request data
    if not data or 'user_id' not in data or 'product_id' not in data or 'quantity' not in data:
        return jsonify({"error": "Missing required fields: user_id, product_id, quantity"}), 400

    user_id = data['user_id']
    product_id = data['product_id']
    quantity = data['quantity']

    # Step 1: Validate user exists and is active
    user_valid, user_info = validate_user_exists(user_id)
    if not user_valid:
        logger.warning(f"User validation failed: {user_info}")
        return jsonify({"error": f"User validation failed: {user_info}"}), 400

    # Step 2: Check product availability
    product_available, product_info, error = check_product_availability(product_id, quantity)
    if not product_available:
        logger.warning(f"Product check failed: {error}")
        return jsonify({"error": f"Product check failed: {error}"}), 400

    # Step 3: Reserve product inventory
    reservation_success, reservation_info = reserve_product_inventory(product_id, quantity)
    if not reservation_success:
        logger.error(f"Failed to reserve product: {reservation_info}")
        return jsonify({"error": "Failed to reserve product inventory"}), 500

    # Step 4: Calculate order total
    unit_price = product_info['price']
    total = calculate_order_total(quantity, unit_price)

    # Step 5: Create order
    new_order = {
        "id": order_counter,
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "total": total,
        "status": "CONFIRMED",
        "created_at": datetime.utcnow().isoformat()
    }

    orders_db[order_counter] = new_order
    order_counter += 1

    logger.info(f"Order created successfully: {new_order}")
    return jsonify(new_order), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
