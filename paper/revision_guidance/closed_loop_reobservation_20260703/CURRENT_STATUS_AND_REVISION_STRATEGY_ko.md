# CoM3D-ACE Revision Status and Strategy

작성일: 2026-07-03

## 1. 지금 새로 끝난 보완 실험

Fresh commanded Isaac/Cesium targeted re-observation을 수행했다. 기존 MarineCity
viewer160 evidence graph에서 `targeted_reobserve`로 라우팅된 9개 hypothesis를
읽고, 각 hypothesis의 missing UAV/view 방향으로 graph-generated camera pose를
만든 뒤 S0/S1/S2 actor layer에서 새 RGB/depth를 캡처했다.

핵심 결과:

- Fresh targeted capture: S0/S1/S2 모두 완료
- Detector token 수: S0 23개, S1 25개, S2 28개, merged 76개
- Routed targeted hypotheses: 9개
- Matching same-class re-observation evidence: 6개
- `targeted_reobserve -> monitor` 전환: 6개
- 계속 `targeted_reobserve` 유지: 3개
- Mean ambiguity: 0.923 before -> 0.901 raw insertion -> 0.775 closed-loop update

논문에서 안전한 claim:

> We validate the targeted re-observation branch through fresh commanded
> Isaac/Cesium camera-pose recapture. Six of nine routed hypotheses receive
> matching follow-up evidence and move from targeted re-observation to monitor,
> reducing mean closed-loop ambiguity from 0.923 to 0.775. This validates the
> camera-pose/evidence-update contract, not autonomous physical UAV flight.

## 2. 바로 볼 파일

Closed-loop fresh 결과:

- Summary report: `outputs/reports/live/closed_loop_reobservation_fresh_20260703/closed_loop_reobservation_report.md`
- Paper-ready summary card: `outputs/reports/live/closed_loop_reobservation_fresh_20260703/figures/closed_loop_summary_card.png`
- Before/after ambiguity plot: `outputs/reports/live/closed_loop_reobservation_fresh_20260703/figures/closed_loop_ambiguity_before_after.png`
- Contact sheet: `outputs/reports/live/closed_loop_reobservation_fresh_20260703/closed_loop_contact_sheet.png`
- Per-hypothesis CSV: `outputs/reports/live/closed_loop_reobservation_fresh_20260703/closed_loop_reobservation_results.csv`
- Confidence sensitivity: `outputs/reports/live/closed_loop_reobservation_confidence_sensitivity/closed_loop_confidence_sensitivity.md`

Overleaf/GPT Pro용 복사본:

- Guidance root: `paper/revision_guidance/closed_loop_reobservation_20260703/`
- Figure snippets: `paper/revision_guidance/closed_loop_reobservation_20260703/figure_insert_candidates.tex`
- Candidate tables: `paper/revision_guidance/closed_loop_reobservation_20260703/tables/`

## 3. LLM reasoner prompt 투명성

LLM/Reasoner가 어떤 prompt를 받는지 보이지 않는 문제를 줄이기 위해 prompt audit을
생성했다. 현재 audit의 provider는 `rule_based_aerograph`이므로, 이것을 외부 LLM
성능 벤치마크처럼 쓰면 안 된다. 대신 prompt contract/schema, graph-grounded input,
response JSON, final action adjudication이 투명하다는 증거로 쓰는 것이 안전하다.

파일:

- Prompt audit: `outputs/reports/live/aerograph_prompt_audit/aerograph_prompt_audit.md`
- Guidance copy: `paper/revision_guidance/closed_loop_reobservation_20260703/prompt_audit/aerograph_prompt_audit.md`

논문 표현:

> We expose the verifier prompt/schema and graph metadata passed to the
> reasoner. The current audit is a transparent rule-based AeroGraph plumbing
> check, while external LLM-provider benchmarking is left as a bounded extension.

## 4. 3D reconstruction visual 상태

3D 생성/재구성 결과가 어떤 이미지 형태인지 볼 수 있도록 visual audit sheet를 만들었다.
Nerfacto와 Instant-NGP는 held-out render/depth 형태를 보여줄 수 있다. 3DGS/Splatfacto는
render composite는 있으나 depth panel이 blank라서 주력 claim으로 밀면 위험하다.

파일:

- 3D visual audit: `outputs/reports/live/marinecity_3d_visual_audit/marinecity_3d_visual_audit_sheet.png`
- Guidance copy: `paper/revision_guidance/closed_loop_reobservation_20260703/3d_visual_audit/marinecity_3d_visual_audit_sheet.png`

논문 전략:

- Main claim은 detector/evidence graph/closed-loop evidence update에 둔다.
- 3D는 completed benchmark가 아니라 bounded handoff/interface and visual readiness로 둔다.
- Nerfacto/Instant-NGP 중심으로 보여주고, 3DGS/Splatfacto blank depth는 supplement나
  limitation으로 처리한다.

## 5. 추천 논문 수정 순서

1. Main paper에는 `closed_loop_summary_card.png` 또는 compact table 하나만 넣는다.
2. Main text는 2-3문장으로만: 9 routed, 6 matched/resolved, ambiguity 0.923 -> 0.775.
3. Supplementary에는 per-hypothesis table, contact sheet, prompt audit 설명을 자세히 넣는다.
4. Claim boundary에는 반드시 autonomous physical UAV flight가 아님을 쓴다.
5. 3D/LLM은 broad contribution처럼 보이지 않게, bounded handoff/interface validation으로 제한한다.

## 6. Confidence Sensitivity

Low-confidence follow-up evidence에 대한 reviewer 질문을 대비해 confidence threshold
sensitivity를 만들었다.

- Min conf 0.00/0.01: matched/resolved 6/9, mean A(loop) 0.775
- Min conf 0.05: matched/resolved 5/9, mean A(loop) 0.795
- Min conf 0.10/0.25: matched/resolved 4/9, mean A(loop) 약 0.81
- Min conf 0.50: matched/resolved 3/9, mean A(loop) 0.815

이 표는 main result로 크게 밀기보다, supplement나 rebuttal에서 “permissive detector
threshold를 쓰는 이유와 보수적 threshold에서도 일부 closure가 유지된다”는 방어용으로
쓰는 것이 좋다.

파일:

- Plot: `outputs/reports/live/closed_loop_reobservation_confidence_sensitivity/closed_loop_confidence_sensitivity.png`
- Table: `paper/tables/marinecity_closed_loop_confidence_sensitivity_table.tex`
- Guidance copy: `paper/revision_guidance/closed_loop_reobservation_20260703/confidence_sensitivity/`

## 7. 3일 안에 추가하면 좋은 것

- Fresh capture raw image/contact sheet를 supplement에 넣어 fake/block-city 의심을 줄인다.
- 3DGS/Splatfacto blank depth는 제출물에서 주력 figure로 쓰지 않는다.
- LLM external provider 결과를 넣고 싶다면 prompt/response JSON을 반드시 저장하고, rule-based audit과 분리해서 보고한다.
