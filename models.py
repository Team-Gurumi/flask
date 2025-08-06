from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# ✅ 공급자(서버) 모델 추가
class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)         # 예: node-1
    cpu_free = db.Column(db.Float, nullable=False)          # CPU 여유율 (%)
    ram_free = db.Column(db.Float, nullable=False)          # RAM 여유량 (GiB)
    status = db.Column(db.String(16), nullable=False)       # 예: 정상, 과부하
    ip_address = db.Column(db.String(64), nullable=True)    # 선택: IP 표시용
