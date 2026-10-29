# 오목 실드 (Gomoku Shield)

## 프로젝트 개요
유튜브 Shorts / 인스타그램 Reels 탭 진입을 감지해 오목 퍼즐로 끼어드는 **Android 전용**, **사이드로드(개인/비상업) 배포** 앱. (Play Store 배포는 취소됨 — 아래 "퍼즐 뱅크 생성 방식"의 RenjuNet 데이터 라이선스 조건과 맞추기 위한 결정.)

## 스택
- React Native + Expo, **Android 전용 custom dev client** (`expo prebuild`, Android 빌드 프로파일만 — iOS 미대응)
- 언어: TypeScript
- 네이티브 모듈: Kotlin (AccessibilityService)

## 핵심 기능 설계 (grilling으로 확정된 사항)

1. **감지 범위**: 앱 단위가 아니라 **탭 단위**. 유튜브 Shorts 탭, 인스타그램 Reels 탭 진입을 view-id/리소스-id 패턴으로 감지. 두 앱 업데이트될 때마다 패턴 깨질 수 있음 — 유지보수 부담 있는 걸 알고 가는 것.
2. **차단 트리거**: 감지 즉시 **포커스를 가진 풀스크린 Activity**로 전환 (`FLAG_ACTIVITY_NEW_TASK`). `SYSTEM_ALERT_WINDOW` 오버레이 권한 불필요 — 순수 오버레이만으로는 밑에 깔린 영상/오디오가 멈춘다는 보장이 없어서 포커스 뺏는 Activity 전환 방식으로 감.
3. **강제력 없음**: 원래는 Play Store 정책(뒤로가기/홈 버튼 막는 패턴 반려 위험) 때문에 정한 설계였는데, 사이드로드 전환 후에도 **사용자가 명시적으로 이 설계를 유지하기로 함**(기술적으로는 이제 진짜 강제 차단도 가능하지만 안 함). 퍼즐을 안 풀고 나가면 **재진입마다 다시 뜸**(반복 인터럽트) — 강제 차단이 아니라 피로감으로 억제하는 설계.
4. **게임 = 고정 퍼즐 뱅크**: 실시간 AI 대국 아님. 미리 만들어둔 포지션 세트에서 매번 하나씩 냄. 각 퍼즐은 고유 ID 있음(유저가 나중에 식별 가능하도록 노출). AI 엔진 불필요.
5. **보상**: 퍼즐 풀면 유저가 설정에서 고른 면제시간(3분/5분/10분 중 택1) 동안 재감지 안 함.
6. **데이터 정책**: 서버/분석/크래시리포팅 전혀 없음, 완전 온디바이스. 승패·사용 기록(로그)은 저장 안 함(매번 휘발). 단 면제시간 선택값 같은 **앱 설정**은 로컬에 저장 가능(이건 "사용 기록"이 아니라 환경설정이라 구분).

## 퍼즐 뱅크 생성 방식 (구현됨: `tools/puzzle-gen/`)

**데이터 소스는 RenjuNet 실제 대국 데이터베이스(renju.net).** 처음엔 Play Store
배포를 전제로 해서 라이선스 조건(비상업·오프라인 전용)과 안 맞아 자체 생성(랜덤
셀프플레이)으로 갔었는데, **배포 전략을 사이드로드·비상업으로 바꾸면서 RenjuNet
데이터가 다시 유효한 선택지가 됨.**

- 라이선스 원문(데이터 파일에 그대로 박혀있음): "It is allowed to use this
  database for non-commercial purposes in the forms of OFFLINE databases only.
  It is forbidden to use any contents of this database or its modifications in
  any website or ONLINE system." — 사이드로드·비상업·완전 온디바이스 배포라는
  전제 위에서 조건 충족한다고 판단. **이 전제가 깨지면(예: 나중에 Play Store로
  다시 가면) 데이터 소스를 재검토해야 함.**
- 다른 경로(GomokuZero 등 RenjuNet 데이터를 MIT로 재포장한 GitHub 레포, Renlib의
  `.lib` 파일들)도 검토했으나 라이선스 불명확 또는 파싱 불가(독자 바이너리 포맷,
  공개 파서 없음)로 제외. RenjuNet 공식 XML 다운로드를 직접 쓰는 쪼으로 확정.
- `tools/puzzle-gen/gomoku.py` — 15x15 프리스타일 보드(금수 없음, 5+ 승리).
- `tools/puzzle-gen/vcf.py` — VCF 강제승리 솔버. 매 수마다 "이기는 수가 정확히 하나"인지 검증해서 cook(복수 정답) 있는 포지션은 버림 → Lichess 퍼즐과 동일한 "유일 정답" 원칙.
- `tools/puzzle-gen/renjunet.py` — RenjuNet XML 다운로드/캐싱, 좌표 파싱(`h8` 등 → `(r,c)`), 대국 재생.
- `tools/puzzle-gen/generate.py` — 포지션 생성(`--source renjunet` 기본값 / `--source random` 비교용) → 유일 강제승리 체크 → 난이도(공격 측 수 개수)별 버킷에 모아 JSON 출력.
- `tools/puzzle-gen/preview.py` — 생성된 퍼즐을 ASCII 보드로 렌더링해서 직접 확인.
- 현재 출력: `output/puzzles.json` RenjuNet 기반 90개(난이도 1~3, 각 30개). 예전 자체 셀프플레이 60개는 `output/puzzles.random.json`에 비교용으로 보관. 앱 스캐폴딩 후 이 JSON을 static asset으로 번들할 예정. 상세 사용법은 `tools/puzzle-gen/README.md`.

## 폴더 구조
(앱 스캐폴딩 전 — 다음 단계에서 `expo prebuild` 이후 실제 구조 반영 예정)

## 코드 컨벤션

1. **주석**: 한글. 함수/복잡한 로직 블록 단위로 "이게 뭘, 왜 하는지" 1~2줄 설명(너무 당연한 getter/setter류는 안 씀). 나중에 다시 봐도 이해되는 수준으로 — WHY만 쓰는 극단적 미니멀은 지양.
2. **네이밍**: 각 언어의 표준 컨벤션 그대로 따름.
   - TypeScript/JS: 변수·함수 `camelCase`, 타입·컴포넌트 `PascalCase`, 상수 `UPPER_SNAKE_CASE`.
   - Kotlin: 변수·함수 `camelCase`, 클래스 `PascalCase`, 상수 `UPPER_SNAKE_CASE`(companion object 등).
   - Python(`tools/puzzle-gen`): PEP8 — 변수·함수 `snake_case`, 클래스 `PascalCase`.
   - 식별자 자체는 영어, 주석·커밋 메시지만 한글.
3. **TypeScript**: strict mode 켬. `any` 쓰면 그 자리에 왜 불가피한지 주석 필수.
4. **폴더 구조**: feature 기반(`src/features/<기능>/{components,hooks,...}`) — 기술 타입별로 흩어놓지 않고 기능 단위로 묶음.
5. **함수 길이**: 대략 40줄 넘으면 분리 고려(강제 규칙 아니고 가이드).
6. **Kotlin 네이티브 모듈**: 공식 Kotlin 스타일 가이드 따름. AccessibilityService처럼 권한 민감한 로직은 주석 필수(뭘 수집하는지/왜 필요한지 명시).
7. **테스트**: MVP 단계라 전면 강제 안 함, 단 `vcf.py` 같은 핵심 로직(퍼즐 솔버, 강제승리 판정)은 유닛테스트 둠.

## 커밋 컨벤션
- Conventional Commits (`feat:`, `fix:`, `chore:` 등)

## 참고 / 리스크
- AccessibilityService 네이티브 모듈(Kotlin) 작업 시 권한 범위 최소로 — 사이드로드라 Play 심사는 없지만, 권한 오남용 자체는 여전히 조심해야 할 부분.
- 유튜브/인스타 view-id 기반 탐지라 두 앱 업데이트 추적 필요(깨짐 감시 체계 나중에 고려).
- RenjuNet 데이터 사용은 "사이드로드·비상업·완전 온디바이스"라는 배포 전제에 근거함 — 이 전제가 바뀌면(재상업화, Play Store 재검토 등) 데이터 소스도 같이 재검토해야 함.
