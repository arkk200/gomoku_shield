"""포지션(랜덤 셀프플레이 또는 RenjuNet 실제 대국)에서 '유일 정답' 오목 VCF
퍼즐 뱅크를 생성함.

개발용 도구일 뿐 앱에는 포함 안 됨 — 출력은 그냥 JSON 파일(보드+강제승리 수순)이고
앱이 이걸 static asset으로 번들함.

--source renjunet(기본값)는 RenjuNet 실제 대국 데이터베이스를 씀 — 사이드로드·
비상업·완전 온디바이스 배포라는 전제 위에서 그 라이선스 조건(비상업·오프라인
전용)과 맞는다고 판단함. 자세한 내용은 renjunet.py, CLAUDE.md 참고.
--source random은 외부 데이터 전혀 없이 자체 생성(비교/검증용으로 남겨둠).

사용법:
    python3 generate.py --source renjunet --target 15 --max-difficulty 3 --out output/puzzles.json
"""

import argparse
import json
import random

import renjunet
from gomoku import Board, BLACK, other
from vcf import solve_unique_vcf, attacker_move_count

MIN_STONES_BEFORE_CHECK = 6
MAX_STONES_PER_GAME = 40


def random_self_play_positions(rng, max_stones=MAX_STONES_PER_GAME):
    """랜덤 게임 한 판을 두면서 매 수마다 (board, player_to_move)를 yield함.
    중간에 누가 5개를 완성해버리면(= 게임 끝) 그 즉시 멈춤(그 마지막 수는 yield 안 됨).

    주의: 매번 같은 Board 객체를 계속 변형해서 yield함(복사 안 함) — 호출하는 쪽에서
    받은 상태를 바로바로 써야 하고, 나중에 비교하려고 모아두면 전부 최종 상태로 보임."""
    board = Board()
    player = BLACK
    for _ in range(max_stones):
        candidates = board.candidate_cells(margin=2)
        if not candidates:
            return
        r, c = rng.choice(candidates)
        board.place(r, c, player)
        if board.is_five(r, c, player):
            return  # 게임 끝난 상태라 퍼즐로 못 씀
        player = other(player)
        yield board, player


def board_signature(board):
    return tuple(tuple(row) for row in board.grid)


def extract_puzzle(board, player, max_difficulty):
    """탐색 깊이를 1부터 늘려가면서 유일한 강제승리 수순이 나올 때까지 시도함(안 나오면 포기)."""
    for depth in range(1, max_difficulty + 1):
        moves = solve_unique_vcf(board, player, depth)
        if moves is not None:
            return moves, attacker_move_count(moves, player)
    return None, None


def to_puzzle_record(puzzle_id, board, player, moves, difficulty):
    return {
        "id": puzzle_id,
        "size": 15,
        "toMove": "black" if player == BLACK else "white",
        "stones": [
            {"r": r, "c": c, "player": "black" if board.grid[r][c] == BLACK else "white"}
            for (r, c) in board.occupied_cells()
        ],
        "solution": [
            {"player": "black" if m["player"] == BLACK else "white", "r": m["pos"][0], "c": m["pos"][1]}
            for m in moves
        ],
        "difficulty": difficulty,
    }


def game_position_streams(args, rng):
    """source에 따라 "게임 한 판어치 포지션 스트림"을 하나씩 내놓는 제너레이터.
    random: 끝없이 새 랜덤 셀프플레이 게임을 만듦.
    renjunet: 실제 대국 데이터베이스를 한 번 받아서 섞은 뒤, 있는 만큼 순서대로 재생."""
    if args.source == "random":
        while True:
            yield random_self_play_positions(rng)

    renjunet.download_database(args.renjunet_xml)
    move_lists = renjunet.load_move_lists(args.renjunet_xml)
    rng.shuffle(move_lists)  # 항상 같은(파일 앞쪽) 대국부터 쓰지 않도록
    for moves in move_lists:
        yield renjunet.replay_positions(moves)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["renjunet", "random"], default="renjunet",
                     help="포지션 소스 — renjunet(실제 대국, 기본값) 또는 random(자체 생성, 비교용)")
    ap.add_argument("--renjunet-xml", default="renjunet_cache/games.xml",
                     help="RenjuNet XML 캐시 경로(없으면 자동으로 받음)")
    ap.add_argument("--target", type=int, default=15, help="난이도별로 모을 퍼즐 개수")
    ap.add_argument("--max-difficulty", type=int, default=3, help="탐색할 최대 난이도(공격 측 수 개수)")
    ap.add_argument("--max-games", type=int, default=2000, help="목표 못 채우면 포기할 상한 게임 수")
    ap.add_argument("--seed", type=int, default=42, help="재현용 랜덤 시드")
    ap.add_argument("--out", default="output/puzzles.json", help="출력 JSON 경로")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    buckets = {d: [] for d in range(1, args.max_difficulty + 1)}
    seen_signatures = set()
    puzzle_id = 1
    games = 0

    def total_collected():
        return sum(len(v) for v in buckets.values())

    def target_total():
        return args.target * args.max_difficulty

    for position_stream in game_position_streams(args, rng):
        if games >= args.max_games or total_collected() >= target_total():
            break
        games += 1
        for board, player in position_stream:
            if len(board.occupied_cells()) < MIN_STONES_BEFORE_CHECK:
                continue
            if all(len(buckets[d]) >= args.target for d in buckets):
                break
            sig = board_signature(board)
            if sig in seen_signatures:
                continue
            moves, difficulty = extract_puzzle(board, player, args.max_difficulty)
            # 더블 포로 끝나는 경우 탐색 깊이는 안 늘어도 공격 측 수는 하나 더 붙음 ->
            # 실제 난이도가 탐색 깊이보다 커질 수 있음. 지금 목표로 두는 버킷에만 담음.
            if moves is None or difficulty not in buckets or len(buckets[difficulty]) >= args.target:
                continue
            seen_signatures.add(sig)
            buckets[difficulty].append(to_puzzle_record(puzzle_id, board, player, moves, difficulty))
            puzzle_id += 1
            break  # 게임당 퍼즐 하나만 — 같은 게임 연속 스냅샷으로 비슷한 판만 쌓이는 걸 방지

    puzzles = [p for d in sorted(buckets) for p in buckets[d]]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"puzzles": puzzles}, f, ensure_ascii=False, indent=2)

    print(f"source: {args.source}")
    print(f"games played: {games}")
    for d in sorted(buckets):
        print(f"difficulty {d}: {len(buckets[d])}/{args.target}")
    print(f"total: {len(puzzles)} -> {args.out}")


if __name__ == "__main__":
    main()
