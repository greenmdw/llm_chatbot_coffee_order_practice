# members/admin.py

# 관리자 사이트에 모델을 등록하기 위해 가져옴
from django.contrib import admin

# Django 기본 사용자 관리 화면을 재사용하기 위해 가져옴
from django.contrib.auth.admin import UserAdmin

# 우리가 만든 회원 모델
from .models import Member


@admin.register(Member)
class MemberAdmin(UserAdmin):
    """관리자 사이트에서 회원을 관리하는 화면입니다."""

    # 목록 화면에 보여줄 컬럼
    list_display = ("username", "display_name", "email", "gender", "age", "is_staff")

    # 회원 상세/수정 화면의 항목 구성
    # UserAdmin 기본 구성에 우리가 추가한 필드를 넣음
    fieldsets = UserAdmin.fieldsets + (
        (
            "추가 회원 정보",
            {"fields": ("display_name", "gender", "age", "phone", "photo")},
        ),
    )

    # 관리자 화면에서 회원을 새로 추가할 때 보여줄 항목
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "추가 회원 정보",
            {"fields": ("display_name", "email", "gender", "age", "phone", "photo")},
        ),
    )
