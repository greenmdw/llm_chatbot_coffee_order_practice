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