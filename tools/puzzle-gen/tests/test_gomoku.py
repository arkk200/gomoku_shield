"""gomoku.py 각 함수의 input/output 문서화 겸 테스트.

실행: tools/puzzle-gen 디렉토리에서 `python3 -m unittest discover -s tests`
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gomoku import Board, BLACK, WHITE, EMPTY, SIZE, other


class TestOther(unittest.TestCase):
    def test_black_input_returns_white(self):
        """input: BLACK -> output: WHITE"""
        self.assertEqual(other(BLACK), WHITE)

    def test_white_input_returns_black(self):
        """input: WHITE -> output: BLACK"""
        self.assertEqual(other(WHITE), BLACK)


class TestBoardBasics(unittest.TestCase):
    def test_in_bounds_accepts_corners_rejects_outside(self):
        """input: (r, c) 좌표 -> output: 보드(0~14) 안이면 True, 벗어나면 False."""
        board = Board()
        self.assertTrue(board.in_bounds(0, 0))
        self.assertTrue(board.in_bounds(SIZE - 1, SIZE - 1))
        self.assertFalse(board.in_bounds(-1, 0))
        self.assertFalse(board.in_bounds(0, SIZE))

    def test_empty_cells_on_fresh_board_returns_every_cell(self):
        """input: 돌 하나도 없는 보드 -> output: SIZE*SIZE개 빈 칸 전부."""
        board = Board()
        self.assertEqual(len(board.empty_cells()), SIZE * SIZE)

    def test_place_then_undo_round_trips_to_empty(self):
        """input: place(r, c, player) 후 undo(r, c) -> output: 다시 EMPTY."""
        board = Board()
        board.place(3, 4, BLACK)
        self.assertEqual(board.grid[3][4], BLACK)
        board.undo(3, 4)
        self.assertEqual(board.grid[3][4], EMPTY)

    def test_occupied_cells_matches_placed_stones(self):
        """input: 두 점 place -> output: occupied_cells()가 그 두 점만 반환(순서 무관)."""
        board = Board()
        board.place(1, 1, BLACK)
        board.place(2, 2, WHITE)
        self.assertEqual(set(board.occupied_cells()), {(1, 1), (2, 2)})

    def test_clone_grid_is_independent_copy(self):
        """input: clone_grid() 결과를 수정 -> output: 원본 board.grid는 영향 없음."""
        board = Board()
        board.place(0, 0, BLACK)
        clone = board.clone_grid()
        clone[0][0] = WHITE
        self.assertEqual(board.grid[0][0], BLACK)


class TestIsFive(unittest.TestCase):
    def test_four_in_a_row_is_not_five(self):
        """input: 가로로 4개 연속 -> output: False (아직 5개 아님)."""
        board = Board()
        for c in range(4):
            board.place(0, c, BLACK)
        self.assertFalse(board.is_five(0, 3, BLACK))

    def test_five_in_a_row_horizontal_is_true(self):
        """input: 가로로 5개 연속 -> output: True."""
        board = Board()
        for c in range(5):
            board.place(0, c, BLACK)
        self.assertTrue(board.is_five(0, 4, BLACK))

    def test_six_in_a_row_overlength_is_still_true(self):
        """input: 가로로 6개 연속(5개보다 많음) -> output: True (5개 이상이면 승리)."""
        board = Board()
        for c in range(6):
            board.place(0, c, BLACK)
        self.assertTrue(board.is_five(0, 5, BLACK))

    def test_diagonal_five_is_true(self):
        """input: 대각선으로 5개 연속 -> output: True (가로/세로뿐 아니라 대각선도 체크함)."""
        board = Board()
        for i in range(5):
            board.place(i, i, BLACK)
        self.assertTrue(board.is_five(4, 4, BLACK))

    def test_five_in_a_row_of_other_color_does_not_count(self):
        """input: WHITE 5개 연속인 자리를 BLACK 기준으로 체크 -> output: False."""
        board = Board()
        for c in range(5):
            board.place(0, c, WHITE)
        self.assertFalse(board.is_five(0, 4, BLACK))


class TestCompletionCells(unittest.TestCase):
    def test_open_four_returns_both_ends(self):
        """input: 양쪽 다 열린 4개 연속(c3~c6) -> output: 양 끝(c2, c7) 둘 다 반환
        (= 더블 포, 상대가 둘 다 못 막음)."""
        board = Board()
        for c in range(3, 7):
            board.place(0, c, BLACK)
        self.assertEqual(board.completion_cells(0, 6, BLACK), {(0, 2), (0, 7)})

    def test_one_end_blocked_returns_single_cell(self):
        """input: 한쪽 끝이 상대 돌로 막힌 4개 연속 -> output: 열린 쪽 끝 자리 하나만 반환."""
        board = Board()
        board.place(0, 2, WHITE)  # 왼쪽 끝 막음
        for c in range(3, 7):
            board.place(0, c, BLACK)
        self.assertEqual(board.completion_cells(0, 6, BLACK), {(0, 7)})

    def test_both_ends_blocked_returns_empty_set(self):
        """input: 양쪽 다 상대 돌로 막힌 4개 연속 -> output: 빈 집합(완성 불가능)."""
        board = Board()
        board.place(0, 2, WHITE)
        board.place(0, 7, WHITE)
        for c in range(3, 7):
            board.place(0, c, BLACK)
        self.assertEqual(board.completion_cells(0, 6, BLACK), set())

    def test_three_in_a_row_returns_empty_set(self):
        """input: 3개 연속(아직 4개 아님) -> output: 빈 집합 (완성 자리 자체가 없음)."""
        board = Board()
        for c in range(3, 6):
            board.place(0, c, BLACK)
        self.assertEqual(board.completion_cells(0, 5, BLACK), set())


class TestCandidateCells(unittest.TestCase):
    def test_empty_board_returns_center_cell_only(self):
        """input: 빈 보드 -> output: 정중앙 한 칸만 ([(7, 7)])."""
        board = Board()
        self.assertEqual(board.candidate_cells(margin=2), [(SIZE // 2, SIZE // 2)])

    def test_margin_one_returns_surrounding_ring_only(self):
        """input: (7, 7)에 돌 하나, margin=1 -> output: 바로 주변 8칸만(멀리 떨어진 칸 제외)."""
        board = Board()
        board.place(7, 7, BLACK)
        cells = board.candidate_cells(margin=1)
        self.assertEqual(len(cells), 8)
        self.assertNotIn((7, 7), cells)  # 이미 돌이 있는 칸은 후보가 아님
        self.assertNotIn((5, 7), cells)  # margin=1 범위 밖


if __name__ == "__main__":
    unittest.main()
