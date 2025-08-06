from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask import render_template, redirect, request

app = Flask(__name__)
CORS(app)

# DB 연결 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mutualcloud.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User 모델
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# 기본 라우터
@app.route('/')
def home():
    return "Mutual Cloud 서버 실행 중!"

# 회원가입 API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': '빈칸이 있어요'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': '이미 존재하는 사용자'}), 409

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': '회원가입 성공!'}), 201

# 로그인 API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({'message': '로그인 성공', 'userId': user.id}), 200
    else:
        return jsonify({'error': '로그인 실패'}), 401

# HTML용 회원가입 페이지
@app.route('/register', methods=['GET', 'POST'])
def html_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            return "이미 존재하는 사용자"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return "회원가입 성공!"

    return render_template('register.html')


# HTML용 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def html_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return f"{username}님 로그인 성공!"
        else:
            return "로그인 실패"

    return render_template('login.html')

# 서버 실행
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)