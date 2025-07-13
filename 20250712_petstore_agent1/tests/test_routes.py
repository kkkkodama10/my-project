import pytest
from flask import url_for
from web.src.models.pet import db, Pet
from web.src.app import create_app

@pytest.fixture
def test_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SERVER_NAME'] = 'localhost'  # SERVER_NAMEを追加
    app.config['SECRET_KEY'] = 'test_secret_key'  # SECRET_KEYを追加
    app_context = app.app_context()
    app_context.push()  # 明示的にコンテキストをプッシュ
    with app.test_client() as client:
        db.create_all()
        yield client
    db.session.remove()  # セッションのクリーンアップを追加
    app_context.pop()  # 明示的にコンテキストをポップ

@pytest.fixture
def sample_pet(test_client):
    with test_client.application.app_context():
        pet = Pet(name='ポチ', species='イヌ', sex='male')
        db.session.add(pet)
        db.session.commit()
        return db.session.merge(pet)  # DetachedInstanceErrorを防ぐためにmergeを使用

def test_list_pets(test_client, sample_pet):
    with test_client.application.app_context():
        response = test_client.get(url_for('pet.list_pets'))
        assert response.status_code == 200
        assert 'ポチ'.encode('utf-8') in response.data

def test_create_pet(test_client):
    with test_client.application.app_context():
        # CSRFトークンを取得
        response_get = test_client.get(url_for('pet.list_pets'))
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response_get.data, 'html.parser')
        csrf_token = soup.find('input', {'id': 'csrf_token'})['value']
        response = test_client.post(url_for('pet.create_pet'), data={
            'name': 'タマ',
            'species': 'ネコ',
            'sex': 'female',
            'csrf_token': csrf_token
        })
        assert response.status_code == 302  # Redirect
        assert Pet.query.filter_by(name='タマ').first() is not None

def test_get_pet(test_client, sample_pet):
    with test_client.application.app_context():
        pet = db.session.merge(sample_pet)
        response = test_client.get(url_for('pet.get_pet', id=pet.id))
        assert response.status_code == 200
        assert 'ポチ'.encode('utf-8') in response.data

def test_edit_pet(test_client, sample_pet):
    with test_client.application.app_context():
        pet = db.session.merge(sample_pet)
        # CSRFトークンを取得
        response_get = test_client.get(url_for('pet.edit_pet', id=pet.id))
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response_get.data, 'html.parser')
        csrf_token = soup.find('input', {'id': 'csrf_token'})['value']
        response = test_client.post(url_for('pet.edit_pet', id=pet.id), data={
            'name': 'ポチ改',
            'species': 'イヌ',
            'sex': 'male',
            'csrf_token': csrf_token
        })
        assert response.status_code == 302  # Redirect
        updated_pet = Pet.query.get(pet.id)
        assert updated_pet.name == 'ポチ改'

def test_delete_pet(test_client, sample_pet):
    with test_client.application.app_context():
        pet = db.session.merge(sample_pet)
        response = test_client.post(url_for('pet.delete_pet', id=pet.id))
        assert response.status_code == 302  # Redirect
        assert Pet.query.get(pet.id) is None
