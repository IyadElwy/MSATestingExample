from flask import Flask, jsonify, request
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory product database (simplified for demo)
products_db = {
    1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
    2: {"id": 2, "name": "Mouse", "price": 29.99, "stock": 50},
    3: {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 25},
    4: {"id": 4, "name": "Monitor", "price": 299.99, "stock": 0}
}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy", "service": "product-service", "timestamp": datetime.utcnow().isoformat()}), 200


@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Get all products"""
    logger.info("Fetching all products")
    return jsonify({"products": list(products_db.values())}), 200


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product by ID"""
    logger.info(f"Fetching product with ID: {product_id}")

    product = products_db.get(product_id)
    if product:
        return jsonify(product), 200
    else:
        logger.warning(f"Product not found: {product_id}")
        return jsonify({"error": "Product not found"}), 404


@app.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product"""
    data = request.get_json()

    if not data or 'name' not in data or 'price' not in data:
        return jsonify({"error": "Missing required fields: name, price"}), 400

    new_id = max(products_db.keys()) + 1 if products_db else 1
    new_product = {
        "id": new_id,
        "name": data['name'],
        "price": float(data['price']),
        "stock": data.get('stock', 0)
    }

    products_db[new_id] = new_product
    logger.info(f"Created new product: {new_product}")

    return jsonify(new_product), 201


@app.route('/api/products/<int:product_id>/check-stock', methods=['GET'])
def check_stock(product_id):
    """Check if product has sufficient stock"""
    quantity = request.args.get('quantity', default=1, type=int)
    logger.info(f"Checking stock for product {product_id}, quantity: {quantity}")

    product = products_db.get(product_id)
    if not product:
        return jsonify({"available": False, "reason": "Product not found"}), 404

    available = product['stock'] >= quantity
    return jsonify({
        "available": available,
        "product_id": product_id,
        "requested_quantity": quantity,
        "current_stock": product['stock']
    }), 200


@app.route('/api/products/<int:product_id>/reserve', methods=['PUT'])
def reserve_product(product_id):
    """Reserve product inventory"""
    data = request.get_json()
    quantity = data.get('quantity', 1)

    logger.info(f"Reserving {quantity} units of product {product_id}")

    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product['stock'] < quantity:
        return jsonify({
            "error": "Insufficient stock",
            "requested": quantity,
            "available": product['stock']
        }), 400

    # Reserve the stock
    product['stock'] -= quantity
    logger.info(f"Reserved {quantity} units. New stock: {product['stock']}")

    return jsonify({
        "status": "RESERVED",
        "product_id": product_id,
        "reserved_qty": quantity,
        "remaining_stock": product['stock']
    }), 200


def calculate_product_total(quantity, unit_price):
    """Business logic: Calculate total price for a product
    This is a simple function that can be unit tested in isolation
    """
    return quantity * unit_price


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
