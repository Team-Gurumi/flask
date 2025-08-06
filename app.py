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

# 홈 페이지 (공급자 리스트)
@app.route('/')
def home():
    providers = Provider.query.all()
    return render_template('home.html', providers=providers)

# HTML 회원가입
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
        return redirect('/login')

    return render_template('register.html')

# HTML 로그인
@app.route('/login', methods=['GET', 'POST'])
def html_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect('/')
        else:
            return "로그인 실패"

    return render_template('login.html')

# 공급자 상세 페이지
@app.route('/provider/<int:provider_id>')
def provider_detail(provider_id):
    provider = Provider.query.get_or_404(provider_id)
    return render_template('prov-detail.html', provider=provider)

# 작업 요청 (로그인 필수)
@app.route('/submit_job/<int:provider_id>', methods=['POST'])
def submit_job(provider_id):
    if 'user_id' not in session:
        return redirect(url_for('html_login'))

    job_id = str(uuid4())[:8]
    provider = Provider.query.get_or_404(provider_id)

    # 결과 저장 경로 생성
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

# 로그아웃
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

# 서버 실행
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
