from flask import Flask
from src.routes.users import users_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(users_bp, url_prefix='/v1')

if __name__ == '__main__':
    app.run(debug=True)