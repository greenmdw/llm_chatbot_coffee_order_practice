# 회원 / 게시판 연습 프로젝트

Django 학습을 위해 처음부터 만들어본 회원 관리 + 게시판 웹 애플리케이션입니다.
MySQL과 연동되며, 회원가입부터 게시글 CRUD, 권한 처리까지 실제 서비스에 필요한 기본 기능을 갖추고 있습니다.

## 주요 기능

### 회원 관리
- 회원가입 / 로그인 / 로그아웃
- 회원정보 조회 / 수정 / 탈퇴(계정 삭제)
- 사용자 정의 `Member(AbstractUser)` 모델 (아이디, 이름, 성별, 나이, 전화번호, 프로필 사진 등)
- 세션 기반 로그인 상태 유지 (30분 비활성 시 자동 만료)
- 비밀번호 해시 저장 (`UserCreationForm` + `set_password`, 평문 저장 없음)
- 관리자 `is_staff` / `is_superuser` 권한 처리
- 계정 비활성화(`is_active`)를 통한 로그인 제한 — 관리자가 특정 회원의 로그인을 막을 수 있음
- Django Admin에서 회원 목록 조회 및 관리

### 게시판
- 게시글 목록 / 상세보기 / 등록 / 수정 / 삭제 (CRUD)
- 제목 · 내용 기준 검색
- 10개 단위 페이지네이션 (검색 결과에서도 페이지 이동 시 검색어 유지)
- 로그인한 회원만 게시글 등록 가능
- 작성자 본인만 게시글 수정 가능
- 작성자 본인 또는 관리자(`is_staff`/`is_superuser`)만 게시글 삭제 가능
- 게시글 첨부파일 업로드
- 게시글 조회수 자동 증가
- 회원 탈퇴 시 작성한 게시글도 함께 삭제(`on_delete=CASCADE`)
- Django Admin에서 게시글 조회 · 검색 · 관리

### 공통
- MySQL 연동, Django Migration 기반 테이블 관리
- `.env` 환경변수로 비밀 정보(SECRET_KEY, DB 접속정보) 분리
- 가입/로그인/등록/수정/삭제 등 모든 동작에 성공·실패 안내 메시지(배너) 표시
- 첨부파일/프로필 사진 업로드(media)와 CSS(static) 분리 관리

## 기술 스택

| 구분 | 사용 기술 |
|---|---|
| 언어/프레임워크 | Python, Django 5.2 |
| 데이터베이스 | MySQL (`mysqlclient`) |
| 이미지 처리 | Pillow (`ImageField` 업로드용) |
| 환경변수 | python-dotenv |

## 프로젝트 구조

```text
20260810_django_mypj/
├── config/         # 프로젝트 설정 (settings, urls)
├── members/        # 회원 앱 (가입/로그인/로그아웃/회원정보/탈퇴)
├── boards/         # 게시판 앱 (게시글 CRUD, 검색, 페이징)
├── templates/      # HTML 템플릿 (home, members/*, boards/*)
├── static/css/     # 공통 스타일시트
├── media/          # 업로드된 프로필 사진 / 첨부파일
├── db/             # MySQL DB·계정 생성용 SQL
├── .env            # DB 접속정보, SECRET_KEY 등 (git에 올리지 않음)
└── manage.py
```

## 시작하기

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. .env 파일 작성 (DB 접속정보, SECRET_KEY 등)
#    아래 학습 문서의 9번 항목 참고

# 4. MySQL DB/계정 생성
#    db/create_database.sql 참고

# 5. 마이그레이션
python manage.py migrate

# 6. 관리자 계정 생성
python manage.py createsuperuser

# 7. 서버 실행
python manage.py runserver
```

## 학습 문서

이 프로젝트를 처음부터 만드는 전체 과정과, 각 단계를 왜 그렇게 하는지에 대한 설명은 아래 문서에 정리되어 있습니다.

| 문서 | 내용 |
|---|---|
| [pj설명.md](pj설명.md) | 1단계 — 프로젝트 뼈대, MySQL 연동, 회원 모델(Member) 생성 |
| [pj설명2.md](pj설명2.md) | 2단계 — 회원가입 / 로그인 / 로그아웃 / 회원정보 조회·수정·탈퇴 |
| [pj설명3.md](pj설명3.md) | 3단계 — 게시판 앱(CRUD, 검색, 페이징, 권한 처리) |
