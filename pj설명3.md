# 3단계 : 게시판 앱 만들기

> `pj설명.md`, `pj설명2.md` 에서 회원 기능(가입/로그인/로그아웃)을 만들었습니다.
> 이번엔 **게시판**입니다. 순서 자체는 회원 기능과 똑같습니다 — Model → Form → View → URL → Template.
> 다른 점은 딱 하나, 게시글에는 **"글쓴이"**가 있고, 그 글쓴이만(또는 관리자만) 수정/삭제할 수 있어야 한다는 **권한 검사**가 추가되는 것입니다.

---

## 1. 게시판 model 만들기

`boards/models.py`

```python
# boards/models.py

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
        return user.is_authenticated and self.author == user

    # 삭제 권한에 대한 메소드 추가
    def can_delete(self, user):
        """삭제 권한은 작성자 본인 또는 관리자에게 허용합니다."""
        # 작성자 본인이거나 staff/superuser 관리자이면 삭제할 수 있습니다.
        return user.is_authenticated and (self.author_id == user.id or user.is_staff or user.is_superuser)
```

### `ForeignKey` — 게시글과 회원을 연결하기

`members/models.py` 의 `Member` 는 독립된 테이블이었습니다. `Board` 는 **"누가 썼는지"** 를 알아야 하므로, 다른 테이블(Member)을 가리키는 컬럼이 필요합니다. 이게 `ForeignKey` 입니다.

```text
boards_board 테이블
┌────┬──────────┬─────────┬───────────┐
│ id │ title    │ content │ author_id │  ← author_id 컬럼이 members_member.id 를 가리킴
├────┼──────────┼─────────┼───────────┤
│ 1  │ 안녕하세요 │ ...     │ 3         │  ← 3번 회원이 쓴 글
└────┴──────────┴─────────┴───────────┘
```

- `settings.AUTH_USER_MODEL` : `"members.Member"` 문자열이 여기 들어갑니다. `from members.models import Member` 로 직접 모델을 가져와도 되지만, `settings.AUTH_USER_MODEL` 을 쓰면 **나중에 사용자 모델이 바뀌어도 이 코드는 그대로 둘 수 있어서** Django 공식 문서가 이 방식을 권장합니다.
- `on_delete=models.CASCADE` : 회원이 탈퇴(삭제)하면 그 회원이 쓴 글도 같이 삭제합니다. (다른 옵션: `SET_NULL` — 글은 남기고 작성자만 비움, `PROTECT` — 글이 있으면 회원 삭제 자체를 막음)
- `related_name='boards'` : `member.boards.all()` 처럼 **"이 회원이 쓴 글 전체"** 를 역방향으로 조회할 때 쓰는 이름입니다. 안 적으면 기본값 `board_set` 이 됩니다.

> **직접 겪은 오류** : `settings.AUTH_USER_MDDEL` 처럼 오타가 나면
> `AttributeError: module 'config.settings' has no attribute 'AUTH_USER_MDDEL'` 가 `makemigrations` 단계에서 납니다.
> 오타 하나로 앱 전체가 멈추니 이런 긴 이름은 자동완성을 쓰는 습관을 들이면 좋습니다.

### `FileField` — 첨부파일

`members/models.py` 의 `photo = models.ImageField(...)` 와 형제입니다. `ImageField` 는 이미지 파일만, `FileField` 는 어떤 파일이든 받습니다(pdf, zip, 문서 등). `upload_to='board_files/%Y/%m/'` 로 연/월 폴더에 나눠 저장되는 것도 동일한 패턴입니다.

### 왜 `can_edit`, `can_delete` 를 **모델 메소드**로 만들었을까?

권한 검사 코드를 View 안에 직접 쓸 수도 있습니다.

```python
# View에 직접 쓴다면 (비추천)
if request.user.is_authenticated and board.author == request.user:
    ...
```

문제는 이 조건문이 **수정 뷰에도, 삭제 뷰에도, 상세보기 화면(버튼을 보여줄지 말지)에도 반복해서 필요하다**는 점입니다. 모델 메소드로 한 번만 정의해두면:

```python
board.can_edit(request.user)      # View 에서
board.can_delete(request.user)    # View 에서 또
```

**"이 게시글이 규칙적으로 해야 하는 일"** 은 그 게시글의 모델에 두는 것이 Django(그리고 객체지향 프로그래밍) 방식입니다. 데이터(글쓴이)와 그 데이터를 다루는 규칙(권한 검사)을 같은 곳에 두면 나중에 규칙이 바뀌어도 **한 곳만 고치면** 됩니다.

> **직접 겪은 오류** : 처음 작성한 `can_delete` 에 `self.author_id == user_id` 라는 코드가 있었는데, `user_id` 라는 이름은 어디서도 정의된 적이 없었습니다(오타로 `user.id` 를 쓰려던 것). 이 상태로 실행하면 이 메소드가 **호출되는 순간** `NameError: name 'user_id' is not defined` 가 납니다. `makemigrations`/`migrate` 는 이 메소드를 실행하지 않으므로 그때는 안 걸리고, 실제로 삭제를 시도할 때만 터지는 오류였습니다. **모델 코드는 저장할 때가 아니라 "그 메소드를 실제로 호출할 때" 문제가 드러난다**는 걸 기억해두면 디버깅이 빨라집니다.

### `is_staff` 와 `is_superuser` — "스태프"라는 역할이 따로 있는 게 아님

```python
return user.is_authenticated and (self.author_id == user.id or user.is_staff or user.is_superuser)
```

`is_staff`, `is_superuser` 는 둘 다 `AbstractUser`(따라서 우리 `Member`)가 기본으로 가진 필드입니다. 이름만 보면 "스태프"와 "슈퍼유저"라는 서로 다른 역할이 있는 것처럼 보이지만, **이 프로젝트에는 그런 역할 구분이 없습니다.** 여기서 `or`로 두 값을 같이 검사하는 이유는 단순히 **"관리자 계정인지"를 판단하는 두 가지 신호를 둘 다 받아주는 것**입니다.

- `python manage.py createsuperuser` 로 만든 계정은 `is_staff=True`, `is_superuser=True` **둘 다 자동으로 켜집니다.**
- Django Admin(`/admin/`)에서 회원 하나를 열어서 `is_staff` 체크박스만 수동으로 켜준 경우(슈퍼유저는 아니지만 관리자 사이트 로그인은 되는 계정)도 있을 수 있습니다.

`or`로 묶어두면 이 두 경우 모두 "관리자"로 인정되어 다른 사람 글을 지울 수 있습니다. `and`로 바꾸면(`user.is_staff and user.is_superuser`) 오히려 **둘 다 켜진 사람만** 관리자로 인정하게 되어, 조건이 더 까다로워집니다 — 지금 목적(작성자 본인 아니면 관리자는 지울 수 있게)에는 `or`가 맞습니다.

> **정리** : 작성자 본인인지 확인하는 조건은 `self.author_id == user.id` **하나뿐**입니다. `is_staff`, `is_superuser`는 "역할"이 아니라 그 뒤에 붙는 **"또는 관리자라면"** 조건일 뿐입니다.

---

## 2. Board Migration 생성

```bash
python manage.py makemigrations boards
```

```bash
python manage.py migrate
```

Workbench에서

```sql
SHOW TABLES;
```

`boards_board` 테이블이 보이면 성공입니다.

> **직접 겪은 오류 1** : `python magnage.py ...` 처럼 `manage.py` 를 오타내면
> `can't open file '...\magnage.py': [Errno 2] No such file or directory` 가 납니다. 파일을 못 찾는다는 뜻이니, 명령어 철자부터 확인하세요.
>
> **직접 겪은 오류 2** : 오타를 고쳐도 테이블이 안 생겼습니다. 원인은 `config/settings.py` 의 `INSTALLED_APPS` 에 `'boards'` 가 **주석 처리**된 채로 남아 있었기 때문입니다.
> ```python
> INSTALLED_APPS = [
>     ...
>     'members',
>     # 'boards',   ← 이 상태면 Django가 boards 앱의 존재 자체를 모름
> ]
> ```
> `models.py` 를 아무리 잘 작성해도, **앱이 등록되어 있지 않으면 Django가 그 앱의 모델을 읽지 않습니다.** `startapp` 직후엔 항상 이 줄의 주석부터 확인하는 습관을 들이세요.

---

## 3. BoardForm 만들기

`boards/forms.py` **(직접 새로 만드는 파일 — 파일 이름이 정확히 `forms.py` 여야 합니다)**

```python
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
```

`members/forms.py` 의 `SignUpForm` 과 완전히 같은 패턴입니다 (`pj설명2.md` 1번 항목 참고). `ModelForm` 이 `Board` 모델을 보고 입력칸을 자동으로 만들어 줍니다.

### `fields` 에 `author` 를 안 넣는 이유

`author` 는 **"로그인한 사람이 누구인지"** 로 정해지는 값이지, 사용자가 폼에서 직접 골라 입력하는 값이 아닙니다. (만약 넣으면 회원가입 목록이 드롭다운으로 뜨고, 누구나 다른 사람 이름으로 글을 쓸 수 있게 되어버립니다 — 보안 문제!) 그래서 `fields` 목록에서 빼고, **View 안에서 서버가 직접 채워 넣습니다** (4.2번 항목 참고).

### `widgets` — 입력칸의 생김새 바꾸기

`content` 필드는 모델에서 `TextField` 로 선언했는데, ModelForm의 기본값은 이걸 한 줄짜리 `<input>` 으로 만듭니다. `widgets` 딕셔너리로 "이 필드는 이 위젯을 써라"라고 지정하면, `<textarea rows="10">` 처럼 여러 줄 입력칸으로 바뀝니다.

> **직접 겪은 오류 1** : 파일 이름을 실수로 `forms.py` 가 아니라 `homes.py` 로 만들었습니다. 그 상태에서 `views.py` 에 `from .forms import BoardForm` 이라고 써버리면
> `ModuleNotFoundError: No module named 'boards.forms'` 가 납니다. **파일 이름 = 모듈 이름** 이라서, import 문의 이름과 실제 파일 이름이 정확히 일치해야 합니다.
>
> **직접 겪은 오류 2** : `field.widget.attrs.update('class', 'form-control')` 처럼 쓰면
> `TypeError: dict.update() takes at most 1 argument (2 given)` 가 납니다. `attrs` 는 딕셔너리이므로 `update({'class': 'form-control'})` 처럼 **딕셔너리 하나**를 넘겨야 합니다. (`pj설명2.md` 1번 항목에서 `SignUpForm` 을 만들 때도 똑같은 실수를 했었습니다.)

---

## 4. 게시글 관련 View 작성

`boards/views.py`

```python
# boards/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BoardForm
from .models import Board
```

먼저 파일 맨 위에서 필요한 것들을 전부 가져옵니다. (처음엔 필요할 때마다 파일 중간중간에 import 문을 흩어 놨었는데, 한눈에 안 들어와서 맨 위로 모았습니다. 이렇게 정리하면 "이 파일이 무엇에 의존하는지"가 첫 줄만 봐도 보입니다.)

### 4.1 게시글 목록 view

```python
def board_list(request):
    """게시글 목록 페이지입니다."""
    # ORM을 사용해서 전체 게시글을 조회함: all() 사용
    # 작성자 정보도 함께 조회함: select_related로 JOIN 해서 쿼리 수를 줄임(역참조: related_name='boards')
    boards = Board.objects.select_related('author').all()

    # 주소 끝의 ?q=검색어 를 읽어옴. 없으면 빈 문자열
    query = request.GET.get('q', '').strip()

    if query:
        # 제목(title) 또는 내용(content)에 검색어가 포함된 게시글만 걸러냄
        # icontains: 대소문자 구분 없이 포함 여부 검사 (SQL의 LIKE '%검색어%' 에 해당)
        # Q(...) | Q(...) : 두 조건 중 하나라도 맞으면 됨(OR)
        boards = boards.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    # 한 페이지에 10개씩 나눠서 보여줌
    paginator = Paginator(boards, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'boards/board_list.html', {'page_obj': page_obj, 'query': query})
```

**`select_related('author')` 를 왜 붙였을까? — N+1 문제**

이게 없으면 이렇게 동작합니다.

```text
1. Board.objects.all()                     → SELECT * FROM boards_board            (쿼리 1번)
2. 목록을 화면에 뿌리면서 board.author.display_name 을 읽을 때마다
   → SELECT * FROM members_member WHERE id=1   (게시글 1번의 작성자 조회)
   → SELECT * FROM members_member WHERE id=2   (게시글 2번의 작성자 조회)
   → ... (게시글 개수만큼 반복!)
```

게시글이 10개면 **쿼리가 11번** 나갑니다(1 + 10). 이걸 **N+1 문제**라고 부릅니다. `select_related('author')` 를 붙이면 Django가 SQL `JOIN` 을 써서 게시글과 작성자를 **쿼리 1번**으로 한꺼번에 가져옵니다. `ForeignKey` 로 연결된 데이터를 화면에 같이 보여줄 땐 거의 항상 붙인다고 생각하면 됩니다.

**`Paginator` — 페이지 나누기**

```python
paginator = Paginator(boards, 10)          # 10개씩 자름
page_number = request.GET.get('page', 1)   # 주소 뒤에 ?page=2 로 넘어온 값 (없으면 1페이지)
page_obj = paginator.get_page(page_number) # 그 페이지에 해당하는 부분만 꺼냄
```

`request.GET` 은 주소창의 `?키=값` 부분입니다. `/boards/?page=2` 로 접속하면 `request.GET.get('page')` 가 `"2"` 를 돌려줍니다. `page_obj` 안에는 이번 페이지의 게시글뿐 아니라 `has_next`, `has_previous`, `paginator.count`(전체 개수), `paginator.num_pages`(전체 페이지 수) 같은 정보가 같이 들어 있어서, 템플릿에서 페이지 이동 버튼을 만들 때 그대로 씁니다 (7.1번 항목 참고).

**제목/내용 검색 — `Q` 객체와 `icontains`**

```python
query = request.GET.get('q', '').strip()

if query:
    boards = boards.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    )
```

- `request.GET.get('q', '')` : `page`와 똑같은 방식입니다. `/boards/?q=파이썬`으로 접속하면 `"파이썬"`을 돌려주고, 검색을 안 했으면 빈 문자열이 돼서 `if query:`가 거짓이 되어 필터링을 건너뜁니다.
- `title__icontains=query` : `title` 컬럼에 `query`가 (대소문자 구분 없이) **포함되어 있으면** 참. SQL로 치면 `WHERE title LIKE '%검색어%'`와 같습니다. `contains`는 대소문자를 구분하고, `icontains`의 `i`는 "insensitive"(구분 안 함)라는 뜻입니다.
- `Q(...) | Q(...)` : `.filter(title__icontains=query, content__icontains=query)`처럼 쉼표로 조건을 나열하면 **AND**(둘 다 만족)로 묶입니다. 제목에 있거나 **또는** 내용에 있으면 걸리게 하려면 **OR**가 필요한데, 이건 `Q` 객체를 `|`로 묶어야만 표현할 수 있습니다.

```text
boards.filter(title__icontains=query, content__icontains=query)
→ 제목 "그리고" 내용에 둘 다 검색어가 있어야 함 (AND, 우리가 원하는 게 아님)

boards.filter(Q(title__icontains=query) | Q(content__icontains=query))
→ 제목 "또는" 내용 어느 한쪽에만 있어도 됨 (OR, 우리가 원하는 것)
```

`boards`는 이미 만들어진 QuerySet인데, 여기에 `.filter(...)`를 한 번 더 걸었습니다. Django의 QuerySet은 **지연 평가(lazy evaluation)**라서, `select_related()`, `.filter()`를 아무리 이어 붙여도 실제 SQL은 템플릿에서 `page_obj`를 순회하며 값을 꺼낼 때 **딱 한 번** 실행됩니다. 그래서 조건을 이렇게 단계적으로 덧붙여도 성능 걱정 없이 코드를 읽기 좋게 나눌 수 있습니다.

### 4.2 새 게시글 등록 View

```python
@login_required
def board_create(request):
    """로그인한 사용자만 게시글을 작성할 수 있습니다."""
    form = BoardForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        # 바로 DB에 저장하지 않음 (author 를 먼저 채워야 하므로)
        board = form.save(commit=False)

        # 현재 로그인한 사용자를 작성자로 지정함
        board.author = request.user

        # db에 저장 처리 (ORM에 의해 INSERT INTO 문 실행됨)
        board.save()

        messages.success(request, "게시글이 등록되었습니다.")
        return redirect('boards:list')
    elif request.method == 'POST':
        messages.error(request, "게시글 등록에 실패했습니다. 아래 항목을 확인해주세요.")

    return render(request, 'boards/board_form.html', {'form': form, 'mode': '등록'})
```

**핵심: `form.save(commit=False)`**

`form.save()` 를 바로 부르면 `title`, `content`, `attachment` 만 채워진 채로 즉시 DB에 저장을 시도합니다. 그런데 `author` 는 **`NOT NULL`** 컬럼이라 빠지면 저장이 실패합니다. `commit=False` 를 주면 **"DB에 저장하지 말고, 값이 채워진 Board 객체만 나에게 돌려줘"** 라는 뜻이 됩니다. 그 객체에 `board.author = request.user` 를 채운 다음, `board.save()` 로 진짜 저장을 실행합니다.

```text
form.save(commit=False)   →  메모리에만 Board(title=..., content=...) 객체 생성 (아직 DB 아님)
board.author = request.user  →  빠진 값 채움
board.save()               →  이제 진짜 INSERT INTO 실행
```

`@login_required` 를 함수 맨 위에 붙였으므로, 로그인 안 한 사람이 `/boards/create/` 로 들어오면 `LOGIN_URL`(로그인 페이지)로 자동으로 보내집니다 (`pj설명2.md` 2번 항목 참고).

### 4.3 게시글 상세 조회 View

```python
def board_detail(request, pk):
    """게시글 상세 조회 뷰"""
    # 받은 글번호(pk)로 select 조회해 옴
    board = get_object_or_404(Board, pk=pk)

    # 조회수 1 증가 처리
    board.read_count += 1
    # read_count 필드만 db 테이블의 해당 글에 update 함
    board.save(update_fields=['read_count'])

    return render(request, 'boards/board_detail.html', {
        'board': board,
        # 템플릿에서는 인자가 필요한 메소드를 직접 호출할 수 없으므로
        # can_edit(user), can_delete(user) 결과를 뷰에서 미리 계산해서 넘겨줌
        'can_edit': board.can_edit(request.user),
        'can_delete': board.can_delete(request.user),
    })
```

**`pk` 는 어디서 오나요?** `boards/urls.py` 의 `path("<int:pk>/", views.board_detail, name="detail")` 부분이 주소의 숫자 부분을 잘라서 `pk` 라는 이름의 인자로 넘겨줍니다 (`/boards/12/` → `pk=12`). `get_object_or_404(Board, pk=12)` 는 "Board 테이블에서 `id=12` 인 행을 찾아라, 없으면 404 오류를 내라"는 뜻입니다. 직접 `Board.objects.get(pk=12)` 을 쓰면 없을 때 `DoesNotExist` 예외가 나서 500 에러 화면이 뜨는데, `get_object_or_404` 를 쓰면 사용자에게 훨씬 자연스러운 **404 Not Found** 화면이 뜹니다.

**`update_fields=['read_count']` 를 쓰는 이유** : `board.save()` 만 부르면 `title`, `content` 등 **모든 컬럼**을 다시 UPDATE 합니다. 지금 바꾼 건 조회수 하나뿐이므로, `update_fields` 로 "이 컬럼만 갱신해라"라고 알려주면 더 가벼운 SQL이 나갑니다.

> **중요한 함정: 템플릿에서 `board.can_edit(request.user)` 를 직접 부를 수 없습니다**
>
> Django 템플릿 문법은 `{{ 객체.속성 }}` 이나 `{{ 객체.메소드 }}` (인자 없는 메소드) 까지는 되지만, **`{{ board.can_edit(request.user) }}` 처럼 괄호로 인자를 넘기는 문법 자체가 존재하지 않습니다.** 억지로 써도 오류조차 나지 않고, 그냥 조용히 빈 값(`False` 취급)으로 렌더링됩니다 — 그래서 발견하기 더 어렵습니다.
>
> 그래서 **인자가 필요한 메소드는 View 에서 미리 실행한 결과(참/거짓)만 템플릿에 넘겨줍니다.** 위 코드의 `can_edit`, `can_delete` 가 그 예시입니다. 템플릿에서는 그냥 `{% if can_edit %}` 로 쓰면 됩니다 (7.3번 항목 참고).

### 4.4 게시글 수정 View

```python
@login_required
def board_update(request, pk):
    """본인 게시글만 수정하는 뷰"""
    # 수정할 대상 게시글 조회해 옴
    board = get_object_or_404(Board, pk=pk)

    # 현재 로그인한 사용자와 작성자 확인(본인 글인지 확인)
    if not board.can_edit(request.user):
        # HTTP 403: Forbidden 예외 발생
        raise PermissionDenied("본인이 작성한 글만 수정할 수 있습니다.")

    # form 의 input과 textarea에 board의 값이 출력되게 처리 함(instance 사용)
    form = BoardForm(request.POST or None, request.FILES or None, instance=board)

    if request.method == 'POST' and form.is_valid():
        # 기존 게시글 update 실행 처리 (instance 가 있으므로 insert 대신 update 됨)
        form.save()

        messages.success(request, "게시글이 수정되었습니다.")
        return redirect('boards:detail', pk=pk)
    elif request.method == 'POST':
        messages.error(request, "게시글 수정에 실패했습니다. 아래 항목을 확인해주세요.")

    return render(request, 'boards/board_form.html', {'form': form, 'mode': '수정'})
```

**`instance=board` 가 핵심입니다.** `BoardForm(request.POST, instance=board)` 처럼 기존 객체를 넘기면 두 가지가 달라집니다.

1. GET 요청일 때, 입력칸에 **기존 값이 미리 채워진 채로** 출력됩니다 (수정 화면이니 당연히 필요하죠).
2. `form.save()` 를 호출하면 새 글을 만드는(`INSERT`) 게 아니라, 그 `board` 객체를 **갱신(`UPDATE`)** 합니다.

`instance` 가 없으면(4.2번 등록 View 처럼) 매번 새 글이 만들어지고, 있으면 그 글이 수정됩니다 — **같은 `BoardForm` 클래스를 등록/수정 두 군데서 재사용**할 수 있는 이유가 바로 이 `instance` 인자 덕분입니다. `board_form.html` 템플릿도 등록/수정 공용으로 하나만 씁니다 (7.2번 항목 참고).

**`raise PermissionDenied(...)` 는 무엇을 하나요?** Django에게 "이 요청은 403 Forbidden 으로 응답해라"라고 알려주는 예외입니다. `if` 문으로 직접 `render` 해서 에러 메시지를 보여줄 수도 있지만, `PermissionDenied` 를 쓰면 **HTTP 상태 코드 자체가 403**으로 정확히 나가서, 브라우저나 검색엔진, 다른 프로그램이 "이건 접근이 거부된 요청이구나"라고 올바르게 인식합니다.

### 4.5 게시글 삭제 View

```python
@login_required
def board_delete(request, pk):
    """전송받은 글번호에 해당하는 게시글 삭제하는 뷰"""
    # 해당 글번호에 대한 게시글 조회해 옴
    board = get_object_or_404(Board, pk=pk)

    # 본인 글도 아니고 관리자도 아니라면 삭제 불가
    if not board.can_delete(request.user):
        raise PermissionDenied('삭제 권한이 없습니다.')

    # 실제 삭제는 post요청에서만 수행함 (get 요청으로 삭제되면 안 됨)
    if request.method == 'POST':
        board.delete()
        messages.success(request, "게시글이 삭제되었습니다.")
        return redirect('boards:list')

    # get 요청이면 삭제 확인 화면만 출력되게 함
    return render(request, 'boards/board_confirm_delete.html', {'board': board})
```

**왜 삭제를 GET 으로 바로 실행하지 않을까?**

`board_edit()` 처럼 링크(`<a href="...">삭제</a>`)만 클릭해도 실행되는 GET 요청으로 삭제를 처리하면 위험합니다.

- 검색엔진 크롤러가 그 링크를 따라가기만 해도 글이 삭제될 수 있습니다.
- 브라우저가 페이지를 미리 불러오는 기능(prefetch)에 걸려 실수로 삭제될 수도 있습니다.

그래서 **GET 요청일 때는 "정말 삭제하시겠습니까?" 확인 화면만 보여주고, 실제 삭제는 그 화면의 `<form method="post">` 를 통해 사용자가 명시적으로 버튼을 눌러야만** 일어나게 만듭니다 (`pj설명2.md` 에서 배운 PRG 패턴과 같은 이유 — 의도치 않은 요청 한 번으로 상태가 바뀌면 안 됩니다).

---

## 5. boards/urls.py 작성

`boards/urls.py` **(직접 새로 만드는 파일)**

```python
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
```

### `<int:pk>` — 경로 변환기(path converter)

`members/urls.py` 의 경로는 전부 고정 문자열(`"signup/"`)이었지만, 게시글은 **몇 번 글인지**가 주소에 포함되어야 합니다. `<int:pk>` 는 "숫자 하나를 받아서, `pk` 라는 이름으로 뷰 함수에 넘겨줘라"는 뜻입니다.

```text
path("<int:pk>/", views.board_detail, name="detail")
                              ↓
/boards/12/  요청이 오면 →  board_detail(request, pk=12) 호출됨
```

뷰 함수의 매개변수 이름(`pk`)과 `<int:pk>` 의 이름이 **정확히 같아야** 합니다. 이름이 다르면 `TypeError: board_detail() got an unexpected keyword argument 'pk'` 가 납니다.

> **직접 겪은 오류** : 처음 작성한 `urls.py` 에는 이런 문제가 있었습니다.
> ```python
> path("<int:pk>/", views.board_detail, name="detail"),
> path("<int:pk>/", views.board_detail, name="detail"),   # 수정용이라고 적어놨지만 실제로는 detail 을 또 등록
> path("<int:pk>/", views.board_detail, name="detail"),   # 삭제용이라고 적어놨지만 이것도 detail
> ```
> `name="detail"` 인 경로가 3번 등록되어 있었고, `update`/`delete` 라는 이름의 경로는 **아예 없었습니다.** 이 상태에서 템플릿에 `{% url 'boards:update' board.pk %}` 라고 쓰면
> `NoReverseMatch: Reverse for 'update' not found` 가 납니다. **경로를 3개(상세/수정/삭제) 만들려면, 서로 다른 `name` 을 가진 경로도 3개 있어야 합니다.**

---

## 6. config(myproject)/urls.py 에 boards 연결

`config/urls.py`

```python
from django.urls import include, path
# ... (admin, TemplateView 등 기존 내용)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("members/", include("members.urls")),

    # /boards/ 로 시작하는 주소는 boards/urls.py 가 처리함
    path("boards/", include("boards.urls", namespace="boards")),
]
```

`members/urls.py` 를 연결할 때(`pj설명2.md` 4번)와 완전히 같은 패턴입니다. `boards/urls.py` 안에 이미 `app_name = "boards"` 가 있으므로 `namespace="boards"` 는 사실 생략해도 같은 결과지만, 명시적으로 적어두면 **"이 URL들은 boards 네임스페이스로 묶인다"** 는 게 이 파일만 봐도 바로 보입니다.

> **직접 겪은 오류** : `boards/models.py`, `views.py`, `urls.py` 를 다 작성해도 `config/urls.py` 에 이 `include()` 한 줄을 안 넣으면, `/boards/` 로 아무리 접속해도 Django는 그 주소를 아예 모릅니다(404). **URL은 앱 안에 등록하는 것과, 프로젝트 최상위에 연결하는 것, 두 단계가 모두 필요합니다.**

---

## 7. 게시판 관련 template 추가 작성

`templates/boards/*.html`

### 7.1 게시글 목록 html — `templates/boards/board_list.html`

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>게시판</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body class="wide">
    <h1>게시판</h1>

    {% if messages %}
        <ul class="messages">
            {% for message in messages %}
                <li class="{{ message.tags }}">{{ message }}</li>
            {% endfor %}
        </ul>
    {% endif %}

    <!-- 검색창. GET 으로 보내야 주소에 ?q=검색어 가 남아서 새로고침·공유가 가능함 -->
    <form method="get" class="board-search">
        <input type="text" name="q" value="{{ query }}" placeholder="제목 또는 내용 검색">
        <button type="submit">검색</button>
        {% if query %}
            <a href="{% url 'boards:list' %}">전체보기</a>
        {% endif %}
    </form>

    <!-- 검색 중이면 검색 결과 건수를, 아니면 전체 건수를 보여줌 -->
    {% if query %}
        <p>"{{ query }}" 검색 결과 {{ page_obj.paginator.count }}건</p>
    {% else %}
        <p>전체 게시글 {{ page_obj.paginator.count }}건</p>
    {% endif %}

    {% if user.is_authenticated %}
        <p><a href="{% url 'boards:create' %}">글쓰기</a></p>
    {% endif %}

    <table class="board-table">
        <thead>
            <tr>
                <th>번호</th><th>제목</th><th>글쓴이</th><th>작성일</th><th>조회수</th>
            </tr>
        </thead>
        <tbody>
            {% for board in page_obj %}
                <tr>
                    <td>{{ board.pk }}</td>
                    <td><a href="{% url 'boards:detail' board.pk %}">{{ board.title }}</a></td>
                    <td>{{ board.author.display_name }}</td>
                    <td>{{ board.created_at|date:"Y-m-d" }}</td>
                    <td>{{ board.read_count }}</td>
                </tr>
            {% empty %}
                <tr><td colspan="5">등록된 게시글이 없습니다.</td></tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- 검색 중이었다면 다음/이전 페이지로 넘어가도 검색어(q)가 유지되게 함 -->
    {% if page_obj.paginator.num_pages > 1 %}
        <div class="pagination">
            {% if page_obj.has_previous %}
                <a href="?q={{ query }}&page={{ page_obj.previous_page_number }}">이전</a>
            {% endif %}
            {% for num in page_obj.paginator.page_range %}
                {% if num == page_obj.number %}
                    <span class="current">{{ num }}</span>
                {% else %}
                    <a href="?q={{ query }}&page={{ num }}">{{ num }}</a>
                {% endif %}
            {% endfor %}
            {% if page_obj.has_next %}
                <a href="?q={{ query }}&page={{ page_obj.next_page_number }}">다음</a>
            {% endif %}
        </div>
    {% endif %}

    <a href="{% url 'home' %}">첫 페이지로</a>
</body>
</html>
```

**`{% for board in page_obj %}`** — `page_obj` 를 그대로 순회하면 Django가 알아서 **"이번 페이지에 해당하는 게시글만"** 꺼내 줍니다. 전체 목록에서 자르는 계산(`[10:20]` 같은)을 우리가 직접 안 해도 됩니다.

**페이지 번호 링크 (`?page=2`)** — `<a href="?page=2">` 처럼 쓰면 **지금 보고 있는 주소는 그대로 두고 쿼리스트링만 바뀝니다.** `/boards/?page=2` 가 되고, 뷰의 `request.GET.get('page')` 가 이 값을 받아 그 페이지를 계산해 줍니다.

**`{{ board.created_at|date:"Y-m-d" }}`** — `|date:"..."` 는 Django 템플릿의 **필터**입니다. `날짜시간(datetime)` 값을 원하는 형식의 문자열로 바꿔 출력합니다. `Y-m-d` → `2026-08-11` 처럼.

**`body class="wide"`** — 회원가입/로그인 폼은 좁은 화면(480px)이 어울리지만, 표가 있는 게시판 목록은 더 넓어야 보기 편합니다. `static/css/style.css` 에 `body.wide { max-width: 900px; }` 를 추가해서, 이 클래스가 붙은 페이지만 폭을 넓혔습니다.

**검색창은 왜 `method="get"` 인가요?**

`members/login.html`, `boards/board_form.html` 같은 입력 폼은 전부 `method="post"` 였습니다. 검색은 다릅니다.

- POST는 "서버의 상태를 바꾸는 요청"(가입, 글쓰기, 삭제 ...)에 씁니다. 새로고침하면 브라우저가 "다시 제출하시겠습니까?"라고 경고하는 이유도 이 때문입니다.
- 검색은 상태를 바꾸지 않고 **조회만** 하므로 GET이 맞습니다. GET으로 보내면 검색어가 `/boards/?q=파이썬`처럼 **주소 자체에 남아서**, 새로고침해도 같은 결과가 나오고, 그 주소를 복사해서 다른 사람에게 공유할 수도 있습니다.

**검색어가 페이지 이동에서도 유지되는 이유**

검색 결과가 10개보다 많으면 페이지네이션이 같이 뜨는데, 그 "다음" 링크가 그냥 `?page=2`로만 되어 있으면 페이지를 넘기는 순간 검색 조건(`q`)이 사라져서 **전체 목록의 2페이지**로 가버립니다. 그래서 페이지 링크에도 `?q={{ query }}&page=2`처럼 검색어를 항상 같이 붙여서, "이 검색 결과의 2페이지"로 가게 만들었습니다.

> **직접 겪은 오류** : 처음 만든 목록 화면은 `{% url 'boards:secrete' %}` 라는, `urls.py` 어디에도 없는 이름을 쓰고 있었습니다(`create` 를 잘못 적은 것으로 보입니다). 이러면 `NoReverseMatch: Reverse for 'secrete' not found` 가 납니다. 그리고 렌더링하는 템플릿 파일명도 `board_list_html.html` 로 되어 있었는데, `views.py` 는 `'boards/board_list.html'` 을 찾고 있어서 `TemplateDoesNotExist` 가 났습니다. **뷰가 지정한 템플릿 경로 문자열과 실제 파일 이름은 한 글자도 다르면 안 됩니다.**

### 7.2 게시글 작성/수정 html — `templates/boards/board_form.html`

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>게시글 {{ mode }}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <h1>게시글 {{ mode }}</h1>

    {% if messages %}
        <ul class="messages">
            {% for message in messages %}
                <li class="{{ message.tags }}">{{ message }}</li>
            {% endfor %}
        </ul>
    {% endif %}

    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">{{ mode }}하기</button>
    </form>

    <a href="{% url 'boards:list' %}">목록으로</a>
</body>
</html>
```

**등록/수정 화면을 파일 하나로 같이 쓰는 이유** — 두 화면은 "입력칸 + 저장 버튼"이라는 구조가 완전히 같습니다. `views.py` 에서 `board_create` 는 `{'form': form, 'mode': '등록'}` 을, `board_update` 는 `{'form': form, 'mode': '수정'}` 을 넘기는 것만 다릅니다. `{{ mode }}` 하나로 제목과 버튼 글자가 "게시글 등록" / "게시글 수정" 으로 자동으로 바뀝니다. 화면 하나를 두 번 안 만들어도 되는 셈입니다.

### 7.3 게시글 상세보기 html — `templates/boards/board_detail.html`

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{ board.title }}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body class="wide">
    <h1>{{ board.title }}</h1>

    {% if messages %}
        <ul class="messages">
            {% for message in messages %}
                <li class="{{ message.tags }}">{{ message }}</li>
            {% endfor %}
        </ul>
    {% endif %}

    <p class="board-meta">
        작성자: {{ board.author.display_name }} /
        작성일: {{ board.created_at|date:"Y-m-d H:i" }} /
        수정일: {{ board.updated_at|date:"Y-m-d H:i" }} /
        조회수: {{ board.read_count }}
    </p>

    <div class="board-content">
        {{ board.content|linebreaks }}
    </div>

    {% if board.attachment %}
        <p>첨부파일: <a href="{{ board.attachment.url }}">다운로드</a></p>
    {% endif %}

    <div class="board-actions">
        {% if can_edit %}
            <a href="{% url 'boards:update' board.pk %}">수정</a>
        {% endif %}
        {% if can_delete %}
            <a href="{% url 'boards:delete' board.pk %}">삭제</a>
        {% endif %}
        <a href="{% url 'boards:list' %}">목록으로</a>
    </div>
</body>
</html>
```

**`{{ board.content|linebreaks }}`** — `TextField` 에 저장된 텍스트는 줄바꿈이 그냥 `\n` 문자일 뿐이라, HTML은 이걸 무시하고 한 줄로 이어 붙여 버립니다. `linebreaks` 필터가 `\n` 을 `<br>` 이나 `<p>` 태그로 바꿔줘서 사용자가 입력한 줄바꿈 그대로 보이게 합니다.

**`{% if can_edit %}` / `{% if can_delete %}`** — 4.3번에서 설명한 대로, `board.can_edit(request.user)` 를 템플릿에서 직접 호출할 수 없기 때문에 **뷰가 미리 계산해서 넘겨준 `can_edit`, `can_delete` 값**을 그대로 씁니다. 본인 글이면 수정+삭제 버튼이, 남의 글이면 아무 버튼도 안 보이고, 관리자로 보면 삭제 버튼만 보입니다 (관리자는 `can_edit` 은 `False` — 본인 글이 아니면 수정은 여전히 금지, 삭제만 가능하도록 설계했습니다).

**게시판 목록에는 있던 `{% if messages %}` 블록이 왜 상세보기에도 있나요?** — 수정 성공 후 `redirect('boards:detail', pk=pk)` 로 이 화면으로 돌아오기 때문입니다. `messages.success()` 로 남긴 "게시글이 수정되었습니다" 메시지가 여기서 표시됩니다 (`pj설명2.md` 6번 항목의 messages 패턴을 게시판에도 그대로 적용한 것입니다).

### 7.4 게시글 삭제 확인 html — `templates/boards/board_confirm_delete.html`

스펙에는 없지만, 4.5번 View(`board_delete`)가 `render(request, 'boards/board_confirm_delete.html', ...)` 를 호출하므로 **반드시 있어야 하는 파일**입니다.

```html
<!DOCTYPE html>
{% load static %}
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>게시글 삭제</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <h1>게시글을 삭제하시겠습니까?</h1>
    <p><strong>{{ board.title }}</strong></p>

    <form method="post">
        {% csrf_token %}
        <button type="submit">삭제</button>
        <a href="{% url 'boards:detail' board.pk %}">취소</a>
    </form>
</body>
</html>
```

`<form method="post">` 로 감싼 "삭제" 버튼만 실제로 삭제를 실행합니다(4.5번 항목 "왜 삭제를 GET 으로 바로 실행하지 않을까?" 참고). "취소" 는 그냥 상세보기로 돌아가는 링크(GET)라 아무 것도 삭제하지 않습니다.

> **직접 겪은 오류** : 이 파일 자체가 없는 상태로 게시글 삭제 버튼을 누르면 View 코드는 문제가 없는데도 `TemplateDoesNotExist: boards/board_confirm_delete.html` 오류가 났습니다. **View가 `render()` 로 지정한 템플릿 파일은 실제로 존재해야 합니다** — 스펙 목록(7.1~7.3)에 없어도, 코드가 참조한다면 만들어야 합니다.

---

## 8. 홈 화면에 게시판 메뉴 연결하기

`boards/urls.py`, `config/urls.py` 를 다 연결했어도 **주소를 직접 쳐서 들어가야만** `/boards/` 에 갈 수 있다면 실제 사용자 입장에선 그 기능이 없는 것과 마찬가지입니다. `templates/home.html` (`pj설명2.md` 5번 항목에서 만든 첫 페이지)에 게시판으로 가는 링크를 추가해야 합니다.

```html
<!-- templates/home.html, <h1> 바로 아래 -->

<!-- 사이트 메뉴. 게시판 목록은 비로그인 상태에서도 볼 수 있음 -->
<nav>
    <a href="{% url 'boards:list' %}">게시판</a>
</nav>
```

**`{% if user.is_authenticated %}` 블록 밖에 놓은 이유** — `boards/views.py` 의 `board_list` 뷰에는 `@login_required` 가 없습니다(4.1번 항목 참고). 즉 **게시글 목록은 로그인 여부와 상관없이 누구나 볼 수 있고, "글쓰기"만 로그인이 필요**합니다. 그래서 이 메뉴 링크도 로그인 조건 안에 가둬두면 안 됩니다. (글쓰기 버튼은 `board_list.html` 안에서 `{% if user.is_authenticated %}` 로 이미 따로 감싸져 있습니다 — 7.1번 항목 참고.)

> **왜 이 단계가 빠지기 쉬울까?** Model → Form → View → URL → Template 순서로 한 기능을 완성하고 나면 "다 됐다"고 느끼기 쉽지만, 그 기능으로 **들어가는 입구(진입점)** 를 다른 화면에 만드는 건 별개의 작업입니다. `/boards/` 로 직접 주소를 쳐보면서 개발할 땐 이 문제를 못 느끼다가, 실제로 로그인부터 시작해서 화면을 눌러가며 써보면 바로 드러납니다. 그래서 10번 항목(동작 테스트)에서 **주소를 직접 치지 않고 화면의 링크만 눌러서** 확인하는 과정이 중요합니다.

---

## 9. admin 계정 생성

관리자 계정으로 모든 글 삭제 권한이 있어야 합니다.

```bash
python manage.py createsuperuser
```

터미널에서 아이디/이메일/비밀번호를 순서대로 입력합니다.

```text
아이디(username): admin
이메일: admin@example.com
비밀번호: admin1234
비밀번호(확인): admin1234
```

> `createsuperuser` 는 기본적으로 대화형(터미널에 하나씩 물어보는 방식)입니다. 스크립트로 한 번에 만들고 싶다면 Django shell에서:
> ```bash
> python manage.py shell
> ```
> ```python
> from django.contrib.auth import get_user_model
> Member = get_user_model()
> Member.objects.create_superuser(
>     username="admin",
>     email="admin@example.com",
>     password="admin1234",
>     display_name="관리자",
> )
> ```
> `Member` 모델에는 `display_name` 처럼 **직접 추가한 필수 필드**가 있으므로, 이런 필드는 `create_superuser()` 호출 시 키워드 인자로 같이 넘겨줘야 합니다. 안 넘기면 `display_name` 이 빈 값으로 만들어지거나(필드 옵션에 따라) `IntegrityError` 가 날 수 있습니다.

### `createsuperuser` 로 만든 계정이 왜 "모든 글 삭제 권한"을 가질까?

`createsuperuser` 로 만들면 그 계정은 `is_staff=True`, `is_superuser=True` 두 값이 **모두** 자동으로 켜집니다. 1번 항목에서 작성한 `can_delete()` 메소드를 다시 보면:

```python
def can_delete(self, user):
    return user.is_authenticated and (self.author_id == user.id or user.is_staff or user.is_superuser)
```

`user.is_staff` 나 `user.is_superuser` 둘 중 하나라도 `True` 면, 본인 글이 아니어도 삭제가 허용됩니다. `createsuperuser` 로 만든 계정은 이 두 값이 항상 `True` 이므로, **이 한 줄 덕분에** "관리자는 모든 글 삭제 가능"이라는 요구사항이 자동으로 충족됩니다. 회원가입 화면으로 가입한 일반 계정은 두 값 다 기본값 `False` 이므로 본인 글만 지울 수 있습니다. (`is_staff`/`is_superuser` 를 왜 같이 검사하는지는 1번 항목의 "`is_staff` 와 `is_superuser`" 부분을 참고하세요.)

---

## 10. 동작 테스트

아래 순서대로 브라우저에서 직접 눌러보면서 확인합니다.

```bash
python manage.py runserver
```

| 순서 | 계정 상태 | 동작 | 기대 결과 |
|---|---|---|---|
| 1 | 비로그인 | `/boards/` 접속 | 목록은 보이되 "글쓰기" 링크는 안 보임 |
| 2 | 비로그인 | `/boards/create/` 직접 접속 | 로그인 페이지로 이동 (`@login_required`) |
| 3 | 일반 회원 로그인 | 글쓰기 → 등록 | "게시글이 등록되었습니다" 배너 + 목록에 추가됨 |
| 4 | 같은 회원 | 방금 쓴 글 상세보기 | 조회수 1로 증가, 수정/삭제 버튼 둘 다 보임 |
| 5 | 같은 회원 | 수정 → 저장 | 기존 값이 입력칸에 채워져 있었는지, 저장 후 바뀐 내용이 보이는지 확인 |
| 6 | 다른 일반 회원 로그인 | 그 글 상세보기 | 수정/삭제 버튼이 안 보임 |
| 7 | 다른 일반 회원 | 그 글의 `/boards/&lt;pk&gt;/delete/` 주소 직접 입력 | 403 Forbidden |
| 8 | `admin` 관리자 로그인 | 그 글 상세보기 | 삭제 버튼만 보임(수정 버튼은 안 보임) |
| 9 | `admin` | 삭제 실행 | 삭제 확인 화면 → 삭제 → 목록에서 사라짐 |
| 10 | 아무 계정 | 게시글 11개 이상 등록 | 목록이 10개씩 나뉘고, 하단에 페이지 번호 + 이전/다음 표시 |
| 11 | 아무 계정 | 목록에서 제목에만 있는 단어로 검색 | 그 글만 결과에 남음, "OO건" 건수가 줄어듦 |
| 12 | 아무 계정 | 목록에서 내용에만 있는 단어로 검색 | 제목엔 없어도 결과에 걸림(제목 OR 내용) |
| 13 | 아무 계정 | 검색 결과가 10건을 넘는 검색어로 검색 후 "다음" 클릭 | 2페이지에서도 검색 조건이 유지됨 (전체 목록 2페이지로 안 튕김) |
| 14 | 아무 계정 | 검색 후 "전체보기" 클릭 | 검색창이 비고 전체 목록으로 돌아옴 |

### 자주 만나는 오류 정리

| 오류 메시지 | 원인 |
|---|---|
| `can't open file '...\magnage.py'` | `manage.py` 오타 |
| `AttributeError: ...has no attribute 'AUTH_USER_MDDEL'` | `models.py` 에서 `settings.AUTH_USER_MODEL` 오타 |
| 마이그레이션은 되는데 테이블이 안 생김 | `INSTALLED_APPS` 에 앱 이름이 주석 처리되어 있음 |
| `ModuleNotFoundError: No module named 'boards.forms'` | 파일 이름이 `forms.py` 가 아님(`homes.py` 등) |
| `NameError: name 'user_id' is not defined` | 모델 메소드에서 `user.id` 를 `user_id` 로 잘못 씀 |
| `NoReverseMatch: Reverse for 'update' not found` | `urls.py` 에 그 `name` 의 경로가 없거나, 오타 |
| `TemplateDoesNotExist: boards/board_confirm_delete.html` | view가 참조하는 템플릿 파일이 실제로 없음 |
| 수정/삭제 버튼이 조건과 상관없이 항상 안 보임 | 템플릿에서 `board.can_edit(request.user)` 처럼 인자 있는 메소드를 직접 호출 (조용히 실패함) |
| `TypeError: dict.update() takes at most 1 argument` | `attrs.update('class', 'x')` → `attrs.update({'class': 'x'})` 로 수정 |
| 403 Forbidden 이 아니라 다른 사람 글이 그냥 지워짐 | `can_delete()` 검사를 View 맨 앞에서 안 하고 있음 |
| 검색 후 페이지 이동하면 검색 결과가 사라짐 | 페이지네이션 링크(`?page=2`)에 `q=` 검색어를 같이 안 붙임 |
| 검색이 제목에서만 되고 내용에서는 안 됨(또는 그 반대) | `Q(...) \| Q(...)` 대신 `.filter(title__icontains=q, content__icontains=q)` 처럼 쉼표(AND)로 씀 |

---

## 11. 3단계 체크리스트

```text
□ boards/models.py : Board 모델, Meta.ordering, can_edit(), can_delete() 작성
□ INSTALLED_APPS 에 'boards' 등록 (주석 해제 확인!)
□ makemigrations boards → migrate → MySQL에 boards_board 테이블 확인
□ boards/forms.py (파일명 정확히!) : BoardForm, author는 fields에서 제외
□ boards/views.py : board_list(검색 + 페이지네이션) / board_create(commit=False) /
  board_detail(조회수, can_edit·can_delete 계산) / board_update(instance=) / board_delete(POST만 삭제)
□ board_list 에 Q(title__icontains=q) | Q(content__icontains=q) 검색 필터 추가
□ boards/urls.py : list / create / detail / update / delete 5개 name, 전부 다른 이름
□ config/urls.py 에 path("boards/", include("boards.urls", namespace="boards")) 추가
□ templates/boards/board_list.html : 검색창(GET), 표, 총 개수, 페이지네이션(검색어 유지)
□ templates/boards/board_form.html : 등록/수정 공용, mode 로 문구 분기
□ templates/boards/board_detail.html : can_edit/can_delete 로 버튼 분기, linebreaks
□ templates/boards/board_confirm_delete.html : POST 전용 삭제 확인 화면
□ templates/home.html 에 게시판 메뉴(nav) 링크 추가 (주소를 직접 안 쳐도 들어가지도록)
□ can_delete() : 작성자 본인 or is_staff or is_superuser
□ python manage.py createsuperuser (admin / admin1234)
□ 10번 표의 시나리오 1~14번 브라우저에서 직접 확인
```
