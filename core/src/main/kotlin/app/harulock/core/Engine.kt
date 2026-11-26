package app.harulock.core

import java.time.DayOfWeek
import java.time.Duration
import java.time.Instant
import java.time.ZoneId

/** 잠금 판단에 필요한 상태 전부. [pending]은 다음 초기화 때 적용할 설정. */
data class CoreState(
    val settings: Settings,
    val pending: Settings?,
    val armed: Boolean,
    val period: Period,
    val meter: MeterState,
    val instantUntil: Instant?,
)

enum class LockReason { LIMIT, INSTANT, PERMISSION_MISSING }

object Engine {
    private const val MINUTE_MILLIS = 60_000L

    /** 남은 시간이 이만큼(분)이 되면 알린다. 작은 값부터. */
    private val WARNING_MINUTES = listOf(1, 5, 10)

    fun arm(settings: Settings, now: Instant, zone: ZoneId): CoreState = CoreState(
        settings = settings,
        pending = null,
        armed = true,
        period = DayClock.periodAt(now, settings.week, zone),
        meter = MeterState(now),
        instantUntil = null,
    )

    /** [now]까지 사용 시간을 반영한다. 기간이 끝났으면 먼저 초기화한다. */
    fun step(s: CoreState, events: List<UsageEvent>, now: Instant, zone: ZoneId, alwaysFree: Set<String>): CoreState {
        val current = if (now >= s.period.end) reset(s, events, now, zone, alwaysFree) else s
        return current.copy(meter = measure(current, events, now, alwaysFree))
    }

    /** 이미 걸린 즉시 잠금보다 일찍 끝나게 바꾸지 않는다. */
    fun startInstantLock(s: CoreState, minutes: Int, now: Instant): CoreState {
        require(minutes in 1..1440) { "minutes out of range: $minutes" }
        val until = now.plus(Duration.ofMinutes(minutes.toLong()))
        return s.copy(instantUntil = s.instantUntil?.let { maxOf(it, until) } ?: until)
    }

    fun lockReasons(s: CoreState, now: Instant, permissionsOk: Boolean): Set<LockReason> {
        if (!s.armed) return emptySet()
        return buildSet {
            if (remainingMillis(s) == 0L) add(LockReason.LIMIT)
            if (s.instantUntil != null && now < s.instantUntil) add(LockReason.INSTANT)
            if (!permissionsOk) add(LockReason.PERMISSION_MISSING)
        }
    }

    fun remainingMillis(s: CoreState): Long {
        val limit = s.settings.week.getValue(s.period.day).limitMinutes * MINUTE_MILLIS
        return (limit - s.meter.usedMillis).coerceAtLeast(0)
    }

    /** 남은 시간이 [beforeMs]에서 [afterMs]로 줄며 지나친 알림 기준 중 가장 작은 분. 없으면 null. */
    fun dueWarning(beforeMs: Long, afterMs: Long): Int? =
        WARNING_MINUTES.firstOrNull { beforeMs > it * MINUTE_MILLIS && afterMs <= it * MINUTE_MILLIS }

    private fun measure(s: CoreState, events: List<UsageEvent>, until: Instant, alwaysFree: Set<String>): MeterState =
        UsageMeter.advance(s.meter, events, until, alwaysFree + s.settings.allowed)

    /** 지난 기간을 경계까지 측정해 닫고, 대기 중인 설정으로 새 기간을 연다. 며칠이 지났어도 한 번만 한다. */
    private fun reset(
        s: CoreState,
        events: List<UsageEvent>,
        now: Instant,
        zone: ZoneId,
        alwaysFree: Set<String>,
    ): CoreState {
        val boundary = s.period.end
        val closed = measure(s, events, boundary, alwaysFree)
        val settings = s.pending ?: s.settings

        // 시작 시각이 바뀌면 새 시각이 더 일러도 24시간 안에는 다시 초기화하지 않는다.
        val extended = if (startChanged(s.settings, settings)) stretched(boundary, settings, zone) else null
        val period = extended?.takeIf { now < it.end } ?: DayClock.periodAt(now, settings.week, zone)

        return s.copy(
            settings = settings,
            pending = null,
            period = period,
            meter = closed.copy(countedUntil = maxOf(boundary, period.start), usedMillis = 0),
        )
    }

    /**
     * 지금 기간이 끝난 뒤 이어질 기간. 대기 중인 설정을 쓰고, 초기화가 제때 일어난다고 본다.
     * 시작 시각이 바뀌면 이 기간은 24시간보다 길다(더 이른 시각으로 바꾸면 48시간 가까이).
     */
    fun nextPeriod(s: CoreState, zone: ZoneId): Period {
        val settings = s.pending ?: s.settings
        val boundary = s.period.end
        return if (startChanged(s.settings, settings)) {
            stretched(boundary, settings, zone)
        } else {
            DayClock.periodAt(boundary, settings.week, zone)
        }
    }

    /** [boundary]에서 시작해 24시간 뒤 이후 첫 시작 시각에 끝나는 기간. */
    private fun stretched(boundary: Instant, settings: Settings, zone: ZoneId): Period {
        val end = DayClock.firstStartAtOrAfter(boundary.plus(Duration.ofHours(24)), settings.week, zone)
        return Period(boundary.atZone(zone).dayOfWeek, boundary, end)
    }

    private fun startChanged(old: Settings, new: Settings): Boolean =
        DayOfWeek.values().any { old.week.getValue(it).startMinute != new.week.getValue(it).startMinute }
}
