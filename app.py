from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # .env 로드
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
FASTAPI_TIMEOUT = 120  # 로그 대기 타임아웃(초)

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
    password = request.form['password']
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
        session['username'] = user.username
        return redirect(url_for('home'))
    else:
        return "로그인 실패", 401
    
# 홈 > 상세보기
@app.route('/provider/<int:provider_id>', methods=['GET'])
def provider_detail(provider_id):
    provider = Provider.query.get_or_404(provider_id)
    return render_template('prov-detail.html', provider=provider)

# 작업 요청 (Flask → FastAPI 프록시)
@app.route('/submit_job/<int:provider_id>', methods=['POST'])
def submit_job(provider_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    provider = Provider.query.get_or_404(provider_id)

    # 홈 화면 폼에서 값 수집
    image = (request.form.get('image') or 'alpine:3.19').strip()
    script = (request.form.get('script') or '').strip()
    env_text = (request.form.get('env') or '').strip()

    # "KEY=VALUE" 줄바꿈 파싱
    env_dict = {}
    if env_text:
        for line in env_text.splitlines():
            line = line.strip()
            if not line or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env_dict[k.strip()] = v.strip()

    # 간단히 provider.name을 K8S 라벨값으로 사용 (라벨 체계 다르면 이 부분을 매핑)
    payload = {
        "image": image,
        "script": script,
        "provider_label_value": provider.name,
        "namespace": "mutual-cloud",
        "env": env_dict,
        "backoff_limit": 0,
        "ttl_seconds_after_finished": 300
    }

    try:
        resp = requests.post(
            f"{FASTAPI_BASE_URL}/submit-job",
            json=payload,
            timeout=20
        )
        resp.raise_for_status()
        data = resp.json()  # { "job_name": "...", "namespace": "..." }
    except Exception as e:
        return f"FastAPI 호출 오류: {e}", 500

    return redirect(url_for('result', namespace=data["namespace"], job_id=data["job_name"]))


# 결과 보기
@app.route('/result/<namespace>/<job_id>')
def result(namespace, job_id):
    try:
        resp = requests.get(
            f"{FASTAPI_BASE_URL}/jobs/{namespace}/{job_id}/logs",
            params={"timeout": FASTAPI_TIMEOUT},
            timeout=FASTAPI_TIMEOUT + 10
        )
        resp.raise_for_status()
        data = resp.json()  # {"pod": "...", "phase": "Succeeded|Failed|...", "logs": "..."}
    except Exception as e:
        return f"FastAPI 로그 조회 오류: {e}", 500

    return render_template('result.html', ns=namespace, job_id=job_id, result=data)

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
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))

# 실행
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
