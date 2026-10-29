"""생성된 퍼즐을 눈으로 바로 확인하기 위한 도구. output/puzzles.json 같은 파일을
읽어서 각 퍼즐을 ASCII 보드로 렌더링함 — raw JSON 좌표만 보고는 판 모양을 가늠하기
어려워서 만듦.

사용법:
    python3 preview.py output/puzzles.json
    python3 preview.py output/puzzles.json --difficulty 2 --limit 5
"""

import argparse
import json


def render_board(puzzle):
    """퍼즐 하나를 ASCII 보드 문자열로 그림. 흑=B, 백=W, 빈칸=."""
    size = puzzle["size"]
    grid = [["." for _ in range(size)] for _ in range(size)]
    for s in puzzle["stones"]:
        grid[s["r"]][s["c"]] = "B" if s["player"] == "black" else "W"
    lines = [" ".join(row) for row in grid]
    header = f'--- id={puzzle["id"]} difficulty={puzzle["difficulty"]} toMove={puzzle["toMove"]} ---'
    solution = ", ".join(f'{m["player"]}({m["r"]},{m["c"]})' for m in puzzle["solution"])
    return "\n".join([header, *lines, f"solution: {solution}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("puzzles_json")
    ap.add_argument("--difficulty", type=int, default=None, help="이 난이도만 보기")
    ap.add_argument("--limit", type=int, default=None, help="최대 몇 개까지 보여줄지")
    args = ap.parse_args()

    with open(args.puzzles_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    puzzles = data["puzzles"]
    if args.difficulty is not None:
        puzzles = [p for p in puzzles if p["difficulty"] == args.difficulty]
    if args.limit is not None:
        puzzles = puzzles[: args.limit]

    for p in puzzles:
        print(render_board(p))
        print()


if __name__ == "__main__":
    main()
