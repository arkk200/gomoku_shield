import { useCallback, useEffect, useState } from 'react';
import { AppState, StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import ShortsDetector from './modules/shorts-detector/src/ShortsDetectorModule';
import { PuzzleScreen } from './src/features/puzzle/PuzzleScreen';
import { SettingsScreen } from './src/features/settings/SettingsScreen';

type Screen = 'home' | 'puzzle';

export default function App() {
  const [screen, setScreen] = useState<Screen>('home');

  // AccessibilityService가 MainActivity를 재실행시킨 거면(퍼즐 트리거) 퍼즐 화면으로 전환.
  // 앱 첫 실행 때도 한 번 체크하고, 이미 떠있는 상태에서 다시 포그라운드로 올 때도 체크함
  // (singleTask라 재실행이 onNewIntent로 오지 JS가 다시 마운트되는 게 아니라서).
  const checkLaunchTrigger = useCallback(() => {
    if (ShortsDetector.consumeLaunchTrigger() === 'puzzle') {
      setScreen('puzzle');
    }
  }, []);

  useEffect(() => {
    checkLaunchTrigger();
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') checkLaunchTrigger();
    });
    return () => subscription.remove();
  }, [checkLaunchTrigger]);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container}>
        {screen === 'puzzle' ? (
          <PuzzleScreen onDone={() => setScreen('home')} />
        ) : (
          <SettingsScreen />
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
});
