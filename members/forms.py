# members/forms.py

# Django Form 기능 가져옴
from django import forms

# Django 기본 인증 폼을 가져옴
from django.contrib.auth.forms import(
    AuthenticationForm,
    UserCreationForm,
)

# 사용자 정의 Member 모델 가져옴
# 같은 앱 안의 models.py 이므로 앞에 점(.)을 붙인 상대경로로 가져옴
from .models import Member

class SignUpForm(UserCreationForm):
    """회원 가입 form 입니다."""
    class Meta:
        # 이 form 이 사용할 모델 선언함
        model = Member

        # 화면에서 입력할 필드
        # password1 / password2 는 모델 필드가 아니라
        # UserCreationForm 이 스스로 만들어 주는 필드이므로 여기에 적지 않음
        fields = ('username', 'display_name', 'email', 'gender', 'age', 'phone', 'photo')

    # signup 계정 만들기
    def __init__(self, *args, **kwargs):
        # super 는 함수처럼 괄호를 붙여서 호출해야 함
        super().__init__(*args, **kwargs)

        # 모든 입력 요소에 css 클래스 추가함
        for field in self.fields.values():
            # attrs 는 dict 이므로 update() 로 값을 넣음
            field.widget.attrs.update({'class': 'form-control'})

# 로그인 form 만들기
class LoginForm(AuthenticationForm):
    # login form
    def __init__(self, request = None, *args, **kwargs):
        # Django 기본 AuthenticationForm 을 초기화 함
        super().__init__(request, *args, **kwargs)

        # 아이디 입력 필드 css 지정
        self.fields['username'].widget.attrs.update({'class': 'form-control'})

        # 비밀번호 입력 필드 css 지정
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    """로그인한 회원이 본인 정보를 수정하는 form 입니다."""
    class Meta:
        model = Member

        # username(아이디)은 로그인 식별자라 여기서 바꾸지 않음
        # password 는 별도 비밀번호 변경 기능에서 다룰 값이라 여기 넣지 않음
        fields = ('display_name', 'email', 'gender', 'age', 'phone', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 모든 입력 요소에 css 클래스 추가함
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
