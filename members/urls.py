# members/urls.py

# URL을 VIew와 연결하기 위한 Path임
from django.urls import path

# 현재 앱의 View 가져옴
from . import views

# URL namespace 설정
app_name = "members"

urlpatterns = [
    # /members/signup/
    # name 은 템플릿에서 {% url 'members:signup' %} 로 부르는 이름이므로
    # 슬래시(/) 없이 이름만 적음
    path(
        "signup/",
        views.signup,
        name="signup",
    ),

    # /members/login/
    path(
        "login/",
        views.login_view,
        name="login",
    ),

    # /members/logout/
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    # /members/profile/  : 회원정보 조회
    path(
        "profile/",
        views.profile,
        name="profile",
    ),

    # /members/profile/edit/  : 회원정보 수정
    path(
        "profile/edit/",
        views.profile_edit,
        name="profile_edit",
    ),

    # /members/withdraw/  : 회원 탈퇴
    path(
        "withdraw/",
        views.withdraw,
        name="withdraw",
    ),
]
