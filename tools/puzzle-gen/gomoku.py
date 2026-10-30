"""최소 구현 프리스타일 오목 보드: 15x15, 5개 이상 연속이면 승리.

이 모듈 자체엔 흑/백 구분되는 규칙 제약이 없음(순수 기하 판정만) — 렌주 흑 금수
(장목/사사/삼삼)는 여기 안 넣고 renju_forbidden.py에 별도 레이어로 분리해뒀고,
vcf.py가 퍼즐 생성/검증에서 그 레이어를 얹어 씀. 즉 "오목 실드 전체"는 흑 금수를
지키지만, 이 Board 클래스 혼자서는 금수를 모름 — 의도된 설계(관심사 분리)."""

SIZE = 15
EMPTY, BLACK, WHITE = 0, 1, 2
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]


def other(player):
    return WHITE if player == BLACK else BLACK


class Board:
    def __init__(self):
        self.grid = [[EMPTY] * SIZE for _ in range(SIZE)]

    def in_bounds(self, r, c):
        return 0 <= r < SIZE and 0 <= c < SIZE

    def empty_cells(self):
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.grid[r][c] == EMPTY]

    def place(self, r, c, player):
        self.grid[r][c] = player

    def undo(self, r, c):
        self.grid[r][c] = EMPTY

    def is_five(self, r, c, player):
        """(r, c)에 `player`가 돌을 놓았을 때, 이 자리를 지나는 5개 이상 연속이 생기는지 확인."""
        for dr, dc in DIRECTIONS:
            count = 1
            rr, cc = r + dr, c + dc
            while self.in_bounds(rr, cc) and self.grid[rr][cc] == player:
                count += 1
                rr += dr
                cc += dc
            rr, cc = r - dr, c - dc
            while self.in_bounds(rr, cc) and self.grid[rr][cc] == player:
                count += 1
                rr -= dr
                cc -= dc
            if count >= 5:
                return True
        return False

    def completion_cells(self, r, c, player):
        """(r, c)에 `player`가 돌을 놓은 뒤, 거기 두면 5개가 완성되는 빈 자리들을 반환
        (= 상대가 막아야 하는 자리). (r, c)를 지나는 모든 5칸짜리 구간 중
        플레이어 돌 4개 + 빈칸 1개인 패턴을 찾아서 그 빈칸을 모음.

        성능 참고(렌주 금수 체크를 VCF 솔버 깊은 재귀에서 매 후보마다 돌게 되면서
        이 함수가 호출 빈도 1위 핫패스가 됨 — 프로파일링으로 확인): 윈도우 5칸을
        하나씩 in_bounds로 검사하는 대신, 직선 윈도우의 양 끝 두 칸만 in_bounds면
        (dr, dc가 -1/0/1이라 그 사이 칸들은 보드 안에 있는 게 보장됨) 안 보고
        넘어가도 됨 — in_bounds 호출 수를 5번에서 2번으로 줄임."""
        cells = set()
        for dr, dc in DIRECTIONS:
            for offset in range(-4, 1):
                start_r, start_c = r + offset * dr, c + offset * dc
                end_r, end_c = r + (offset + 4) * dr, c + (offset + 4) * dc
                if not (self.in_bounds(start_r, start_c) and self.in_bounds(end_r, end_c)):
                    continue
                window = [(r + (offset + i) * dr, c + (offset + i) * dc) for i in range(5)]
                values = [self.grid[wr][wc] for wr, wc in window]
                if values.count(player) == 4 and values.count(EMPTY) == 1:
                    idx = values.index(EMPTY)
                    cells.add(window[idx])
        return cells

    def clone_grid(self):
        return [row[:] for row in self.grid]

    def occupied_cells(self):
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if self.grid[r][c] != EMPTY]

    def candidate_cells(self, margin=2):
        """기존 돌 주변 `margin` 칸 이내의 빈 자리만 반환.
        매 수마다 15x15 전체를 뒤지면 너무 느려지니 탐색 범위를 돌 근처로 좁힘."""
        occupied = self.occupied_cells()
        if not occupied:
            mid = SIZE // 2
            return [(mid, mid)]
        cand = set()
        for (r, c) in occupied:
            for dr in range(-margin, margin + 1):
                for dc in range(-margin, margin + 1):
                    rr, cc = r + dr, c + dc
                    if self.in_bounds(rr, cc) and self.grid[rr][cc] == EMPTY:
                        cand.add((rr, cc))
        return sorted(cand)
