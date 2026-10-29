import { Pressable, StyleSheet, View, useWindowDimensions } from 'react-native';
import type { StoneColor } from './types';

export type Grid = (StoneColor | null)[][];

interface PuzzleBoardProps {
  size: number;
  grid: Grid;
  wrongCell: { r: number; c: number } | null;
  onCellPress: (r: number, c: number) => void;
}

const BOARD_PADDING = 16;
const LINE_THICKNESS = 1;

export function PuzzleBoard({ size, grid, wrongCell, onCellPress }: PuzzleBoardProps) {
  const { width } = useWindowDimensions();
  const boardSize = width - BOARD_PADDING * 2;
  // 오목판은 칸 안이 아니라 가로/세로선이 겹치는 교차점에 돌을 놓음 — 각 교차점을
  // (칸 하나 크기의) 격자 중심으로 두고, 선은 교차점끼리를 잇는 식으로 그림.
  const spacing = boardSize / size;
  const center = (i: number) => spacing * (i + 0.5);
  const lineSpan = spacing * (size - 1);
  const firstCenter = center(0);

  return (
    <View style={[styles.board, { width: boardSize, height: boardSize }]}>
      {Array.from({ length: size }, (_, i) => (
        <View
          key={`h${i}`}
          style={[
            styles.line,
            { top: center(i), left: firstCenter, width: lineSpan, height: LINE_THICKNESS },
          ]}
        />
      ))}
      {Array.from({ length: size }, (_, i) => (
        <View
          key={`v${i}`}
          style={[
            styles.line,
            { left: center(i), top: firstCenter, height: lineSpan, width: LINE_THICKNESS },
          ]}
        />
      ))}

      {grid.map((row, r) =>
        row.map((stone, c) => {
          const isWrong = wrongCell?.r === r && wrongCell?.c === c;
          return (
            <Pressable
              key={`${r}-${c}`}
              onPress={() => onCellPress(r, c)}
              disabled={stone !== null}
              style={[
                styles.intersection,
                {
                  left: center(c) - spacing / 2,
                  top: center(r) - spacing / 2,
                  width: spacing,
                  height: spacing,
                },
                isWrong && styles.wrongIntersection,
              ]}
            >
              {stone && (
                <View
                  style={[
                    styles.stone,
                    {
                      width: spacing * 0.8,
                      height: spacing * 0.8,
                      borderRadius: (spacing * 0.8) / 2,
                      backgroundColor: stone === 'black' ? '#1a1a1a' : '#f5f5f5',
                      borderColor: stone === 'white' ? '#999' : 'transparent',
                    },
                  ]}
                />
              )}
            </Pressable>
          );
        }),
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  board: {
    backgroundColor: '#dcb35c',
    borderWidth: 1,
    borderColor: '#8a6d3b',
  },
  line: {
    position: 'absolute',
    backgroundColor: '#8a6d3b',
  },
  intersection: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  wrongIntersection: {
    backgroundColor: 'rgba(220, 50, 50, 0.35)',
    borderRadius: 999,
  },
  stone: {
    borderWidth: 1,
  },
});
