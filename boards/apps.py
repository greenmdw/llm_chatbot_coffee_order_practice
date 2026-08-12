# boards/apps.py

# 앱 설정 클래스를 만들기 위해 가져옴
from django.apps import AppConfig


class BoardsConfig(AppConfig):
    # 이 앱의 모델들이 사용할 기본 기본키(pk) 자료형
    default_auto_field = "django.db.models.BigAutoField"

    # 앱 이름(폴더 이름과 같아야 함)
    name = "boards"

    # 관리자 화면 등에 표시될 이름
    verbose_name = "게시판 관리"
