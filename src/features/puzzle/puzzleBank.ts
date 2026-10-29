import puzzlesData from './puzzles.json';
import type { Puzzle, PuzzleBank } from './types';

const bank = puzzlesData as PuzzleBank;

// 매번 다른 퍼즐 나오게 무작위로 하나 뽑음. 승패·사용 기록은 저장 안 하는
// 데이터 정책(CLAUDE.md)이라 "이전에 어떤 퍼즐 냈는지" 같은 상태도 안 둠.
export function pickRandomPuzzle(): Puzzle {
  const index = Math.floor(Math.random() * bank.puzzles.length);
  return bank.puzzles[index];
}
