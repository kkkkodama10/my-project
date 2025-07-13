from flask import Flask
from web.src.models.pet import db

def create_app():
    import os
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    # プロジェクトルート直下にDBを配置
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    
    db_path = os.path.join(project_root, 'pet_catalog.db')
    print(f"DB path: {db_path}")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from web.src.routes.pet import pet_bp
    from web.src.routes.api import api_bp

    app.register_blueprint(pet_bp)
    app.register_blueprint(api_bp)

    # ここでテーブル自動作成
    with app.app_context():
        print("Creating database tables...")
        db.create_all()

    return app
