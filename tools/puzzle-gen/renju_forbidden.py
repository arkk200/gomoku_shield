"""렌주 금수(흑 전용 금지수) 판정 — 장목(overline), 사사(double-four), 삼삼(double-three).

gomoku.py의 Board는 "프리스타일, 금수 없음"이 기본 계약임(그쪽 모듈 docstring 참고) —
그래서 이 로직은 일부러 분리된 모듈로 둠. 필요한 곳(vcf.py의 퍼즐 생성/검증)에서만
명시적으로 불러써서, 앱이 실제로 쓰는 "자유형" 규칙 자체는 안 건드림.

왜 필요했는지(CLAUDE.md 참고): 퍼즐 포지션은 RenjuNet 실제 대국(렌주 공식룰로 둔
기보)에서 가져오는데, 강제승리 수순은 우리 자유형 VCF 솔버가 처음부터 다시 계산함.
그러다 보니 흑이 렌주 룰에서는 애초에 둘 수 없는 수(장목을 만드는 수 등)를 "합법한
이기는 수"로 써버리는 경우가 실제로 있었음(유저 제보로 발견, 퍼즐 #86). 이 모듈을
vcf.py에 연결해서 흑이 관련된 모든 수(공격이든 수비든)가 렌주 금수를 어기지 않게 함.

렌주 공식룰(RIF)에서 흑에게만 적용되는 세 가지 금지수:
- 장목(overline): 흑이 둬서 6개 이상 연속이 되면 그 수는 금수. 단, 같은 수가 어느
  방향으로든 "정확히 5개"를 동시에 완성하면 그건 이미 승리고 금수보다 우선임.
- 사사(double-four): 흑의 한 수가 동시에 "사"(한 수 더 두면 5개가 완성되는 4개
  연속) 두 개 이상을 만들면 금수. 역시 그 수 자체가 승리 수면 우선 적용 안 됨.
- 삼삼(double-three): 흑의 한 수가 동시에 "열린 삼"(한 수 더 두면 '열린 사'—
  양쪽 다 막히지 않아서 못 막는 사—가 되는 3개 연속) 두 개 이상을 만들면 금수.

**구현 범위 명시(의도적 단순화)**: RIF 공식룰 9.3조는 "그 삼을 사로 키웠을 때
장목이나 다른 금수 없이 진짜 사가 되는 경우가 하나 이하면 삼삼 아님"이라는 예외를
두는데, 이건 "삼을 사로 키우는 가상의 수 자체가 또 금수인지"까지 재귀적으로
따져야 해서 공식 렌주 소프트웨어도 흔히 버그 나는 부분으로 알려져 있음. 이 구현은
그 예외 없이 "열린 삼이 2개 이상이면 무조건 삼삼"으로 단순화함 — 아주 드문 경계
케이스에서 공식 룰보다 살짝 더 엄격하게(흑에게 불리하게) 판정할 수 있음. 사이드로드
개인 프로젝트 범위에서 합리적인 타협으로 판단함.
"""

from gomoku import BLACK, DIRECTIONS, EMPTY


def _run_span(board, r, c, player, dr, dc):
    """(r, c)를 포함해서 (dr, dc) 방향으로 이어지는 연속된 player 구간의
    시작/끝 좌표와 길이를 반환. (r, c) 자리에 player가 이미 놓여 있어야 함."""
    sr, sc = r, c
    while True:
        pr, pc = sr - dr, sc - dc
        if board.in_bounds(pr, pc) and board.grid[pr][pc] == player:
            sr, sc = pr, pc
        else:
            break
    er, ec = r, c
    while True:
        nr, nc = er + dr, ec + dc
        if board.in_bounds(nr, nc) and board.grid[nr][nc] == player:
            er, ec = nr, nc
        else:
            break
    length = 1
    rr, cc = sr, sc
    while (rr, cc) != (er, ec):
        rr += dr
        cc += dc
        length += 1
    return sr, sc, er, ec, length


def _span_is_open(board, sr, sc, er, ec, dr, dc):
    """[sr,sc]~[er,ec] 구간 바로 양 옆 칸이 둘 다 빈칸인지(= 막히지 않은 '열린'
    구간인지) 확인. 하나라도 막혀 있으면(상대 돌/보드 밖) False."""
    before = (sr - dr, sc - dc)
    after = (er + dr, ec + dc)
    return (
        board.in_bounds(*before)
        and board.grid[before[0]][before[1]] == EMPTY
        and board.in_bounds(*after)
        and board.grid[after[0]][after[1]] == EMPTY
    )


def _on_span(r, c, sr, sc, er, ec, dr, dc):
    """(r, c)가 [sr,sc]~[er,ec] 구간 안에 있는지(그 직선 위의 칸인지) 확인."""
    rr, cc = sr, sc
    while True:
        if (rr, cc) == (r, c):
            return True
        if (rr, cc) == (er, ec):
            return False
        rr += dr
        cc += dc


def wins_with_exact_five(board, r, c):
    """(r, c)에 흑이 이미 놓인 상태에서, 어느 방향으로든 '정확히 5개'(6개 이상은
    장목이라 승리 아님)를 완성하는지. 이기는 수는 금수 판정보다 항상 우선임.
    vcf.py가 흑의 승리 판정에 직접 씀(백은 gomoku.py의 is_five를 그대로 씀 —
    백은 장목 제한이 없어서 5개 이상이면 다 승리)."""
    return any(_run_span(board, r, c, BLACK, dr, dc)[4] == 5 for dr, dc in DIRECTIONS)


def _is_overline(board, r, c):
    """장목(6개 이상 연속) 여부."""
    return any(_run_span(board, r, c, BLACK, dr, dc)[4] >= 6 for dr, dc in DIRECTIONS)


def _is_double_four(board, r, c, comp=None):
    """사사(이 한 수로 '사'가 동시에 2개 이상 생기는지) 여부.
    gomoku.py의 completion_cells가 정확히 이 패턴(4개 연속+빈칸1)을 모든 방향에서
    찾아주는 함수라 그대로 재사용함(VCF 솔버의 '더블 포' 분기와 같은 개념).
    `comp`를 미리 계산해서 넘기면 다시 안 돌림 — vcf.py의 _solve가 같은 (r,c)에
    대해 completion_cells를 이미 호출해둔 경우가 많아서(성능 핫패스, 프로파일링으로
    확인) 중복 호출을 피하려고 둠."""
    if comp is None:
        comp = board.completion_cells(r, c, BLACK)
    return len(comp) >= 2


def _is_live_three_direction(board, r, c, dr, dc):
    """(r, c)에 흑이 이미 놓인 상태에서, 이 방향으로 지나는 흑 돌이 '열린 삼'인지.
    정적인 패턴(BBB 등)을 미리 나열하는 대신, "이 방향 근처 빈 칸 하나에 흑을
    더 뒀을 때 (r,c)를 포함하는 열린 사가 실제로 만들어지는가"를 직접 시뮬레이션
    해서 확인함 — 이어진 삼(BBB)이든 끊긴 삼(BB_B, B_BB)이든 따로 패턴을 안 챙겨도
    같은 로직으로 맞게 처리됨."""
    candidates = list(range(-4, 0)) + list(range(1, 5))

    # 빠른 선필터(성능용): 이 방향에 (r,c) 말고 흑 돌이 하나도 없으면 삼 자체가
    # 안 되니, 비싼 시뮬레이션(돌 놓기/되돌리기) 전에 그냥 바로 포기함 — 후보
    # 칸 대부분은 주변에 흑이 아예 없는 경우라 이 선필터가 실제로 많이 걸러냄.
    if not any(
        board.in_bounds(r + k * dr, c + k * dc) and board.grid[r + k * dr][c + k * dc] == BLACK
        for k in candidates
    ):
        return False

    for k in candidates:
        pr, pc = r + k * dr, c + k * dc
        if not board.in_bounds(pr, pc) or board.grid[pr][pc] != EMPTY:
            continue
        board.place(pr, pc, BLACK)
        sr, sc, er, ec, length = _run_span(board, pr, pc, BLACK, dr, dc)
        becomes_open_four = length == 4 and _span_is_open(board, sr, sc, er, ec, dr, dc)
        includes_move = becomes_open_four and _on_span(r, c, sr, sc, er, ec, dr, dc)
        board.undo(pr, pc)
        if includes_move:
            return True
    return False


def _is_double_three(board, r, c):
    """삼삼(이 한 수로 '열린 삼'이 동시에 2개 이상 생기는지) 여부. 2개를 찾는
    순간 바로 반환 — 나머지 방향까지 다 돌 필요 없음(성능용 조기 종료)."""
    live_count = 0
    for dr, dc in DIRECTIONS:
        if _is_live_three_direction(board, r, c, dr, dc):
            live_count += 1
            if live_count >= 2:
                return True
    return False


def is_forbidden_for_black(board, r, c, comp=None):
    """board.place(r, c, BLACK)가 이미 호출된 상태에서 호출해야 함(gomoku.py의
    is_five/completion_cells와 같은 호출 관례). 장목/사사/삼삼 중 하나라도
    해당하면 True(= 렌주 룰에서 흑이 둘 수 없는 자리). 그 수가 어느 방향으로든
    정확히 5개를 완성하는 승리 수면 항상 우선이라 금수 아님(False). `comp`는
    _is_double_four로 그대로 전달됨(호출 쪽에서 completion_cells를 이미
    구해뒀으면 중복 계산 피하려고 넘길 수 있음 — 선택 사항, 안 넘기면 알아서 구함)."""
    if wins_with_exact_five(board, r, c):
        return False
    if _is_overline(board, r, c):
        return True
    if _is_double_four(board, r, c, comp):
        return True
    if _is_double_three(board, r, c):
        return True
    return False
