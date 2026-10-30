# puzzle-gen

오목 실드 퍼즐 뱅크 생성기. 기본 포지션 소스는 **RenjuNet 실제 대국 데이터베이스**
(renju.net) — 라이선스/배포 전제는 아래 "데이터 출처" 참고. 외부 엔진 의존은 없음
(VCF 솔버는 순수 자체 구현).

앱에 포함되지 않는 **개발용 도구**. 여기서 뽑은 `output/puzzles.json`만 앱 쪽 static asset으로 번들됨.

## 구조

- `gomoku.py` — 15x15 프리스타일 오목 보드(이 모듈 자체는 순수 기하 규칙만, 5개 이상이면 승리 — 흑/백 구분 규칙 없음).
- `renju_forbidden.py` — 렌주 흑 전용 금수(장목/사사/삼삼) 판정. gomoku.py 위에 별도 레이어로 얹음 — vcf.py가 흑이 두는 모든 수(공격이든 수비든)에 적용함.
- `vcf.py` — VCF(연속 사삼 강제승리) 솔버. 매 수마다 "이기는 수가 정확히 하나"인지 검증해서 cook(복수 정답) 있는 포지션은 버림. 흑 관련 수는 renju_forbidden.py로 금수 체크도 함.
- `renjunet.py` — RenjuNet XML 다운로드/캐싱 + 좌표 파싱 + 대국 재생.
- `generate.py` — 포지션 생성(`--source renjunet`: 실제 대국 재생 / `--source random`: 자체 셀프플레이, 비교용) → 강제승리 유무/유일성 체크 → 난이도(공격 측 수 개수)별로 버킷에 모아 JSON 출력.
- `preview.py` — 생성된 퍼즐을 ASCII 보드로 렌더링해서 눈으로 바로 확인.

## 데이터 출처 (RenjuNet)

renju.net이 공개 배포하는 실제 토너먼트 대국 데이터베이스(현재 12만 판 이상)를 씀.
데이터 파일에 박혀있는 라이선스 원문:

> It is allowed to use this database for non-commercial purposes in the forms of
> OFFLINE databases only. It is forbidden to use any contents of this database or
> its modifications in any website or ONLINE system.

**오목 실드가 사이드로드(개인/비상업, 완전 온디바이스) 배포라는 전제 위에서 이
조건과 맞는다고 판단해서 씀** — Play Store 등 상업적 유통을 하게 되면 이 전제가
깨지므로 그때는 데이터 소스를 다시 검토해야 함. "앱이 온라인 시스템인가"는
해석 여지가 있는 지점(네트워크 호출 없는 완전 오프라인 앱이라는 점으로 방어).

대국 자체는 렌주 공식 규칙(흑 금수 있음)으로 뒀음 — 여기서 뽑는 포지션(돌 배치)은
그대로 렌주 룰 기준으로 합법함. 강제승리 수순을 다시 계산할 때는 vcf.py가
renju_forbidden.py를 통해 흑 금수(장목/사사/삼삼)를 그대로 지킴(흑이 렌주 룰로는
둘 수 없는 수를 강제승리 수순에 섞어 쓰는 버그가 실제로 있었음 — CLAUDE.md 참고).

## 사용법

```
python3 generate.py --source renjunet --target 20 --max-difficulty 3 --out output/puzzles.json
python3 preview.py output/puzzles.json --difficulty 2 --limit 5
```

- `--source`: `renjunet`(기본값, 실제 대국) 또는 `random`(자체 셀프플레이, 비교용)
- `--renjunet-xml`: RenjuNet XML 캐시 경로(없으면 자동 다운로드, `renjunet_cache/` — git에는 안 올라감)
- `--target`: 난이도별 목표 개수
- `--max-difficulty`: 탐색할 최대 난이도(공격 측 수 개수)
- `--max-games`: 목표 못 채우면 포기할 상한 게임 수
- `--seed`: 재현용 랜덤 시드(`--source random`일 때만 의미 있음, renjunet은 대국 섞는 순서에만 씀)

## 출력 포맷

```json
{
  "puzzles": [
    {
      "id": 1,
      "size": 15,
      "toMove": "black",
      "stones": [{"r": 0, "c": 5, "player": "black"}, ...],
      "solution": [{"player": "black", "r": 3, "c": 4}, ...],
      "difficulty": 1
    }
  ]
}
```

`solution`은 공격 측 수 + 강제된 상대 수까지 전부 순서대로 들어있음(상대 수는 앱에서 자동 재생, 유저는 공격 측 수만 클릭하면 됨).

## 테스트

각 함수의 input/output을 문서화 겸 검증하는 테스트가 `tests/`에 있음(표준 `unittest`, 외부 패키지 설치 불필요).

```
python3 -m unittest discover -s tests
```

`vcf.py`의 핵심 케이스 두 개는 실제로 생성됐던 퍼즐 포지션을 그대로 하드코딩한 회귀 테스트임(더블 포로 depth=1에서 바로 끝나는 경우 / depth=1은 실패하고 depth=2에서야 찾아지는 경우).

## 알아둘 것

- 난이도는 "탐색 깊이"가 아니라 실제 정답 수순의 공격 측 수 개수로 매김 — 더블 포(double-four) 마무리는 탐색 깊이 1에서 끝나도 공격 수가 2개라 난이도 2로 분류됨.
- 한 대국/게임당 퍼즐 하나만 채택(연속 스냅샷이 전부 비슷한 판이라 다양성 떨어지는 거 방지).
- 현재 기본 출력 `output/puzzles.json`은 RenjuNet 기반 90개(난이도 1~3, 각 30개), 생성에 로컬에서 약 3~4분. `output/puzzles.random.json`은 예전 자체 셀프플레이 배치(비교 참고용으로 보관) — 실제 대국 쪼이 돌 배치가 훨씬 자연스러움(`preview.py`로 둘 다 직접 비교 가능).
- 더 어려운 난이도(4+)는 탐색 비용이 급격히 커짐 — 필요해지면 margin/depth 튜닝 필요.
