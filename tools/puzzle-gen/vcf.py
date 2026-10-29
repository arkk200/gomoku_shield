"""VCF(연속 사삼으로 강제승리) 솔버 — 정답 유일성까지 검증함.

수순 중 어느 지점에서든 공격 측이 이기는 수가 정확히 하나뿐일 때만 퍼즐로 인정함
(다른 정답, 즉 "cook"이 있으면 버림). 상대(수비) 쪽 응수는 규칙상 강제됨
(완성되는 자리 하나를 막아야 하거나, 더블 포라서 아예 못 막는 경우뿐)이라
반환하는 수순 안에 같이 포함시킴 — 앱에서 유저 클릭 사이사이에 자동 재생하면 됨.
"""

from gomoku import other

FAIL, UNIQUE, MULTIPLE = 0, 1, 2


def _solve(board, player, depth_limit):
    """(status, move_list) 반환. move_list는 status가 UNIQUE일 때만 의미 있음."""
    if depth_limit <= 0:
        return FAIL, None

    winners = []  # [(두는 자리, 수순)]
    for (r, c) in board.candidate_cells(margin=2):
        board.place(r, c, player)

        if board.is_five(r, c, player):
            winners.append(((r, c), [{"player": player, "pos": (r, c)}]))
            board.undo(r, c)
            if len(winners) > 1:
                break
            continue

        comp = board.completion_cells(r, c, player)

        if len(comp) >= 2:
            # 더블 포(double threat): 상대는 둘 중 하나만 막을 수 있어서, 남은 자리로 공격 측이 마무리함.
            block, finish = sorted(comp)[:2]
            moves = [
                {"player": player, "pos": (r, c)},
                {"player": other(player), "pos": block},
                {"player": player, "pos": finish},
            ]
            winners.append(((r, c), moves))
            board.undo(r, c)
            if len(winners) > 1:
                break
            continue

        if len(comp) == 1:
            block = next(iter(comp))
            board.place(block[0], block[1], other(player))
            status, sub_moves = _solve(board, player, depth_limit - 1)
            board.undo(block[0], block[1])
            if status == UNIQUE:
                moves = [
                    {"player": player, "pos": (r, c)},
                    {"player": other(player), "pos": block},
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
