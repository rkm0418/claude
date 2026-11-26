# 하루잠금 1단계 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 하루 한도, 요일별 설정, 즉시 잠금, 설정 안내, 해제 방지, 비상 해제가 동작하는 Galaxy S25+용 시험판과 정식판을 만든다.

**Architecture:** 모든 판단(하루 경계, 설정 변경, 시간 측정, 잠금 여부)은 순수 Kotlin 모듈 `:core`에 둔다. `:app`은 안드로이드 이벤트를 읽어 `:core`에 넘기고, 결과를 DevicePolicyManager로 실행한다. 비상 해제는 별도 프로세스에서 자체 파일만으로 동작한다.

**Tech Stack:** Kotlin 2.0.21, AGP 8.13.0, Gradle 8.14.3, JUnit 4.13.2, Android 기본 View (외부 UI 라이브러리 없음)

**Spec:** 설계 https://claude.ai/artifact/KArgX3gkZo6ReKxA8A9Vh1 · 디자인 요청서 https://claude.ai/artifact/HZbcBtaM6nrLzWwbwkPx1d

## Global Constraints

- `applicationId = "app.harulock"`, `minSdk = 30`, `compileSdk = targetSdk = 36`, JVM 17, 앱 이름 "하루잠금"
- 한도 1~1440분, 시작 시각 0~1439분(자정 기준), 즉시 잠금 1~1440분
- 배경화면(홈), 허용앱, 이 앱, 잠금 화면에서는 시간이 줄지 않는다
- 긴급전화와 기본 전화 앱은 절대 정지하지 않는다
- 느슨해지는 변경(한도 늘리기, 허용앱 추가, 시작 시각 변경)은 다음 초기화부터
- 예고 알림 10, 5, 1분. 상시 알림 문구는 "하루잠금 실행 중"(남은 시간 표시 없음)
- 레이아웃 파일명과 요소 ID는 디자인 요청서의 "납품 형식" 표를 그대로 쓴다
- debug = 시험판(`testOnly`), release = 정식판. 둘 다 debug 키로 서명한다
- 2·3단계 기능은 만들지 않는다
- 작업공간에는 Android SDK가 없다. Task 1~7은 여기서 시험하고, Task 8~13은 PC(Android Studio)와 실기기에서 확인한다

## 계획에서 새로 정한 것 (확인 필요)

- 비상 해제 확인 가능 시간은 24시간이고 지나면 만료된다 (요청만 해 두고 나중에 바로 푸는 우회 방지)
- 정식판 업데이트는 비상 해제 후 재설치한다
- 시험판에서 정식판으로 갈 때는 PC로 해제, 삭제, 설치, 재설정한다
- 저장 상태가 모두 손상되면 잠금을 풀고 재설정을 안내한다

## Review Focus

1. 휴대폰이 며칠 꺼졌다 켜짐: 한 번만 초기화되고 대기 중 변경이 적용된다 (Task 4)
2. 재부팅 뒤 시계가 과거: 초기화와 해제 대기가 앞당겨지지 않는다 (Task 5)
3. 저장 상태 손상: 백업을 쓰고, 둘 다 손상이면 영구 잠김 없이 풀린다 (Task 6, 8)
4. 분할 화면에 허용앱과 일반 앱: 시간이 줄어든다 (Task 3)
5. 기본 전화·홈·키보드 앱을 바꿈: 새 앱도 정지되지 않는다 (Task 7, 9)

---

## 파일 구조

```
settings.gradle.kts, build.gradle.kts, tools/test-core.sh
core/src/main/kotlin/app/harulock/core/
  Model.kt DayClock.kt SettingsRules.kt UsageMeter.kt Engine.kt TrustedClock.kt EmergencyRelease.kt StateCodec.kt Policy.kt
core/src/test/kotlin/app/harulock/core/  (파일별 *Test.kt, Fixtures.kt)
app/src/main/kotlin/app/harulock/
  admin/{AdminReceiver,Guard,Enforcer}.kt
  data/{StateStore,DeviceInfo,UsageReader,Permissions}.kt
  service/{LockService,Controller,Receivers,SettingsWatchService}.kt
  ui/{Main,Settings,AllowedApps,Setup,Release}Activity.kt, InstantLockDialog.kt
app/src/debug/AndroidManifest.xml
docs/SETUP.md, docs/TEST.md
```

---

### Task 1: 뼈대와 하루 경계

**Files:** Create `settings.gradle.kts`(`:core`만 포함), `core/build.gradle.kts`, `tools/test-core.sh`, `Model.kt`, `DayClock.kt`, `Fixtures.kt`, `DayClockTest.kt`

**Interfaces — Produces:**
```kotlin
data class DayRule(val limitMinutes: Int, val startMinute: Int)          // 범위 밖이면 IllegalArgumentException
data class Settings(val week: Map<DayOfWeek, DayRule>, val allowed: Set<String>) // 7요일 필수
data class Period(val day: DayOfWeek, val start: Instant, val end: Instant)
object DayClock {
  fun periodAt(now: Instant, week: Map<DayOfWeek, DayRule>, zone: ZoneId): Period
  fun firstStartAtOrAfter(t: Instant, week: Map<DayOfWeek, DayRule>, zone: ZoneId): Instant
}
// Fixtures.kt
val SEOUL: ZoneId
fun at(local: String): Instant                       // "2026-11-26T05:00", 서울 기준
fun week(limit: Int = 120, start: Int = 300): Map<DayOfWeek, DayRule>
```

- [ ] **Step 1: `git init` 후 테스트 스크립트 작성**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
L=${GRADLE_LIB:-/opt/gradle/lib}; out=$(mktemp -d)
CP=$(ls $L/kotlin-{compiler-embeddable,stdlib,script-runtime,reflect,daemon-embeddable}-*.jar $L/trove4j-*.jar $L/kotlinx-coroutines-core-jvm-*.jar $L/annotations-*.jar | paste -sd:)
TCP="$(ls $L/kotlin-stdlib-2*.jar):$L/junit-4.13.2.jar:$L/hamcrest-core-1.3.jar"
java -cp "$CP" org.jetbrains.kotlin.cli.jvm.K2JVMCompiler -no-stdlib -no-reflect -classpath "$TCP" -d "$out" core/src
classes=$(cd "$out" && find . -name '*Test.class' | sed 's|^\./||; s|\.class$||; s|/|.|g')
java -cp "$out:$TCP" org.junit.runner.JUnitCore $classes
```

- [ ] **Step 2: 실패하는 테스트 작성**

```kotlin
@Test fun beforeStartBelongsToPreviousDay() = assertEquals(
  Period(WEDNESDAY, at("2026-11-25T05:00"), at("2026-11-26T05:00")),
  DayClock.periodAt(at("2026-11-26T04:59"), week(), SEOUL))
@Test fun startInstantOpensNewDay() =
  assertEquals(THURSDAY, DayClock.periodAt(at("2026-11-26T05:00"), week(), SEOUL).day)
@Test fun weekdayStartsCanDiffer() = assertEquals(
  Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-28T08:00")),
  DayClock.periodAt(at("2026-11-28T07:59"), week() + (SATURDAY to DayRule(120, 480)), SEOUL))
@Test fun firstStartIncludesExactMatch() =
  assertEquals(at("2026-11-27T05:00"), DayClock.firstStartAtOrAfter(at("2026-11-27T05:00"), week(), SEOUL))
```

- [ ] **Step 3:** `bash tools/test-core.sh` → 컴파일 실패 확인
- [ ] **Step 4:** `Model.kt`, `DayClock.kt` 구현
- [ ] **Step 5:** `bash tools/test-core.sh` → `OK (4 tests)`
- [ ] **Step 6:** `git add -A && git commit -m "feat: day boundary"`

### Task 2: 설정 변경 규칙

**Files:** Create `SettingsRules.kt`, `SettingsRulesTest.kt`

**Interfaces — Produces:** `data class Change(val active: Settings, val pending: Settings?)`, `SettingsRules.request(active: Settings, requested: Settings, armed: Boolean): Change`

규칙: 잠금 시작 전에는 즉시 전부 적용. 이후 `active`는 요일별 한도의 작은 값, 기존 시작 시각, 허용앱 교집합. `requested`가 그 결과와 다르면 `pending = requested`.

- [ ] **Step 1: 테스트**

```kotlin
val base = Settings(week(120), setOf("a", "b"))
@Test fun looserParts_wait() {
  val req = Settings(week(180), setOf("a", "c"))
  assertEquals(Change(Settings(week(120), setOf("a")), req), SettingsRules.request(base, req, true))
}
@Test fun stricter_isImmediate() {
  val req = Settings(week(60), setOf("a"))
  assertEquals(Change(req, null), SettingsRules.request(base, req, true))
}
@Test fun startChange_waits() {
  val c = SettingsRules.request(base, base.copy(week = week(120, 240)), true)
  assertEquals(base, c.active); assertEquals(240, c.pending!!.week[MONDAY]!!.startMinute)
}
@Test fun unarmed_isImmediate() {
  val req = Settings(week(600), setOf("z"))
  assertEquals(Change(req, null), SettingsRules.request(base, req, false))
}
```

- [ ] **Step 2:** 실패 확인 → **Step 3:** 구현 → **Step 4:** `OK (8 tests)` → **Step 5:** commit `feat: settings change rules`

### Task 3: 사용 시간 측정

**Files:** Create `UsageMeter.kt`, `UsageMeterTest.kt`

**Interfaces — Produces:**
```kotlin
sealed interface UsageEvent { val at: Instant
  data class Resumed(override val at: Instant, val pkg: String, val activity: String) : UsageEvent
  data class Paused(override val at: Instant, val pkg: String, val activity: String) : UsageEvent
  data class Screen(override val at: Instant, val on: Boolean) : UsageEvent
  data class Keyguard(override val at: Instant, val shown: Boolean) : UsageEvent
  data class Restart(override val at: Instant) : UsageEvent }
data class MeterState(val countedUntil: Instant, val usedMillis: Long = 0,
  val resumed: Set<String> = emptySet(), val screenOn: Boolean = true, val keyguard: Boolean = false)
object UsageMeter { fun advance(state: MeterState, events: List<UsageEvent>, until: Instant, free: Set<String>): MeterState }
```
규칙: `screenOn && !keyguard`이고 `resumed`("pkg/activity") 중 `free`에 없는 패키지가 있으면 센다. `countedUntil` 이전 이벤트는 상태만 바꾼다. `until` 이후 이벤트는 무시한다. `Restart` 직전 구간은 세지 않고, `resumed`를 비우며 화면을 꺼짐으로 둔다. 이벤트는 시각순 정렬 후 처리한다.

- [ ] **Step 1: 테스트** (`t0 = at("2026-11-26T10:00")`, `m(n) = t0 + n분`, `r/p` = Resumed/Paused 도우미, activity `"A"`)

```kotlin
fun used(vararg e: UsageEvent, free: Set<String> = emptySet()) =
  UsageMeter.advance(MeterState(t0), e.toList(), m(10), free).usedMillis
@Test fun countsForeground() = assertEquals(600_000, used(r(0, "game")))
@Test fun freeApp_notCounted() = assertEquals(0, used(r(0, "home"), free = setOf("home")))
@Test fun screenOff_stops() = assertEquals(300_000, used(r(0, "game"), Screen(m(5), false)))
@Test fun keyguard_stops() = assertEquals(120_000, used(r(0, "game"), Keyguard(m(2), true)))
@Test fun splitScreen_counts() = assertEquals(600_000, used(r(0, "ok"), r(0, "game"), free = setOf("ok")))
@Test fun restartGap_notCounted() = assertEquals(0, UsageMeter.advance(
  MeterState(t0, resumed = setOf("game/A")), listOf(Restart(m(120))), m(120), emptySet()).usedMillis)
@Test fun replayedEvents_notDoubleCounted() {
  val ev = listOf(r(0, "game"))
  val a = UsageMeter.advance(MeterState(t0), ev, m(5), emptySet())
  assertEquals(600_000, UsageMeter.advance(a, ev, m(10), emptySet()).usedMillis)
}
```

- [ ] **Step 2:** 실패 확인 → **Step 3:** 구현 → **Step 4:** `OK (15 tests)` → **Step 5:** commit `feat: usage meter`

### Task 4: 잠금 엔진

**Files:** Create `Engine.kt`, `EngineTest.kt`

**Interfaces — Consumes:** Task 1~3. **Produces:**
```kotlin
data class CoreState(val settings: Settings, val pending: Settings?, val armed: Boolean,
  val period: Period, val meter: MeterState, val instantUntil: Instant?)
enum class LockReason { LIMIT, INSTANT, PERMISSION_MISSING }
object Engine {
  fun arm(settings: Settings, now: Instant, zone: ZoneId): CoreState
  fun step(s: CoreState, events: List<UsageEvent>, now: Instant, zone: ZoneId, alwaysFree: Set<String>): CoreState
  fun startInstantLock(s: CoreState, minutes: Int, now: Instant): CoreState   // 기존 종료 시각보다 줄지 않음
  fun lockReasons(s: CoreState, now: Instant, permissionsOk: Boolean): Set<LockReason> // armed 아니면 빈 집합
  fun remainingMillis(s: CoreState): Long                                     // 0 이상
  fun dueWarning(beforeMs: Long, afterMs: Long): Int?                         // 지나친 기준 중 가장 작은 분
}
```
초기화: `now >= period.end`이면 경계까지 측정 → `pending` 적용 → 사용 시간 0, 앱 상태 유지. 시작 시각이 바뀌었으면 새 기간은 `[경계, firstStartAtOrAfter(경계 + 24h))`, 요일은 경계의 요일. 바뀌지 않았거나 `now`가 그 끝도 지났으면 `periodAt(now)`. 새 `countedUntil = max(경계, period.start)`. 그 뒤 `now`까지 측정한다.

- [ ] **Step 1: 테스트** (`s(t, limit)` = `Engine.arm(Settings(week(limit), emptySet()), at(t), SEOUL)`, `step(st, t, ev…)` 도우미)

```kotlin
@Test fun usageAcrossBoundary_splits() {
  val r = step(s("2026-11-26T04:50"), "2026-11-26T05:10", Resumed(at("2026-11-26T04:50"), "game", "A"))
  assertEquals(THURSDAY, r.period.day); assertEquals(600_000, r.meter.usedMillis)
}
@Test fun startChange_nextPeriodAtLeast24h() {
  val st = s("2026-11-26T06:00").copy(pending = Settings(week(120, 240), emptySet()))
  val r = step(st, "2026-11-27T05:00")
  assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-29T04:00")), r.period)
}
@Test fun offForDays_resetsOnceAndAppliesPending() {
  val st = s("2026-11-26T06:00").copy(pending = Settings(week(180), emptySet()))
  val r = step(st, "2026-11-30T12:00")
  assertEquals(180, r.settings.week[MONDAY]!!.limitMinutes); assertNull(r.pending)
  assertEquals(0, r.meter.usedMillis); assertEquals(at("2026-11-30T05:00"), r.period.start)
}
@Test fun limitReached_locks() {
  val r = step(s("2026-11-26T10:00", 1), "2026-11-26T10:01", Resumed(at("2026-11-26T10:00"), "game", "A"))
  assertEquals(setOf(LIMIT), Engine.lockReasons(r, at("2026-11-26T10:01"), true))
}
@Test fun instantLock_survivesReset_thenEnds() {
  val st = Engine.startInstantLock(s("2026-11-26T04:50"), 30, at("2026-11-26T04:50"))
  val r = step(st, "2026-11-26T05:00")
  assertTrue(INSTANT in Engine.lockReasons(r, at("2026-11-26T05:00"), true))
  assertTrue(Engine.lockReasons(r, at("2026-11-26T05:20"), true).isEmpty())
}
@Test fun shorterInstantLock_doesNotShorten() {
  val now = at("2026-11-26T10:00")
  val a = Engine.startInstantLock(s("2026-11-26T10:00"), 60, now)
  assertEquals(a.instantUntil, Engine.startInstantLock(a, 10, now).instantUntil)
}
@Test fun missingPermission_locks() = assertEquals(setOf(PERMISSION_MISSING),
  Engine.lockReasons(s("2026-11-26T10:00"), at("2026-11-26T10:00"), false))
@Test fun warnings() {
  assertEquals(10, Engine.dueWarning(601_000, 600_000))
  assertEquals(1, Engine.dueWarning(660_000, 30_000))
  assertNull(Engine.dueWarning(500_000, 400_000))
}
```

- [ ] **Step 2:** 실패 확인 → **Step 3:** 구현 → **Step 4:** `OK (23 tests)` → **Step 5:** commit `feat: lock engine`

### Task 5: 신뢰 시계와 비상 해제 상태

**Files:** Create `TrustedClock.kt`, `EmergencyRelease.kt`, 각 테스트

**Interfaces — Produces:**
```kotlin
data class ClockAnchor(val wall: Instant, val elapsedMillis: Long, val bootCount: Int)
object TrustedClock { fun now(anchor: ClockAnchor?, wall: Instant, elapsedMillis: Long, bootCount: Int): Pair<Instant, ClockAnchor> }
sealed interface ReleaseStatus { object None; data class Waiting(val left: Duration); data class Ready(val left: Duration); object Expired }
object EmergencyRelease { fun status(requestedAt: Instant?, now: Instant): ReleaseStatus }
```
시계: 앵커가 없으면 `wall`, 같은 부팅이면 `anchor.wall + 경과`, 다른 부팅이면 `max(wall, anchor.wall)`. 반환 앵커는 결과 시각 기준.

- [ ] **Step 1: 테스트**

```kotlin
val a = ClockAnchor(at("2026-11-26T10:00"), 1_000_000, 3)
@Test fun sameBoot_ignoresWallChange() = assertEquals(at("2026-11-26T10:01"),
  TrustedClock.now(a, at("2027-01-01T00:00"), 1_060_000, 3).first)
@Test fun reboot_neverGoesBack() = assertEquals(a.wall,
  TrustedClock.now(a, at("2026-11-26T09:00"), 5_000, 4).first)
@Test fun reboot_movesForward() = assertEquals(at("2026-11-26T12:00"),
  TrustedClock.now(a, at("2026-11-26T12:00"), 5_000, 4).first)
val t = at("2026-11-26T10:00")
fun st(min: Long) = EmergencyRelease.status(t, t.plus(Duration.ofMinutes(min)))
@Test fun waiting() = assertEquals(Waiting(Duration.ofMinutes(1)), st(1439))
@Test fun ready() = assertEquals(Ready(Duration.ofHours(24)), st(1440))
@Test fun expired() = assertEquals(Expired, st(2880))
@Test fun none() = assertEquals(None, EmergencyRelease.status(null, t))
```

- [ ] **Step 2:** 실패 확인 → **Step 3:** 구현 → **Step 4:** `OK (30 tests)` → **Step 5:** commit `feat: trusted clock and release`

### Task 6: 상태 저장 형식

**Files:** Create `StateCodec.kt`, `StateCodecTest.kt`

**Interfaces — Produces:** `StateCodec.encode(s: CoreState): String`, `StateCodec.decode(text: String): CoreState?`
줄 단위 `key=value`, 첫 줄 `v=1`, 마지막 줄은 본문의 CRC32. 어떤 오류든 `null`.

- [ ] **Step 1: 테스트** (`full` = pending, instantUntil, 허용앱 2개, resumed 1개가 모두 있는 상태)

```kotlin
@Test fun roundTrip() = assertEquals(full, StateCodec.decode(StateCodec.encode(full)))
@Test fun garbage_isNull() = assertNull(StateCodec.decode("garbage"))
@Test fun truncated_isNull() = assertNull(StateCodec.decode(StateCodec.encode(full).dropLast(20)))
@Test fun tampered_isNull() = assertNull(StateCodec.decode(StateCodec.encode(full).replace("v=1", "v=2")))
```

- [ ] **Step 2:** 실패 확인 → **Step 3:** 구현 → **Step 4:** `OK (34 tests)` → **Step 5:** commit `feat: state codec`

### Task 7: 정지 대상과 설정 화면 차단 판단

**Files:** Create `Policy.kt`, `PolicyTest.kt`

**Interfaces — Produces:**
```kotlin
data class DeviceApps(val candidates: Set<String>, val self: String, val homes: Set<String>,
  val dialers: Set<String>, val keyboards: Set<String>)
object Policy {
  fun alwaysFree(d: DeviceApps): Set<String>   // self, homes, dialers, com.android.systemui
  fun suspendTargets(d: DeviceApps, allowed: Set<String>): Set<String>
  fun shouldCloseSettings(pkg: String, texts: List<String>, appLabel: String, armed: Boolean, permissionsOk: Boolean): Boolean
}
```
정지 제외: `alwaysFree`, 허용앱, 키보드, `com.android.settings`, `com.android.phone`, `com.android.server.telecom`, `com.android.emergency`. 설정 화면은 `armed && permissionsOk && pkg == "com.android.settings"`이고 글자에 앱 이름이 있을 때 닫는다.

- [ ] **Step 1: 테스트**

```kotlin
val d = DeviceApps(setOf("self","home","dial","kb","com.android.settings","com.android.phone","ok","game"),
  "self", setOf("home"), setOf("dial"), setOf("kb"))
@Test fun onlyOrdinaryAppsSuspended() = assertEquals(setOf("game"), Policy.suspendTargets(d, setOf("ok")))
@Test fun newDialerIsProtected() =
  assertFalse("game" in Policy.suspendTargets(d.copy(dialers = setOf("game")), emptySet()))
@Test fun settingsNotFree() = assertFalse("com.android.settings" in Policy.alwaysFree(d))
fun close(pkg: String, ok: Boolean) = Policy.shouldCloseSettings(pkg, listOf("하루잠금"), "하루잠금", true, ok)
@Test fun closesOwnSettingsPage() = assertTrue(close("com.android.settings", true))
@Test fun leavesOpenForRepair() = assertFalse(close("com.android.settings", false))
@Test fun ignoresOtherApps() = assertFalse(close("game", true))
```

- [ ] **Step 2:** 실패 확인 → **Step 3:** 구현 → **Step 4:** `OK (40 tests)` → **Step 5:** commit `feat: policy`

### Task 8: 안드로이드 앱 뼈대, 저장, 기기 소유자

**Files:** `:app` 추가(`app/build.gradle.kts`, 두 manifest, `res/xml/device_admin.xml`), `admin/*.kt`, `data/StateStore.kt`, `data/DeviceInfo.kt`

**Interfaces — Produces:**
```kotlin
sealed interface Loaded { data class Ok(val state: CoreState); object Empty; object Corrupt }
class StateStore(ctx: Context) { fun load(): Loaded; fun save(s: CoreState); var anchor: ClockAnchor? }
class Guard(ctx: Context) { fun isOwner(): Boolean; fun harden(); fun relax() }
class Enforcer(ctx: Context) { fun apply(locked: Boolean, allowed: Set<String>); fun unsuspendAll() }
fun deviceApps(ctx: Context): DeviceApps
```
- `StateStore`: device-protected SharedPreferences, `current`와 `backup` 두 칸, `commit()`.
- `harden()`: `setUninstallBlocked`, `setUserControlDisabledPackages`, `DISALLOW_SAFE_BOOT`, `DISALLOW_FACTORY_RESET`, `DISALLOW_CONFIG_DATE_TIME`, `DISALLOW_ADD_USER`, `DISALLOW_ADD_MANAGED_PROFILE`, 자동 시간·시간대 켜기. `BuildConfig.FINAL_GUARD`일 때만 `DISALLOW_DEBUGGING_FEATURES`. `relax()`는 전부 되돌린다.
- `DeviceInfo.candidates`: 실행 아이콘이 있는 앱 ∪ 사용자 설치 앱 (`QUERY_ALL_PACKAGES`).
- manifest: receiver `.admin.AdminReceiver`. debug manifest에 `android:testOnly="true"`.

- [ ] **Step 1:** 빈 임시 폴더에서 `gradle wrapper --gradle-version 8.14.3`로 만든 wrapper를 복사하고 모듈 설정 작성
- [ ] **Step 2:** 위 클래스 구현
- [ ] **Step 3 (PC):** `./gradlew :core:test :app:assembleDebug` → `BUILD SUCCESSFUL`
- [ ] **Step 4:** commit `feat: android shell and device owner guard`

### Task 9: 잠금 서비스

**Files:** `data/UsageReader.kt`, `data/Permissions.kt`, `service/{Controller,LockService,Receivers}.kt`

**Interfaces — Produces:** `class Controller(ctx: Context) { fun tick(); fun arm(settings: Settings); fun requestSettings(s: Settings); fun instantLock(minutes: Int) }`, `Permissions.usage(ctx)`, `Permissions.accessibility(ctx)`

`tick()` 순서: 해제 완료 파일이 있으면 중단 → 상태 로드(`Corrupt`면 `unsuspendAll`, `relax`, 재설정 알림) → 신뢰 시각 → 이벤트 읽기 → `Engine.step` → 저장 → 예고 알림 → `Enforcer.apply`.

- 화면이 켜진 동안 1초마다 실행. foreground service type `specialUse`.
- 초기화와 즉시 잠금 종료 시각에 정확한 알람(`USE_EXACT_ALARM`, API 31~32는 `SCHEDULE_EXACT_ALARM`).
- `LOCKED_BOOT_COMPLETED`, `BOOT_COMPLETED`, `MY_PACKAGE_REPLACED`에서 재시작. `PACKAGE_ADDED`는 서비스에서 등록.
- 사용 기록은 사용자 잠금 해제 전에는 읽지 않는다.
- 이벤트 매핑: `ACTIVITY_RESUMED`→Resumed, `ACTIVITY_PAUSED`/`STOPPED`→Paused, `SCREEN_(NON_)INTERACTIVE`→Screen, `KEYGUARD_SHOWN/HIDDEN`→Keyguard, `DEVICE_STARTUP`→Restart, `DEVICE_SHUTDOWN`→Screen(off).

- [ ] **Step 1:** 구현 → **Step 2 (PC):** `./gradlew :app:assembleDebug` 성공 → **Step 3:** commit `feat: lock service`

### Task 10: 설정 화면 차단

**Files:** `service/SettingsWatchService.kt`, `res/xml/accessibility.xml`

창 변화 때 화면 글자를 모아 `Policy.shouldCloseSettings`가 참이면 `GLOBAL_ACTION_HOME`. directBootAware.

- [ ] **Step 1:** 구현 → **Step 2 (PC):** 빌드 성공 → **Step 3:** commit `feat: settings watch`

### Task 11: 화면

**Files:** `ui/` Activity 4개와 `InstantLockDialog.kt`, 디자인 요청서의 레이아웃·values·drawable 파일

- 먼저 지정된 ID만 갖춘 기본 모양으로 만든다. ChatGPT 결과물은 `res/`를 교체해 적용하며 Kotlin은 바꾸지 않는다.
- 설정 안내: 기기 소유자, 사용 정보 접근, 접근성이 모두 완료돼야 `btn_arm` 활성. 알림과 배터리는 권장.
- 허용앱에서 브라우저(https 처리 앱)나 `com.android.vending`을 고르면 확인 창.
- 즉시 잠금은 경고를 보여준 뒤 `Controller.instantLock`. 1~1440 밖이면 `tv_error`.
- 설정 저장은 `Controller.requestSettings`, 대기 중이면 `tv_pending_notice`와 `tv_pending_change` 표시.

- [ ] **Step 1:** 구현 → **Step 2 (PC):** 빌드 성공, 각 화면 열림 → **Step 3:** commit `feat: screens`

### Task 12: 비상 해제

**Files:** `ui/ReleaseActivity.kt` (`android:process=":release"`)

- `StateStore`를 쓰지 않는다. device-protected 파일 `release.txt`(요청 시각, 앵커)와 완료 표시 `released`만 사용한다.
- 상태는 `TrustedClock` + `EmergencyRelease.status`. 열 때마다 앵커를 갱신한다.
- `Ready`에서 확인 창을 거쳐: `released` 생성 → `unsuspendAll` → `relax` → `clearDeviceOwnerApp`.
- 기기 소유자를 다시 설정하고 `Controller.arm`을 실행하면 두 파일을 지운다.

- [ ] **Step 1:** 구현 → **Step 2 (PC):** 빌드 성공 → **Step 3:** commit `feat: emergency release`

### Task 13: 설치 안내와 실기기 시험

**Files:** `docs/SETUP.md`, `docs/TEST.md`

SETUP: 백업 → 모든 계정 삭제, 보안 폴더·듀얼 메신저 제거 → "보안 위험 자동 차단" 끄기 → USB 디버깅 켜기 → 아래 명령.

```bash
adb install -t app/build/outputs/apk/debug/app-debug.apk
adb shell dpm set-device-owner app.harulock/.admin.AdminReceiver
adb shell dpm remove-active-admin app.harulock/.admin.AdminReceiver   # 시험판 해제
```

- [ ] **Step 1:** 위 문서 작성. TEST.md에는 아래 항목을 통과/실패로 기록
  - 해제 명령이 먼저 동작하는지(다른 시험 전에 확인)
  - 한도 1분: 게임 정지, 전화·긴급전화·허용앱 사용 가능
  - 홈, 허용앱, 이 앱에서는 시간이 줄지 않음
  - 5분 뒤로 시작 시각 설정(잠금 시작 전) 후 초기화 확인
  - 삭제, 강제 종료, 안전 모드, 설정 초기화, 시간 변경, 사용자 추가가 막힘
  - 권한 끄기 시도 시 화면이 닫힘
  - 재부팅 후 잠금 유지, 새 설치 앱 정지
  - 비상 해제의 요청·취소(24시간 완료 시험 포함)
- [ ] **Step 2:** 시험판을 1주 이상 사용한 뒤에만 정식판 설치: 해제 → 삭제 → `./gradlew :app:assembleRelease` → 설치 → 소유자 설정
- [ ] **Step 3:** commit `docs: setup and test`
