# boards 앱에 작성된 View들의 url만 등록 처리함
from django.urls import path

from . import views

app_name = "boards"
urlpatterns = [
    # 게시판 목록: /boards/
    path("", views.board_list, name="list"),

    # 게시글 등록: /boards/create/
    path("create/", views.board_create, name="create"),

    # 게시글 상세보기: /boards/12/
    path("<int:pk>/", views.board_detail, name="detail"),

    # 게시글 수정: /boards/12/update/
    path("<int:pk>/update/", views.board_update, name="update"),

    # 게시글 삭제: /boards/12/delete/
    path("<int:pk>/delete/", views.board_delete, name="delete"),
]
