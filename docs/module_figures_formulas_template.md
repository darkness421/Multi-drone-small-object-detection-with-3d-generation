# 모듈별 그림 및 수식 정리 템플릿

## 목적

제안하는 시스템의 세부 모듈별 그림, 설명, 수식을 정리하기 위한 카드입니다.  
이 카드는 Notion의 `Proposed Method` 열에 넣습니다.

## Module 1. Multi-UAV Observation

### 설명

여러 UAV가 같은 object를 서로 다른 altitude와 view angle에서 관측합니다. 각 view는 RGB, depth, camera pose, 2D bbox를 생성합니다.

### 입력

- UAV id
- RGB image
- depth map
- camera intrinsics
- camera extrinsics
- 2D bbox

### 출력

- per-view object evidence

### 수식 초안

```text
E_i^v = {I_i^v, D_i^v, B_i^v, K_i^v, T_i^v, p_i^v}
```

여기서 `v`는 UAV view, `i`는 object index입니다.

## Module 2. 2D-to-3D Lifting

### 설명

2D bbox 중심과 bbox 내부 median depth를 이용해 camera coordinate의 3D point를 계산하고, camera extrinsics로 world coordinate로 변환합니다.

### 수식 초안

```text
z_i = median(D[u, v]), (u, v) ∈ B_i
```

```text
x_i = (u_i - c_x) z_i / f_x
y_i = (v_i - c_y) z_i / f_y
```

```text
P_i^w = T_{cw} [x_i, y_i, z_i, 1]^T
```

### 그림 후보

- bbox center
- depth crop
- camera ray
- world 3D point

## Module 3. 3D Object Evidence Graph

### 설명

여러 UAV view에서 나온 evidence를 object 중심 node로 묶습니다. Node는 crop, logits, geometry, view angle, occlusion, uncertainty, missing evidence를 포함합니다.

### 수식 초안

```text
G = (V, E)
```

```text
v_i = {P_i^w, C_i, L_i, A_i, O_i, U_i, M_i}
```

여기서 `P_i^w`는 3D center, `C_i`는 multi-view crop, `L_i`는 logits, `A_i`는 view angle, `O_i`는 occlusion, `U_i`는 uncertainty, `M_i`는 missing evidence입니다.

## Module 4. Ambiguity Diagnosis

### 설명

Object evidence graph를 보고 객체가 왜 애매한지 진단합니다. 결과는 ambiguity type, missing evidence, recommended next view로 정리합니다.

### Output JSON

```json
{
  "ambiguity_type": "missing_side_view",
  "missing_evidence": ["side marking", "roof light bar"],
  "recommended_next_view": {
    "view_type": "right_oblique",
    "altitude": 80
  },
  "need_reobservation": true
}
```

## Module 5. Evidence Completion Policy

### 설명

모호한 object에 대해서만 추가 view를 요청하거나 hard case scenario를 생성합니다.

### 수식 초안

```text
a_i^* = argmax_a Gain(a | G_i, M_i, U_i)
```

```text
Gain(a) = λ_1 ΔConf_i(a) + λ_2 ΔView_i(a) - λ_3 Cost(a)
```

## 나중에 채울 TODO

- [ ] Survey 후 최종 모듈 수 확정
- [ ] 각 모듈별 figure draft 생성
- [ ] 실제 논문에 넣을 수식만 남기기
- [ ] 수식 notation 통일
- [ ] caption 초안 작성

