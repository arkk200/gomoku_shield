"""vcf.py 각 함수의 input/output 문서화 겸 테스트.

실행: tools/puzzle-gen 디렉토리에서 `python3 -m unittest discover -s tests`

주의: `_solve`는 내부 함수(이름 앞 `_`)라 직접 테스트하지 않고, 공개 API인
`solve_unique_vcf`를 통해서만 검증함.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gomoku import Board, BLACK, WHITE
from vcf import solve_unique_vcf, attacker_move_count


def place_all(board, stones):
    """테스트 셋업용. stones: [(r, c, player), ...] 전부 놓음."""
    for r, c, player in stones:
        board.place(r, c, player)


class TestSolveUniqueVcfBasics(unittest.TestCase):
    def test_empty_board_has_no_forced_win(self):
        """input: 빈 보드 -> output: None (강제승리 수가 있을 리 없음)."""
        board = Board()
        self.assertIsNone(solve_unique_vcf(board, BLACK, max_attacker_moves=3))

    def test_single_gap_in_four_is_depth_one_win(self):
        """input: 가로 4개 중 가운데 하나만 빔(c1,c2,c3,_,c5), depth=1
        -> output: 그 빈 칸(c4) 하나 두는 수순 (바로 5개 완성)."""
        board = Board()
        place_all(board, [(3, 1, BLACK), (3, 2, BLACK), (3, 3, BLACK), (3, 5, BLACK)])
        moves = solve_unique_vcf(board, BLACK, max_attacker_moves=1)
        self.assertEqual(moves, [{"player": BLACK, "pos": (3, 4)}])

    def test_open_four_has_two_winning_cells_so_returns_none(self):
        """input: 양쪽 다 열린 4개 연속(c5~c8) -> output: None.
        양 끝(c4, c9) 둘 다 독자적으로 5개를 완성시켜서 정답이 2개(= cook) -> 유일성 깨짐."""
        board = Board()
        for c in range(5, 9):
            board.place(7, c, BLACK)
        self.assertIsNone(solve_unique_vcf(board, BLACK, max_attacker_moves=1))

    def test_double_threat_requires_depth_two_not_depth_one(self):
        """실제 생성된 퍼즐 데이터 기반 회귀 테스트(버그 수정 후).
        input: 백 차례, (8,9)에 두면 (8,8)(8,9)(8,10)(8,11) 4개 연속이 되고
        양 끝(8,7)/(8,12)이 둘 다 열려 더블 포가 됨 — 이 수순은 공격 측 수가 2개
        (지금 수 + 마무리 수) 들어가니 depth=1에서는 못 찾아야 정상(예전엔 버그로
        depth=1에서 공짜로 찾아버려서, 같은 depth에서 찾아야 할 다른 대안 수순을
        놓치고 "유일해"로 오판하는 문제가 있었음 — 실제 퍼즐 #56이 이래서 cook됨).
        depth=1 -> None. depth=2 -> [백(8,9), 흑이 강제로 (8,7) 막음, 백이 (8,12)로 마무리]."""
        board = Board()
        stones = [
            (0, 5, BLACK), (0, 6, WHITE), (0, 7, BLACK), (1, 7, WHITE), (2, 4, BLACK),
            (3, 3, BLACK), (3, 5, BLACK), (3, 6, WHITE), (3, 9, WHITE), (4, 9, BLACK),
            (5, 5, WHITE), (5, 7, WHITE), (6, 4, BLACK), (6, 6, BLACK), (7, 5, BLACK),
            (7, 7, BLACK), (8, 8, WHITE), (8, 10, WHITE), (8, 11, WHITE),
        ]
        place_all(board, stones)

        self.assertIsNone(solve_unique_vcf(board, WHITE, max_attacker_moves=1))

        moves = solve_unique_vcf(board, WHITE, max_attacker_moves=2)
        self.assertEqual(
            moves,
            [
                {"player": WHITE, "pos": (8, 9)},
                {"player": BLACK, "pos": (8, 7)},
                {"player": WHITE, "pos": (8, 12)},
            ],
        )
        self.assertEqual(attacker_move_count(moves, WHITE), 2)

    def test_depth_matching_difficulty_finds_true_forced_win(self):
        """실제 생성된 퍼즐 데이터 기반 회귀 테스트 — 탐색 깊이(depth) 제한 동작 확인.
        input: 아래 복잡한 중반 포지션에서 백 차례.
        depth=1, depth=2 -> None(둘 다 강제승리 없음 — depth=2는 수정 전엔 버그로
        3수짜리 수순을 "유일해"로 잘못 찾아냈었는데, 실제로는 depth=2 안에서 다른
        대안도 있어서 cook이었음. 수정 후엔 정상적으로 None).
        depth=3 -> 백-흑-백-흑-백 5수짜리 강제승리 수순(공격 측 수 3개)."""
        board = Board()
        stones = [
            (3, 12, WHITE), (4, 1, BLACK), (4, 3, BLACK), (4, 6, WHITE), (5, 4, BLACK),
            (5, 12, BLACK), (6, 3, WHITE), (6, 9, WHITE), (7, 4, BLACK), (7, 7, BLACK),
            (7, 10, WHITE), (7, 11, BLACK), (8, 2, BLACK), (8, 5, BLACK), (8, 6, BLACK),
            (8, 7, WHITE), (8, 9, WHITE), (8, 11, WHITE), (9, 4, WHITE), (9, 8, WHITE),
            (9, 11, BLACK), (9, 12, BLACK), (10, 5, WHITE), (10, 7, BLACK), (10, 9, BLACK),
            (10, 11, WHITE), (11, 2, WHITE), (11, 4, BLACK), (11, 14, WHITE), (12, 0, BLACK),
            (12, 6, BLACK), (12, 8, WHITE), (12, 9, WHITE), (12, 13, BLACK), (13, 1, WHITE),
            (13, 5, WHITE), (13, 6, WHITE), (13, 11, BLACK), (14, 8, BLACK),
        ]
        place_all(board, stones)

        self.assertIsNone(solve_unique_vcf(board, WHITE, max_attacker_moves=1))
        self.assertIsNone(solve_unique_vcf(board, WHITE, max_attacker_moves=2))

        moves = solve_unique_vcf(board, WHITE, max_attacker_moves=3)
        self.assertEqual(
            moves,
            [
                {"player": WHITE, "pos": (7, 8)},
                {"player": BLACK, "pos": (9, 6)},
                {"player": WHITE, "pos": (9, 10)},
                {"player": BLACK, "pos": (6, 7)},
                {"player": WHITE, "pos": (11, 12)},
            ],
        )
        self.assertEqual(attacker_move_count(moves, WHITE), 3)


class TestRenjuForbiddenIntegration(unittest.TestCase):
    """vcf.py가 renju_forbidden.py를 실제로 쓰는지 확인하는 회귀 테스트.
    유저가 퍼즐 #86에서 "반박수로 흑이 6목(장목)을 만든다"고 제보해서 추가함."""

    def test_double_threat_block_prefers_the_legal_black_cell(self):
        """input: 백이 한 수로 두 '사'(가로/세로 각각 막힌 사 하나씩)를 동시에
        만드는 더블 포 — 완성 자리 (3,4)/(4,3) 중 (3,4)는 그 자리에 흑을 두면
        대각선으로 장목이 되는 자리(정렬하면 (3,4)가 (4,3)보다 먼저라서, 좌표
        순서로만 고르면 이 금수 자리를 '막는 수'로 잘못 골랐을 것). output: 수비
        (흑)의 '막는 수'로는 합법한 (4,3)을 고르고, 공격(백)의 마무리 수로
        (3,4)를 씀(마무리는 백 자신의 수라 흑 금수와 무관해서 상관없음)."""
        board = Board()
        place_all(board, [(3, 0, WHITE), (3, 1, WHITE), (3, 2, WHITE)])
        place_all(board, [(0, 3, WHITE), (1, 3, WHITE), (2, 3, WHITE)])
        # (3,4)에 흑을 두면 (1,1) 대각선으로 (4,5)(5,6)(6,7)(7,8)(8,9)와 이어져서
        # 6개 연속(장목) -> 흑 입장에서 금수인 자리.
        place_all(board, [(4, 5, BLACK), (5, 6, BLACK), (6, 7, BLACK), (7, 8, BLACK), (8, 9, BLACK)])

        moves = solve_unique_vcf(board, WHITE, max_attacker_moves=2)
        self.assertEqual(
            moves,
            [
                {"player": WHITE, "pos": (3, 3)},
                {"player": BLACK, "pos": (4, 3)},
                {"player": WHITE, "pos": (3, 4)},
            ],
        )

    def test_single_block_skipped_when_the_only_block_is_forbidden_for_black(self):
        """input: 백이 사(완성 자리 하나뿐, (10,4))를 만드는데, 그 자리가 흑에게는
        (세로로 이미 흑 5개가 이어져 있어서) 장목이 되는 금수 자리라 흑이 합법하게
        못 막음. output: 공격 측이 사실상 이기는 상황이지만 "수비 한 수 + 마무리
        한 수"로 표현 가능한 수순이 없어서(보드에 아직 5개가 안 보이는 상태라
        '풀었다'로 잘못 표시될 수 있음) 이 경로는 퍼즐로 안 쓰고 버림 -> None."""
        board = Board()
        place_all(board, [(10, 0, WHITE), (10, 1, WHITE), (10, 2, WHITE)])
        place_all(board, [(5, 4, BLACK), (6, 4, BLACK), (7, 4, BLACK), (8, 4, BLACK), (9, 4, BLACK)])

        self.assertIsNone(solve_unique_vcf(board, WHITE, max_attacker_moves=2))


class TestAttackerMoveCount(unittest.TestCase):
    def test_counts_only_the_given_player_moves(self):
        """input: [흑, 백, 흑] 수순에서 player=BLACK -> output: 2 (백 수는 안 셈)."""
        moves = [
            {"player": BLACK, "pos": (0, 0)},
            {"player": WHITE, "pos": (0, 1)},
            {"player": BLACK, "pos": (0, 2)},
        ]
        self.assertEqual(attacker_move_count(moves, BLACK), 2)

    def test_empty_move_list_returns_zero(self):
        """input: 빈 리스트 -> output: 0."""
        self.assertEqual(attacker_move_count([], BLACK), 0)


if __name__ == "__main__":
    unittest.main()
