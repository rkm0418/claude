# 초반 도시: 처음 장소 이후의 공간 나열 (수정 방법)

처음 떨어진 곳(인공 수풀 화단, #254) → **긴 직선 거리(#273, 가로등이 뒷벽 쪽으로 60px 간격)** → 정사각형 방(#274) → **아래로 꺾이는 통로(#275)** → 방(#276) → 지하도 통로(#255) → 이후 도시 구간.

추가 필드(선택): `len`(통로 길이 px), `lamp`(통로 가로등 간격 px, 기본 120), `bend`(`down`/`up`, ㄱ자 꺾이는 방향), `dout`(방에서 나가는 길의 높이 0~1, 클수록 뒤쪽). 첫 방 `dout`=.75, 정사각형 방(#274) `dout`=.82 로 거리를 뒤쪽에 두고 아래로 꺾는다.

## 순서·모양 고치기: `tools/scene_chains.json` 의 `"city"` 배열
배열 순서가 곧 이동 순서다. 한 줄이 한 장면(방 또는 통로).

| 필드 | 뜻 |
|---|---|
| `key` | 이름(번호 고정용). 새 장면은 **아직 안 쓴 key**를 붙인다(예 `cityx15`, `cityp14`). 번호는 `tools/scene_ids.json` 에 한 번 붙으면 바뀌지 않는다. |
| `kind` | `room` 방 / `passage` 통로 |
| `shape` | 방: `square`(정사각형) `wide` `deep` `long`(긴 롱테이크). 통로: `hall`(짧은 복도) `tunnel`(긴 직선) `bend`(ㄱ자) `zig`(지그재그) `switch`(ㄹ자 3차원 계단) |
| `entry`, `epos` | 들어오는 쪽(`L` 왼쪽 / `B` 뒷벽)과 그 위치(0~1) |
| `exit`, `xpos` | 나가는 쪽과 위치(0~1) |
| `gate` | 문(아치) 모양 번호 0~2 (도시 문 3종) |

- 빼려면 줄을 지우고, 끼우려면 줄을 추가한다. 통로와 방은 번갈아 놓는다(통로-방-통로-방…).
- 지금 끼워 둔 것: `cityp10 tunnel`(len 420, lamp 60) → `cityx11 square` → `cityp11 bend`(down) → `cityx12 deep`.

## 방 하나의 연출 고르기: `tools/theme_design.py` 의 `SETS_KEY`
특정 방(key)에 정해 둔 대표 연출. 적은 방은 무작위 대신 이것을 쓰고, 일반 소품은 더 놓지 않는다.
- 지금은 `'cityx01'`(처음 장소) = 인공 수풀 화단(`p_hedgebed`) + 가로등 + 벤치.
- 다른 방도 `'cityx11': S(('p', P.p_bench, 0, 0), ...)` 처럼 한 줄 추가하면 된다. `S()` 안 항목은 `('p', 소품함수, 가로 어긋남, 세로 어긋남)`.
- 쓸 수 있는 도시 소품: `p_hedgebed p_car p_vending p_busstop p_trafficlight p_hydrant p_mailbox p_bike p_manhole p_crosswalk p_bench p_bin` (`tools/render_more.py`).

## 다시 만들기
```
python3 tools/render_strips.py city      # 도시 띠만 다시 그림 (약 10초, 길 막힘이 있으면 '!! 길이 막힘' 출력)
python3 tools/export_web.py              # 번호·시작 위치 갱신 (docs/scene-index.md 도 갱신)
python3 tools/build_single.py            # web/yeoksang.html
```
시작 위치(`#city0`)는 처음 방의 화단 앞이다(`tools/render_strips.py` 의 `spec['start']`).
