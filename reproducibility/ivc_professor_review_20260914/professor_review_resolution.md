# Professor review resolution

## 1. 지적별 판정과 근거

- P0: **부분 해결.** 원시 CSV, 캐시, 실행 명령, descriptor/source hash와 현재
  source commit을 연결했고 핵심 비교군을 복원했다. 단, 지정된 SHA-256의
  review PDF가 로컬에 없어 그 PDF와의 byte-level 연결만 미확인이다.
- P1: **해결.** `aflink_source_record.json`, `aflink_stage_audit.csv`,
  `minimal_failure_case/`, `native_vs_adapted_results.csv`에 원인과 결과를 저장했다.
- P2: **해결.** 1,989개 실제 인스턴스 property test가 통과했다. guard는 평가된
  규칙에서 방어적 assertion이며 독립 성능 모듈이 아니다.
- P3: **해결.** 동일 후보 graph/cost 기반 solver 통제, edge trace, error--coverage,
  CPU solver 시간/메모리를 산출했다. 사후 threshold 선택은 하지 않았다.
- P4: **해결.** M3OT 16개 기존 인스턴스를 오차 0으로 재현하고 기회 손실,
  오연결, greedy/reciprocal/Hungarian 결과를 비교했다.
- P5: **부분 해결.** 주요 linker 대비 paired sequence CI를 계산했다. 공식 metadata에
  source-flight mapping이 없어 block bootstrap은 수행하지 않았다.
- P6: **부분 해결/원고 반영 완료.** 본 보고서 수치를 근거로 main comparison,
  AFLink, guard, M3OT와 confirmation scope를 수정했다. AI-use 선언은 사용자의
  최종 명시 지시에 따라 원고에서 제외했다. 저자 제작
  Fig. 1/2 파일은 보존하고 캡션과 본문에서 motivation/system context로 범위를
  제한했다. 따라서 교수님이 요청한 Fig. 1의 temporal before/after 교체 자체는
  범위에서 제외되어 부분 해결로 남는다.

## 2. AFLink failure stage, 원인, raw 및 adapter 결과

Frozen StrongSORT commit `ee995076da5083e28d0da1f885297df62705ebd7`의 `AppFreeLink.py:107`는 ID remap
뒤 `deduplicate`를 호출한다. Cached official assignments는 13개
sequence/tracker/class context에서 overlapping IDs를 만들었고, native deduplication은
총 15개 box를 삭제했다.
2-decimal save formatting은 별도의 numeric serialization 변화다. 클래스별 local ID
재사용은 evaluator namespace 때문에 충돌 원인이 아니다. 무GT validity adapter는
overlap을 만드는 merge를 거부하여 모든 box를 보존했고, 전 6개 full-set 조건에서
유효한 수치를 생성했다. 자세한 수치는 `native_vs_adapted_results.csv`에 있다.

## 3. Guard 코드/명세 일치와 역할

실제 코드는 proposal을 한 번 생성하고, strict forward-time edge와 reciprocal
predecessor/successor를 사용한다. 관측 indegree/outdegree는 최대 1/1이고 cycle,
입력 frame duplicate, guard rejection, guard/no-guard 차이는 모두 0이었다. 따라서
현재 명세에서 component guard는 구조적으로 중복이며 defensive assertion/output
validation으로만 유지한다.

## 4. 주요 linker 대비 정확도, risk, 비용과 주장 근거

Historical CoM3D는 None보다 6개 조건의 평균 IDF1을 모두 개선한다. 그러나
Geometry+ReID greedy와 partial Hungarian보다 IDF1이 6개 모두 낮다. Common scalar
cost를 쓴 reciprocal은 historical ranking보다 6개 모두 IDF1이 높고, 고정 0.30에서
coverage도 높으며 known-link error도 낮다. Reciprocal solver의 CPU 시간/peak memory는
Hungarian보다 대체로 작지만 descriptor/candidate 비용에 비해 절대 차이가 작다.
따라서 historical rule의 최고 정확도·최적 risk·실질 end-to-end 비용 우위는
입증되지 않았다. 유지 가능한 핵심 주장은 box-preserving deterministic refinement와
None 대비 평균 개선, 명시적 failure audit이다.

## 5. M3OT 원인과 재설계 필요성

Held-out 정답 기회 8개 중 5개는 55-pixel gate 밖이고, 2개는 incoming rank, 1개는
outgoing rank에서 탈락했다. Common-cost reciprocal은 tracker별 정답 링크 1개를
복원하고 false link를 줄였지만 두 tracker 모두 None보다 IDF1이 낮다. Ranking과
fixed pixel/MOT17 appearance cue의 domain mismatch가 함께 남으므로, 새로운 transfer
주장 전에는 development-only redesign과 새 confirmation data가 필요하다.

## 6. 원고 수정과 수치 변경 근거

Main Results에 여섯 비교군을 복원하고, controlled ranking 진단과 paired CI를 부록에
추가했다. AFLink는 native와 `+ common validity adapter`를 구분했다. Guard는 assertion으로
정정하고, “all 50 sequences improve”를 “the equal-sequence mean over 50 improves”로
제한했다. Confirmation38은 외부 독립성이 아니라 locally pre-specified partition으로
표현했다. M3OT oracle crop admission과 실패 분석을 명시했다. 사용자의 최종 지시에
따라 AI-use 선언과 Methods의 관련 문장은 포함하지 않았다. 표 수치는
`main_comparison.csv`, `paired_linker_deltas.csv`, `m3ot_linker_comparison.csv`의
full-precision 값에서 한 번만 반올림했다. `verify_manuscript_numbers.py`가 주요 LaTeX
표와 초록/본문 delta 94개를 원시 CSV에 대조했고 94/94가 통과했다. Docker의 고정
LaTeX 환경에서 27쪽 PDF를 생성했으며 unresolved citation/reference와 overfull box는
0개다. 참고문헌 URL에서 생기는 underfull box 경고 4개만 남는다.

## 7. 독립 검증 미완료 사항과 필요한 산출물

- Review PDF hash `7a04b4d4aa7a6c1f1462aca97a5d9346548c72792c4313b48d0f87756734aab6`: 정확한 PDF 파일이 필요하다.
- MMOT 원영상/비행 단위 block bootstrap: 공식 sequence-to-flight metadata가 필요하다.
- Confirmation38의 외부 preregistration/독립 timestamp: 해당 시점의 외부 기록이 필요하다.
- M3OT descriptor의 detector-only transfer: 현재 기록은 oracle GT IoU crop admission이므로,
  별도 사전 고정 detector-input protocol과 새 실행이 필요하다.
- GIAOTracker 공식 비교: 공개 implementation과 compatible weights가 필요하다.
