from flask import Blueprint, jsonify, request, abort
from web.src.models.pet import db, Pet

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/pets', methods=['GET'])
def get_pets():
    pets = Pet.query.all()
    return jsonify([{
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'sex': pet.sex,
        'created_at': pet.created_at,
        'updated_at': pet.updated_at
    } for pet in pets])

@api_bp.route('/pets', methods=['POST'])
def create_pet():
    data = request.get_json()
    if not data or 'name' not in data or 'species' not in data or 'sex' not in data:
        abort(400, description='Invalid data')
    pet = Pet(
        name=data['name'],
        species=data['species'],
        sex=data['sex']
    )
    db.session.add(pet)
    db.session.commit()
    return jsonify({'id': pet.id}), 201

@api_bp.route('/pets/<int:id>', methods=['GET'])
def get_pet(id):
    pet = Pet.query.get_or_404(id)
    return jsonify({
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'sex': pet.sex,
        'created_at': pet.created_at,
        'updated_at': pet.updated_at
    })

@api_bp.route('/pets/<int:id>', methods=['PUT'])
def update_pet(id):
    pet = Pet.query.get_or_404(id)
    data = request.get_json()
    if not data or 'name' not in data or 'species' not in data or 'sex' not in data:
        abort(400, description='Invalid data')
    pet.name = data['name']
    pet.species = data['species']
    pet.sex = data['sex']
    db.session.commit()
    return jsonify({'id': pet.id})

@api_bp.route('/pets/<int:id>', methods=['DELETE'])
def delete_pet(id):
    pet = Pet.query.get_or_404(id)
    db.session.delete(pet)
    db.session.commit()
    return '', 204
