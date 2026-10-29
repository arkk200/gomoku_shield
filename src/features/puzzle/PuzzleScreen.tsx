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
  const lastMove = movesPlayed > 0 ? puzzle.solution[movesPlayed - 1] : null;

  // 진행 상황 표시용 — 전체 수가 아니라 "내가(공격 측) 둬야 하는 수" 기준으로 셈.
  // (상대 강제수까지 같이 세면 유저 입장에서 분모가 왜 그런지 헷갈림)
  const attackerMovesTotal = useMemo(
    () => puzzle.solution.filter((m) => m.player === puzzle.toMove).length,
    [puzzle],
  );
  const attackerMovesPlayed = useMemo(
    () => puzzle.solution.slice(0, movesPlayed).filter((m) => m.player === puzzle.toMove).length,
    [puzzle, movesPlayed],
  );

  // 공격 측이 아닌 수(강제로 막는 상대 수)는 유저가 안 두고 자동으로 재생됨.
  // 이 수가 재생되길 기다리는 동안인지(=defenderPending)를 따로 들고 있다가
  // 화면에 "상대가 막는 중" 표시를 띄움 — 안 그러면 유저가 탭했는데 갑자기
  // 반대색 돌이 생기는 걸 보고 "내 탭이 잘못 처리됐다"고 오해함(실제 QA에서
  // 나온 피드백).
  const defenderPending = !solved && puzzle.solution[movesPlayed].player !== puzzle.toMove;

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
        {puzzle.toMove === 'black' ? '흑' : '백'}이 공격 — 난이도 {puzzle.difficulty} ·{' '}
        {attackerMovesPlayed}/{attackerMovesTotal}수
      </Text>
      <Text style={styles.turnIndicator}>
        {solved ? ' ' : defenderPending ? '상대가 막는 중...' : '내 차례 — 이기는 수를 두세요'}
      </Text>
      <PuzzleBoard
        size={puzzle.size}
        grid={grid}
        wrongCell={wrongCell}
        lastMove={lastMove}
        onCellPress={handleCellPress}
      />
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
  turnIndicator: {
    fontSize: 13,
    fontWeight: '600',
    color: '#2d7cf0',
    minHeight: 18,
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
