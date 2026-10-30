"""VCF(연속 사삼으로 강제승리) 솔버 — 정답 유일성까지 검증함.

수순 중 어느 지점에서든 공격 측이 이기는 수가 정확히 하나뿐일 때만 퍼즐로 인정함
(다른 정답, 즉 "cook"이 있으면 버림). 상대(수비) 쪽 응수는 규칙상 강제됨
(완성되는 자리 하나를 막아야 하거나, 더블 포라서 아예 못 막는 경우뿐)이라
반환하는 수순 안에 같이 포함시킴 — 앱에서 유저 클릭 사이사이에 자동 재생하면 됨.

**렌주 흑 금수 반영**: 이 솔버가 두는 수는(공격이든 수비든) 색이 흑이면 렌주
공식 금수(장목/사사/삼삼, renju_forbidden.py)를 지킴 — 금수인 자리는 후보에서
아예 빼고, 흑의 "승리"도 장목이 아니라 정확히 5개일 때만 인정함(백은 기존대로
5개 이상이면 다 승리, 금수 제한 없음). 유저가 퍼즐 #86에서 "반박수로 흑이
6목을 만드는데 렌주 룰이면 그거 금수 아니야?"라고 제보해서 추가함 — 전엔
자유형 규칙으로만 계산해서 흑이 렌주 룰로는 둘 수 없는 수를 강제승리 수순에
섞어 쓰는 경우가 있었음.
"""

from gomoku import BLACK, WHITE, other
import renju_forbidden

FAIL, UNIQUE, MULTIPLE = 0, 1, 2


def _wins(board, r, c, player):
    """(r, c)에 player가 이미 놓인 상태에서, 이게 '진짜' 승리인지. 백은 기존
    is_five(5개 이상 다 승리) 그대로, 흑은 정확히 5개일 때만(장목은 승리 아님)."""
    if player == WHITE:
        return board.is_five(r, c, player)
    return renju_forbidden.wins_with_exact_five(board, r, c)


def _legal(board, r, c, player, comp=None):
    """(r, c)에 player가 이미 놓인 상태에서, 이 수 자체가 합법인지. 백은 항상
    합법(렌주 금수 없음), 흑은 장목/사사/삼삼이면 불법. 승리 수는 항상 합법
    (renju_forbidden의 우선순위 규칙 — 이기는 수가 금수보다 늘 우선). `comp`를
    미리 계산해서 넘기면(아래 _solve 메인 루프처럼) 중복 계산 피함."""
    if player == WHITE:
        return True
    return not renju_forbidden.is_forbidden_for_black(board, r, c, comp)


def _real_win_completion_cells(board, player, comp):
    """completion_cells()가 찾아준 '4개+빈칸1'은 순수 기하학적 패턴이라, 흑이면
    그 중 일부가 실제로는 장목(진짜 승리 아님)일 수 있음 — 하나씩 가정으로 둬서
    실제 승리(정확히 5개)가 맞는 자리만 거름. 백은 그럴 걱정이 없어서 그대로 반환."""
    if player == WHITE:
        return comp
    valid = set()
    for (cr, cc) in comp:
        board.place(cr, cc, player)
        if _wins(board, cr, cc, player):
            valid.add((cr, cc))
        board.undo(cr, cc)
    return valid


def _pick_block_and_finish(board, comp, defender):
    """더블 포(완성 자리 2개 이상) 상황에서, "수비 측이 흉내만 내듯 막는 자리"
    (block)와 "그래도 공격 측이 마무리하는 자리"(finish)를 고름. 수비가 백이면
    아무 자리나 상관없음(백은 항상 합법). 수비가 흑이면, 막는 흉내로 보여줄
    자리가 실제로 흑이 합법하게 둘 수 있는 자리여야 함 — 후보 중 합법한 자리가
    하나도 없으면(흑이 둘 다 못 막음) None을 반환해서 이 분기를 통째로 포기함
    (공격 측이 사실상 이기긴 하지만, 그 상태를 "수비 한 수 + 마무리 한 수"로
    깔끔하게 표현할 방법이 없어서 — 흑이 어디에도 합법하게 못 막는데 그렇다고
    공격 측 수 하나만으로 "풀었다"고 하면 보드에 아직 5개가 안 보이는 상태라
    앱 쪽 로직과 안 맞음. 이런 극히 드문 경우는 퍼즐로 안 씀)."""
    cells = sorted(comp)
    if defender == WHITE:
        return cells[0], cells[1]
    legal = [cell for cell in cells if _legal(board, cell[0], cell[1], BLACK)]
    if not legal:
        return None
    block = legal[0]
    finish = next(cell for cell in cells if cell != block)
    return block, finish


def _solve(board, player, depth_limit):
    """(status, move_list) 반환. move_list는 status가 UNIQUE일 때만 의미 있음."""
    if depth_limit <= 0:
        return FAIL, None

    defender = other(player)
    winners = []  # [(두는 자리, 수순)]
    for (r, c) in board.candidate_cells(margin=2):
        board.place(r, c, player)

        if _wins(board, r, c, player):
            # 이기는 수는 항상 합법(렌주 금수 우선순위 규칙) -> completion_cells
            # 계산 자체가 필요 없어서 건너뜀(성능 핫패스, 프로파일링으로 확인).
            winners.append(((r, c), [{"player": player, "pos": (r, c)}]))
            board.undo(r, c)
            if len(winners) > 1:
                break
            continue

        # completion_cells는 이 아래에서 금수 판정(사사)과 위협 판정 둘 다에
        # 쓰이는데, 예전엔 따로따로 두 번 불렀음 — 한 번만 구해서 재사용함
        # (가장 많이 불리는 함수라 프로파일링으로 확인된 핫패스).
        raw_comp = board.completion_cells(r, c, player)

        if not _legal(board, r, c, player, raw_comp):
            # 흑 차례인데 이 수 자체가 렌주 금수라 애초에 못 둠.
            board.undo(r, c)
            continue

        comp = _real_win_completion_cells(board, player, raw_comp)

        if len(comp) >= 2:
            # 더블 포(double threat): 상대는 둘 중 하나만 막을 수 있어서, 남은 자리로 공격 측이 마무리함.
            # 이 수순은 공격 측 수가 2개(지금 수 + 마무리 수) 들어가니 depth_limit도 최소 2는
            # 있어야 함 — 안 그러면 "depth=1 탐색"이라면서 실제로는 2수짜리 승리를 공짜로
            # 찾아버려서, 같은 depth에서 동등하게 탐색돼야 할 다른 2수 강제승리 수순(아래
            # len(comp)==1 재귀 분기)을 놓치고 "유일해"로 잘못 판정하는 버그가 있었음
            # (실전 QA에서 퍼즐 #56이 사실 공격 측 첫 수가 3가지나 되는 cook으로 드러남).
            if depth_limit >= 2:
                chosen = _pick_block_and_finish(board, comp, defender)
                if chosen is not None:
                    block, finish = chosen
                    moves = [
                        {"player": player, "pos": (r, c)},
                        {"player": defender, "pos": block},
                        {"player": player, "pos": finish},
                    ]
                    winners.append(((r, c), moves))
            board.undo(r, c)
            if len(winners) > 1:
                break
            continue

        if len(comp) == 1:
            block = next(iter(comp))
            if not _legal(board, block[0], block[1], defender):
                # 유일하게 막을 자리 자체가 수비 측(흑) 금수라 못 막음 — 공격 측이
                # 사실상 이기지만, 보드에 아직 5개가 안 보이는 상태라 "공격 측 수
                # 하나만으로 풀었다" 식으로는 표현이 안 됨(위 _pick_block_and_finish
                # 설명과 같은 이유) -> 이 경로는 퍼즐로 안 쓰고 스킵.
                board.undo(r, c)
                continue
            board.place(block[0], block[1], defender)
            status, sub_moves = _solve(board, player, depth_limit - 1)
            board.undo(block[0], block[1])
            if status == UNIQUE:
                moves = [
                    {"player": player, "pos": (r, c)},
                    {"player": defender, "pos": block},
                ] + sub_moves
                winners.append(((r, c), moves))
            board.undo(r, c)
            if len(winners) > 1:
                break
            continue

        # 포 위협을 만들지 못하는 수 -> 순수 VCF 수순으로 이어지지 않으니 버림.
        board.undo(r, c)

    if len(winners) == 1:
        return UNIQUE, winners[0][1]
    if len(winners) == 0:
        return FAIL, None
    return MULTIPLE, None


def solve_unique_vcf(board, player, max_attacker_moves):
    """외부에서 호출하는 진입점. `max_attacker_moves` 수 이내에 유일한 강제승리
    수순이 있으면 그 수순({"player", "pos"} 딕셔너리 리스트, 공격+강제수비 교차,
    마지막엔 5개 완성)을 반환. 없거나 정답이 여러 개면 None."""
    status, moves = _solve(board, player, max_attacker_moves)
    return moves if status == UNIQUE else None


def attacker_move_count(move_sequence, player):
    return sum(1 for m in move_sequence if m["player"] == player)
