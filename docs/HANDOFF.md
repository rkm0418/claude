# 이어받는 사람(또는 다른 모델)을 위한 안내

「역상」: 7살 아이가 주인공인 언더테일풍 도트 게임(약 90분, 가벼운 스릴러). 전체 설계는
`docs/superpowers/specs/2026-11-14-stopped-clock-design.md` (§13 이야기 구조, §17~§21 최근 확정 사항)를 먼저 읽는다.

## 작업 규칙
- 사용자는 짧고 오타가 많은 한국어로 지시하고, 스케치·주석 이미지를 자주 보낸다. **추측하지 말고 말한 그대로** 한다. 정말 모호할 때만 짧게 한 번 묻는다.
- 그림은 손으로 PNG를 고치지 않는다. **생성 스크립트(`tools/*.py`)를 고치고 다시 실행**한다. 결과 이미지는 `maps/out/`, 스프라이트는 `art/out/sprites/`.
- 바꿀 때마다 결과 이미지를 직접 열어 확인하고, 커밋·푸시한다(브랜치 `ccr-31c677f6-jf9v7k`). PR은 요청이 있을 때만.
- 도우미 캐릭터 눈 규칙: 동그란 점 눈, 하이라이트·눈썹·속눈썹 없음, 입은 일자. 주인공은 얼굴 없음. 외곽선은 가늘게.
- 조현병이라는 낱말은 게임 글에 쓰지 않는다. 착지 장면과 가족을 해치는 장면은 그리지 않는다.

## 그림 자산과 만드는 법
| 무엇 | 원본 | 만드는 명령 | 결과 |
|---|---|---|---|
| 글자 격자 스프라이트·타일 | `art/objects.txt`, `art/tiles.txt`, `art/palette.txt` | `python3 tools/render.py` | `art/out/sprites/*.png` |
| 입체 가구(상자) | `art/boxes.txt` | `python3 tools/boxes.py` | 같은 폴더 |
| 주인공 8방향(서기+걷기4) | `tools/gen_child_8dir.py` | 실행 | `art/out/sprites/child8/` + `manifest.json`, `maps/out/child_8dir_sheet.png`, `child_8dir_walk.gif` |
| 주인공 뒷모습 동작(걷기·밀기·잡기·발 올리기·매달리기) | `tools/gen_child_back.py` (`pose()`, `hold()`, `limb()`) | 실행 | `art/out/sprites/child_b_*.png`, `maps/out/child_back_poses.png` |
| 괴물·조력자 방향별 움직임 | `tools/gen_actor_dirs.py` | 실행 | `art/out/sprites/actors/` + `manifest.json`, `maps/out/actors_sheet.png` |
| 괴물의 기괴한 움직임(경련 걸음·고개 꺾임·늘어남·끊김·기어옴) | `tools/gen_chaser_creepy.py` | 실행 | `art/out/sprites/actors/chaser_<방향>_<동작><번호>.png`, `chaser_creepy.json`(장당 시간), `maps/out/chaser_creepy.gif` |
| 쇠 의자·탁자 | `tools/gen_iron_chair.py [배율 이름]`, `tools/gen_iron_table.py [지름 높이 이름]` | 실행 | `art/objects.txt` 에 기록 |
| 숲 타일·사물·횃불·그루터기 | `tools/gen_forest_assets.py` (+ `tools/forest_draw.py`: 잎·둥치·전나무) | 실행 | `art/forest/*.png` |

스프라이트 규칙: 기준점은 **아래 가운데(발)**. 주인공 24×38(위 여유 4칸 포함 24×42), 방·복도 맵에서는 절반 크기(12×19, `child_s*`). 걷기는 `w1→w2→w3→w4` 반복, 초당 6장.
방향 이름: `d` 아래(정면) `u` 위(뒷모습) `l` `r` 옆, `dl dr ul ur` 대각. 왼쪽 계열은 오른쪽의 좌우 반전.

## 맵·배경
| 장면 | 명령 | 결과 |
|---|---|---|
| 아이 방 / 복도(아파트, 사선 시점) | `python3 tools/render_room.py maps/2_child_room_kr.txt 5`, `maps/3_corridor_kr.txt` | `maps/out/*_oblique.png` |
| 같은 방 / 복도(숲 버전) | `maps/2_child_room_forest.txt`, `maps/3_corridor_forest.txt` | 같음 |
| 베란다(게임 모드 사선) | `python3 tools/render_balcony_oblique.py` | `maps/out/4_balcony_oblique*.png` |
| 베란다(1인칭 정면, 컷신용) | `python3 tools/render_balcony2d.py` (`scene(chair_pos, actors)`) | `maps/out/4_balcony_2d*.png` |
| 숲 베란다(수미상관) | `python3 tools/render_balcony_forest.py` (`scene(actors, flick)`) | `maps/out/4_balcony_forest*.png` |

화면 규격: 논리 해상도 320×240, 그림은 2배 표시(§18). 맵 파일 문법과 헤더 옵션은 `tools/render_room.py` 주석과 설계 문서 §17.

## 컷신
- 프롤로그 추락(1인칭): `python3 tools/gen_cutscene_prologue.py` → `maps/out/prologue_cutscene.gif`, `_sheet.png` (순서는 §20).
- 수미상관(숲, 게임 모드): `python3 tools/gen_cutscene_ending.py` → `maps/out/ending_cutscene.gif`. 추격자는 꺼져 있다(스크립트의 `CD[0] = 0.0` 주석을 살리면 나타난다).
- 두 스크립트 모두 `add(상태, 프레임 수, 라벨)` 로 장면을 쌓는다. 배우는 `(화면x, 발y, 스프라이트, 'front'|'behind', 기울기)`.

## 소리·글
- 라디오 소리 초안: `python3 tools/gen_radio.py` → `audio/radio_draft.wav|mp3` (§13.6).
- 책상 위의 시: `docs/content/poem_on_desk.md`. 신화 모티프(헤라클레스의 광기 채택): `docs/content/myth_motifs.md`, §21.

## 품질 메모(임시인 것)
- `gen_actor_dirs.py`: 조력자는 캐릭터별 좌표표(`SPECS`)로 뒷모습·옆모습·걷기를 만든다(아이와 같은 방식). 괴물 옆모습은 정면을 눌러 좁힌 **임시 품질**이고, 걷기는 `s1~s8` 8장이다. 미리보기 `maps/out/actors_walk.gif`.
- 주인공 대각 4방향은 정면/뒷모습을 조금 고친 것이라 차이가 작다. 옆모습 다리·팔도 단순하다.
- 컷신의 다리 동작은 다리 그림을 위로 옮기는 방식이다(관절 방식 아님). 제목 글꼴은 임시.

## 남은 일
1. 1장 식탁방을 사선 시점으로 전환, 거실 맵.
2. 장면별 라디오 사물 배치(R1~R7), 조력자 단계 변화(귀여움 → 수상함 → 기괴함), 조력자와 주인공의 맵 크기 통일.
3. 숲 버전 1인칭 베란다(프롤로그와 같은 구도의 수미상관을 원할 때), 숲 방·복도의 숲 느낌 강화.
4. 내용 주의 화면, 반대편 장(부모 시점, 약 10분), 엔딩, 엔진 선택.
5. 설계 문서는 아직 "승인 대기" 상태. 승인되면 구현 계획을 쓴다.

## 웹 엔진 시험판 (터치 이동)
- 실행: `python3 tools/render_country_house.py && python3 tools/export_web.py` 뒤 `web/index.html` 을 브라우저로 연다(서버 불필요).
- 구조와 규칙은 설계 문서 §23. 새 장면을 넣으려면 렌더러가 `그림 + 깊이 지도 + {W, D, X0, Y0, rects, exits}` 를 내보내게 하고 `export_web.py` 에 추가한다.
- 오른쪽 위 "경로 보기" 버튼: 걸을 수 있는 칸(초록)·막힌 칸(빨강)·문 자리(노랑)·현재 경로(흰 선).
