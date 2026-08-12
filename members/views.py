# members/views.py

# Django 로그인/로그아웃 기능
from django.contrib.auth import login, logout

# 성공 안내 메시지
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# HTML 출력과 URL 이동 기능
from django.shortcuts import render, redirect

# 회원 관련 form
# 같은 앱 안의 forms.py 이므로 점(.) 상대경로로 가져옴
from .forms import SignUpForm, LoginForm, ProfileForm

def home(request):
    """로그인 여부와 관계없이 접근 가능한 첫 화면"""
    # 로그인 성공시 Django가 자동으로 request.user 정보를 Template에 전달하게 됨
    return render(request, 'home.html')

def signup(request):
    """회원 가입 처리 view 입니다"""
    # POST 요청이면, 사용자가 입력한 데이터를 받음
    if request.method == 'POST':
        # 일반 데이터와 업로드 파일을 form 에 전달함
        form = SignUpForm(request.POST, request.FILES)

        # 입력값 검증 후 수행
        if form.is_valid():
            # 입력값들이 모두 유효하면, 가입한 회원 정보를 db에 저장 처리
            # 비밀번호는 평문이 아닌 해시로 저장됨
            member = form.save()

            # 가입한 사용자를 즉시 로그인 처리함
            # 이 때, Django Session이 생성됨
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
            # {{ form.as_p }} 가 자동으로 출력해 줌
            messages.error(
                request,
                "회원 가입에 실패했습니다. 아래 빨간 글씨로 표시된 항목을 확인해주세요."
            )
    else:
        # Get 요청이면 빈 회원가입 form을 만듦
        form = SignUpForm()

    # POST 인데 입력값이 잘못된 경우에는
    # 오류 메시지가 담긴 form 을 다시 그려줌
    return render(request, 'members/signup.html', {'form': form})

# 로그인 뷰도 작성
def login_view(request):
    """회원 로그인 뷰 입니다."""
    # Django AuthenticationForm 생성
    form = LoginForm(
        request=request,
        data=request.POST or None,
    )

    # Post 요청이면서 인증에 성공했다면
    if request.method == 'POST' and form.is_valid():
        # 인증된 회원 객체를 가져옴
        member = form.get_user()

        # Django 세션에 사용자 인증 정보를 저장
        login(request, member)

        messages.success(
            request,
            f"{member.display_name}님 로그인 되었습니다.",
        )

        return redirect('home')

    # Post 요청인데 인증에 실패했다면
    elif request.method == 'POST':
        # 아이디가 없거나 비밀번호가 틀린 경우, 실패 사실을 눈에 띄게 알려줌
        # 구체적인 사유(아이디/비밀번호 불일치)는 form 이 자동으로 출력해 줌
        messages.error(
            request,
            "로그인에 실패했습니다. 아이디와 비밀번호를 다시 확인해주세요."
        )

    return render(request, 'members/login.html', {'form': form})

@login_required
# 로그아웃 View 작성
def logout_view(request):
    """현재 세션의 로그인 인증 정보를 제거"""
    logout(request)
    messages.success(
        request,
        "로그아웃 되었습니다."
    )

    return redirect('home')


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
