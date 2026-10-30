"""RenjuNet(renju.net) 실제 대국 데이터베이스 다운로드/파싱.

라이선스(파일 자체에 박혀있는 원문 그대로):
  "It is allowed to use this database for non-commercial purposes in the
  forms of OFFLINE databases only. It is forbidden to use any contents of
  this database or its modifications in any website or ONLINE system."

오목 실드는 사이드로드(비상업, 완전 온디바이스) 배포라 위 조건과 맞는다고
판단해서 씀 — CLAUDE.md "퍼즐 뱅크 생성 방식" 참고.

대국은 렌주 공식 규칙(흑 금수 있음)으로 뒀고, 여기서 뽑는 건 포지션(돌 배치)과
좌표 변환뿐 — 금수 판정 자체는 vcf.py가 renju_forbidden.py를 통해 강제승리
수순을 다시 계산할 때 적용함(흑이 렌주 룰로는 둘 수 없는 수를 강제승리 수순에
섞어 쓰는 실제 버그가 있었음, 유저가 퍼즐 #86에서 제보 — CLAUDE.md 참고).
그래서 재생된 포지션 자체는 렌주 룰 기준으로 합법하지만, 거기서 계산하는
강제승리 수순은 gomoku.py(순수 기하 규칙)가 아니라 renju_forbidden.py가 얹힌
vcf.py 쪽에서 흑 금수를 따로 지킴.
"""

import gzip
import re
import urllib.request

DATABASE_URL = "https://www.renju.net/game/download/"
MOVE_RE = re.compile(r"<move>(.*?)</move>", re.DOTALL)
COORD_RE = re.compile(r"^([a-o])(\d{1,2})$")


def download_database(cache_path):
    """cache_path에 XML이 이미 있으면 그대로 쓰고, 없으면 내려받아서 저장함.
    input: 캐시 파일 경로. output: 없음(파일을 그 경로에 씀)."""
    import os

    if os.path.exists(cache_path):
        return
    req = urllib.request.Request(DATABASE_URL, headers={"User-Agent": "gomoku-shield-puzzle-gen/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    xml_bytes = gzip.decompress(raw)
    with open(cache_path, "wb") as f:
        f.write(xml_bytes)


def parse_coord(token):
    """"h8" 같은 표기를 (r, c) 0-indexed 튜플로 변환. "h8" -> (7, 7)(중앙).
    형식이 안 맞으면 None 반환(깨진 데이터 방어용)."""
    m = COORD_RE.match(token)
    if not m:
        return None
    letter, number = m.group(1), m.group(2)
    c = ord(letter) - ord("a")
    r = int(number) - 1
    if not (0 <= r < 15 and 0 <= c < 15):
        return None
    return (r, c)


def load_move_lists(xml_path):
    """XML 파일에서 모든 대국의 수순만 뽑아냄 — 메타데이터(선수/대회 등)는 안 봄,
    <move> 안의 좌표 문자열만 정규식으로 긁어서 (r, c) 리스트로 변환.
    input: xml 파일 경로. output: [[(r, c), ...], ...] (대국별 수순 리스트)."""
    with open(xml_path, "r", encoding="utf-8") as f:
        text = f.read()

    move_lists = []
    for raw in MOVE_RE.findall(text):
        coords = [parse_coord(tok) for tok in raw.split()]
        if any(c is None for c in coords):
            continue  # 깨진/예외적인 좌표가 섞인 대국은 통째로 건너뜀
        if len(coords) < 2:
            continue
        move_lists.append(coords)
    return move_lists


def replay_positions(moves):
    """random_self_play_positions와 동일한 인터페이스: 실제 대국 수순(moves)을
    처음부터 재생하면서 매 수마다 (board, player_to_move)를 yield함.
    흑이 먼저 두고 번갈아 둠(RenjuNet 표기 관례). 중간에 5개가 완성되면(=승부 결정)
    그 즉시 멈춤(그 마지막 수는 yield 안 됨) — random_self_play_positions과 동일.

    주의: 매번 같은 Board 객체를 변형해서 yield함(복사 안 함)."""
    from gomoku import Board, BLACK, EMPTY, other

    board = Board()
    player = BLACK
    for (r, c) in moves:
        if board.grid[r][c] != EMPTY:
            return  # 같은 자리에 중복 착수 — 데이터 이상, 이 대국은 중단
        board.place(r, c, player)
        if board.is_five(r, c, player):
            return
        player = other(player)
        yield board, player
