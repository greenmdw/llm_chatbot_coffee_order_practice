# boards/forms.py

from django import forms

from .models import Board


class BoardForm(forms.ModelForm):
    """게시글 작성 및 수정 Form 입니다."""

    class Meta:
        # 값을 저장할 모델 지정
        model = Board

        # 사용자로부터 입력받을 필드만 지정함
        # author 는 폼 입력 항목이 아니라, 뷰에서 request.user 로 직접 채움
        fields = ['title', 'content', 'attachment']

        widgets = {
            # 본문은 넓은 textarea로 출력함
            "content": forms.Textarea(attrs={"rows": 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 모든 입력 요소에 css 클래스 추가함
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
