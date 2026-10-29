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

export function PuzzleBoard({ size, grid, wrongCell, onCellPress }: PuzzleBoardProps) {
  const { width } = useWindowDimensions();
  const boardSize = width - BOARD_PADDING * 2;
  const cellSize = Math.floor(boardSize / size);

  return (
    <View style={[styles.board, { width: cellSize * size, height: cellSize * size }]}>
      {grid.map((row, r) => (
        <View key={r} style={styles.row}>
          {row.map((stone, c) => {
            const isWrong = wrongCell?.r === r && wrongCell?.c === c;
            return (
              <Pressable
                key={c}
                onPress={() => onCellPress(r, c)}
                disabled={stone !== null}
                style={[
                  styles.cell,
                  { width: cellSize, height: cellSize },
                  isWrong && styles.wrongCell,
                ]}
              >
                {stone && (
                  <View
                    style={[
                      styles.stone,
                      {
                        width: cellSize * 0.8,
                        height: cellSize * 0.8,
                        borderRadius: (cellSize * 0.8) / 2,
                        backgroundColor: stone === 'black' ? '#1a1a1a' : '#f5f5f5',
                        borderColor: stone === 'white' ? '#999' : 'transparent',
                      },
                    ]}
                  />
                )}
              </Pressable>
            );
          })}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  board: {
    backgroundColor: '#dcb35c',
    borderWidth: 1,
    borderColor: '#8a6d3b',
  },
  row: {
    flexDirection: 'row',
  },
  cell: {
    borderWidth: 0.5,
    borderColor: '#8a6d3b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  wrongCell: {
    backgroundColor: 'rgba(220, 50, 50, 0.35)',
  },
  stone: {
    borderWidth: 1,
  },
});
