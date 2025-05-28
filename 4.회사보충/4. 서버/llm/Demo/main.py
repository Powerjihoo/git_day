from app import create_app, generate
import os
import setproctitle

# 프로세스의 이름을 'gaon_bm'으로 설정하여 시스템 모니터에서 식별할 수 있게 합니다.
setproctitle.setproctitle('gaon_bm')

# Flask 애플리케이션 인스턴스를 생성합니다.
app = create_app()

# 애플리케이션 컨텍스트 내에서 모델을 초기화합니다.
with app.app_context():
    generate.initialize_models()

if __name__ == "__main__":
    # Flask 개발 서버를 실행합니다.
    #NOTE
    port = int(os.getenv('FLASK_RUN_PORT', '46986'))
    app.run('0.0.0.0', debug=True, use_reloader=False, port=port)