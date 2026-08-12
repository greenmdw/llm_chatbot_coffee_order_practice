# 게시글 작성시 로그인한 사용자 아이디(예: user01)를 글 작성자에 자동 기록되게 하기
# settings의 AUTH_USER_MODEL을 사용함
from django.conf import settings
from django.db import models

class Board(models.Model):
    """게시글 모델입니다."""
    # 게시글 작성자
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # 회원이 삭제되면 해당 회원의 게시글도 삭제함
        on_delete=models.CASCADE,

        # 역참조 이름 지정
        related_name='boards',
    )

    # 게시글 제목
    title = models.CharField('제목', max_length=200)

    # 게시글 본문
    content = models.TextField("내용")

    # 첨부 파일
    attachment = models.FileField("첨부파일", upload_to='board_files/%Y/%m/', null=True, blank=True)

    # 조회수
    read_count = models.PositiveIntegerField("조회수", default=0)

    # 작성 시간, 수정시각
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        # 가장 최근 글 부터 보여줌
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.author})"


    # 수정 권한에 대한 메소드 추가
    def can_edit(self, user):
        """게시글 수정 가능 여부를 반환합니다."""
        # 로그인 상태이고, 게시글 작성자와 현재 로그인한 사용자가 같아야 함.
        return (user.is_authenticated and self.author == user)

    # 삭제 권한에 대한 메소드 추가
    def can_delete(self, user):
        """삭제 권한은 작성자 본인 또는 관리자에게 허용합니다."""
        # 작성자 본인이거나 staff/superuser 관리자이면 삭제할 수 있습니다.
        return user.is_authenticated and (self.author_id == user.id or user.is_staff or user.is_superuser)
