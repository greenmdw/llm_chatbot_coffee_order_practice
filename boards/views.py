# boards/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BoardForm
from .models import Board


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

        # 목록 뷰로 이동(뷰에서 뷰를 호출할 때: redirect 사용)
        return redirect('boards:list')
    elif request.method == 'POST':
        # 검증 실패시, 실패했다는 사실을 눈에 띄게 알려줌
        messages.error(request, "게시글 등록에 실패했습니다. 아래 항목을 확인해주세요.")

    # 전송방식이 get이거나, 유효성 검사가 실패라면, 새 게시글 등록 페이지 계속 출력되게 함
    return render(request, 'boards/board_form.html', {'form': form, 'mode': '등록'})


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

        # 수정 성공하면, 상세보기 뷰를 작동시킴 (뷰에서 다른 뷰 실행은 redirect 사용)
        return redirect('boards:detail', pk=pk)
    elif request.method == 'POST':
        messages.error(request, "게시글 수정에 실패했습니다. 아래 항목을 확인해주세요.")

    # 전송 방식이 get이거나, 유효성 검사가 false 이면 계속 수정 페이지 출력
    return render(request, 'boards/board_form.html', {'form': form, 'mode': '수정'})


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
