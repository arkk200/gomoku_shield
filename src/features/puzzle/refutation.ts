// 오답 피드백용 — tools/puzzle-gen/gomoku.py의 completion_cells 로직을 TS로 그대로 포팅.
// 전체 강제승리 수순을 다시 탐색하는 게 아니라(그건 재귀라 비싸고, 유저가 누를 수
// 있는 빈 칸 전부에 대해 미리 계산해두기도 비현실적임), "방금 놓은 수가 사삼
// (4개 연속 + 빈칸 1개)을 만드는지"만 그 자리에서 즉시 계산하는 가벼운 체크임.
// 막을 자리가 정확히 하나면 그 자리를 "반박 수"로 보여줌 — 바둑 사활 문제 앱들이
// 오답에 상대 반박수를 1수만 보여주는 것과 같은 패턴.
import type { Grid } from './PuzzleBoard';
import type { StoneColor } from './types';

const DIRECTIONS: ReadonlyArray<readonly [number, number]> = [
  [1, 0],
  [0, 1],
  [1, 1],
  [1, -1],
];

function inBounds(size: number, r: number, c: number): boolean {
  return r >= 0 && r < size && c >= 0 && c < size;
}

/**
 * grid에 (r, c)에 player가 방금 뒀다고 가정했을 때, 그 수를 지나는 5칸 구간 중
 * player 돌 4개 + 빈칸 1개인 패턴이 정확히 하나면 그 빈칸(= 상대가 막아야 하는
 * 자리)을 반환. 위협이 없으면(0개) null, 더블 포(2개 이상 — 실제 오목 실드
 * 퍼즐 뱅크는 cook 검증을 거쳐서 유저의 오답이 더블 포가 되는 경우가 없어야
 * 정상이지만, 방어적으로) 역시 null.
 */
export function findRefutationCell(
  grid: Grid,
  size: number,
  r: number,
  c: number,
  player: StoneColor,
): { r: number; c: number } | null {
  const seen = new Set<string>();
  const completions: { r: number; c: number }[] = [];

  for (const [dr, dc] of DIRECTIONS) {
    for (let offset = -4; offset <= 0; offset++) {
      const window: { r: number; c: number }[] = [];
      let ok = true;
      for (let i = 0; i < 5; i++) {
        const rr = r + (offset + i) * dr;
        const cc = c + (offset + i) * dc;
        if (!inBounds(size, rr, cc)) {
          ok = false;
          break;
        }
        window.push({ r: rr, c: cc });
      }
      if (!ok) continue;

      let playerCount = 0;
      let emptyCell: { r: number; c: number } | null = null;
      let emptyCount = 0;
      for (const cell of window) {
        const value = cell.r === r && cell.c === c ? player : grid[cell.r][cell.c];
        if (value === player) playerCount++;
        else if (value === null) {
          emptyCount++;
          emptyCell = cell;
        }
      }

      if (playerCount === 4 && emptyCount === 1 && emptyCell) {
        const key = `${emptyCell.r},${emptyCell.c}`;
        if (!seen.has(key)) {
          seen.add(key);
          completions.push(emptyCell);
        }
      }
    }
  }

  return completions.length === 1 ? completions[0] : null;
}
