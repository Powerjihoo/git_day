from flask import Flask

def create_app():
    """
    Flask 애플리케이션을 생성하고 블루프린트를 등록합니다.

    이 함수는 Flask 애플리케이션 인스턴스를 초기화하고, 애플리케이션 컨텍스트 내에서
    필요한 기능들을 설정합니다. 주로 애플리케이션의 구성 및 블루프린트 등록을 처리합니다.

    Returns:
        app: 초기화가 완료된 Flask 애플리케이션 인스턴스.
    """
    app = Flask(__name__)
    
    with app.app_context():
        # 등록된 블루프린트를 가져옵니다.
        from .routes import main as main_blueprint
        app.register_blueprint(main_blueprint)
    
    return app