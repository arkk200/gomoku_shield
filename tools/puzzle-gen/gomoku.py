"""최소 구현 프리스타일 오목 보드: 15x15, 5개 이상 연속이면 승리, 금수 규칙 없음."""

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
        플레이어 돌 4개 + 빈칸 1개인 패턴을 찾아서 그 빈칸을 모음."""
        cells = set()
        for dr, dc in DIRECTIONS:
            for offset in range(-4, 1):
                window = [(r + (offset + i) * dr, c + (offset + i) * dc) for i in range(5)]
                if not all(self.in_bounds(wr, wc) for wr, wc in window):
                    continue
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
