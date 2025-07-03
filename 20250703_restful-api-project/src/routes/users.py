from flask import Blueprint, jsonify

users_bp = Blueprint('users', __name__)

# Sample user data
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]

@users_bp.route('/v1/users', methods=['GET'])
def get_users():
    return jsonify(users)