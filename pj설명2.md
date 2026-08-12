# 2단계 : 회원 가입 / 로그인 / 로그아웃 만들기

> `pj설명.md` 에서 Member 모델과 테이블까지 만들었습니다.
> 이제 사용자가 실제로 쓸 **화면과 처리 로직**을 만듭니다.

---

## 0. 먼저 큰 그림부터 : 요청 하나가 처리되는 흐름

Django는 MTV 구조입니다. 브라우저에서 `/members/signup/` 을 열면 이 순서로 흘러갑니다.

```text
[브라우저]  http://127.0.0.1:8000/members/signup/
     │
     ▼
[config/urls.py]      최상위 URL 지도
     │   "members/" 로 시작하네? → members/urls.py 에게 넘김
     ▼
[members/urls.py]     앱 URL 지도
     │   "signup/" 이네? → views.signup 함수 호출
     ▼
[members/views.py]    View : 실제 처리 담당
     │   GET 이면 빈 폼을 만들고
     │   POST 면 입력값 검증 → 저장
     ├──────────────► [members/forms.py]  Form : 입력값 검증
     │                        │
     │                        ▼
     │                 [members/models.py] Model : DB 저장
     ▼
[templates/members/signup.html]  Template : HTML 만들기
     │
     ▼
[브라우저]  완성된 HTML 응답
```

**각 역할을 한 문장으로**

| 구성 | 역할 | 비유 |
|---|---|---|
| **URL** | 어떤 주소를 어떤 함수로 보낼지 | 안내 데스크 |
| **View** | 요청을 받아 처리하고 응답을 만듦 | 담당 직원 |
| **Form** | 사용자 입력이 올바른지 검사 | 서류 검토 |
| **Model** | DB 테이블 (저장/조회) | 서류 보관함 |
| **Template** | 최종 HTML 화면 | 출력물 |

이 다섯 개를 **만드는 순서는 Model → Form → View → URL → Template** 이 편합니다.
안쪽(데이터)부터 만들고 바깥쪽(화면)으로 나오는 순서입니다.

---

## 1. 회원가입 / 로그인 Form 만들기

`members/forms.py` **(직접 새로 만드는 파일)**

```python
# members/forms.py

# Django Form 기능 가져옴
from django import forms

# Django 기본 인증 폼을 가져옴
from django.contrib.auth.forms import (
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

    def __init__(self, *args, **kwargs):
        # 부모(UserCreationForm)의 초기화를 먼저 실행
        super().__init__(*args, **kwargs)

        # 모든 입력 요소에 css 클래스 추가함
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class LoginForm(AuthenticationForm):
    """회원 로그인 form 입니다."""

    def __init__(self, request=None, *args, **kwargs):
        # Django 기본 AuthenticationForm 을 초기화 함
        super().__init__(request, *args, **kwargs)

        # 아이디 입력 필드 css 지정
        self.fields['username'].widget.attrs.update({'class': 'form-control'})

        # 비밀번호 입력 필드 css 지정
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
```

### Form 은 왜 쓰나요?

HTML로 `<input>` 을 직접 다 쓰고, 뷰에서 `request.POST['username']` 을 하나하나 꺼내서 검사할 수도 있습니다. 하지만 그러면:

- 필수값 검사, 길이 검사, 이메일 형식 검사, 중복 검사를 **전부 직접** 짜야 하고
- 오류가 났을 때 사용자가 입력한 값을 다시 채워 넣는 것도 직접 해야 하고
- CSRF, XSS 같은 보안 처리도 놓치기 쉽습니다.

Form을 쓰면 **입력칸 생성 + 검증 + 오류 메시지 + 값 복원**을 Django가 다 해 줍니다.

### ModelForm 과 Meta 클래스

`UserCreationForm` 은 **ModelForm** 의 한 종류입니다. ModelForm은 "모델을 보고 폼을 자동 생성"합니다.

```python
class Meta:
    model = Member          # 어떤 모델을 쓸지
    fields = (...)          # 그 중 어떤 필드를 화면에 낼지
```

`Meta` 는 "이 폼에 대한 설명서"를 담는 내부 클래스입니다.
모델에 `max_length=50`, `unique=True` 를 이미 적어 놨으므로, 폼은 그 규칙을 그대로 가져와 검사합니다. **같은 규칙을 두 번 쓸 필요가 없습니다.**

`fields` 대신 `exclude = ('...',)` 로 "이것만 빼고 전부"라고 쓸 수도 있지만, 실수로 위험한 필드(`is_superuser` 등)가 노출될 수 있어 `fields` 로 **명시하는 쪽이 안전**합니다.

### UserCreationForm 을 상속하는 이유

비밀번호는 **평문으로 저장하면 안 됩니다.** `UserCreationForm` 은

- `password1`, `password2` 두 칸을 자동으로 만들고
- 두 값이 같은지 확인하고
- `AUTH_PASSWORD_VALIDATORS` 규칙(8자 이상, 숫자만 안 됨 등)을 검사하고
- 저장할 때 `set_password()` 로 **해시**해서 저장합니다.

이걸 직접 만들면 실수하기 쉽고 보안 사고로 이어집니다.

> ### ⚠️ 자주 하는 실수 3가지
>
> **1) `Meta.fields` 에 `password1`, `password2` 를 넣는 것**
> ```python
> fields = ('username', ..., 'password1', 'password2')   # ❌
> ```
> ModelForm의 `fields` 에는 **모델에 있는 필드만** 적을 수 있습니다.
> `password1/2` 는 폼이 따로 만드는 것이라 여기 적으면
> `FieldError: Unknown field(s) (password1, password2) specified for Member` 가 납니다.
> 적지 않아도 화면에는 **자동으로 나옵니다.**
>
> **2) `super.__init__()` 처럼 괄호 빼먹기**
> ```python
> super.__init__(*args, **kwargs)     # ❌ AttributeError
> super().__init__(*args, **kwargs)   # ✅
> ```
> `super` 는 함수라서 `super()` 로 **호출**해야 부모 객체가 나옵니다.
>
> **3) `attrs` 를 함수처럼 호출하기**
> ```python
> field.widget.attrs('class', 'form-control')          # ❌ TypeError
> field.widget.attrs.update({'class': 'form-control'}) # ✅
> ```
> `attrs` 는 HTML 속성을 담는 **딕셔너리**입니다.

### `__init__` 을 오버라이드해서 CSS 넣기

폼이 만들어지는 순간에 끼어들어서 모든 입력칸에 `class="form-control"` 을 붙이는 코드입니다.
이렇게 하면 HTML에서 `{{ form.as_p }}` 한 줄만 써도 부트스트랩 스타일이 적용됩니다.
`super().__init__()` 을 **먼저** 호출해야 `self.fields` 가 만들어져 있다는 점이 중요합니다.

---

## 2. View 작성

`members/views.py`

```python
# members/views.py

# Django 로그인/로그아웃 기능
from django.contrib.auth import login, logout

# 성공 안내 메시지
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# HTML 출력과 URL 이동 기능
from django.shortcuts import render, redirect

# 회원 관련 form
from .forms import SignUpForm, LoginForm


def signup(request):
    """회원 가입 처리 view 입니다"""
    # POST 요청이면, 사용자가 입력한 데이터를 받음
    if request.method == 'POST':
        # 일반 데이터와 업로드 파일을 form 에 전달함
        form = SignUpForm(request.POST, request.FILES)

        # 입력값 검증 후 수행
        if form.is_valid():
            # 입력값들이 모두 유효하면 db에 저장. 비밀번호는 해시로 저장됨
            member = form.save()

            # 가입한 사용자를 즉시 로그인 처리함 (Django Session 생성)
            login(request, member)

            messages.success(
                request,
                f"{member.display_name}님, 회원 가입이 완료되었습니다. 바로 로그인되었습니다."
            )

            # 첫 페이지로 이동
            return redirect('home')
        else:
            # 검증에 실패한 경우, 실패했다는 사실을 먼저 눈에 띄게 알려줌
            # 구체적으로 무엇이 잘못됐는지는 각 입력칸 아래 빨간 글씨로
            # {{ form.as_p }} 가 자동으로 출력해 줌 (6번 항목 참고)
            messages.error(
                request,
                "회원 가입에 실패했습니다. 아래 빨간 글씨로 표시된 항목을 확인해주세요."
            )
    else:
        # GET 요청이면 빈 회원가입 form을 만듦
        form = SignUpForm()

    # GET 이거나, POST 인데 입력값이 잘못된 경우
    # (잘못된 경우 form 안에 오류 메시지가 들어 있음)
    return render(request, 'members/signup.html', {'form': form})


def login_view(request):
    """회원 로그인 뷰 입니다."""
    form = LoginForm(
        request=request,
        data=request.POST or None,
    )

    # POST 요청이면서 인증에 성공했다면
    if request.method == 'POST' and form.is_valid():
        # 인증된 회원 객체를 가져옴
        member = form.get_user()

        # Django 세션에 사용자 인증 정보를 저장
        login(request, member)

        messages.success(request, f"{member.display_name}님 로그인 되었습니다.")

        return redirect('home')

    # POST 요청인데 인증에 실패했다면
    elif request.method == 'POST':
        messages.error(
            request,
            "로그인에 실패했습니다. 아이디와 비밀번호를 다시 확인해주세요."
        )

    return render(request, 'members/login.html', {'form': form})


@login_required
def logout_view(request):
    """현재 세션의 로그인 인증 정보를 제거"""
    logout(request)
    messages.success(request, "로그아웃 되었습니다.")

    return redirect('home')
```

### View 가 하는 일

View는 **`request` 를 받아서 `response` 를 돌려주는 함수**입니다. 이 규칙만 지키면 됩니다.
`render()` 와 `redirect()` 는 응답을 편하게 만들어 주는 도구입니다.

- `render(request, '템플릿경로', {템플릿에 넘길 값})` → HTML 응답을 만듭니다.
- `redirect('URL이름')` → "저 주소로 다시 가라"는 응답(302)을 보냅니다.

### GET / POST 를 나누는 이유 — 가장 중요한 패턴

같은 주소 `/members/signup/` 이 두 가지 일을 합니다.

| 요청 | 언제 | 하는 일 |
|---|---|---|
| **GET** | 주소창에 입력하거나 링크 클릭 | **빈 폼**을 보여줌 |
| **POST** | 폼에서 "회원 가입" 버튼 클릭 | 입력값 **검증 후 저장** |

그래서 뷰의 뼈대는 항상 이 모양입니다. 외워두면 좋습니다.

```python
def 뷰이름(request):
    if request.method == 'POST':
        form = 폼클래스(request.POST)
        if form.is_valid():
            form.save()
            return redirect('어디로')     # 성공 → 다른 주소로 이동
    else:
        form = 폼클래스()                 # GET → 빈 폼
    return render(request, '템플릿', {'form': form})   # 실패하면 오류와 함께 다시 그림
```

> ### ⚠️ 들여쓰기 실수 주의
>
> ```python
>     if request.method == 'POST':
>         form = SignUpForm(request.POST, request.FILES)
>         if form.is_valid():
>             ...
>             return redirect('home')
>         else:
>             form = SignUpForm()                    # ❌ else 위치가 틀림
>
>         return render(...)                          # ❌ POST 안에만 있음
> ```
> 이렇게 쓰면 **GET 요청일 때 함수가 아무것도 return 하지 않아서**
> `The view didn't return an HttpResponse object. It returned None instead.` 오류가 납니다.
> `else` 는 `if form.is_valid()` 가 아니라 **`if request.method == 'POST'` 와 짝**이어야 하고,
> `return render(...)` 는 **함수 맨 마지막**에 있어야 합니다.

### 성공하면 왜 redirect 하나요? (PRG 패턴)

저장 성공 후 `render()` 로 화면을 그려 주면, 사용자가 **새로고침(F5)** 했을 때 브라우저가 POST를 다시 보내서 **중복 가입**이 됩니다.
`redirect()` 로 다른 주소로 보내면 새로고침해도 GET만 다시 일어나서 안전합니다.
이걸 **POST-Redirect-GET (PRG) 패턴** 이라고 합니다. 폼 처리의 기본 규칙입니다.

### `request.FILES` 는 왜 따로 넘기나요?

일반 텍스트 입력은 `request.POST`, 업로드된 **파일**은 `request.FILES` 에 따로 담깁니다.
프로필 사진을 받으려면 폼에 둘 다 넘겨야 합니다.

```python
form = SignUpForm(request.POST, request.FILES)
```

그리고 HTML `<form>` 태그에 `enctype="multipart/form-data"` 가 **반드시** 있어야 합니다. 없으면 파일이 서버로 오지 않습니다.

### `login()` 과 세션

`login(request, member)` 는 **세션(session)** 을 만듭니다.

```text
1. 서버가 세션 데이터를 django_session 테이블에 저장
2. 브라우저에 sessionid 라는 쿠키를 내려줌
3. 이후 요청마다 브라우저가 그 쿠키를 보냄
4. 서버가 쿠키로 "아, 이 사람은 홍길동" 이라고 알아봄
```

HTTP는 원래 **누가 누군지 기억하지 못하는(stateless)** 프로토콜입니다. 세션이 그 기억을 대신해 줍니다.
가입 직후 `login()` 을 호출해 주면 사용자가 다시 로그인할 필요가 없어 편합니다.

### `messages` 프레임워크

```python
messages.success(request, "회원 가입이 완료되었습니다.")
```

**다음 화면에서 딱 한 번만 보여줄 메시지**를 저장합니다. redirect로 페이지가 바뀌어도 메시지가 살아남고, 한 번 표시되면 자동으로 사라집니다.
`success` 외에 `info`, `warning`, `error` 가 있습니다.
표시하려면 템플릿에 `{% if messages %}` 블록을 넣어야 합니다 (아래 5번 참고).

### `@login_required` 데코레이터

로그인한 사람만 이 뷰를 쓸 수 있게 막습니다. 로그인 안 한 사람은 로그인 페이지로 자동 이동됩니다.
어디로 보낼지는 `settings.py` 의 `LOGIN_URL` 로 정합니다. 안 정하면 Django 기본값 `/accounts/login/` 으로 보내서 **404**가 납니다.

`@` 로 시작하는 것을 **데코레이터**라고 하며, "함수를 실행하기 전에 검사 하나를 끼워 넣는" 문법입니다.

### `AuthenticationForm` 의 특이한 점

로그인 폼만 첫 인자로 `request` 를 받습니다.

```python
form = LoginForm(request=request, data=request.POST or None)
```

- `request` 가 필요한 이유 : 인증 실패 횟수 기록 등 요청 정보를 쓰기 때문입니다.
- `request.POST or None` : GET일 때 `request.POST` 는 빈 딕셔너리인데, 빈 값이면 `None` 이 들어가서 **"아직 제출 안 한 폼"** 으로 취급됩니다. `None` 을 안 주면 처음 화면부터 "이 항목을 입력하세요" 오류가 뜹니다.
- `form.get_user()` : 검증에 성공했을 때 인증된 사용자 객체를 꺼냅니다. `form.save()` 가 아닙니다 (로그인은 저장하는 게 아니니까요).

---

## 3. 앱 URL 만들기

`members/urls.py` **(직접 새로 만드는 파일)**

```python
# members/urls.py

# URL을 View와 연결하기 위한 path
from django.urls import path

# 현재 앱의 View 가져옴
from . import views

# URL namespace 설정
app_name = "members"

urlpatterns = [
    # /members/signup/
    path("signup/", views.signup, name="signup"),

    # /members/login/
    path("login/", views.login_view, name="login"),

    # /members/logout/
    path("logout/", views.logout_view, name="logout"),
]
```

### `path()` 의 세 인자

```python
path("signup/", views.signup, name="signup")
      ①주소       ②실행할 함수    ③이 주소의 별명
```

### `name` 을 왜 붙이나요? — 하드코딩 금지

템플릿에서 주소를 직접 쓰지 않고 **이름으로 부릅니다.**

```html
<a href="/members/signup/">가입</a>              <!-- ❌ 주소가 바뀌면 전부 수정 -->
<a href="{% url 'members:signup' %}">가입</a>    <!-- ✅ urls.py만 고치면 됨 -->
```

나중에 `/members/` 를 `/user/` 로 바꿔도 HTML은 한 줄도 안 고쳐도 됩니다.

### `app_name` 과 namespace

`app_name = "members"` 를 선언하면 이름 앞에 앱 이름을 붙여야 합니다 → `members:signup`.
앱마다 `signup`, `list`, `detail` 같은 흔한 이름이 겹치기 때문에 **`앱이름:이름`** 형태로 구분하는 것입니다.
`boards` 앱을 만들면 `boards:list`, `members:list` 처럼 충돌 없이 쓸 수 있습니다.

> **자주 하는 실수** : `name="signup/"` 처럼 슬래시를 붙이는 것.
> `name` 은 **주소가 아니라 별명**입니다. 슬래시를 붙이면 템플릿의 `{% url 'members:signup' %}` 와 이름이 달라서
> `NoReverseMatch: Reverse for 'signup' not found` 오류가 납니다.

---

## 4. 프로젝트 URL과 연결

`config/urls.py`

```python
# 개발 중에 업로드 파일(media)을 보여주기 위해 필요함
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin

# 앱의 urls.py 를 통째로 가져다 붙이려면 include 가 필요함
from django.urls import include, path

# 첫 페이지를 templates/home.html 로 바로 보여주기 위해 사용
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),

    # 첫 페이지 => views 에서 redirect('home') 이 찾는 이름
    path("", TemplateView.as_view(template_name="home.html"), name="home"),

    # /members/ 로 시작하는 주소는 members/urls.py 가 처리함
    path("members/", include("members.urls")),
]

# 개발 모드(DEBUG=True)일 때만 업로드된 사진을 브라우저에서 볼 수 있게 함
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
```

### `include()` 가 하는 일

```text
/members/signup/
 └──┬──┘└──┬──┘
    │      └── members/urls.py 가 처리 ("signup/")
    └───────── config/urls.py 가 처리 ("members/")
```

주소의 **앞부분만 잘라서** 나머지를 앱에게 넘깁니다.
그래서 `members/urls.py` 안에는 `"signup/"` 만 적으면 되고, 실제 주소는 `/members/signup/` 이 됩니다.

**왜 나누나요?** 앱마다 URL 파일을 따로 두면 앱을 다른 프로젝트로 복사해도 그대로 동작하고, 최상위 파일이 수백 줄로 길어지지 않습니다.

### 첫 페이지(`name="home"`)가 필요한 이유

뷰에서 `redirect('home')` 이라고 썼으므로 **`home` 이라는 이름의 URL이 반드시 존재해야** 합니다.
없으면 `NoReverseMatch: Reverse for 'home' not found` 가 납니다.
`TemplateView` 는 "그냥 HTML 하나만 보여주면 될 때" 뷰 함수를 안 만들고 쓸 수 있는 클래스형 뷰입니다.

### `static(...)` 이 필요한 이유

`runserver` 는 개발용 서버라 업로드된 파일(media)을 자동으로 서비스해 주지 않습니다.
이 두 줄이 있어야 `/media/members_photos/...` 주소로 올린 사진이 보입니다.
`if settings.DEBUG:` 로 감싸는 이유는 **실제 배포 환경에서는 nginx 같은 웹서버가 이 역할을 훨씬 빠르게 처리**하기 때문입니다. 개발 중에만 쓰는 임시 방편입니다.

---

## 5. 템플릿(HTML) 작성

### `templates/home.html` — 첫 페이지

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>첫 페이지</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <h1>회원 / 게시판 연습 프로젝트</h1>

    <!-- 로그인 성공, 회원가입 완료 같은 안내 메시지 출력 -->
    {% if messages %}
        <ul>
            {% for message in messages %}
                <li>{{ message }}</li>
            {% endfor %}
        </ul>
    {% endif %}

    <!-- user 는 context_processors 의 auth 덕분에 항상 쓸 수 있음 -->
    {% if user.is_authenticated %}
        <p>{{ user.display_name }}님 반갑습니다.</p>
        <a href="{% url 'members:logout' %}">로그아웃</a>
    {% else %}
        <a href="{% url 'members:signup' %}">회원가입</a>
        <a href="{% url 'members:login' %}">로그인</a>
    {% endif %}
</body>
</html>
```

### `templates/members/signup.html`

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>회원가입</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <h1>회원 가입</h1>
    <!-- 파일 업로드가 있으므로 enctype 속성과 post 전송이어야 함 -->
    <form method="post" enctype="multipart/form-data">
        <!-- Django CSRF 공격 방지 토큰 -->
        {% csrf_token %}

        <!-- Django Form 을 자동 출력 -->
        {{ form.as_p }}

        <button type="submit">회원 가입</button>
    </form>
    <a href="{% url 'members:login' %}">로그인</a>
</body>
</html>
```

### `templates/members/login.html`

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>로그인</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <h1>로그인</h1>
    <form method="post">
        <!-- POST form은 CSRF 토큰 사용함 -->
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">로그인</button>
    </form>
    <a href="{% url 'members:signup' %}">회원가입</a>
</body>
</html>
```

### 템플릿 문법 정리

| 문법 | 뜻 |
|---|---|
| `{{ 변수 }}` | 값 출력 |
| `{% 태그 %}` | 로직 (if, for, url, csrf_token ...) |
| `{% load static %}` | `{% static %}` 태그를 쓰기 위한 선언. **파일 위쪽에 한 번** |
| `{% static 'css/style.css' %}` | `/static/css/style.css` 주소로 변환 |
| `{% url 'members:signup' %}` | `/members/signup/` 주소로 변환 |
| `{% csrf_token %}` | POST 폼마다 **필수** |

### `{% csrf_token %}` 은 왜 필수인가요?

CSRF(사이트 간 요청 위조)는 **다른 사이트가 사용자 몰래 우리 사이트로 요청을 보내는 공격**입니다.
Django는 폼마다 무작위 토큰을 심어두고, 그 토큰이 없는 POST 요청은 거부합니다.
빼먹으면 `403 Forbidden - CSRF verification failed` 가 납니다. **POST 폼에는 무조건 넣는다**고 외우세요.

### `{{ form.as_p }}` 가 만들어 주는 것

라벨 + 입력칸 + 도움말 + **오류 메시지**까지 `<p>` 태그로 감싸서 한 번에 출력합니다.
`as_p` 대신 `as_div`(Django 권장), `as_table`, `as_ul` 도 있습니다.

칸마다 위치를 직접 잡고 싶으면 하나씩 꺼내 쓸 수도 있습니다.

```html
{{ form.username.label_tag }}
{{ form.username }}
{{ form.username.errors }}
```

### 입력값이 틀리면 어떻게 되나요?

뷰가 `render()` 로 **같은 페이지를 다시** 그리는데, 이때 `form` 안에는

- 사용자가 입력했던 값 (다시 타이핑 안 해도 됨)
- 무엇이 틀렸는지에 대한 오류 메시지

가 들어 있고, `{{ form.as_p }}` 가 그걸 자동으로 화면에 표시합니다.

```text
사용자의 회원 아이디은/는 이미 존재합니다.
비밀번호는 최소 4자 이상이어야 합니다.
비밀번호가 일치하지 않습니다.
```

**"가입 버튼을 눌렀는데 같은 화면이 나온다" 면 오류가 난 것입니다.** 다음 6번 항목에서 이 오류를 훨씬 눈에 잘 띄게 만듭니다.

---

## 6. 가입/로그인 성공·실패를 화면에서 확실히 보여주기

### 처음엔 왜 성공했는지 실패했는지 구분이 안 갔을까

`{{ form.as_p }}` 는 오류가 나면 분명히 `<ul class="errorlist">` 태그로 오류 문구를 출력합니다.
문제는 **CSS를 아무것도 안 입혔을 때**입니다. 오류 문구든 원래 있던 도움말이든 전부 같은 검정 글씨, 같은 크기로 나오기 때문에 다음처럼 보입니다.

```text
비밀번호:
다른 개인 정보와 유사한 비밀번호는 사용할 수 없습니다.     ← 도움말(항상 나옴, 오류 아님)
비밀번호는 최소 8자 이상이어야 합니다.                     ← 도움말(항상 나옴, 오류 아님)
...
이 비밀번호는 너무 짧습니다. 최소 8자 이상이어야 합니다.    ← 진짜 오류(이번에만 나옴)
```

넷 다 똑같이 생겨서, 실제로 실패했는데도 "그냥 안내문이 몇 줄 있나보다" 하고 지나치기 쉽습니다.
가입 성공 메시지도 마찬가지로 `home.html` 맨 위에 검은 글씨 한 줄로만 나와서 눈에 잘 안 띕니다.

**즉, 코드는 정상 동작하고 있었는데 "결과를 알려주는 방식"이 부실했던 것입니다.** 세 가지를 고칩니다.

### ① 실패했을 때 상단에 안내 배너 추가

`members/views.py` 의 `signup()` 에 `else:` 를 추가해서, 검증에 실패하면 성공 메시지와 대칭되는 실패 메시지를 남깁니다. (전체 코드는 위 2번 항목 참고)

```python
if form.is_valid():
    ...
    messages.success(request, f"{member.display_name}님, 회원 가입이 완료되었습니다. 바로 로그인되었습니다.")
    return redirect('home')
else:
    # 무엇이 틀렸는지는 form.as_p 가 알아서 보여주므로,
    # 여기서는 "실패했다"는 사실 자체를 눈에 띄게 알려주기만 함
    messages.error(request, "회원 가입에 실패했습니다. 아래 빨간 글씨로 표시된 항목을 확인해주세요.")
```

`login_view()` 에도 실패했을 때만 실행되는 `elif request.method == 'POST':` 분기를 추가해 같은 방식으로 처리합니다.

`messages.success()` 와 `messages.error()` 는 둘 다 같은 messages 프레임워크를 쓰지만 **태그(tag)** 가 다릅니다.
템플릿에서 `{{ message.tags }}` 로 그 태그 이름(`success`, `error`, `info`, `warning`)을 그대로 꺼낼 수 있고, 이걸 CSS 클래스로 쓰면 종류별로 다른 색을 입힐 수 있습니다 (③ 참고).

### ② signup.html / login.html 에도 메시지 블록 추가

`{% if messages %}` 블록은 원래 `home.html` 에만 있었습니다. 그런데 가입/로그인이 **실패하면 페이지가 이동하지 않고** 같은 폼 화면이 다시 그려지므로, 그 실패 메시지를 보려면 **signup.html, login.html 에도 각각** 메시지 블록이 있어야 합니다.

```html
<!-- templates/members/signup.html, templates/members/login.html 공통 -->
{% if messages %}
    <ul class="messages">
        {% for message in messages %}
            <li class="{{ message.tags }}">{{ message }}</li>
        {% endfor %}
    </ul>
{% endif %}
```

`<li class="{{ message.tags }}">` 부분이 핵심입니다. 성공이면 `<li class="success">`, 실패면 `<li class="error">` 로 렌더링되어 다음 ③번의 CSS가 자동으로 알맞은 색을 입혀 줍니다.

### ③ style.css 로 "오류다운 모습" 만들기

`static/css/style.css` 에 아래 내용을 추가합니다.

```css
/* 회원가입 완료 / 실패, 로그인 성공 / 실패 등 안내 배너 */
.messages {
    list-style: none;
    padding: 0;
    margin: 0 0 16px;
}

.messages li {
    padding: 10px 14px;
    margin-bottom: 8px;
    border-radius: 4px;
    font-weight: bold;
}

.messages .success {
    background: #e6f4ea;
    color: #1e7e34;
    border: 1px solid #b7dfc0;
}

.messages .error {
    background: #fdecea;
    color: #c0392b;
    border: 1px solid #f5c2c0;
}

/* Django Form 이 자동으로 만들어 주는 항목별 오류 목록(빨간 글씨) */
form ul.errorlist {
    list-style: none;
    padding: 0;
    margin: 4px 0;
    color: #c0392b;
    font-weight: bold;
    font-size: 0.9em;
}

/* 입력칸 아래 도움말(회색, 작은 글씨) — 오류와 겉모습이 겹치지 않게 함 */
form .helptext {
    display: block;
    color: #888888;
    font-size: 0.85em;
    font-weight: normal;
}
```

포인트는 **오류(errorlist)는 빨간 굵은 글씨, 도움말(helptext)은 회색 작은 글씨**로 서로 확실히 다르게 만드는 것입니다.
`errorlist`, `helptext` 는 Django가 폼을 `as_p` 로 출력할 때 **자동으로 붙여주는 클래스 이름**이라, 우리 CSS가 별도 손댈 것 없이 바로 적용됩니다.

> **CSS를 고쳤는데 화면이 그대로면?** 브라우저가 예전 `style.css` 를 **캐시**해 둔 것일 수 있습니다.
> `Ctrl + Shift + R` (강력 새로고침)로 캐시를 무시하고 다시 불러오세요.

### 결과적으로 이렇게 바뀝니다

| 상황 | 이전 | 이후 |
|---|---|---|
| 가입 성공 | 검은 글씨 한 줄, 눈에 안 띔 | 초록 배경 배너 + `redirect('home')` 으로 화면 자체가 바뀜 |
| 가입 실패 | 도움말과 구분 안 되는 검은 글씨 | 빨간 배경 배너("가입에 실패했습니다") + 항목별 빨간 굵은 글씨 |
| 로그인 실패 | 문구는 있으나 안 보임 | 빨간 배경 배너 + "아이디/비밀번호 확인" 안내 |

### ④ 테스트용으로 비밀번호 규칙 완화하기

`config/settings.py` 의 `AUTH_PASSWORD_VALIDATORS` 는 기본값이 4개나 켜져 있어서, 학습 중 계정을 가볍게 만들어보기엔 너무 빡빡합니다.
검증기 목록에서 필요한 것만 남기고 나머지는 **지우지 않고 주석 처리**해서, 필요할 때 다시 켤 수 있게 합니다.

```python
# 학습/테스트 단계라 계정을 편하게 만들 수 있도록 규칙을 완화함
# 최소 길이만 검사하고(4자), 나머지 3개는 주석으로 꺼 둠
# 실제 서비스로 배포할 때는 아래 주석을 풀어서 다시 켤 것
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 4,
        },
    },
    # 이름/아이디/이메일과 비슷한 비밀번호 금지
    # {
    #     "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    # },
    # "123456", "password" 같은 흔한 비밀번호 금지
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    # 숫자로만 이루어진 비밀번호 금지
    # {
    #     "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    # },
]
```

**검증기 하나하나가 하는 일**

| 검증기 | 막는 것 | 지금 상태 |
|---|---|---|
| `MinimumLengthValidator` | 너무 짧은 비밀번호 (`OPTIONS.min_length` 로 길이 조절) | ✅ 켜둠, 8자 → 4자로 완화 |
| `UserAttributeSimilarityValidator` | 아이디/이름/이메일과 비슷한 비밀번호 (`hong1234` 처럼 예측하기 쉬운 것) | ⏸ 꺼둠 |
| `CommonPasswordValidator` | 흔히 쓰는 비밀번호 2만 개 목록과 대조 (`password`, `123456` 등) | ⏸ 꺼둠 |
| `NumericPasswordValidator` | 숫자로만 이루어진 비밀번호 (`12345678` 등) | ⏸ 꺼둠 |

> **왜 지우지 않고 주석으로 남겨두나요?**
> 학습이 끝나고 실제로 배포할 서비스를 만들 때는 이 4개를 **전부 다시 켜는 것이 정석**입니다.
> 지금 지워버리면 나중에 무엇을 다시 켜야 하는지 기억이 안 나므로, 코드 자체를 "설명서" 삼아 남겨둡니다.
> 이런 식으로 "당장은 끄지만 나중에 되돌릴 것"을 주석으로 남기는 습관은 `INSTALLED_APPS` 의 `'boards'` 를 주석 처리했던 것과 같은 패턴입니다.

---

## 7. settings.py 에 인증 관련 설정 추가

```python
# @login_required 가 로그인 안 된 사용자를 보낼 주소
# 지정하지 않으면 Django 기본값인 /accounts/login/ 으로 보내서 404가 남
LOGIN_URL = "members:login"

# 로그인 성공 후 갈 기본 주소 (직접 redirect 하면 그쪽이 우선)
LOGIN_REDIRECT_URL = "home"

# 로그아웃 후 이동할 기본 주소
LOGOUT_REDIRECT_URL = "home"

# 사용자의 비활성 시간이 30분이 넘으면 세션을 만료시킴
SESSION_COOKIE_AGE = 30 * 60

# 요청이 발생할 때마다 세션 만료 시간 다시 30분 연장
SESSION_SAVE_EVERY_REQUEST = True
```

- `SESSION_COOKIE_AGE` : 초 단위입니다. `30 * 60` = 30분.
- `SESSION_SAVE_EVERY_REQUEST = True` : 사용자가 계속 활동하면 시간이 연장됩니다. 이게 없으면 로그인 후 30분이 지나면 활동 중이어도 로그아웃됩니다.
- 비밀번호 규칙은 `AUTH_PASSWORD_VALIDATORS` 가 담당합니다. 연습 중 짧은 비밀번호를 쓰고 싶으면 이 리스트를 잠시 비워도 되지만, **실제 서비스에서는 반드시 켜 두세요.**

---

## 8. 실행하고 확인하기

```bash
python manage.py runserver
```

| 확인 순서 | 주소 | 기대 결과 |
|---|---|---|
| 1 | `http://127.0.0.1:8000/` | 첫 페이지, 회원가입/로그인 링크 |
| 2 | `/members/signup/` | 가입 폼 (아이디, 이름, 이메일, 성별, 나이, 전화, 사진, 비번 2칸) |
| 3 | 가입 제출 | 첫 페이지로 이동 + "회원 가입이 완료되었습니다." + 이름 표시 |
| 4 | `/admin/` | 회원 목록에 방금 가입한 계정이 보임 |
| 5 | `/members/logout/` | 첫 페이지 + "로그아웃 되었습니다." |
| 6 | `/members/login/` | 로그인 후 첫 페이지 + 인사 메시지 |

DB에서 직접 확인하려면 MySQL Workbench에서:

```sql
SELECT id, username, display_name, email, gender, age, date_joined
FROM django_member_board.members_member;
```

비밀번호 컬럼이 `pbkdf2_sha256$...` 처럼 알아볼 수 없는 문자열이면 **해시 저장이 잘 된 것**입니다.

---

## 9. 자주 만나는 오류 정리

| 오류 메시지 | 원인과 해결 |
|---|---|
| `ModuleNotFoundError: No module named 'members'` | 앱 폴더가 프로젝트 루트에 없음 (templates 안에 있는 등). 위치를 옮길 것 |
| `ModuleNotFoundError: No module named 'boards'` | 안 만든 앱을 `INSTALLED_APPS` 에 적음 |
| `TemplateDoesNotExist: members/login.html` | 파일 이름이 다름(`signin.html` 등) 또는 `TEMPLATES.DIRS` 미설정 |
| `NoReverseMatch: Reverse for 'signup' not found` | `urls.py` 의 `name` 오타, `app_name` 누락, 또는 `include` 안 함 |
| `The view didn't return an HttpResponse object` | 뷰에 `return` 이 빠진 경로가 있음 (들여쓰기 확인) |
| `FieldError: Unknown field(s) (password1, password2)` | ModelForm `Meta.fields` 에 폼 전용 필드를 적음 |
| `AttributeError: 'super' object has no attribute` | `super.__init__` → `super().__init__` |
| `403 CSRF verification failed` | `{% csrf_token %}` 누락 |
| 사진이 저장은 되는데 안 보임 | `config/urls.py` 의 `static(...)` 누락, 또는 `MEDIA_URL/MEDIA_ROOT` 미설정 |
| 사진이 아예 안 올라감 | `<form>` 에 `enctype="multipart/form-data"` 누락, 뷰에 `request.FILES` 누락 |
| `Error: That port is already in use` | 이전 runserver가 안 꺼짐. `netstat -ano \| findstr :8000` 로 PID 확인 후 종료 |
| 코드를 고쳐도 반영이 안 됨 | 서버가 두 개 떠 있거나, 브라우저 캐시. 서버 완전 종료 후 재실행 |

---

## 10. 회원정보 조회 / 수정 / 탈퇴 추가하기

지금까지는 가입·로그인·로그아웃만 있었습니다. 여기에 로그인한 **본인이 자기 정보를 보고, 고치고, 계정을 지우는** 기능 세 개를 추가합니다. 게시글 CRUD(`pj설명3.md`)와 원리는 같지만, "대상이 항상 로그인한 사람 자신으로 고정된다"는 점이 다릅니다.

### `members/forms.py` 에 `ProfileForm` 추가

```python
class ProfileForm(forms.ModelForm):
    """로그인한 회원이 본인 정보를 수정하는 form 입니다."""
    class Meta:
        model = Member

        # username(아이디)은 로그인 식별자라 여기서 바꾸지 않음
        # password 는 별도 비밀번호 변경 기능에서 다룰 값이라 여기 넣지 않음
        fields = ('display_name', 'email', 'gender', 'age', 'phone', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
```

`SignUpForm`은 `UserCreationForm`을 상속해서 비밀번호 입력칸(`password1`, `password2`)까지 같이 만들었지만, `ProfileForm`은 그냥 `ModelForm`입니다. **정보 수정 화면에서 비밀번호까지 같이 바꾸게 하면 로직이 복잡해지므로(현재 비밀번호 확인 등), 이 프로젝트에서는 비밀번호 변경은 범위 밖으로 뒀습니다.** 나중에 필요하면 Django가 기본 제공하는 `PasswordChangeForm`을 별도 화면으로 추가하면 됩니다.

`fields`에 `username`도 넣지 않았습니다. 로그인 아이디는 세션·게시글 작성자 연결 등 여러 곳에서 식별자로 쓰이므로, 함부로 바꾸게 하면 꼬입니다.

### `members/views.py` 에 뷰 3개 추가

```python
@login_required
def profile(request):
    """로그인한 본인의 회원정보를 조회하는 뷰"""
    # request.user 가 곧 로그인한 회원 자신이므로, 그대로 템플릿에 넘기면 됨
    return render(request, 'members/profile.html', {'member': request.user})


@login_required
def profile_edit(request):
    """로그인한 본인의 회원정보를 수정하는 뷰"""
    # instance=request.user 로 넘기면, 수정 대상이 "로그인한 본인"으로 고정됨
    # (다른 회원의 정보를 수정하는 실수를 애초에 할 수 없음)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "회원정보가 수정되었습니다.")
        return redirect('members:profile')
    elif request.method == 'POST':
        messages.error(request, "회원정보 수정에 실패했습니다. 아래 항목을 확인해주세요.")

    return render(request, 'members/profile_form.html', {'form': form})


@login_required
def withdraw(request):
    """로그인한 본인의 회원 탈퇴(계정 삭제) 처리 뷰"""
    if request.method == 'POST':
        # 삭제하기 전에 회원 객체를 변수에 먼저 담아 둠
        # (logout() 이후에는 request.user 가 비로그인 상태로 바뀌기 때문)
        member = request.user

        # 세션을 먼저 정리(로그아웃)한 다음 계정을 삭제함
        logout(request)

        # Board.author 가 on_delete=CASCADE 이므로,
        # 이 회원이 작성한 게시글도 함께 삭제됨
        member.delete()

        messages.success(request, "탈퇴 처리되었습니다. 그동안 이용해주셔서 감사합니다.")
        return redirect('home')

    # get 요청이면 탈퇴 확인 화면만 보여줌 (실제 삭제는 위의 POST 에서만 일어남)
    return render(request, 'members/withdraw_confirm.html')
```

**왜 게시글 수정(`board_update`)처럼 `pk`를 URL로 안 받나요?**

게시판은 "몇 번 글이냐"에 따라 대상이 달라지지만(`/boards/12/update/`), 회원정보 수정은 **항상 "지금 로그인한 사람 자신"**이 대상입니다. 그래서 URL에 번호가 필요 없고(`/members/profile/edit/`), 뷰 안에서 `instance=request.user`로 대상을 직접 고정합니다. 만약 실수로 `/members/profile/edit/?id=5` 처럼 다른 사람 번호를 받아서 그 사람 정보를 수정하게 만들면, 로그인한 사람이 **다른 회원의 정보를 마음대로 바꿀 수 있는 심각한 보안 구멍**이 됩니다. "URL로 대상을 받지 않고 `request.user`로 고정한다"는 이 패턴 자체가 자기 자신의 리소스를 다루는 기능(마이페이지, 내 정보 수정 등)의 기본 원칙입니다.

**탈퇴 처리 순서가 중요합니다: `logout()` → `member.delete()`**

```python
member = request.user   # ① 삭제하기 전에 미리 변수에 담아 둠
logout(request)         # ② 세션 정리. 이 순간 request.user 는 AnonymousUser 로 바뀜
member.delete()         # ③ ①에서 담아둔 진짜 객체를 삭제
```

순서를 반대로(`delete()` 먼저, `logout()` 나중) 해도 당장 에러가 나진 않지만, "이미 지워진 계정의 세션이 잠깐 동안 살아있는" 상태가 됩니다. 로그아웃을 먼저 해서 세션부터 확실히 끊어두는 것이 안전합니다.

**탈퇴하면 게시글도 같이 사라지는 이유** — 새로 만든 코드가 아니라, `boards/models.py`의 `Board.author` 필드를 만들 때 이미 정해둔 규칙입니다.

```python
author = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,   # ← 회원이 삭제되면 그 회원의 게시글도 자동으로 삭제됨
    related_name='boards',
)
```

`member.delete()` 한 줄만 실행해도, Django가 **DB 차원에서 이 회원을 참조하는 모든 게시글을 알아서 함께 삭제**합니다. 게시글마다 따로 지우는 코드를 작성할 필요가 없습니다.

### `members/urls.py` 에 경로 3개 추가

```python
# /members/profile/  : 회원정보 조회
path("profile/", views.profile, name="profile"),

# /members/profile/edit/  : 회원정보 수정
path("profile/edit/", views.profile_edit, name="profile_edit"),

# /members/withdraw/  : 회원 탈퇴
path("withdraw/", views.withdraw, name="withdraw"),
```

### 템플릿 3개 작성

`templates/members/profile.html` (조회)

```html
<table class="board-table">
    <tr><th>아이디</th><td>{{ member.username }}</td></tr>
    <tr><th>이름</th><td>{{ member.display_name }}</td></tr>
    <tr><th>이메일</th><td>{{ member.email }}</td></tr>
    <!-- get_gender_display() : choices 가 있는 필드는 Django가 자동으로 만들어 주는 메소드.
         gender 는 DB에 'M' 이 저장되어 있어도, 이 메소드를 쓰면 '남자' 처럼
         choices 에 적어둔 사람이 읽는 이름으로 나옴 -->
    <tr><th>성별</th><td>{{ member.get_gender_display }}</td></tr>
    <tr><th>나이</th><td>{{ member.age|default:"-" }}</td></tr>
    <tr><th>전화번호</th><td>{{ member.phone|default:"-" }}</td></tr>
    <tr><th>가입일</th><td>{{ member.date_joined|date:"Y-m-d" }}</td></tr>
</table>

<div class="board-actions">
    <a href="{% url 'members:profile_edit' %}">정보 수정</a>
    <a href="{% url 'members:withdraw' %}">회원 탈퇴</a>
</div>
```

`get_<필드명>_display` 는 `choices` 옵션이 있는 필드마다 Django가 공짜로 만들어 주는 메소드입니다. `Board`의 `.board-table`, `.board-actions` CSS 클래스를 그대로 재사용했습니다 — 표와 버튼 줄이라는 생김새가 같아서, 게시판용으로 이미 만든 스타일을 회원정보 화면에도 그대로 쓸 수 있습니다.

`templates/members/profile_form.html` (수정) 은 `board_form.html`과, `templates/members/withdraw_confirm.html` (탈퇴 확인) 은 `board_confirm_delete.html`과 구조가 완전히 같습니다. **폼으로 값을 고치는 화면, 삭제 전 확인하는 화면**이라는 패턴 자체가 게시판과 동일하기 때문입니다.

### `templates/home.html` 메뉴에 링크 추가

```html
<nav>
    <a href="{% url 'boards:list' %}">게시판</a>
    {% if user.is_authenticated %}
        <a href="{% url 'members:profile' %}">회원정보</a>
    {% endif %}
</nav>
```

로그인 안 한 사람에게는 "회원정보" 링크 자체를 안 보여줍니다. (뷰에 `@login_required`가 있어서 링크 없이 주소를 직접 쳐도 로그인 페이지로 튕기긴 하지만, 애초에 못 누르게 숨겨두는 게 더 친절합니다.)

---

## 11. 2단계 체크리스트

```text
□ members/forms.py 작성 (SignUpForm, LoginForm, ProfileForm)
□ members/views.py 작성 (signup, login_view, logout_view, profile, profile_edit, withdraw)
□ members/urls.py 작성 (app_name + 6개 path)
□ config/urls.py 에 include("members.urls") 추가
□ config/urls.py 에 name="home" 인 첫 페이지 추가
□ config/urls.py 에 DEBUG용 media static(...) 추가
□ templates/home.html, members/signup.html, members/login.html 작성
□ 모든 POST form 에 {% csrf_token %}
□ 사진 있는 form 에 enctype="multipart/form-data"
□ settings 에 LOGIN_URL 지정
□ signup(), login_view() 에 실패시 messages.error() 추가
□ signup.html, login.html 에도 {% if messages %} 블록 추가
□ style.css 에 .messages, errorlist, helptext 색상 추가
□ AUTH_PASSWORD_VALIDATORS 필요한 만큼만 켜기 (나머지는 주석 처리)
□ templates/members/profile.html, profile_form.html, withdraw_confirm.html 작성
□ templates/home.html 메뉴에 로그인시에만 보이는 "회원정보" 링크 추가
□ 가입 → 로그인 → 로그아웃 브라우저에서 확인
□ 일부러 틀린 값으로 제출해서 실패 배너(빨간색)가 보이는지 확인
□ 회원정보 조회 → 수정 → 값이 반영되는지 확인
□ 회원 탈퇴 → 재로그인 시도해서 계정이 진짜 삭제됐는지 확인
□ 탈퇴한 회원이 쓴 게시글도 같이 삭제됐는지 확인 (on_delete=CASCADE)
□ /admin/ 에서 회원 데이터 확인
```

---

## 12. 다음에 할 것 (boards 앱)

게시판도 **똑같은 순서**를 반복하면 됩니다. 흐름이 같다는 걸 확인하는 것이 이 단계의 목표입니다.

```bash
python manage.py startapp boards
```

```text
1. settings.py 의 INSTALLED_APPS 에 'boards' 등록
2. boards/models.py     : Board 모델 (제목, 내용, 작성자 FK, 첨부파일, 작성일)
3. makemigrations / migrate
4. boards/admin.py      : 관리자 등록
5. boards/forms.py      : BoardForm (ModelForm)
6. boards/views.py      : 목록 / 상세 / 작성 / 수정 / 삭제 (CRUD)
7. boards/urls.py       : app_name = "boards" + path 들
8. config/urls.py       : path("boards/", include("boards.urls"))
9. templates/boards/    : list.html, detail.html, form.html
```

게시판에서 새로 배우게 될 개념:

- **ForeignKey** : 게시글이 어느 회원의 것인지 연결 (`models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`)
- **QuerySet** : `Board.objects.all()`, `.filter()`, `.order_by()` 로 데이터 조회
- **Paginator** : 목록 페이지 나누기
- **base.html + `{% extends %}`** : 지금은 HTML마다 head를 반복해서 쓰고 있는데, 공통 뼈대를 하나 만들고 상속받는 방식으로 정리
