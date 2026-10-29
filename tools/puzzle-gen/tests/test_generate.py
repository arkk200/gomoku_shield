"""generate.py 각 함수의 input/output 문서화 겸 테스트.

실행: tools/puzzle-gen 디렉토리에서 `python3 -m unittest discover -s tests`

주의: `main()`은 argparse + 파일 I/O 연결부라 "핵심 로직"이 아니라서(코드 컨벤션 7번)
단위 테스트 대상에서 뺌 — 실제 동작 확인은 README의 사용법대로 직접 실행해서 함.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gomoku import Board, BLACK, WHITE
from generate import (
    random_self_play_positions,
    board_signature,
    extract_puzzle,
    to_puzzle_record,
)


class ScriptedRng:
    """테스트에서 랜덤 대신 정해진 수순을 강제로 재생시키기 위한 가짜 rng.
    `.choice(candidates)`를 호출해도 candidates 내용과 무관하게 미리 정해둔
    다음 좌표를 순서대로 돌려줌."""

    def __init__(self, moves):
        self._moves = list(moves)

    def choice(self, _candidates):
        return self._moves.pop(0)


class TestRandomSelfPlayPositions(unittest.TestCase):
    def test_each_yield_adds_exactly_one_stone(self):
        """input: 시드 고정 rng, max_stones=5 -> output: 5번 yield,
        매번 보드 돌 개수가 1,2,3,4,5로 정확히 하나씩 늘어남."""
        import random

        rng = random.Random(1)
        counts = [len(board.occupied_cells()) for board, _ in random_self_play_positions(rng, max_stones=5)]
        self.assertEqual(counts, [1, 2, 3, 4, 5])

    def test_player_to_move_alternates_starting_with_white(self):
        """input: 흑이 먼저 둠 -> output: 매 yield마다 반환되는 '다음 차례'가
        백,흑,백,흑... 순으로 번갈아 나옴 (흑이 막 뒀으니 다음은 백부터)."""
        import random

        rng = random.Random(1)
        players = [player for _, player in random_self_play_positions(rng, max_stones=4)]
        self.assertEqual(players, [WHITE, BLACK, WHITE, BLACK])

    def test_stops_without_yielding_the_five_completing_move(self):
        """input: 9수째에 흑이 가로 5개를 완성하도록 강제한 스크립트 수순
        -> output: 8번만 yield됨(5개를 완성시킨 마지막 수는 yield 안 되고 바로 멈춤).

        주의: yield되는 board는 매번 복사본이 아니라 같은 객체를 계속 변형한 것 —
        그래서 돌 개수는 반드시 반복문을 '도는 동안' 바로 확인해야 함
        (list()로 다 모아놓고 나중에 보면 전부 최종 상태로 보임)."""
        scripted = ScriptedRng([
            (7, 7), (0, 0), (7, 8), (0, 1), (7, 9), (0, 2), (7, 10), (0, 3), (7, 11),
        ])
        stone_counts = []
        last_player = None
        for board, player in random_self_play_positions(scripted, max_stones=20):
            stone_counts.append(len(board.occupied_cells()))
            last_player = player
        self.assertEqual(stone_counts, [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(last_player, BLACK)  # 8번째 수는 백이 뒀으니 다음은 흑


class TestBoardSignature(unittest.TestCase):
    def test_same_board_state_gives_equal_signature(self):
        """input: 똑같은 자리에 똑같이 둔 두 보드 -> output: 같은 signature."""
        b1 = Board()
        b2 = Board()
        b1.place(3, 3, BLACK)
        b2.place(3, 3, BLACK)
        self.assertEqual(board_signature(b1), board_signature(b2))

    def test_different_board_state_gives_different_signature(self):
        """input: 돌 하나 위치가 다른 두 보드 -> output: 다른 signature."""
        b1 = Board()
        b2 = Board()
        b1.place(3, 3, BLACK)
        b2.place(3, 4, BLACK)
        self.assertNotEqual(board_signature(b1), board_signature(b2))

    def test_signature_is_hashable(self):
        """input: signature 결과 -> output: set에 넣을 수 있음(중복 보드 체크용 용도)."""
        board = Board()
        board.place(0, 0, BLACK)
        seen = {board_signature(board)}
        self.assertIn(board_signature(board), seen)


class TestExtractPuzzle(unittest.TestCase):
    def test_finds_difficulty_one_puzzle(self):
        """input: 가로 4개 중 가운데 하나 빈 보드, max_difficulty=2
        -> output: (수순, 1) — 난이도 1에서 바로 찾아짐."""
        board = Board()
        for c in (1, 2, 3, 5):
            board.place(3, c, BLACK)
        moves, difficulty = extract_puzzle(board, BLACK, max_difficulty=2)
        self.assertEqual(difficulty, 1)
        self.assertEqual(moves, [{"player": BLACK, "pos": (3, 4)}])

    def test_empty_board_returns_none_none(self):
        """input: 빈 보드 -> output: (None, None) — 강제승리 자체가 없음."""
        board = Board()
        moves, difficulty = extract_puzzle(board, BLACK, max_difficulty=2)
        self.assertIsNone(moves)
        self.assertIsNone(difficulty)


class TestToPuzzleRecord(unittest.TestCase):
    def test_builds_expected_json_shape(self):
        """input: 돌 2개짜리 보드 + 수순 1개 -> output: 정해진 키(id/size/toMove/
        stones/solution/difficulty)를 가진 dict, 색은 'black'/'white' 문자열로 변환됨."""
        board = Board()
        board.place(3, 3, BLACK)
        board.place(3, 4, WHITE)
        moves = [{"player": BLACK, "pos": (3, 5)}]

        record = to_puzzle_record(puzzle_id=42, board=board, player=BLACK, moves=moves, difficulty=1)

        self.assertEqual(record["id"], 42)
        self.assertEqual(record["size"], 15)
        self.assertEqual(record["toMove"], "black")
        self.assertEqual(record["difficulty"], 1)
        self.assertEqual(
            sorted((s["r"], s["c"], s["player"]) for s in record["stones"]),
            [(3, 3, "black"), (3, 4, "white")],
        )
        self.assertEqual(record["solution"], [{"player": "black", "r": 3, "c": 5}])


if __name__ == "__main__":
    unittest.main()
