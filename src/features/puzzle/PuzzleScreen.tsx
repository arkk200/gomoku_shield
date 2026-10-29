import { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import ShortsDetector from '../../../modules/shorts-detector/src/ShortsDetectorModule';
import { PuzzleBoard, type Grid } from './PuzzleBoard';
import { pickRandomPuzzle } from './puzzleBank';
import type { Puzzle } from './types';

const DEFENDER_MOVE_DELAY_MS = 500;
const WRONG_FLASH_MS = 400;

function buildGrid(size: number, puzzle: Puzzle, movesPlayed: number): Grid {
  const grid: Grid = Array.from({ length: size }, () => Array(size).fill(null));
  for (const s of puzzle.stones) {
    grid[s.r][s.c] = s.player;
  }
  for (let i = 0; i < movesPlayed; i++) {
    const m = puzzle.solution[i];
    grid[m.r][m.c] = m.player;
  }
  return grid;
}

interface PuzzleScreenProps {
  onDone: () => void;
}

export function PuzzleScreen({ onDone }: PuzzleScreenProps) {
  const [puzzle] = useState<Puzzle>(() => pickRandomPuzzle());
  const [movesPlayed, setMovesPlayed] = useState(0);
  const [wrongCell, setWrongCell] = useState<{ r: number; c: number } | null>(null);

  const solved = movesPlayed >= puzzle.solution.length;
  const grid = useMemo(() => buildGrid(puzzle.size, puzzle, movesPlayed), [puzzle, movesPlayed]);

  // 공격 측이 아닌 수(강제로 막는 상대 수)는 유저가 안 두고 자동으로 재생됨.
  useEffect(() => {
    if (solved) return;
    const next = puzzle.solution[movesPlayed];
    if (next.player === puzzle.toMove) return; // 공격 측 차례 -> 유저 입력 기다림
    const timer = setTimeout(() => setMovesPlayed((n) => n + 1), DEFENDER_MOVE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [movesPlayed, puzzle, solved]);

  function handleCellPress(r: number, c: number) {
    if (solved) return;
    const next = puzzle.solution[movesPlayed];
    if (next.player !== puzzle.toMove) return; // 지금은 상대(강제) 차례라 입력 무시

    if (next.r === r && next.c === c) {
      setMovesPlayed((n) => n + 1);
    } else {
      setWrongCell({ r, c });
      setTimeout(() => setWrongCell(null), WRONG_FLASH_MS);
    }
  }

  function handleConfirmDone() {
    ShortsDetector.markPuzzleSolved(ShortsDetector.getGraceMinutesSetting());
    ShortsDetector.moveToBack(); // 유튜브/인스타가 다시 보이게
    onDone(); // 다음에 앱 아이콘으로 직접 열면 홈(설정) 화면부터 보이게 상태 리셋
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>오목 퍼즐 #{puzzle.id}</Text>
      <Text style={styles.subtitle}>
        {puzzle.toMove === 'black' ? '흑' : '백'} 차례 — 난이도 {puzzle.difficulty}
      </Text>
      <PuzzleBoard size={puzzle.size} grid={grid} wrongCell={wrongCell} onCellPress={handleCellPress} />
      {solved && (
        <View style={styles.solvedPanel}>
          <Text style={styles.solvedText}>풀었다! 🎉</Text>
          <Pressable style={styles.confirmButton} onPress={handleConfirmDone}>
            <Text style={styles.confirmButtonText}>돌아가기</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
  },
  subtitle: {
    fontSize: 14,
    color: '#555',
  },
  solvedPanel: {
    marginTop: 16,
    alignItems: 'center',
    gap: 12,
  },
  solvedText: {
    fontSize: 18,
    fontWeight: '700',
  },
  confirmButton: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
