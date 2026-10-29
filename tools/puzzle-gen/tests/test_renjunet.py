"""renjunet.py 각 함수의 input/output 문서화 겸 테스트.

실행: tools/puzzle-gen 디렉토리에서 `python3 -m unittest discover -s tests`

주의: `download_database`는 실제 네트워크 요청이라 단위 테스트에서 안 돌림
(코드 컨벤션 7번 — MVP 단계 핵심 로직만 테스트, I/O 연결부는 제외).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gomoku import BLACK, WHITE
from renjunet import parse_coord, load_move_lists, replay_positions


class TestParseCoord(unittest.TestCase):
    def test_center_h8_is_7_7(self):
        """input: "h8"(렌주 표기상 보드 정중앙) -> output: (7, 7) — 우리 보드의 중앙 인덱스와 일치."""
        self.assertEqual(parse_coord("h8"), (7, 7))

    def test_a1_is_top_left_0_0(self):
        """input: "a1" -> output: (0, 0)."""
        self.assertEqual(parse_coord("a1"), (0, 0))

    def test_o15_is_bottom_right_14_14(self):
        """input: "o15"(15번째 열, 15번째 행 — 보드 가장 끝) -> output: (14, 14)."""
        self.assertEqual(parse_coord("o15"), (14, 14))

    def test_letter_i_is_a_valid_column_not_skipped(self):
        """input: "i9" -> output: (8, 8). RenjuNet 표기는 체스식으로 i를 건너뛰지 않음."""
        self.assertEqual(parse_coord("i9"), (8, 8))

    def test_out_of_range_letter_returns_none(self):
        """input: "p1"(a~o 범위 밖 열) -> output: None."""
        self.assertIsNone(parse_coord("p1"))

    def test_malformed_token_returns_none(self):
        """input: 좌표 형식이 아닌 문자열 -> output: None."""
        self.assertIsNone(parse_coord("hello"))


class TestLoadMoveLists(unittest.TestCase):
    def test_parses_moves_and_skips_malformed_games(self):
        """input: <move> 태그 2개(하나는 정상, 하나는 깨진 좌표 포함)짜리 가짜 XML
        -> output: 정상인 대국 하나만 파싱돼서 (r, c) 리스트로 나옴."""
        xml_path = "tests/_fixture_sample.xml"
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write("<database><games>\n")
            f.write("<game id='1'><move>h8 i9 g7</move></game>\n")
            f.write("<game id='2'><move>h8 zz99</move></game>\n")  # 깨진 좌표
            f.write("</games></database>\n")
        try:
            result = load_move_lists(xml_path)
            self.assertEqual(result, [[(7, 7), (8, 8), (6, 6)]])
        finally:
            os.remove(xml_path)


class TestReplayPositions(unittest.TestCase):
    def test_yields_one_position_per_move_alternating_colors(self):
        """input: 수순 3개(흑,백,흑) -> output: 3번 yield, 다음 차례가 백,흑,백 순으로 번갈아 나옴."""
        moves = [(7, 7), (7, 8), (6, 6)]
        results = list(replay_positions(moves))
        self.assertEqual(len(results), 3)
        players = [player for _, player in results]
        self.assertEqual(players, [WHITE, BLACK, WHITE])

    def test_stops_on_duplicate_move_without_crashing(self):
        """input: 같은 자리에 두 번 두는 깨진 수순 -> output: 중복되기 전까지만 yield되고
        조용히 멈춤(예외 안 터짐) — 실제 데이터 이상에 대한 방어."""
        moves = [(7, 7), (7, 7)]  # 두 번째 수가 같은 자리
        results = list(replay_positions(moves))
        self.assertEqual(len(results), 1)

    def test_stops_without_yielding_the_five_completing_move(self):
        """input: 5번째 수(흑)에서 가로 5개가 완성되는 수순 -> output: 4번만 yield됨
        (random_self_play_positions과 동일한 규약: 완성시킨 마지막 수는 yield 안 됨)."""
        moves = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4)]
        results = list(replay_positions(moves))
        self.assertEqual(len(results), 8)


if __name__ == "__main__":
    unittest.main()
