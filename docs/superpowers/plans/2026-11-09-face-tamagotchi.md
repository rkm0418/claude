# 얼굴 다마고치 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 사진 속 얼굴을 오려 만화 몸통에 합성해 키우고, 웃긴 장면을 워터마크 이미지로 공유하는 모바일 앱 프로토타입을 만든다.

**Architecture:** Expo(React Native, TypeScript) 앱. 게임 규칙은 UI 없는 순수 함수 모듈(`pet/`)로 두고 Jest로 검증한다. 얼굴 처리, 렌더링, 공유, 알림, 저장은 각자 하나의 모듈이며 화면(expo-router)이 이를 조합한다. 모든 데이터는 기기 내부에만 저장한다.

**Tech Stack:** Expo SDK (최신 안정판), TypeScript, expo-router, jest-expo, @testing-library/react-native, @react-native-async-storage/async-storage, expo-image-picker, expo-image-manipulator, expo-file-system, react-native-view-shot, expo-sharing, expo-notifications, @react-native-ml-kit/face-detection(개발 빌드 전용)

**Spec:** `docs/superpowers/specs/2026-11-09-face-tamagotchi-design.md`

## Global Constraints

- 앱은 `mobile/` 디렉터리에 만든다. 소스는 `mobile/src/{pet,face,render,share,notify,storage}/`, 화면은 `mobile/app/`(expo-router).
- 서버 전송, 계정, 원격 저장은 없다. 원본 사진은 저장하지 않고 오려낸 얼굴만 앱 내부 저장소에 둔다.
- 펫은 죽지 않는다. 방치 시 `sulking`(삐침) 또는 `away`(가출)가 되고 돌아온다.
- 성장 단계는 `egg`, `baby`, `child`, `adult`, `elder` 5개, 상태는 `satiety`, `mood`, `energy`, `cleanliness` 4개, 행동은 `feed`, `play`, `sleep`, `clean` 4개.
- 첫 등록 시 "본인이거나 동의받은 사진만 사용" 확인을 받는다. 공유 이미지에는 워터마크를 넣는다. 설정에서 얼굴 데이터를 전체 삭제할 수 있다.
- 이벤트와 알림 문구에 외모 비하나 혐오 소재를 쓰지 않는다. 웃음은 음식, 잠, 소동 상황에서만 만든다.
- 프로토타입 범위 밖: 눈/입 인식 표정 변형, 배경 자동 제거 고도화, 영상 공유, 서버/모임형, 미니게임, 수익화.
- `pet/`는 React, Expo, 시간 API(`Date.now`)에 직접 의존하지 않는다. 현재 시각과 난수는 인자로 받는다.

## Review Focus

- 기기 시계가 과거로 되돌려짐(`now < lastSeenAt`): 상태가 변하지 않고 크래시도 없어야 한다. (Task 2)
- 몇 주 이상 방치 후 접속: 상태가 0 밑으로 내려가지 않고 `away`에서 복귀 처리되며 앱이 멈추지 않아야 한다. (Task 2, 4)
- 사진에 얼굴이 없거나 여러 명: 오류 없이 수동 영역 지정으로 이어져야 한다. (Task 6)
- 저장된 얼굴 파일이 사라졌거나 저장 데이터가 깨짐: 크래시 대신 자리표시 얼굴과 빈 목록으로 열려야 한다. (Task 5)
- 알림 권한 거부 또는 공유 취소: 게임은 계속 동작하고 오류 팝업이 뜨지 않아야 한다. (Task 9)
- 이름이 비었거나 매우 긴 경우: 빈 이름은 등록을 막고, 긴 이름은 20자로 잘려 화면이 깨지지 않아야 한다. (Task 8)

---

### Task 1: 프로젝트 골격과 테스트 환경

**Files:**
- Create: `mobile/` (Expo TypeScript 템플릿으로 생성), `mobile/jest.config.js`, `mobile/src/pet/types.ts`, `mobile/src/pet/__tests__/types.test.ts`

**Interfaces:**
- Produces (`mobile/src/pet/types.ts`):
  ```ts
  export type Stat = 'satiety' | 'mood' | 'energy' | 'cleanliness';
  export type Action = 'feed' | 'play' | 'sleep' | 'clean';
  export type Stage = 'egg' | 'baby' | 'child' | 'adult' | 'elder';
  export type Status = 'normal' | 'sulking' | 'away';
  export interface Pet {
    id: string; name: string; faceUri: string | null;
    stats: Record<Stat, number>;          // 0..100
    careCounts: Record<Action, number>;
    stage: Stage; status: Status;
    createdAt: number; lastSeenAt: number; // epoch ms
  }
  export const STATS: Stat[]; export const ACTIONS: Action[];
  ```

- [ ] **Step 1: Scaffold.** `npx create-expo-app@latest mobile --template blank-typescript` 후 expo-router, react-native-web, react-dom, @expo/metro-runtime, jest-expo, @testing-library/react-native를 설치하고 `package.json`에 `"test": "jest"`를 추가한다. 진입점은 expo-router(`"main": "expo-router/entry"`)로 바꾼다.
- [ ] **Step 2: Write failing test** `types.test.ts`: `STATS`는 정확히 `['satiety','mood','energy','cleanliness']`, `ACTIONS`는 `['feed','play','sleep','clean']`.
- [ ] **Step 3: Run** `cd mobile && npx jest` → FAIL (모듈 없음).
- [ ] **Step 4: Implement** 위 Interfaces의 `types.ts`.
- [ ] **Step 5: Run** `npx jest` → PASS. `npx expo export --platform web`이 성공하는지도 확인한다.
- [ ] **Step 6: Commit** `git add mobile && git commit -m "chore: scaffold Expo app with jest"`

---

### Task 2: 펫 생성과 시간 경과 (`pet/time.ts`)

**Files:**
- Create: `mobile/src/pet/time.ts`, `mobile/src/pet/__tests__/time.test.ts`

**Interfaces:**
- Consumes: Task 1의 `Pet`, `Stat`.
- Produces:
  ```ts
  export const DECAY_PER_HOUR: Record<Stat, number>; // satiety 12, mood 8, energy 6, cleanliness 5
  export function createPet(input: { id: string; name: string; faceUri: string | null }, now: number): Pet;
  export function applyElapsed(pet: Pet, now: number): Pet; // lastSeenAt = max(lastSeenAt, now)
  ```
- `createPet`: 모든 상태 80, `careCounts` 전부 0, `stage: 'egg'`, `status: 'normal'`, `createdAt = lastSeenAt = now`.

- [ ] **Step 1: Write failing tests**
  - `createPet`은 위 초기값을 가진다.
  - `applyElapsed(pet80, +1h)` → satiety 68, mood 72, energy 74, cleanliness 75.
  - 100시간 경과 → 모든 상태가 정확히 0 (음수 없음).
  - `now < lastSeenAt`(시계 역행) → 상태 불변, `lastSeenAt` 불변.
  - 입력 `pet`을 변경하지 않는다(새 객체 반환).
- [ ] **Step 2: Run** `npx jest time` → FAIL.
- [ ] **Step 3: Implement** `time.ts`. 경과 시간은 시간 단위 실수로 계산하고 `Math.max(0, …)`로 내린다. `status`는 건드리지 않는다(Task 4 담당).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(pet): creation and elapsed-time decay`

---

### Task 3: 행동과 반응 (`pet/actions.ts`)

**Files:**
- Create: `mobile/src/pet/actions.ts`, `mobile/src/pet/__tests__/actions.test.ts`

**Interfaces:**
- Consumes: `Pet`, `Action`.
- Produces:
  ```ts
  export type ReactionId =
    | 'happy' | 'fire_breath' | 'bloated' | 'sleepy' | 'sweat' | 'cry' | 'hearts' | 'sulk' | 'none';
  export function applyAction(pet: Pet, action: Action, rng: () => number): { pet: Pet; reaction: ReactionId };
  ```
- 규칙: feed satiety +30, play mood +25 / energy −10, sleep energy +40, clean cleanliness +50. 모든 값은 0..100으로 clamp. `careCounts[action]`는 +1. `stage === 'egg'`가 아닐 때만 반응을 만든다(알은 `none`).
- 반응 선택: feed 후 satiety가 clamp 전에 100을 넘으면 `bloated`. 그 외 feed는 `rng() < 0.3`이면 `fire_breath`, 아니면 `happy`. play는 energy가 20 미만이 되면 `sweat`, 아니면 `hearts`. sleep은 `sleepy`. clean은 `happy`. `status`가 `away`이면 행동은 무시하고 `none`을 반환한다. `sulking`이면 행동 후 `normal`로 풀리고 `cry` 반응.

- [ ] **Step 1: Write failing tests** 위 규칙을 한 줄씩 단언한다. 특히 satiety 90에서 feed → satiety 100(clamp)·`bloated`, rng 0.1이면 `fire_breath`, rng 0.9이면 `happy`, `away`는 불변, egg는 `none`.
- [ ] **Step 2: Run** `npx jest actions` → FAIL.
- [ ] **Step 3: Implement** `actions.ts`. 반응 이후 stage 갱신은 Task 4에서 연결한다.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(pet): care actions and reactions`

---

### Task 4: 성장, 방치, 이벤트 (`pet/growth.ts`, `pet/neglect.ts`)

**Files:**
- Create: `mobile/src/pet/growth.ts`, `mobile/src/pet/neglect.ts`, `mobile/src/pet/index.ts`, `mobile/src/pet/__tests__/growth.test.ts`, `mobile/src/pet/__tests__/neglect.test.ts`

**Interfaces:**
- Consumes: Task 2의 `applyElapsed`, Task 3의 `applyAction`.
- Produces:
  ```ts
  export function stageFor(totalCare: number): Stage;       // 0-2 egg, 3-19 baby, 20-59 child, 60-149 adult, 150+ elder
  export function bodyTypeFor(careCounts: Record<Action, number>): Action; // 최다 행동, 동률이면 feed>play>sleep>clean 순
  export function settle(pet: Pet, now: number): { pet: Pet; event: 'none' | 'sulked' | 'ran_away' | 'returned' };
  export function stepPet(pet: Pet, action: Action, now: number, rng: () => number): { pet: Pet; reaction: ReactionId };
  ```
- `settle`: `applyElapsed` 후 방치 판정. `lastSeenAt`과 `now`의 간격이 24시간 이상이면 `status='away'`, event `ran_away`. 이미 `away`였다면 접속 시 `normal`로 복귀하고 event `returned`(상태는 전부 50으로 리셋). 어떤 상태가 0이고 간격이 6시간 이상이면 `sulking`, event `sulked`. 그 외 `none`.
- `stepPet`: `settle`로 접속 처리 → `applyAction` → `stage = stageFor(careCounts 합)`로 갱신. `pet/index.ts`는 위 함수들과 타입을 재노출한다.

- [ ] **Step 1: Write failing tests**
  - `stageFor` 경계값: 2→egg, 3→baby, 19→baby, 20→child, 60→adult, 150→elder.
  - `bodyTypeFor` 동률 처리와 단독 최다.
  - `settle`: 7시간 + 어떤 상태 0 → `sulking`·`sulked`. 25시간 → `away`·`ran_away`. `away` 상태에서 재접속 → `normal`·`returned`·상태 전부 50. 3주(504시간) 경과도 정상 반환하고 상태가 0..100 안에 있다.
  - `stepPet`: 알 상태에서 행동 3번 → `stage === 'baby'`.
- [ ] **Step 2: Run** `npx jest growth neglect` → FAIL.
- [ ] **Step 3: Implement** 두 파일과 `index.ts`.
- [ ] **Step 4: Run** `npx jest` (전체) → PASS.
- [ ] **Step 5: Commit** `feat(pet): growth stages, neglect and return`

---

### Task 5: 저장소 (`storage/`)

**Files:**
- Create: `mobile/src/storage/petRepo.ts`, `mobile/src/storage/faceFiles.ts`, `mobile/src/storage/__tests__/petRepo.test.ts`

**Interfaces:**
- Consumes: `Pet`.
- Produces:
  ```ts
  export async function loadPets(): Promise<Pet[]>;     // 깨진 JSON이면 []
  export async function savePet(pet: Pet): Promise<void>; // id 기준 upsert
  export async function deleteAllData(): Promise<void>;  // 펫 목록과 얼굴 파일 전부 삭제
  // faceFiles.ts
  export async function saveFace(petId: string, tempUri: string): Promise<string>; // 앱 문서 폴더로 복사 후 새 uri 반환
  export async function faceExists(uri: string | null): Promise<boolean>;
  ```
- 저장 키는 `pets.v1`.

- [ ] **Step 1: Write failing tests** (AsyncStorage jest mock 사용): 저장 후 로드 시 동일. 같은 id를 저장하면 덮어쓴다. 저장값이 `"{not json"`이면 `loadPets()`는 `[]`. `deleteAllData` 후 `loadPets()`는 `[]`.
- [ ] **Step 2: Run** `npx jest petRepo` → FAIL.
- [ ] **Step 3: Implement** `petRepo.ts`는 AsyncStorage에 JSON 배열로 저장하고 파싱 실패 시 빈 배열을 반환. `faceFiles.ts`는 expo-file-system의 문서 폴더(`faces/<petId>.png`)를 쓰며 `deleteAllData`가 이 폴더를 지운다.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(storage): local pet repository and face files`

---

### Task 6: 얼굴 검출과 오려내기 (`face/`)

**Files:**
- Create: `mobile/src/face/types.ts`, `mobile/src/face/region.ts`, `mobile/src/face/detect.ts`, `mobile/src/face/crop.ts`, `mobile/src/face/__tests__/region.test.ts`

**Interfaces:**
- Produces:
  ```ts
  export interface Box { x: number; y: number; width: number; height: number } // 픽셀
  export type DetectResult =
    | { kind: 'one'; box: Box }
    | { kind: 'many'; boxes: Box[] }
    | { kind: 'none' }
    | { kind: 'unsupported' };                        // 웹 등 검출 불가 환경
  export function detectFaces(photoUri: string): Promise<DetectResult>;
  export function squareAround(box: Box, imageW: number, imageH: number, padding?: number): Box; // padding 기본 0.25
  export function clampBox(box: Box, imageW: number, imageH: number): Box;
  export function cropFace(photoUri: string, box: Box): Promise<string>; // 임시 PNG uri
  ```

- [ ] **Step 1: Write failing tests** (`region.test.ts`, 순수 함수만): `squareAround`는 정사각형을 반환하고 중심이 원본 박스 중심과 같다. 박스가 이미지 가장자리에 걸치면 `clampBox`로 이미지 안에 들어온다. 이미지보다 큰 박스는 이미지 크기로 줄어든다.
- [ ] **Step 2: Run** `npx jest region` → FAIL.
- [ ] **Step 3: Implement** `region.ts`. `detect.ts`는 네이티브에서 ML Kit 검출을 호출해 얼굴 수에 따라 `one/many/none`을 반환하고, 웹이나 모듈 미탑재 시 예외 없이 `unsupported`를 반환한다. `crop.ts`는 expo-image-manipulator로 `Box`를 자르고 256×256으로 리사이즈한다(타원 마스크는 렌더 단계에서 적용).
- [ ] **Step 4: Run** → PASS. 검출기와 오려내기는 Task 11에서 실제 환경으로 확인한다.
- [ ] **Step 5: Commit** `feat(face): detection adapter, region math, crop`

---

### Task 7: 렌더링 (`render/`)

**Files:**
- Create: `mobile/src/render/expression.ts`, `mobile/src/render/PetView.tsx`, `mobile/src/render/bodies.ts`, `mobile/src/render/__tests__/expression.test.ts`

**Interfaces:**
- Consumes: `Pet`, `ReactionId`, `bodyTypeFor`.
- Produces:
  ```ts
  export interface Expression { scale: number; rotateDeg: number; tint: string | null; stickers: string[] } // stickers는 이모지
  export function expressionFor(pet: Pet, reaction: ReactionId): Expression;
  export function PetView(props: { pet: Pet; reaction: ReactionId; size?: number }): JSX.Element;
  ```
- `expressionFor` 규칙: `bloated` → scale 1.4, `fire_breath` → tint `#ff5a3c`와 스티커 `['🔥']`, `cry` → `['💧']`, `sweat` → `['💦']`, `hearts` → `['💕']`, `sleepy` → `['💤']`, `sulk` → rotateDeg −10과 `['💢']`, 그 외 기본값(scale 1, rotateDeg 0, tint null, stickers []). 상태가 하나라도 20 미만이면 기본 반응이 `none`일 때 `sweat` 표정을 적용한다.
- `bodies.ts`: 성장 단계 5개 × 몸통 종류 4개에 해당하는 몸통 정의(이모지/도형 기반 플레이스홀더)와 단계별 얼굴 앵커(`x, y, size` 비율). 알은 얼굴 없이 알 모양만 그린다.
- `PetView`: 몸통 위에 얼굴 이미지를 원형 마스크로 얹고 `Expression`을 적용한다. `faceUri`가 없거나 파일이 없으면 자리표시 얼굴(😶)을 그린다.

- [ ] **Step 1: Write failing tests** `expressionFor`의 위 규칙 전부, 특히 `bloated`는 scale 1.4, `fire_breath`의 tint, energy가 10이고 반응이 `none`이면 `💦`.
- [ ] **Step 2: Run** `npx jest expression` → FAIL.
- [ ] **Step 3: Implement** `expression.ts`, `bodies.ts`, `PetView.tsx`. 애니메이션은 `Animated`로 scale과 rotate를 200ms 보간한다.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat(render): expressions and pet view`

---

### Task 8: 화면 - 온보딩, 홈, 도감, 설정

**Files:**
- Create: `mobile/app/_layout.tsx`, `mobile/app/index.tsx`(홈), `mobile/app/onboarding.tsx`, `mobile/app/dex.tsx`, `mobile/app/settings.tsx`, `mobile/src/state/usePets.ts`, `mobile/app/__tests__/onboarding.test.tsx`, `mobile/app/__tests__/home.test.tsx`

**Interfaces:**
- Consumes: `loadPets`, `savePet`, `deleteAllData`, `saveFace`, `detectFaces`, `cropFace`, `squareAround`, `createPet`, `stepPet`, `settle`, `PetView`.
- Produces: `usePets(): { pets: Pet[]; current: Pet | null; select(id: string): void; register(name: string, faceUri: string | null): Promise<void>; act(action: Action): ReactionId; wipe(): Promise<void> }`. `act`는 `stepPet(current, action, Date.now(), Math.random)`를 호출하고 저장한다.

**화면 동작**
- 앱 시작 시 `loadPets` 후 모든 펫에 `settle`을 적용한다. 펫이 없으면 온보딩으로 이동한다.
- 온보딩: 동의 체크 → 사진 선택(expo-image-picker) → `detectFaces`. `one`이면 바로 미리보기, `many`면 박스를 눌러 선택, `none`/`unsupported`면 사진 위에서 정사각형 영역을 직접 지정(드래그와 확대/축소) → `cropFace` → 이름 입력 → `register`. 동의를 체크하지 않으면 다음 단계 버튼이 비활성이다. 이름은 앞뒤 공백을 제거하고 비어 있으면 등록 버튼이 비활성이며 20자로 잘린다.
- 홈: `PetView`, 게이지 4개(0..100), 행동 버튼 4개. `away`이면 "가출 중" 안내와 함께 버튼이 비활성이고, 접속 시 복귀하면 "돌아왔어요" 토스트를 띄운다.
- 도감: 펫 목록과 단계 표시, 선택하면 홈이 그 펫으로 바뀌고, "새 얼굴 추가"는 온보딩으로 이동.
- 설정: 알림 토글, "얼굴 데이터 전체 삭제"(확인 대화상자 후 `wipe`), 안내문.

- [ ] **Step 1: Write failing tests**
  - `onboarding.test.tsx`: 동의 체크 전에는 "다음" 비활성. 이름 `"  "`이면 등록 비활성. 25자 이름은 20자로 저장된다.
  - `home.test.tsx`: 먹이기 버튼을 누르면 satiety 게이지가 증가한다. `status: 'away'` 펫이면 모든 행동 버튼이 비활성이다.
- [ ] **Step 2: Run** `npx jest app` → FAIL.
- [ ] **Step 3: Implement** 위 화면과 `usePets`. 저장된 `faceUri` 파일이 없으면(`faceExists` false) `PetView`가 자리표시 얼굴을 쓰도록 `faceUri`를 `null`로 넘긴다.
- [ ] **Step 4: Run** `npx jest` → PASS.
- [ ] **Step 5: Commit** `feat(app): onboarding, home, dex, settings screens`

---

### Task 9: 공유와 알림 (`share/`, `notify/`)

**Files:**
- Create: `mobile/src/share/captureShare.ts`, `mobile/src/share/Watermark.tsx`, `mobile/src/notify/schedule.ts`, `mobile/src/notify/messages.ts`, `mobile/src/notify/__tests__/schedule.test.ts`
- Modify: `mobile/app/index.tsx` (공유 버튼, 알림 예약 호출)

**Interfaces:**
- Consumes: `Pet`, `DECAY_PER_HOUR`.
- Produces:
  ```ts
  export async function captureAndShare(viewRef: React.RefObject<unknown>): Promise<'shared' | 'cancelled' | 'unavailable'>;
  export function nextAlertAt(pet: Pet): number | null;  // 가장 먼저 20 미만이 될 시각(epoch ms), 이미 20 미만이면 now가 아닌 null
  export function alertMessage(pet: Pet, stat: Stat): string; // 예: "<이름> 얼굴이 배고파합니다"
  export async function scheduleAlert(pet: Pet): Promise<void>; // 권한 거부 시 조용히 반환
  ```
- `Watermark`는 캡처 영역 하단에 앱 이름을 고정 문구로 표시한다. 공유 버튼은 이벤트 반응이 `none`이 아닐 때 홈에 나타난다.

- [ ] **Step 1: Write failing tests** (`schedule.test.ts`): satiety 80이면 `nextAlertAt`은 `lastSeenAt` + 5시간(80→20이 되는 데 60/12 = 5시간). 모든 상태가 이미 20 미만이면 `null`. `alertMessage`는 펫 이름을 포함하고 비하 표현 없이 상태별 고정 문구(satiety는 "배고파합니다")를 쓴다.
- [ ] **Step 2: Run** `npx jest schedule` → FAIL.
- [ ] **Step 3: Implement** `schedule.ts`와 `messages.ts`. `scheduleAlert`는 기존 예약을 취소하고 새로 예약하며, 권한이 거부되면 예외 없이 반환한다. `captureAndShare`는 view-shot으로 캡처 후 expo-sharing 호출, 사용자가 취소하면 `cancelled`, 공유 불가 환경이면 `unavailable`을 반환하고 예외를 던지지 않는다. 홈에서 행동할 때마다 `scheduleAlert(current)`를 호출한다.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: share capture with watermark and local alerts`

---

### Task 10: 웹 미리보기 검증

**Files:**
- Create: `mobile/scripts/smoke-web.mjs`
- Modify: `mobile/package.json` (`"smoke": "node scripts/smoke-web.mjs"`)

**Interfaces:**
- Consumes: 웹으로 export된 앱 전체.

- [ ] **Step 1: Write the smoke script.** Playwright로 `npx expo start --web`를 띄운 뒤: 온보딩 진입 → 동의 체크 → 샘플 이미지 파일 업로드 → 수동 영역 지정 → 이름 `테스트` 입력 → 등록 → 홈에서 먹이기를 3번 눌러 알이 아기로 바뀌는지 확인 → 스크린샷 저장.
- [ ] **Step 2: Run** `npm run smoke` → 기대: 종료 코드 0, 스크린샷에 펫과 게이지 4개가 보인다. 실패하면 원인을 수정하고 다시 실행한다.
- [ ] **Step 3: Run** `npx jest` 전체와 `npx tsc --noEmit` → 둘 다 통과.
- [ ] **Step 4: Commit** `test: web smoke check`

---

### Task 11: 실기기 확인 안내 문서

**Files:**
- Create: `mobile/README.md`

- [ ] **Step 1: Write** 실행 방법(`npx expo start`, 웹 `--web`), 얼굴 검출은 개발 빌드(`npx expo run:android` / `run:ios`)에서만 동작하고 웹과 Expo Go에서는 수동 지정으로 대체됨, 알림과 공유는 실기기에서 확인해야 한다는 점을 적는다.
- [ ] **Step 2: Commit** `docs: how to run and what needs a device`

---

## Self-Review 결과

- **Spec 커버리지:** 핵심 루프(Task 2-4, 8), 성장 5단계와 죽음 없음(Task 4), 얼굴 파이프라인과 수동 대체(Task 6, 8), 표정과 스티커(Task 7), 안전장치 — 동의, 워터마크, 비하 금지, 전체 삭제(Task 8, 9), 5개 화면(Task 8), 모듈 6개(Task 2-9), 시간 처리와 알림 예약(Task 2, 4, 9), 테스트 방침(Task 2-4 단위 테스트, Task 10 웹 확인), 성공 기준(Task 10). 빠진 항목 없음.
- **타입 일관성:** `Pet`, `ReactionId`, `stepPet`, `settle`, `expressionFor`, `captureAndShare` 이름이 정의 Task와 사용 Task에서 일치한다.
- **스펙에 없어서 이 계획이 정한 값(검토 대상):** 상태 감소율(시간당 12/8/6/5), 행동 효과량, 성장 경계(3/20/60/150회), 삐침 6시간·가출 24시간 기준, 불 뿜기 확률 30%, 알림 기준 20.
- **위험:** 얼굴 검출(ML Kit)은 웹과 Expo Go에서 동작하지 않으므로 실기기 개발 빌드에서만 검증할 수 있다. 이 환경에서는 수동 지정 경로까지만 자동 검증된다.
