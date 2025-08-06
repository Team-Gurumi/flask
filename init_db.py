from app import app, db, Provider

with app.app_context():
    db.create_all()

    if not Provider.query.first():
        providers = [
            Provider(name="node-1", cpu_free=80.5, ram_free=6.4, status="정상", ip_address="10.0.0.1"),
            Provider(name="node-2", cpu_free=65.0, ram_free=3.2, status="과부하", ip_address="10.0.0.2"),
            Provider(name="node-3", cpu_free=92.0, ram_free=7.9, status="정상", ip_address="10.0.0.3"),
        ]
        db.session.bulk_save_objects(providers)
        db.session.commit()
        print("✅ 공급자 더미 데이터 삽입 완료")
    else:
        print("ℹ️ 이미 데이터가 있습니다. 중복 삽입하지 않습니다.")
