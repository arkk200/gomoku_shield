import { NativeModule, requireNativeModule } from 'expo';
import type { LaunchTrigger } from './ShortsDetector.types';

declare class ShortsDetectorModule extends NativeModule<{}> {
  // 안드로이드 접근성 설정 화면을 염 — 서비스는 유저가 직접 켜야 함.
  openAccessibilitySettings(): void;
  // 지금 ShortsDetectorAccessibilityService가 켜져있는지.
  isAccessibilityServiceEnabled(): boolean;
  // MainActivity가 감지 서비스에 의해 재실행된 거면 'puzzle', 아니면 null.
  // 한 번 읽으면 지워짐(같은 트리거로 두 번 안 반응하게).
  consumeLaunchTrigger(): LaunchTrigger;
  // 퍼즐 풀었을 때 호출 — graceMinutes 동안 재감지 안 되게 면제 기록.
  markPuzzleSolved(graceMinutes: number): void;
  getGraceMinutesSetting(): number;
  setGraceMinutesSetting(minutes: number): void;
}

export default requireNativeModule<ShortsDetectorModule>('ShortsDetector');
