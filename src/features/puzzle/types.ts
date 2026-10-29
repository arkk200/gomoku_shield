// puzzle-gen이 뽑아내는 output/puzzles.json 스키마와 1:1로 맞춰둔 타입.
export type StoneColor = 'black' | 'white';

export interface Stone {
  r: number;
  c: number;
  player: StoneColor;
}

export interface SolutionMove {
  player: StoneColor;
  r: number;
  c: number;
}

export interface Puzzle {
  id: number;
  size: number;
  toMove: StoneColor;
  stones: Stone[];
  solution: SolutionMove[];
  difficulty: number;
}

export interface PuzzleBank {
  puzzles: Puzzle[];
}
