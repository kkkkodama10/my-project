from web.src.app import create_app
from web.src.models.pet import db, Pet
from datetime import datetime

app = create_app()

with app.app_context():
    # モックデータ
    pets = [
        Pet(name='ポチ', species='犬', sex='male', created_at=datetime.now(), updated_at=datetime.now()),
        Pet(name='タマ', species='猫', sex='female', created_at=datetime.now(), updated_at=datetime.now()),
        Pet(name='ピーちゃん', species='鳥', sex='unknown', created_at=datetime.now(), updated_at=datetime.now()),
    ]
    db.session.bulk_save_objects(pets)
    db.session.commit()
    print("Mock data inserted.")
