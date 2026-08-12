"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# 개발 중에 업로드 파일(media)을 보여주기 위해 필요함
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

# 앱의 urls.py 를 통째로 가져다 붙이려면 include 가 필요함
from django.urls import include, path

# 첫 페이지를 templates/home.html 로 바로 보여주기 위해 사용
from django.views.generic import TemplateView

from members.views import home

urlpatterns = [
    path("admin/", admin.site.urls),

    # 첫 페이지 => views 에서 redirect('home') 이 찾는 이름
    path(
        "",
        TemplateView.as_view(template_name="home.html"),
        name="home",
    ),

    # /members/ 로 시작하는 주소는 members/urls.py 가 처리함
    # 예) /members/signup/, /members/login/, /members/logout/
    path("members/", include("members.urls")),

    # /boards/ 로 시작하는 주소는 boards/urls.py 가 처리함
    # 예) /boards/, /boards/create/, /boards/12/
    # boards/urls.py 에 app_name = "boards" 가 이미 있어서 namespace는 생략해도 되지만
    # 명시적으로 적어서 어떤 네임스페이스로 묶이는지 바로 보이게 함
    path("boards/", include("boards.urls", namespace="boards")),

]

# 개발 모드(DEBUG=True)일 때만 업로드된 사진을 브라우저에서 볼 수 있게 함
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
