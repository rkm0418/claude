package app.harulock.service

import android.app.AlarmManager
import android.app.KeyguardManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.PowerManager
import android.os.SystemClock
import android.os.UserManager
import android.util.Log
import app.harulock.admin.Enforcer
import app.harulock.admin.Guard
import app.harulock.core.Change
import app.harulock.core.ClockAnchor
import app.harulock.core.CoreState
import app.harulock.core.DeviceApps
import app.harulock.core.Engine
import app.harulock.core.Policy
import app.harulock.core.Settings
import app.harulock.core.SettingsRules
import app.harulock.core.TrustedClock
import app.harulock.core.UsageEvent
import app.harulock.data.DeviceInfo
import app.harulock.data.Loaded
import app.harulock.data.Permissions
import app.harulock.data.ReleaseFiles
import app.harulock.data.StateStore
import app.harulock.data.UsageReader
import java.io.File
import java.io.RandomAccessFile
import java.time.Duration
import java.time.Instant
import java.time.ZoneId
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock
import android.provider.Settings.Global as GlobalSettings

/**
 * 잠금의 모든 동작. 서비스, 수신기, 화면이 동시에 불러도 [exclusive]로 한 번에 하나씩 실행한다.
 * 한 동작 안에서는 신뢰 시각 하나만 쓴다.
 */
class Controller(ctx: Context) {
    private val context = ctx.applicationContext
    private val store = StateStore(context)
    private val guard = Guard(context)
    private val enforcer = Enforcer(context)
    private val reader = UsageReader(context)
    private val notices = Notices(context)
    private val power = context.getSystemService(PowerManager::class.java)
    private val keyguard = context.getSystemService(KeyguardManager::class.java)
    private val users = context.getSystemService(UserManager::class.java)
    private val prefs = context.createDeviceProtectedStorageContext()
        .getSharedPreferences("controller", Context.MODE_PRIVATE)

    /** 해제 확인 → 상태 로드 → 신뢰 시각 → 이벤트 → step → 저장 → 예고 알림 → 정지 적용. 예외를 밖으로 내지 않는다. */
    fun tick() {
        runCatching { exclusive(context) { tickLocked() } }.onFailure { Log.w(TAG, "tick failed", it) }
    }

    /** 잠금을 시작한다. 이미 잠금 중이거나 기기 소유자가 아니거나 필수 권한(사용 정보, 접근성)이 없으면 false. */
    fun arm(settings: Settings): Boolean =
        runCatching { exclusive(context) { armLocked(settings) } }
            .onFailure { Log.w(TAG, "arm failed", it) }
            .getOrDefault(false)

    /** 설정 변경을 요청한다. 결과(즉시 적용분과 대기분)를 돌려주고, 처리하지 못하면 null. */
    fun requestSettings(s: Settings): Change? =
        runCatching { exclusive(context) { requestLocked(s) } }
            .onFailure { Log.w(TAG, "requestSettings failed", it) }
            .getOrNull()

    /** 즉시 잠금. 잠금 시작 전이거나 [minutes]가 1~1440 밖이면 false. */
    fun instantLock(minutes: Int): Boolean =
        runCatching { exclusive(context) { instantLocked(minutes) } }
            .onFailure { Log.w(TAG, "instantLock failed", it) }
            .getOrDefault(false)

    private fun tickLocked() {
        if (released(context)) return
        val state = loadOrClean() ?: return
        if (!state.armed) {
            // 잠금 전이면 남은 정지와 제한을 모두 푼다. 저장할 때마다 한 번, 실패하면 30초마다 다시 시도한다.
            if (guard.isOwner()) cleanUp(notify = false)
            return
        }
        val m = moment()
        val next = advance(state, m)
        persist(next, m)
        warn(state, next)
        enforce(next, m, force = false)
        hardenIfDue()
    }

    /** 잠금 중에는 5분마다 제한을 다시 건다. 업데이트나 외부 변경(관리자 해제 뒤 재지정 등)으로 풀렸을 수 있다. 해제 뒤에는 걸지 않는다. */
    private fun hardenIfDue() {
        val t = SystemClock.elapsedRealtime()
        val last = Memory.lastHarden
        if (last != null && t - last < HARDEN_EVERY_MILLIS) return
        if (released(context)) return
        guard.harden()
        Memory.lastHarden = t
    }

    /**
     * 비상 해제 뒤에는 저장 상태가 아직 잠금 중이어도 다시 시작할 수 있다(기기 소유자를 다시 설정한 뒤).
     * 두 해제 파일을 지운다(R5). 요청 기록은 저장 전에 지워 이전 요청이 새 잠금에 남지 않게 하고,
     * 완료 표시는 저장 뒤에 지워 그 사이에 실패해도 서비스가 이전 상태로 잠그지 않게 한다.
     */
    private fun armLocked(settings: Settings): Boolean {
        if (!guard.isOwner()) return false
        // 권한 없이 시작하면 곧바로 권한 잠금이 걸리고 설정 감시도 동작하지 않는다.
        if (!Permissions.all(context)) return false
        val loaded = store.load()
        if (loaded is Loaded.Ok && loaded.state.armed && !released(context)) return false
        val files = ReleaseFiles(context)
        if (!files.deleteRecord()) return false
        val m = moment()
        val state = Engine.arm(settings, m.now, m.zone)
        save(state)
        store.anchor = m.anchor
        if (!files.deleteMarker()) return false
        guard.harden()
        Memory.lastHarden = SystemClock.elapsedRealtime()
        enforce(state, m, force = true)
        LockService.start(context)
        return true
    }

    private fun requestLocked(s: Settings): Change? {
        val m = moment()
        val state = (store.load() as? Loaded.Ok)?.state
        // 비상 해제 뒤에는 잠금 중이 아니므로 그대로 저장한다. 저장 상태의 armed도 이렇게 꺼진다.
        if (state == null || !state.armed || released(context)) {
            // 잠금 시작 전에는 그대로 저장한다. 기간과 측정 칸은 arm에서 새로 만든다.
            save(Engine.arm(s, m.now, m.zone).copy(armed = false))
            store.anchor = m.anchor
            return Change(s, null)
        }
        if (!m.unlocked) return null
        // 지난 경계를 먼저 처리해야 느슨해진 요청이 바로 적용되지 않는다.
        val stepped = advance(state, m)
        val change = SettingsRules.request(stepped.settings, s, armed = true)
        val next = stepped.copy(settings = change.active, pending = change.pending)
        persist(next, m)
        warn(state, next)
        enforce(next, m, force = false)
        return change
    }

    private fun instantLocked(minutes: Int): Boolean {
        if (minutes !in 1..1440 || released(context)) return false
        val state = (store.load() as? Loaded.Ok)?.state?.takeIf { it.armed } ?: return false
        val m = moment()
        if (!m.unlocked) return false
        val next = Engine.startInstantLock(advance(state, m), minutes, m.now)
        persist(next, m)
        warn(state, next)
        enforce(next, m, force = true)
        return true
    }

    /** 저장 상태. 비었거나 손상되었으면 정지와 제한을 풀고(끝날 때까지 다시 시도) null. */
    private fun loadOrClean(): CoreState? = when (val loaded = store.load()) {
        is Loaded.Ok -> loaded.state
        Loaded.Empty -> {
            if (guard.isOwner()) cleanUp(notify = false)
            null
        }
        Loaded.Corrupt -> {
            cleanUp(notify = true)
            null
        }
    }

    /**
     * 상태를 읽을 수 없거나 잠금 전일 때 영구히 잠기지 않도록 푼다. 모두 풀릴 때까지 30초마다 다시 시도하고,
     * 화면이 꺼져 있어도 알람으로 깨운다. 다시 저장할 때까지 성공 후에는 하지 않는다. 안내 알림은 처음 한 번만.
     */
    private fun cleanUp(notify: Boolean) {
        if (prefs.getBoolean(KEY_CLEANED, false)) return
        if (notify && !prefs.getBoolean(KEY_NOTIFIED, false)) {
            notices.setupAgain()
            prefs.edit().putBoolean(KEY_NOTIFIED, true).commit()
        }
        val t = SystemClock.elapsedRealtime()
        val last = Memory.lastClean
        if (last != null && t - last < APPLY_EVERY_MILLIS) return
        Memory.lastClean = t
        Memory.lastHarden = null
        Memory.lastLocked = false
        Memory.lastAllowed = emptySet()
        // 기기 소유자가 아니면 풀 권한도, 걸린 제한도 없다.
        val done = runCatching {
            if (!guard.isOwner()) return@runCatching true
            val unsuspended = enforcer.unsuspendAll()
            val relaxed = guard.relax()
            unsuspended && relaxed
        }.onFailure { Log.w(TAG, "clean up failed", it) }.getOrDefault(false)
        if (done) {
            prefs.edit().putBoolean(KEY_CLEANED, true).commit()
        } else {
            setAlarmAt(ALARM_RETRY, t + APPLY_EVERY_MILLIS)
        }
    }

    private fun save(s: CoreState) {
        store.save(s)
        if (prefs.contains(KEY_CLEANED) || prefs.contains(KEY_NOTIFIED)) {
            prefs.edit().remove(KEY_CLEANED).remove(KEY_NOTIFIED).commit()
        }
        Memory.lastClean = null
    }

    /** 잠금 해제 전에는 측정 상태를 저장하지 않는다. 해제 후 기록을 다시 읽어 센다. 앵커는 저장한다. */
    private fun persist(s: CoreState, m: Moment) {
        if (m.unlocked) save(s)
        store.anchor = m.anchor
    }

    private fun moment(): Moment {
        val wall = Instant.now()
        val elapsed = SystemClock.elapsedRealtime()
        val boot = GlobalSettings.getInt(context.contentResolver, GlobalSettings.BOOT_COUNT, 0)
        val (now, anchor) = TrustedClock.now(store.anchor, wall, elapsed, boot)
        return Moment(now, wall, elapsed, anchor, ZoneId.systemDefault(), users.isUserUnlocked)
    }

    /** [m] 시각까지 사용 시간을 반영한다. */
    private fun advance(s: CoreState, m: Moment): CoreState {
        val counted = s.meter.countedUntil
        val bootAt = m.now.minusMillis(m.elapsed)
        val events = ArrayList<UsageEvent>()
        if (!m.unlocked) {
            // 잠금 해제 전 기록은 읽을 수 없다. 부팅 직후이므로 재시작으로 보고 이전 화면 상태로 세지 않는다.
            events.add(UsageEvent.Restart(maxOf(bootAt, counted)))
        } else {
            // 기기가 꺼졌던 구간은 세지 않는다. 시스템의 DEVICE_STARTUP이 빠져도 같게 한다.
            if (bootAt > counted) events.add(UsageEvent.Restart(bootAt))
            val from = counted.toEpochMilli() - m.shiftMillis - REPLAY_MILLIS
            events += runCatching { reader.read(from, m.wall.toEpochMilli() + 1, m.shiftMillis) }
                .onFailure { Log.w(TAG, "cannot read usage events", it) }
                .getOrDefault(emptyList())
        }
        // 부팅 때 화면 켜짐이 기록되지 않을 수 있으므로 지금 상태를 끝에 붙인다.
        events.add(UsageEvent.Screen(m.now, power.isInteractive))
        events.add(UsageEvent.Keyguard(m.now, keyguard.isKeyguardLocked))
        return Engine.step(s, events, m.now, m.zone, alwaysFree())
    }

    /** 남은 시간이 10, 5, 1분을 지나면 알린다. 기간이 바뀌었거나 0분이면 알리지 않는다. */
    private fun warn(before: CoreState, after: CoreState) {
        if (!after.armed || before.period != after.period) return
        val left = Engine.remainingMillis(after)
        if (left == 0L) return
        Engine.dueWarning(Engine.remainingMillis(before), left)?.let { notices.warning(it) }
    }

    private fun enforce(s: CoreState, m: Moment, force: Boolean) {
        val locked = Engine.lockReasons(s, m.now, Permissions.all(context)).isNotEmpty()
        apply(locked, s.settings.allowed, force)
        schedule(s, m)
    }

    /** 잠금 여부, 허용앱, 설치 앱이 바뀌었을 때와 30초마다만 정지를 적용한다. */
    private fun apply(locked: Boolean, allowed: Set<String>, force: Boolean) {
        if (released(context)) return
        val t = SystemClock.elapsedRealtime()
        val due = force || Memory.packagesChanged || locked != Memory.lastLocked ||
            allowed != Memory.lastAllowed || t - Memory.lastApply >= APPLY_EVERY_MILLIS
        if (!due) return
        Memory.packagesChanged = false
        enforcer.apply(locked, allowed)
        Memory.lastLocked = locked
        Memory.lastAllowed = allowed
        Memory.lastApply = t
    }

    /** 시간을 세지 않는 앱(자기 앱, 홈, 전화). 패키지 조회가 무거워 30초 또는 설치 변화 때만 다시 읽는다. */
    private fun alwaysFree(): Set<String> {
        val t = SystemClock.elapsedRealtime()
        val cached = Memory.free
        if (cached != null && !Memory.freeStale && t - Memory.freeAt < APPLY_EVERY_MILLIS) return cached
        Memory.freeStale = false
        val fresh = runCatching {
            Policy.alwaysFree(
                DeviceApps(
                    candidates = emptySet(),
                    self = context.packageName,
                    homes = DeviceInfo.homes(context),
                    dialers = DeviceInfo.dialers(context),
                    keyboards = emptySet(),
                ),
            )
        }.onFailure { Log.w(TAG, "cannot list free apps", it) }.getOrNull()
        val result = fresh ?: cached ?: setOf(context.packageName)
        Memory.free = result
        Memory.freeAt = t
        return result
    }

    /** 초기화 시각과 즉시 잠금 종료 시각에 깨운다. 신뢰 시각과 같은 부팅 경과 시간 기준으로 맞춘다. */
    private fun schedule(s: CoreState, m: Moment) {
        setAlarm(ALARM_RESET, s.period.end, m)
        s.instantUntil?.takeIf { it > m.now }?.let { setAlarm(ALARM_INSTANT, it, m) }
    }

    private fun setAlarm(code: Int, target: Instant, m: Moment) {
        setAlarmAt(code, m.elapsed + Duration.between(m.now, target).toMillis().coerceAtLeast(0) + ALARM_MARGIN_MILLIS)
    }

    /** [at]은 부팅 경과 시간. 같은 시각으로 이미 걸어 두었으면 다시 걸지 않는다. */
    private fun setAlarmAt(code: Int, at: Long) {
        val previous = Memory.alarms[code]
        if (previous != null && kotlin.math.abs(previous - at) < 1_000) return
        val intent = Intent(context, AlarmReceiver::class.java).setAction("$ALARM_ACTION.$code")
        val pending = PendingIntent.getBroadcast(
            context, code, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val alarms = context.getSystemService(AlarmManager::class.java)
        runCatching {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !alarms.canScheduleExactAlarms()) {
                alarms.setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, at, pending)
            } else {
                alarms.setExactAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, at, pending)
            }
            Memory.alarms[code] = at
        }.onFailure { Log.w(TAG, "cannot set alarm $code", it) }
    }

    /** 한 동작에서 쓰는 시각. [now]는 신뢰 시각, [wall]과 [elapsed]는 같은 순간의 벽시계와 부팅 경과 시간. */
    private class Moment(
        val now: Instant,
        val wall: Instant,
        val elapsed: Long,
        val anchor: ClockAnchor,
        val zone: ZoneId,
        val unlocked: Boolean,
    ) {
        /** 신뢰 시각 - 벽시계. 사용 기록 시각을 옮기는 데 쓴다. */
        val shiftMillis: Long = now.toEpochMilli() - wall.toEpochMilli()
    }

    /** 프로세스 안에서 공유하는 기억. [exclusive] 안에서만 바꾼다([packagesChanged] 제외). */
    private object Memory {
        @Volatile var packagesChanged = true
        @Volatile var freeStale = true
        var lastLocked: Boolean? = null
        var lastAllowed: Set<String>? = null
        var lastApply = 0L
        var lastClean: Long? = null
        var lastHarden: Long? = null
        var free: Set<String>? = null
        var freeAt = 0L
        val alarms = HashMap<Int, Long>()
    }

    companion object {
        private const val TAG = "Controller"
        private const val KEY_CLEANED = "cleaned"
        private const val KEY_NOTIFIED = "notified"
        private const val LOCK_FILE = "controller.lock"
        private const val ALARM_ACTION = "app.harulock.ALARM"
        private const val ALARM_RESET = 1
        private const val ALARM_INSTANT = 2
        private const val ALARM_RETRY = 3
        private const val ALARM_MARGIN_MILLIS = 500L
        private const val APPLY_EVERY_MILLIS = 30_000L
        private const val HARDEN_EVERY_MILLIS = 5 * 60_000L

        /** 기록이 늦게 남는 경우를 위해 이미 센 구간 앞 10초부터 다시 읽는다. 다시 넘겨도 결과는 같다. */
        private const val REPLAY_MILLIS = 10_000L

        private val monitor = ReentrantLock()

        /** 설치 앱이나 사용자 잠금 해제 상태가 바뀌었다. 다음 tick에서 정지와 자유 앱 목록을 다시 계산한다. */
        fun packagesChanged() {
            Memory.packagesChanged = true
            Memory.freeStale = true
        }

        /**
         * 비상 해제를 시작했으면(완료 표시가 있으면) 서비스는 아무것도 걸지 않고 멈추고, 화면은 잠금 중으로 보이지 않는다.
         * 해제가 도중에 멈췄어도 마찬가지다. 남은 정지와 제한은 비상 해제 화면에서 다시 시도해 푼다.
         */
        fun released(ctx: Context): Boolean = ReleaseFiles.released(ctx)

        /**
         * 동작을 하나씩 실행한다. 프로세스 안에서는 잠금으로, 프로세스 사이(비상 해제)는 파일 잠금으로 막는다.
         * 파일 잠금을 얻지 못해도 실행은 한다.
         */
        fun <T> exclusive(ctx: Context, block: () -> T): T {
            if (monitor.isHeldByCurrentThread) return block()
            return monitor.withLock {
                val file = runCatching { RandomAccessFile(File(protectedFiles(ctx), LOCK_FILE), "rw") }.getOrNull()
                val lock = file?.let { f -> runCatching { f.channel.lock() }.getOrNull() }
                try {
                    block()
                } finally {
                    runCatching { lock?.release() }
                    runCatching { file?.close() }
                }
            }
        }

        private fun protectedFiles(ctx: Context): File = ctx.createDeviceProtectedStorageContext().filesDir
    }
}
