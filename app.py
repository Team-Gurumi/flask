from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from uuid import uuid4
import json
import os

app = Flask(__name__)
CORS(app)
app.secret_key = 'mutualcloud-very-secret-key'

# 신뢰된 API Key (임시 하드코딩 → 나중에 .env로)
TRUSTED_API_KEY = 'my-secure-api-key'

# DB 연결 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mutualcloud.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User 모델
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# Provider 모델
class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    cpu_free = db.Column(db.Float, nullable=False)
    ram_free = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)

# 홈
@app.route('/')
def home():
    providers = Provider.query.all()
    return render_template('home.html', providers=providers)

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def html_register():
    if request.method == 'GET':
        return render_template('register.html')

    # POST → 회원 생성
    username = request.form['username'].strip()
    password = request.form['password']  # 실제로는 해시 권장
    if not username or not password:
        return "유효하지 않은 입력", 400
    if User.query.filter_by(username=username).first():
        return "이미 존재하는 사용자", 409

    db.session.add(User(username=username, password=password))
    db.session.commit()
    return redirect(url_for('login'))

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET 요청 → 로그인 화면
    if request.method == 'GET':
        return render_template('login.html')

    # POST 요청 → 로그인 처리 로직
    username = request.form['username']
    password = request.form['password']
    # 인증 로직 예시
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        session['user_id'] = user.id
        return redirect(url_for('home'))
    else:
        return "로그인 실패", 401

# 작업 요청
@app.route('/submit_job/<int:provider_id>', methods=['POST'])
def submit_job(provider_id):
    if 'user_id' not in session:
        return redirect(url_for('html_login'))

    job_id = str(uuid4())[:8]
    provider = Provider.query.get_or_404(provider_id)
    os.makedirs('reports', exist_ok=True)

    report_data = {
        "job_id": job_id,
        "provider": provider.name,
        "status": "Running",
        "start_time": datetime.now().isoformat()
    }

    with open(f"reports/{job_id}.json", "w") as f:
        json.dump(report_data, f)

    return redirect(url_for('result', job_id=job_id))

# 결과 보기
@app.route('/result/<job_id>')
def result(job_id):
    try:
        with open(f"reports/{job_id}.json", "r") as f:
            report = json.load(f)
    except FileNotFoundError:
        return "리포트를 찾을 수 없습니다", 404

    return render_template('result.html', report=report)

# 공급자 자원 상태 등록 API
@app.route('/api/provider/register', methods=['POST'])
def register_provider():
    api_key = request.headers.get('X-API-KEY')

    if api_key != TRUSTED_API_KEY:
        return jsonify({'error': '인증 실패'}), 403

    data = request.get_json()

    if data.get('ip_address') != request.remote_addr:
        return jsonify({'error': 'IP 주소 불일치'}), 400

    try:
        cpu = float(data.get('cpu_free'))
        if not (0 <= cpu <= 100):
            raise ValueError
    except:
        return jsonify({'error': '잘못된 CPU 수치'}), 400

    try:
        ram = float(data.get('ram_free'))
        if ram < 0:
            raise ValueError
    except:
        return jsonify({'error': '잘못된 RAM 수치'}), 400

    new = Provider(
        name=data['name'],
        cpu_free=cpu,
        ram_free=ram,
        status=data['status'],
        ip_address=data['ip_address']
    )
    db.session.add(new)
    db.session.commit()

    return jsonify({'message': '등록 완료'}), 201

# 로그아웃
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

# 실행
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
