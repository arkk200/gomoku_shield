import { useCallback, useEffect, useState } from 'react';
import { AppState, Pressable, StyleSheet, Text, View } from 'react-native';
import ShortsDetector from '../../../modules/shorts-detector/src/ShortsDetectorModule';

const GRACE_OPTIONS = [3, 5, 10];

export function SettingsScreen() {
  const [graceMinutes, setGraceMinutes] = useState(10);
  const [serviceEnabled, setServiceEnabled] = useState(false);

  const refreshStatus = useCallback(() => {
    setGraceMinutes(ShortsDetector.getGraceMinutesSetting());
    setServiceEnabled(ShortsDetector.isAccessibilityServiceEnabled());
  }, []);

  useEffect(() => {
    refreshStatus();
    // 접근성 설정 화면 갔다가 돌아왔을 때 상태 다시 읽으려고 포그라운드 복귀마다 갱신.
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') refreshStatus();
    });
    return () => subscription.remove();
  }, [refreshStatus]);

  function selectGraceMinutes(minutes: number) {
    setGraceMinutes(minutes);
    ShortsDetector.setGraceMinutesSetting(minutes);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>오목 실드</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>감지 서비스</Text>
        <Text style={styles.statusText}>
          {serviceEnabled ? '켜짐' : '꺼짐 — 아래에서 켜주세요'}
        </Text>
        <Pressable style={styles.button} onPress={() => ShortsDetector.openAccessibilitySettings()}>
          <Text style={styles.buttonText}>접근성 설정 열기</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>퍼즐 풀면 면제되는 시간</Text>
        <View style={styles.optionRow}>
          {GRACE_OPTIONS.map((minutes) => (
            <Pressable
              key={minutes}
              style={[styles.optionButton, graceMinutes === minutes && styles.optionButtonSelected]}
              onPress={() => selectGraceMinutes(minutes)}
            >
              <Text
                style={[
                  styles.optionButtonText,
                  graceMinutes === minutes && styles.optionButtonTextSelected,
                ]}
              >
                {minutes}분
              </Text>
            </Pressable>
          ))}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    gap: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginTop: 16,
  },
  section: {
    gap: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  statusText: {
    color: '#555',
  },
  button: {
    backgroundColor: '#1a1a1a',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
  },
  optionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  optionButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#999',
  },
  optionButtonSelected: {
    backgroundColor: '#1a1a1a',
    borderColor: '#1a1a1a',
  },
  optionButtonText: {
    color: '#1a1a1a',
    fontWeight: '600',
  },
  optionButtonTextSelected: {
    color: '#fff',
  },
});
