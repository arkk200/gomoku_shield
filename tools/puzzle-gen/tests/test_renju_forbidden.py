"""renju_forbidden.py 각 함수의 input/output 문서화 겸 테스트.

실행: tools/puzzle-gen 디렉토리에서 `python3 -m unittest discover -s tests`
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gomoku import Board, BLACK, WHITE
from renju_forbidden import is_forbidden_for_black


def place_all(board, stones):
    """테스트 셋업용. stones: [(r, c, player), ...] 전부 놓음."""
    for r, c, player in stones:
        board.place(r, c, player)


class TestOverline(unittest.TestCase):
    def test_six_in_a_row_is_forbidden(self):
        """input: 흑 5개(c1~c5) 연속 + 마지막 수로 c6에 둬서 6개 완성
        -> output: 장목이라 금수(True)."""
        board = Board()
        place_all(board, [(3, c, BLACK) for c in range(1, 6)])
        board.place(3, 6, BLACK)
        self.assertTrue(is_forbidden_for_black(board, 3, 6))

    def test_exactly_five_is_not_forbidden_even_with_stone_further_out(self):
        """input: 흑 4개(c2~c5) + 마지막 수로 c1에 둬서 '정확히 5개' 완성,
        c6는 비어 있음(장목 아님) -> output: 이기는 수라 금수 아님(False)."""
        board = Board()
        place_all(board, [(3, c, BLACK) for c in range(2, 6)])
        board.place(3, 1, BLACK)
        self.assertFalse(is_forbidden_for_black(board, 3, 1))

    def test_winning_five_overrides_overline_in_another_direction(self):
        """input: 가로로는 장목(6개)이 되지만, 세로 방향으로 별도로 정확히 5개를
        동시에 완성하는 수 -> output: 이기는 수가 있으면 항상 우선이라 금수 아님."""
        board = Board()
        # 가로: (5,1)~(5,5) 흑 5개 깔아두고 (5,6)에 두면 가로로 6개(장목).
        place_all(board, [(5, c, BLACK) for c in range(1, 6)])
        # 세로: (5,6)을 지나는 세로줄에 흑 4개를 미리 깔아서, (5,6)을 두면
        # 세로로 정확히 5개가 완성되게 함.
        place_all(board, [(1, 6, BLACK), (2, 6, BLACK), (3, 6, BLACK), (4, 6, BLACK)])
        board.place(5, 6, BLACK)
        self.assertFalse(is_forbidden_for_black(board, 5, 6))


class TestDoubleFour(unittest.TestCase):
    def test_single_four_is_not_forbidden(self):
        """input: 왼쪽은 보드 끝(c0)이라 막혀있는 흑 3개(c0~c2) + 마지막 수로
        c3에 둬서 완성 자리가 c4 하나뿐인 닫힌 사 -> output: 사사 아님(False)."""
        board = Board()
        place_all(board, [(3, 0, BLACK), (3, 1, BLACK), (3, 2, BLACK)])
        board.place(3, 3, BLACK)
        self.assertFalse(is_forbidden_for_black(board, 3, 3))

    def test_two_fours_from_one_move_is_forbidden(self):
        """input: 가로/세로 각각 보드 끝으로 막힌(완성 자리가 하나씩뿐인) 닫힌 사
        두 개가 교차점 하나에서 동시에 생기는 마지막 수 -> output: 사사라 금수
        (True)."""
        board = Board()
        # 가로: (3,0)(3,1)(3,2) 흑 + (3,3) -> 완성 자리 (3,4) 하나(왼쪽은 c-1 없어서 막힘).
        place_all(board, [(3, 0, BLACK), (3, 1, BLACK), (3, 2, BLACK)])
        # 세로: (0,3)(1,3)(2,3) 흑 + (3,3) -> 완성 자리 (4,3) 하나(위쪽은 r-1 없어서 막힘).
        place_all(board, [(0, 3, BLACK), (1, 3, BLACK), (2, 3, BLACK)])
        board.place(3, 3, BLACK)
        self.assertTrue(is_forbidden_for_black(board, 3, 3))


class TestDoubleThree(unittest.TestCase):
    def test_single_open_three_is_not_forbidden(self):
        """input: 양쪽 다 열린 흑 3개 연속(c2~c4, c1/c5 빈칸) -> output: 삼삼 아님
        (열린 삼이 하나뿐)."""
        board = Board()
        place_all(board, [(5, 2, BLACK), (5, 3, BLACK)])
        board.place(5, 4, BLACK)
        self.assertFalse(is_forbidden_for_black(board, 5, 4))

    def test_closed_three_is_not_live(self):
        """input: 한쪽이 상대 돌로 막힌 흑 3개 연속(c1이 백) -> output: 그쪽 방향은
        '열린 사'가 될 수 없어서 열린 삼이 아님 -> 삼삼 아님(False)."""
        board = Board()
        board.place(5, 1, WHITE)
        place_all(board, [(5, 2, BLACK), (5, 3, BLACK)])
        board.place(5, 4, BLACK)
        # c5 방향은 열려있지만 c1 방향이 막혀 있어서, c5에 하나 더 둬도
        # 한쪽(c1)이 막힌 사(닫힌 사)만 됨 -> 열린 사 아님 -> 열린 삼 아님.
        self.assertFalse(is_forbidden_for_black(board, 5, 4))

    def test_two_open_threes_from_one_move_is_forbidden(self):
        """input: 가로/세로 두 방향 각각 열린 삼이 동시에 생기는 교차점에 마지막 수
        -> output: 삼삼이라 금수(True)."""
        board = Board()
        # 가로 열린 삼: (5,3)(5,4) 흑, (5,2)(5,5) 빈칸, 마지막 수 (5,5)... 대신
        # 교차점을 하나로 맞추기 위해 (7,7)을 마지막 수로 삼고 가로/세로 둘 다
        # 그 자리를 지나는 열린 삼이 되게 미리 깔아둠.
        place_all(board, [(7, 6, BLACK), (7, 5, BLACK)])  # 가로: (7,5)(7,6)[새 (7,7)]
        place_all(board, [(6, 7, BLACK), (5, 7, BLACK)])  # 세로: (5,7)(6,7)[새 (7,7)]
        board.place(7, 7, BLACK)
        self.assertTrue(is_forbidden_for_black(board, 7, 7))

    def test_broken_three_is_live(self):
        """input: 가로로 끊긴 삼(B B _ B — (5,2)(5,3) 흑, (5,4) 빈칸, 마지막 수
        (5,5))도 한 수(gap인 (5,4))로 열린 사가 되니 열린 삼으로 쳐야 함. 세로로도
        평범한 열린 삼(마지막 수가 공유하는 (3,5)(4,5))을 하나 더 만들어서,
        끊긴 삼이 열린 삼 집계에 제대로 들어가는지 삼삼 판정으로 확인.
        -> output: 두 방향 다 열린 삼이라 삼삼, 금수(True)."""
        board = Board()
        place_all(board, [(5, 2, BLACK), (5, 3, BLACK)])  # 가로 끊긴 삼의 앞부분
        place_all(board, [(3, 5, BLACK), (4, 5, BLACK)])  # 세로 평범한 삼의 앞부분
        board.place(5, 5, BLACK)  # 가로: B B _ B(끊긴 삼) / 세로: B B B(평범한 삼)
        self.assertTrue(is_forbidden_for_black(board, 5, 5))


if __name__ == "__main__":
    unittest.main()
