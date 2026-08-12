# 1단계 : 프로젝트 뼈대 만들기 ~ DB 연결 ~ 회원 모델

> 이 문서는 빈 폴더에서 시작해서 **MySQL에 회원 테이블이 만들어지는 것까지**의 순서입니다.
> 회원가입/로그인 화면 만들기는 `pj설명2.md` 에서 이어집니다.
>
> **전체 흐름 한 줄 요약**
> 가상환경 → 패키지 설치 → 프로젝트 생성 → 앱 생성 → settings 설정 → DB 연결 → 모델 작성 → 마이그레이션

## 이 문서들을 끝까지 따라 하면 완성되는 기능

`pj설명.md`(1단계, 이 문서) → `pj설명2.md`(2단계) → `pj설명3.md`(3단계) 순서대로 진행하면, 최종적으로 아래 기능을 갖춘 프로젝트가 완성됩니다. (전체 요약은 [README.md](README.md) 참고)

**회원 관리** (`pj설명.md`, `pj설명2.md`)
- 회원가입 / 로그인 / 로그아웃
- 회원정보 조회 / 수정 / 탈퇴(계정 삭제)
- 사용자 정의 `Member(AbstractUser)` 모델
- 세션 기반 로그인 상태 유지(30분 비활성 만료), 비밀번호 해시 저장
- 관리자 `is_staff`/`is_superuser` 권한, `is_active` 기반 로그인 제한
- Django Admin에서 회원 관리

**게시판** (`pj설명3.md`)
- 게시글 목록 / 상세 / 등록 / 수정 / 삭제(CRUD)
- 제목·내용 검색, 10개 단위 페이지네이션
- 로그인 회원만 작성, 작성자 본인만 수정, 본인 또는 관리자만 삭제
- 첨부파일 업로드, 조회수 증가
- Django Admin에서 게시글 관리

**공통** (`pj설명.md`)
- MySQL 연동 + Django Migration
- `.env`로 비밀 정보 분리, 성공/실패 안내 메시지 배너

---

## 0. 시작 전에 확인할 것

```bash
python --version
```

```bash
mysql --version
```

- 파이썬 3.10 이상이면 Django 5.2를 쓸 수 있습니다.
- MySQL은 **서버가 실행 중**이어야 합니다. (윈도우: 서비스 목록에서 MySQL이 "실행 중")

---

## 1. 프로젝트 폴더와 가상환경 만들기

```bash
mkdir 20260810_django_mypj
```

```bash
cd 20260810_django_mypj
```

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

**가상환경(virtual environment)이 뭐고 왜 하나요?**

가상환경은 **이 프로젝트만의 전용 파이썬 패키지 창고**입니다.
가상환경 없이 설치하면 컴퓨터 전체에 깔려서, A프로젝트는 Django 4.2가 필요한데 B프로젝트는 5.2가 필요할 때 서로 충돌합니다.
`.venv` 폴더 안에 이 프로젝트가 쓸 Django만 따로 설치해 두면 프로젝트끼리 간섭하지 않습니다.

활성화가 되면 터미널 맨 앞에 `(.venv)` 가 붙습니다. **이게 안 붙어 있으면 패키지를 아무리 깔아도 프로젝트가 못 찾습니다.**
파이참을 쓴다면 `File > Settings > Project > Python Interpreter` 에서 인터프리터가 `.venv\Scripts\python.exe` 로 잡혀 있는지 꼭 확인하세요.

---

## 2. 필요한 패키지 설치

프로젝트 루트에 `requirements.txt` 를 만듭니다.

```text
#Django 웹 프레임워크
Django>=5.2,<5.3

# Django와 MySQL 연결
mysqlclient>=2.2.8,<3.0

# ImageField를 이용한 이미지(사진) 업로드시 사용
Pillow>=11.0,<13.0

# .env환경변수 읽기 위해 사용
python-dotenv>=1.0,<2.0
```

```bash
pip install -r requirements.txt
```

**왜 requirements.txt 에 적어두나요?**

나중에 다른 컴퓨터에서 이 프로젝트를 열거나 친구에게 넘길 때, 이 파일 하나만 있으면 `pip install -r requirements.txt` 로 똑같은 환경이 복원됩니다.
직접 설치했다면 `pip freeze > requirements.txt` 로 현재 설치 목록을 뽑을 수도 있습니다.

**각 패키지의 역할**

| 패키지 | 없으면 생기는 일 |
|---|---|
| `Django` | 당연히 아무것도 안 됨 |
| `mysqlclient` | `django.db.utils.ImproperlyConfigured: Error loading MySQLdb module` |
| `Pillow` | 모델에 `ImageField`를 쓰면 `fields.E210` 오류로 서버가 아예 안 뜸 |
| `python-dotenv` | `.env` 파일을 못 읽어서 SECRET_KEY가 `None`이 됨 |

---

## 3. Django 프로젝트 생성

```bash
django-admin startproject config .
```

**맨 뒤의 점(`.`)이 중요합니다.**
점이 없으면 `20260810_django_mypj/config/manage.py` 처럼 폴더가 한 겹 더 생겨서 경로가 복잡해집니다.
점을 찍으면 **지금 폴더**에 바로 만들어집니다.

생성 결과:

```text
20260810_django_mypj/          ← 프로젝트 루트
├── manage.py                  ← 모든 Django 명령의 입구
└── config/                    ← 프로젝트 설정 폴더
    ├── __init__.py
    ├── settings.py            ← 설정 전부
    ├── urls.py                ← 최상위 URL 지도
    ├── wsgi.py                ← 배포용 진입점 (동기)
    └── asgi.py                ← 배포용 진입점 (비동기)
```

**각 파일이 하는 일**

- `manage.py` : 우리가 치는 모든 명령(`runserver`, `migrate`, ...)이 여기를 거칩니다. 내부에서 `DJANGO_SETTINGS_MODULE=config.settings` 를 지정해 주기 때문에 Django가 어떤 설정을 쓸지 알게 됩니다.
- `settings.py` : DB 주소, 앱 목록, 템플릿 경로 등 프로젝트의 모든 설정. **가장 많이 고치게 될 파일**입니다.
- `urls.py` : 브라우저 주소를 어떤 코드로 보낼지 정하는 지도. 요청은 무조건 여기를 먼저 거칩니다.
- `wsgi.py` / `asgi.py` : 나중에 실제 서버(nginx 등)에 올릴 때 쓰는 진입점. 공부 단계에서는 건드리지 않습니다.

프로젝트 폴더 이름을 `config` 로 하는 이유는, 프로젝트 이름이 바뀌어도 설정 폴더 이름은 그대로 두려는 관례입니다.

---

## 4. 정상 실행 여부 확인

```bash
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000` 에 로켓 그림(장고 기본 페이지)이 나오면 성공입니다.
`Ctrl + C` 로 종료합니다.

> **자주 나는 오류: `Error: That port is already in use.`**
> 8000번 포트를 이미 다른 서버가 쓰고 있다는 뜻입니다. 이전에 켜둔 runserver가 안 꺼졌을 때 자주 납니다.
> ```bash
> netstat -ano | findstr :8000
> ```
> 맨 오른쪽 숫자가 PID입니다. 작업관리자에서 그 PID를 끝내거나, 다른 포트로 실행하세요.
> ```bash
> python manage.py runserver 8001
> ```

---

## 5. 앱(App) 만들기

```bash
python manage.py startapp members
```

**프로젝트와 앱의 차이**

- **프로젝트(config)** = 건물 전체. 설정과 공통 규칙을 가집니다.
- **앱(members, boards)** = 건물 안의 각 사무실. **기능 단위**로 나눕니다.

회원 기능은 `members`, 게시판 기능은 `boards` 로 나누면 나중에 코드 찾기가 쉽고, 앱 단위로 다른 프로젝트에 재사용할 수도 있습니다.

생성 결과:

```text
members/
├── __init__.py     ← 이 폴더가 파이썬 패키지임을 표시
├── admin.py        ← 관리자 사이트에 모델 등록
├── apps.py         ← 앱 설정 클래스
├── models.py       ← DB 테이블 정의
├── tests.py        ← 테스트 코드
├── views.py        ← 요청 처리 로직
└── migrations/     ← 모델 변경 이력
```

`urls.py` 와 `forms.py` 는 자동 생성되지 않으므로 **나중에 직접 만듭니다.**

> ### ⚠️ 반드시 주의 : 앱 폴더 위치
>
> 앱 폴더는 **프로젝트 루트에** 만들어야 합니다. `templates/` 안에 만들면 안 됩니다.
>
> ```text
> 20260810_django_mypj/
> ├── members/          ← ✅ 파이썬 코드(models, views, forms, urls)는 여기
> └── templates/
>     └── members/      ← ✅ HTML 파일만 여기
> ```
>
> `templates` 폴더는 **HTML 전용 창고**입니다.
> 파이썬 파일을 `templates/members/` 에 넣으면 `INSTALLED_APPS` 의 `'members'` 를 Django가 찾지 못해서
> `ModuleNotFoundError: No module named 'members'` 가 납니다.
> 폴더 이름이 둘 다 `members` 라서 헷갈리기 쉬운데, **역할이 완전히 다른 두 폴더**입니다.

---

## 6. 앱을 settings.py 에 등록

`config/settings.py`

```python
INSTALLED_APPS = [
    # 관리자 사이트
    "django.contrib.admin",
    # 사용자 인증과 권한 기능 제공
    "django.contrib.auth",
    # models의 contentType을 관리
    "django.contrib.contenttypes",
    # 사용자 로그인 세션 관리
    "django.contrib.sessions",
    # 성공/실패 오류 안내 메시지 관리
    "django.contrib.messages",
    # css, javascript 같은 정적 파일 관리
    "django.contrib.staticfiles",

    # 우리가 만든 앱을 등록
    'members',
    # 'boards',   ← 앱을 실제로 만든 뒤에 주석 해제
]
```

**왜 등록해야 하나요?**

`startapp` 으로 폴더만 만들면 Django는 그 앱의 존재를 모릅니다.
`INSTALLED_APPS` 에 적어야 Django가 그 앱의 `models.py` 를 읽어서 테이블을 만들고, 앱 안의 `templates/`, `static/` 폴더도 검색합니다.

> **자주 하는 실수** : 아직 만들지도 않은 `'boards'` 를 미리 적어두면
> `ModuleNotFoundError: No module named 'boards'` 로 **서버가 아예 안 뜹니다.**
> 앱을 만든 다음에 등록하세요.

---

## 7. 폴더 구조 만들기 (templates / static / media)

프로젝트 루트에 직접 만듭니다.

```text
20260810_django_mypj/
├── templates/          ← HTML
│   ├── home.html
│   ├── members/
│   └── boards/
├── static/             ← 개발자가 만든 파일 (css, js, 로고 이미지)
│   └── css/
│       └── style.css
├── media/              ← 사용자가 업로드한 파일 (프로필 사진, 첨부파일)
└── db/
    └── create_database.sql
```

**static 과 media 의 차이 — 시험에 잘 나오는 부분**

| | static | media |
|---|---|---|
| 누가 만드나 | **개발자**가 미리 준비 | **사용자**가 업로드 |
| 예시 | style.css, logo.png | 프로필 사진, 게시글 첨부파일 |
| 언제 바뀌나 | 배포할 때만 | 서비스 도중 계속 늘어남 |
| 설정 이름 | `STATIC_URL`, `STATICFILES_DIRS` | `MEDIA_URL`, `MEDIA_ROOT` |

둘을 나누는 이유는 **관리 방식이 다르기 때문**입니다. static은 배포 시 한 번에 모아서(`collectstatic`) 처리하고, media는 사용자가 올린 것이라 백업 대상이 됩니다.

---

## 8. settings.py 에 템플릿 / static / media 경로 설정

### 템플릿 경로

```python
TEMPLATES = [
    {
        # Django Template 엔진을 사용
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        # 프로젝트 공통 templates 폴더 지정
        "DIRS": [BASE_DIR / "templates"],

        # 각 app 내부 templates 폴더도 자동으로 검색 함
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                # Template 에서 user 변수를 사용할 수 있게 함
                "django.contrib.auth.context_processors.auth",
                # Templates에서 messages 를 사용하게 함
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
```

- `DIRS` : 프로젝트 공통 templates 폴더. **이걸 안 적으면** `TemplateDoesNotExist` 가 납니다.
- `APP_DIRS: True` : 각 앱 안의 `templates/` 폴더도 자동 검색.
- `context_processors` : **모든 템플릿에 자동으로 넘어가는 변수** 목록입니다. 이것 덕분에 HTML에서 뷰가 넘겨주지 않아도 `{{ user }}` 와 `{{ messages }}` 를 바로 쓸 수 있습니다.

### static / media 경로

```python
# 브라우저에서 정적 파일(css, js)을 요청할 URL
STATIC_URL = "static/"

# 프로젝트의 static 폴더 위치 등록
STATICFILES_DIRS = [BASE_DIR / "static"]

# 사용자가 업로드한 파일을 요청할 URL
MEDIA_URL = "media/"

# 실제 업로드 파일이 저장되는 디렉토리
MEDIA_ROOT = BASE_DIR / "media"
```

> ### ⚠️ 자주 하는 실수 : 같은 이름에 두 번 대입하기
>
> ```python
> # ❌ 이렇게 하면 안 됨
> STATIC_URL = "media/"
> STATICFILES_DIRS = [BASE_DIR / "media"]
> STATIC_URL = "static/"
> STATICFILES_DIRS = [BASE_DIR / "static"]   ← 위의 media 설정이 지워짐
> ```
>
> 파이썬 변수는 같은 이름에 다시 대입하면 **앞의 값이 사라집니다.**
> media는 `STATIC_URL` 이 아니라 **`MEDIA_URL` / `MEDIA_ROOT`** 라는 다른 이름의 설정을 써야 합니다.
>
> `URL` 과 `ROOT` 의 차이도 기억하세요.
> `MEDIA_URL` = 브라우저 주소창에 보이는 경로(`/media/photo.png`),
> `MEDIA_ROOT` = 하드디스크의 실제 폴더(`C:\...\media`).

### 언어와 시간대

```python
# 화면에 나오는 Django 기본 안내문을 한국어로 표시
LANGUAGE_CODE = "ko-kr"

# 한국 시간 기준으로 날짜/시간 표시
TIME_ZONE = "Asia/Seoul"

USE_I18N = True
USE_TZ = True
```

`LANGUAGE_CODE = "ko-kr"` 로 두면 Django가 만들어 주는 오류 메시지("비밀번호가 너무 짧습니다" 등)가 한국어로 나옵니다.
`USE_TZ = True` 면 DB에는 UTC로 저장하고 화면에 보여줄 때만 한국 시간으로 바꿔 줍니다.

---

## 9. 환경변수(.env) 분리하기

프로젝트 루트에 `.env` 파일을 만듭니다.

```text
# Django 개발 모드 여부입니다. 운영 환경에서는 False로 변경합니다.
DJANGO_DEBUG=True
# Django 암호화/서명에 사용하는 비밀키입니다.
DJANGO_SECRET_KEY=django-insecure-여기에-긴-임의-문자열
# 접속을 허용할 호스트 목록입니다. 쉼표로 구분합니다.
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# MySQL 데이터베이스 이름입니다.
DB_NAME=django_member_board
# MySQL 사용자 이름입니다.
DB_USER=django_user
# MySQL 사용자 비밀번호입니다.
DB_PASSWORD=django1234!
# MySQL 서버 주소입니다.
DB_HOST=127.0.0.1
# MySQL 기본 포트입니다.
DB_PORT=3306
```

`config/settings.py` 위쪽:

```python
from pathlib import Path

# 운영 체제의 환경변수 읽기 위한 os
import os

# .env 파일의 내용을 환경변수로 읽어 드림
from dotenv import load_dotenv

# 현재 프로젝트의 최상위 디렉토리를 구함(프로젝트 루트)
BASE_DIR = Path(__file__).resolve().parent.parent

# 프로젝트 루트의 .env 파일 읽음
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# DEBUG 환경 변수 적용
DEBUG = (os.getenv("DJANGO_DEBUG", 'True').lower() == "true")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", '127.0.0.1,localhost').split(",")
    if host.strip()
]
```

**왜 .env 로 빼나요?**

`settings.py` 는 깃(git)에 올라갑니다. 여기에 DB 비밀번호를 직접 적으면 **비밀번호가 그대로 공개**됩니다.
비밀 값은 `.env` 에 두고, `.env` 는 깃에 올리지 않는 것이 기본 원칙입니다.

**코드 읽는 법**

- `os.getenv("이름", "기본값")` : 환경변수를 문자열로 읽어옵니다. 없으면 기본값.
- `.env` 의 값은 **무조건 문자열**입니다. 그래서 `DEBUG` 는 `== "true"` 로 비교해서 진짜 True/False로 바꿔 줍니다. `DEBUG = os.getenv("DJANGO_DEBUG")` 라고만 쓰면 `"False"` 라는 **글자**가 들어가는데, 비어있지 않은 문자열은 파이썬에서 참이라 DEBUG가 꺼지지 않습니다.
- `ALLOWED_HOSTS` : `"127.0.0.1,localhost"` 한 덩어리를 `split(",")` 으로 잘라 리스트로 만듭니다. `strip()` 은 앞뒤 공백 제거.

> **이름을 맞추세요.** `.env` 에 `DJANGO_ALLOWED_HOSTS` 라고 썼으면 `os.getenv("DJANGO_ALLOWED_HOSTS")` 로 읽어야 합니다.
> `os.getenv("ALLOWED_HOSTS")` 로 쓰면 항상 `None` 이라 기본값만 쓰이게 됩니다. (오류가 안 나서 발견이 늦습니다.)

---

## 10. .gitignore 만들기

프로젝트 루트에 `.gitignore` 파일:

```text
# 가상환경
.venv/

# 파이썬 캐시
__pycache__/
*.pyc

# 환경변수 (비밀번호 포함! 절대 올리지 말 것)
.env

# 사용자 업로드 파일
media/

# 로컬 DB 파일
db.sqlite3

# 파이참 설정
.idea/
```

**왜 필요한가요?** `.venv` 는 수천 개 파일이라 올릴 필요가 없고(어차피 `requirements.txt` 로 복원됨), `.env` 는 비밀번호가 들어 있어서 올리면 안 됩니다.
이미 깃에 올려버렸다면 `git rm --cached .env` 로 추적을 해제하세요.

---

## 11. MySQL 데이터베이스와 계정 만들기

MySQL Workbench를 실행해서 **root 계정으로** 접속한 뒤 실행합니다.

```sql
-- Django 프로젝트가 사용할 db 생성
CREATE DATABASE IF NOT EXISTS django_member_board
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

show databases;

-- Django 전용 사용자계정 만듦
CREATE USER IF NOT EXISTS
'django_user'@'localhost'
IDENTIFIED BY 'django1234!';

-- 127.0.0.1 연결용도 만듦
CREATE USER IF NOT EXISTS
'django_user'@'127.0.0.1'
IDENTIFIED BY 'django1234!';

-- 권한 부여
GRANT ALL privileges
ON django_member_board.*
TO 'django_user'@'localhost';

GRANT ALL privileges
ON django_member_board.*
TO 'django_user'@'127.0.0.1';

-- 적용
FLUSH PRIVILEGES;
```

이 내용을 `프로젝트루트/db/create_database.sql` 로 저장해 둡니다. 나중에 다른 PC에서 그대로 재현할 수 있습니다.

**하나씩 왜 하는지**

- `CHARACTER SET utf8mb4` : 한글과 이모지를 저장하기 위한 문자셋입니다. 옛날 `utf8` 은 3바이트라 이모지(4바이트)가 깨집니다. **반드시 utf8mb4**.
- `COLLATE utf8mb4_unicode_ci` : 문자열 정렬/비교 규칙. `ci` 는 case-insensitive(대소문자 구분 안 함).
- **전용 계정을 따로 만드는 이유** : root로 접속하면 실수로 다른 DB까지 지울 수 있습니다. 이 프로젝트 DB에만 권한이 있는 계정을 쓰면 사고 범위가 제한됩니다. 실무의 기본 원칙(최소 권한)입니다.
- `'django_user'@'localhost'` 와 `@'127.0.0.1'` **둘 다 만드는 이유** : MySQL은 계정을 "아이디 + 접속 위치" 쌍으로 구분합니다. `localhost` 로 만든 계정은 `127.0.0.1` 로 접속할 때 인식되지 않을 수 있어서 둘 다 만들어 둡니다.
- `FLUSH PRIVILEGES` : 바꾼 권한을 메모리에 즉시 반영.

---

## 12. Django 와 MySQL 연결

`config/settings.py`

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",

        # .env 의 db 이름을 읽어온다.
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "PORT": os.getenv("DB_PORT"),
        "HOST": os.getenv("DB_HOST"),
        # 한글과 이모지를 저장할 수 있게 문자셋 지정
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
```

`ENGINE` 은 어떤 DB를 쓸지 정하는 부분입니다. sqlite를 쓰면 `django.db.backends.sqlite3`, MySQL이면 `django.db.backends.mysql` 입니다.
Django는 이 설정만 바꾸면 **같은 모델 코드로 다른 DB를 쓸 수 있습니다.** 이게 ORM의 큰 장점입니다.

### 연결 테스트

```bash
python manage.py check
```

`System check identified no issues` 가 나와야 정상입니다.

**자주 나는 오류**

| 메시지 | 원인 |
|---|---|
| `Error loading MySQLdb module` | `mysqlclient` 미설치. 가상환경 활성화 여부부터 확인 |
| `Access denied for user` | `.env` 의 계정/비번 오타, 또는 GRANT 안 됨 |
| `Unknown database` | `CREATE DATABASE` 를 안 했거나 이름 오타 |
| `Can't connect to MySQL server` | MySQL 서버가 꺼져 있음 |

---

## 13. 사용자 정의 Member 모델 만들기

설정이 끝나면 **모델부터** 작업합니다. 회원 기능에서는 Django 기본 User를 그대로 쓰지 않고 직접 만듭니다.

`members/models.py`

```python
# Django 기본 사용자 모델을 확장하기 위해 가져옴
from django.contrib.auth.models import AbstractUser

# Model과 DB 필드(테이블의 컬럼)를 정의하기 위함
from django.db import models


# AbstractUser 를 상속받아서, Django 인증 기능을 그대로 사용할 수 있다.
class Member(AbstractUser):
    # 성별 선택값
    GENDER_CHOICES = [
        ('M', '남자'),
        ('F', '여자'),
        ("N", '선택 안 함'),
    ]

    # 로그인 아이디
    username = models.CharField('회원 아이디', max_length=50, unique=True)

    # 화면에 보여줄 실제 회원 이름
    display_name = models.CharField("회원 이름", max_length=50)

    # 성별
    gender = models.CharField('성별', max_length=1, choices=GENDER_CHOICES, default='N')

    # 나이
    age = models.PositiveIntegerField("나이", null=True, blank=True)

    # 전화번호
    phone = models.CharField("전화번호", max_length=20, blank=True)

    # 이메일
    email = models.EmailField("이메일", unique=True)

    # 프로필 사진
    photo = models.ImageField("프로필 사진", upload_to='members_photos/%Y/%m/', blank=True, null=True)

    # 수정 날짜
    updated_at = models.DateTimeField("마지막 수정일", auto_now=True)

    # 객체를 문자열로 표현 (관리자 화면·디버깅에서 보임)
    def __str__(self):
        return f"{self.username} ({self.display_name})"
```

### Model 이 뭔가요?

**파이썬 클래스 하나 = DB 테이블 하나** 입니다.
클래스 안의 변수 하나 = 테이블의 컬럼 하나.
우리가 SQL로 `CREATE TABLE` 을 직접 쓰지 않아도 Django가 대신 만들어 줍니다. 이 기능을 **ORM**(Object-Relational Mapping)이라고 합니다.

```text
class Member(models.Model)   →   members_member 테이블
    username = CharField     →   username VARCHAR(50) 컬럼
```

테이블 이름은 기본적으로 `앱이름_모델이름소문자` 가 됩니다. 그래서 `members_member` 입니다.

### 왜 AbstractUser 를 상속하나요?

`AbstractUser` 안에는 이미 `username, password, email, first_name, last_name, is_staff, is_active, is_superuser, last_login, date_joined` 와
**비밀번호 해시 처리, 로그인 검증** 같은 기능이 전부 들어 있습니다.
상속하면 그 기능을 공짜로 받고, 우리는 필요한 필드(`display_name`, `gender`, `phone`, `photo` ...)만 추가하면 됩니다.

| 방법 | 설명 |
|---|---|
| Django 기본 `User` 그대로 | 필드 추가 불가. 나중에 후회함 |
| `AbstractUser` 상속 | ✅ 기본 기능 유지 + 필드 추가. **입문자 추천** |
| `AbstractBaseUser` 상속 | 인증 로직까지 직접 구현. 어려움 |

### 필드 옵션 읽는 법

- 첫 번째 문자열 인자(`'회원 아이디'`)는 **verbose_name** 입니다. 관리자 화면과 폼 라벨에 이 이름이 나옵니다.
- `max_length` : `CharField` 는 필수. VARCHAR 길이가 됩니다.
- `unique=True` : 중복 불가. DB에 UNIQUE 제약이 걸리고, 폼에서 "이미 존재합니다" 오류가 자동으로 나옵니다.
- `null=True` : **DB에** 빈 값(NULL) 허용.
- `blank=True` : **폼에서** 입력 안 해도 통과.
  → 이 둘은 다릅니다. 문자열 필드는 보통 `blank=True` 만 씁니다(빈 문자열 `""` 을 쓰므로). 숫자·날짜·파일은 `null=True, blank=True` 를 같이 씁니다.
- `choices=` : 정해진 값만 선택. 폼에서 자동으로 `<select>` 드롭다운이 됩니다.
- `default=` : 값을 안 주면 들어갈 기본값.
- `upload_to='members_photos/%Y/%m/'` : `MEDIA_ROOT` 아래 저장될 경로. `%Y/%m` 은 연/월 폴더로 자동 분류합니다. 한 폴더에 파일이 수만 개 쌓이는 것을 막는 실무 습관입니다.
- `auto_now=True` : 저장할 때마다 현재 시각으로 갱신 (수정일).
  `auto_now_add=True` : 처음 만들 때만 기록 (생성일).

### `__str__` 은 왜 만드나요?

이걸 안 만들면 관리자 화면이나 디버깅 출력에서 `Member object (1)` 처럼 알아볼 수 없게 나옵니다.
`__str__` 을 정의하면 `testuser1 (홍길동)` 처럼 사람이 읽을 수 있게 나옵니다. **연산자 오버로딩**의 한 예입니다.

---

## 14. settings.py 에 AUTH_USER_MODEL 설정

```python
# Django 기본 auth.User 대신
# members 앱의 Member를 사용자 Model 로 지정함
AUTH_USER_MODEL = "members.Member"
```

형식은 `"앱이름.모델클래스이름"` 입니다. (`members.User` 가 아니라 **`members.Member`** — 클래스 이름과 정확히 같아야 합니다.)

> ### ⚠️ 순서가 매우 중요합니다
>
> 이 설정은 **첫 `migrate` 를 실행하기 전에** 반드시 해야 합니다.
> 이미 마이그레이션을 돌린 뒤에 바꾸면 기존 `auth_user` 테이블과 충돌해서
> `ValueError: The field admin.LogEntry.user was declared with a lazy reference...` 같은 오류가 나고,
> 사실상 **DB를 지우고 처음부터 다시 하는 것**이 가장 빠른 해결책이 됩니다.
>
> 그래서 Django 공식 문서도 "프로젝트 시작할 때 무조건 커스텀 User 모델을 만들어라" 라고 권합니다.

---

## 15. 마이그레이션 : 모델을 실제 테이블로

```bash
python manage.py makemigrations
```

```bash
python manage.py migrate
```

### 두 명령의 차이

```text
models.py 수정
     │
     │  python manage.py makemigrations
     ▼
migrations/0001_initial.py   ← 설계도(파이썬 파일) 생성. DB는 아직 안 바뀜
     │
     │  python manage.py migrate
     ▼
MySQL 에 실제 CREATE TABLE 실행   ← 여기서 진짜 테이블이 생김
```

- `makemigrations` : 모델의 **변경 사항을 감지해서 설계도 파일을 만듭니다.** DB는 건드리지 않습니다.
- `migrate` : 그 설계도를 실제 SQL로 바꿔 DB에 적용합니다.

**왜 두 단계로 나눴을까요?**
설계도가 파일로 남기 때문에 팀원과 깃으로 공유할 수 있고, 변경 이력이 기록되며, 문제가 생기면 되돌릴 수도 있습니다.
`migrations/` 폴더는 **깃에 반드시 포함**시켜야 합니다.

### 유용한 확인 명령

```bash
python manage.py showmigrations
```

```bash
python manage.py sqlmigrate members 0001
```

`sqlmigrate` 는 실제로 실행될 SQL을 보여줍니다. ORM이 어떤 SQL을 만드는지 눈으로 볼 수 있어서 공부에 아주 좋습니다.

**자주 나는 상황**

- `No changes detected` : 모델을 안 바꿨거나, 앱이 `INSTALLED_APPS` 에 없음.
- `No migrations to apply` : 이미 적용됨. 정상입니다.

---

## 16. 관리자 계정 만들고 admin 에 모델 등록

```bash
python manage.py createsuperuser
```

`members/admin.py`

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member


@admin.register(Member)
class MemberAdmin(UserAdmin):
    """관리자 사이트에서 회원을 관리하는 화면입니다."""

    # 목록 화면에 보여줄 컬럼
    list_display = ("username", "display_name", "email", "gender", "age", "is_staff")

    # 회원 상세/수정 화면의 항목 구성
    fieldsets = UserAdmin.fieldsets + (
        ("추가 회원 정보", {"fields": ("display_name", "gender", "age", "phone", "photo")}),
    )

    # 관리자 화면에서 회원을 새로 추가할 때 보여줄 항목
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("추가 회원 정보", {"fields": ("display_name", "email", "gender", "age", "phone", "photo")}),
    )
```

**admin 을 쓰는 이유**

Django는 모델만 등록하면 **CRUD 화면을 공짜로** 만들어 줍니다.
회원 목록 화면을 따로 만들지 않아도 `http://127.0.0.1:8000/admin/` 에서 데이터를 눈으로 확인하고 수정할 수 있어서, **개발 중 데이터가 제대로 들어갔는지 확인하는 용도**로 아주 유용합니다.

`UserAdmin` 을 상속하는 이유는 비밀번호를 평문으로 보여주지 않고 해시로 처리하는 등 사용자 전용 화면 기능을 그대로 쓰기 위해서입니다.
`fieldsets` 에 우리가 추가한 필드를 넣지 않으면 관리자 화면에 그 필드들이 안 보입니다.

```bash
python manage.py runserver
```

`/admin/` 에 로그인해서 회원 목록이 보이면 **1단계 완료**입니다.

---

## 1단계 체크리스트

```text
□ 가상환경 활성화됨 ((.venv) 표시 확인)
□ pip install -r requirements.txt 완료
□ django-admin startproject config .  (점 찍기)
□ python manage.py startapp members   (프로젝트 루트에 생성)
□ INSTALLED_APPS 에 'members' 등록
□ templates / static / media 폴더 생성
□ settings 의 TEMPLATES DIRS, STATIC, MEDIA 설정
□ .env 작성 + load_dotenv
□ .gitignore 작성 (.env, .venv 제외)
□ MySQL DB / 계정 / 권한 생성
□ DATABASES 설정 후 python manage.py check → no issues
□ models.py 에 Member 작성
□ AUTH_USER_MODEL = "members.Member"   ← migrate 전에!
□ makemigrations → migrate
□ createsuperuser → /admin/ 접속 확인
```

다음은 `pj설명2.md` — 회원가입 / 로그인 / 로그아웃 화면 만들기입니다.
