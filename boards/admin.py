# boards/admin.py

# 관리자 사이트에 모델을 등록하기 위해 가져옴
from django.contrib import admin

# 우리가 만든 게시글 모델
from .models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """관리자 사이트에서 게시글을 관리하는 화면입니다."""

    # 목록 화면에 보여줄 컬럼
    list_display = ("id", "title", "author", "read_count", "created_at")

    # 오른쪽에 날짜별로 좁혀 보는 필터 추가
    list_filter = ("created_at",)

    # 관리자 화면 상단에 검색창 추가 (제목, 내용 검색)
    search_fields = ("title", "content")
