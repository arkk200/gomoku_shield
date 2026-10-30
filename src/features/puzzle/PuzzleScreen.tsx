import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import ShortsDetector from '../../../modules/shorts-detector/src/ShortsDetectorModule';
import { PuzzleBoard, type Grid, type MistakeStone } from './PuzzleBoard';
import { pickRandomPuzzle } from './puzzleBank';
import { findRefutationCell } from './refutation';
import type { Puzzle } from './types';

const DEFENDER_MOVE_DELAY_MS = 500;
const WRONG_FLASH_MS = 400;
const MISTAKE_SHOWN_MS = 550; // 오답 돌만 보여주는 시간
const MISTAKE_REFUTED_MS = 900; // 반박수까지 보여준 뒤 되돌리기까지 시간

// 오답이 위협(사삼)을 만들었을 때 — 상대 반박수까지 보여주는 상태.
// phase 'shown' -> (반박수 있으면) 'refuted' -> null(원상복구)로 흘러감.
interface Mistake {
  wrong: { r: number; c: number };
  refutation: { r: number; c: number } | null;
  phase: 'shown' | 'refuted';
}

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
  const [mistake, setMistake] = useState<Mistake | null>(null);

  const solved = movesPlayed >= puzzle.solution.length;
  const grid = useMemo(() => buildGrid(puzzle.size, puzzle, movesPlayed), [puzzle, movesPlayed]);
  // 마지막에 놓인 수(내 수든 상대 강제수든)에 링 하이라이트 — 상대가 탭 없이
  // 자동으로 둔 수를 유저가 "오류"로 오인하지 않게 하는 유일한 단서라서,
  // 텍스트는 다 빼도 이건 남겨둠.
  const lastMove = movesPlayed > 0 ? puzzle.solution[movesPlayed - 1] : null;

  useEffect(() => {
    if (solved) return;
    const next = puzzle.solution[movesPlayed];
    if (next.player === puzzle.toMove) return; // 공격 측 차례 -> 유저 입력 기다림
    const timer = setTimeout(() => setMovesPlayed((n) => n + 1), DEFENDER_MOVE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [movesPlayed, puzzle, solved]);

  // mistake 상태 진행: 오답 돌만 잠깐 보여줬다가(shown), 반박수가 있으면
  // 그걸 추가로 보여주고(refuted), 끝나면 원상복구(null)함.
  useEffect(() => {
    if (!mistake) return;
    if (mistake.phase === 'shown') {
      if (!mistake.refutation) {
        const timer = setTimeout(() => setMistake(null), MISTAKE_SHOWN_MS);
        return () => clearTimeout(timer);
      }
      const timer = setTimeout(
        () => setMistake((m) => (m ? { ...m, phase: 'refuted' } : m)),
        MISTAKE_SHOWN_MS,
      );
      return () => clearTimeout(timer);
    }
    const timer = setTimeout(() => setMistake(null), MISTAKE_REFUTED_MS);
    return () => clearTimeout(timer);
  }, [mistake]);

  const mistakeStones: MistakeStone[] = useMemo(() => {
    if (!mistake) return [];
    const stones: MistakeStone[] = [
      { r: mistake.wrong.r, c: mistake.wrong.c, player: puzzle.toMove, ring: 'wrong' },
    ];
    if (mistake.phase === 'refuted' && mistake.refutation) {
      stones.push({
        r: mistake.refutation.r,
        c: mistake.refutation.c,
        player: puzzle.toMove === 'black' ? 'white' : 'black',
        ring: 'refutation',
      });
    }
    return stones;
  }, [mistake, puzzle.toMove]);

  function handleCellPress(r: number, c: number) {
    if (solved || mistake) return;
    const next = puzzle.solution[movesPlayed];
    if (next.player !== puzzle.toMove) return; // 지금은 상대(강제) 차례라 입력 무시

    if (next.r === r && next.c === c) {
      setMovesPlayed((n) => n + 1);
      return;
    }

    // 오답이 사삼(위협)을 만들면 막는 자리(반박수)까지 보여주고, 아무 위협도
    // 안 만드는 수면 기존처럼 그냥 빨간 플래시만.
    const refutation = findRefutationCell(grid, puzzle.size, r, c, puzzle.toMove);
    if (refutation) {
      setMistake({ wrong: { r, c }, refutation, phase: 'shown' });
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

  // 같은 퍼즐(puzzle 객체는 그대로)을 처음부터 다시 풀 수 있게 진행 상태만 리셋.
  // 새 퍼즐을 뽑는 게 아니라 "다시 풀기"라서 puzzle은 안 건드림.
  function handleRetry() {
    setMovesPlayed(0);
    setWrongCell(null);
    setMistake(null);
  }

  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.container}>
      <Text style={styles.title}>오목 퍼즐 #{puzzle.id}</Text>
      <Text style={styles.subtitle}>{puzzle.toMove === 'black' ? '흑' : '백'}</Text>
      <Text style={styles.mistakeCaption}>
        {mistake?.phase === 'refuted' ? '여기서 막혀요' : ' '}
      </Text>
      <PuzzleBoard
        size={puzzle.size}
        grid={grid}
        wrongCell={wrongCell}
        lastMove={lastMove}
        mistakeStones={mistakeStones}
        onCellPress={handleCellPress}
      />
      {solved && (
        <View style={styles.solvedPanel}>
          <Text style={styles.solvedText}>풀었다! 🎉</Text>
          <View style={styles.buttonRow}>
            <Pressable style={styles.retryButton} onPress={handleRetry}>
              <Text style={styles.retryButtonText}>다시 풀기</Text>
            </Pressable>
            <Pressable style={styles.confirmButton} onPress={handleConfirmDone}>
              <Text style={styles.confirmButtonText}>돌아가기</Text>
            </Pressable>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
  },
  container: {
    alignItems: 'center',
    // 'center'로 두면 풀었을 때 solvedPanel이 추가되면서 전체 블록 높이가
    // 늘어나 보드가 위로 밀려 올라가 보임(세로 중앙 정렬이 다시 계산되는
    // 것뿐이라 버그는 아니었지만 눈에 거슬림) — 위에서부터 고정 배치해서
    // solvedPanel이 보드 밑에 추가돼도 보드 자체 위치는 안 움직이게 함.
    // ScrollView로 감싼 이유: PuzzleBoard가 화면 너비에 맞춰 커지는 정사각형
    // 이라, 좁고 긴 화면에서는 높이 계산을 아무리 잘해도 완벽히 다 들어간다는
    // 보장이 없음 — solvedPanel("돌아가기" 버튼)이 화면 밖으로 밀려나 안
    // 보이던 버그가 실제로 있었음. 보드 크기 자체도 PuzzleBoard 쪽에서
    // 세로 공간을 고려해서 줄이게 해뒀지만(RESERVED_VERTICAL_SPACE),
    // 기기별 오차에 대한 안전장치로 스크롤을 추가함.
    justifyContent: 'flex-start',
    paddingTop: 48,
    paddingBottom: 32,
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
  mistakeCaption: {
    fontSize: 13,
    fontWeight: '600',
    color: '#b35900',
    // 텍스트 유무와 상관없이 높이를 고정해서(빈 스페이스일 때도 똑같이 차지)
    // 캡션이 떴다 사라질 때마다 보드가 위아래로 밀리지 않게 함 — 풀었을 때
    // 보드가 밀리던 버그 고친 것과 같은 이유.
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
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  retryButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#1a1a1a',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#1a1a1a',
    fontSize: 16,
    fontWeight: '600',
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
