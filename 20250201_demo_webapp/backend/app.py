from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ ルートをコントローラファイルから読み込む
from server.controllers.default_controller import register_routes

register_routes(app)  # ✅ ルートを登録

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

