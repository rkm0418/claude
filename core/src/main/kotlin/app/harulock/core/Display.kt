package app.harulock.core

import java.time.DayOfWeek
import java.time.Instant

/** 홈 화면의 상태. */
enum class HomeState { NOT_ARMED, USING, LOW, LIMIT_LOCKED, INSTANT_LOCKED, PERMISSION_LOCKED }

/** 요일 하나의 바뀌는 값. */
data class DayChange(val day: DayOfWeek, val limitFrom: Int, val limitTo: Int, val startFrom: Int, val startTo: Int)

/** 두 설정의 차이. [days]는 월요일부터, 바뀐 요일만. */
data class SettingsDiff(val days: List<DayChange>, val added: Set<String>, val removed: Set<String>) {
    val isEmpty: Boolean get() = days.isEmpty() && added.isEmpty() && removed.isEmpty()
}

/** 처음 설정하기 전의 기본값(R20): 매일 120분, 05:00 시작, 허용앱 없음. */
object Defaults {
    const val LIMIT_MINUTES = 120
    const val START_MINUTE = 5 * 60

    val SETTINGS: Settings = Settings(
        week = DayOfWeek.values().associateWith { DayRule(LIMIT_MINUTES, START_MINUTE) },
        allowed = emptySet(),
    )
}

/** 화면에 보여 줄 값을 정하는 순수 함수. */
object Display {
    /** 남은 시간이 이 분 이하이면 [HomeState.LOW]. */
    const val LOW_MINUTES = 10

    /** 한도, 시작 시각, 즉시 잠금 입력의 범위. */
    val LIMIT_RANGE = 1..1440
    val START_RANGE = 0..1439

    private const val MINUTE_MILLIS = 60_000L

    /**
     * 권한 꺼짐을 먼저 보여 준다(사용자가 고칠 수 있다). 한도와 즉시 잠금이 함께 걸리면
     * 더 늦게 끝나는 쪽을 보여 준다.
     */
    fun homeState(s: CoreState?, now: Instant, permissionsOk: Boolean): HomeState {
        if (s == null || !s.armed) return HomeState.NOT_ARMED
        val reasons = Engine.lockReasons(s, now, permissionsOk)
        val instantUntil = s.instantUntil
        return when {
            LockReason.PERMISSION_MISSING in reasons -> HomeState.PERMISSION_LOCKED
            LockReason.INSTANT in reasons && LockReason.LIMIT in reasons && instantUntil != null ->
                if (instantUntil > s.period.end) HomeState.INSTANT_LOCKED else HomeState.LIMIT_LOCKED
            LockReason.INSTANT in reasons -> HomeState.INSTANT_LOCKED
            LockReason.LIMIT in reasons -> HomeState.LIMIT_LOCKED
            Engine.remainingMillis(s) <= LOW_MINUTES * MINUTE_MILLIS -> HomeState.LOW
            else -> HomeState.USING
        }
    }

    /** 남은 시간을 분으로 올려 센다. 0분은 정말 다 썼을 때만 나온다. */
    fun ceilMinutes(millis: Long): Long = (millis.coerceAtLeast(0) + MINUTE_MILLIS - 1) / MINUTE_MILLIS

    /** 분 입력. 앞뒤 공백을 무시하고, 숫자가 아니거나 1~1440 밖이면 null. */
    fun parseMinutes(text: String): Int? = text.trim().toIntOrNull()?.takeIf { it in LIMIT_RANGE }

    fun diff(from: Settings, to: Settings): SettingsDiff = SettingsDiff(
        days = DayOfWeek.values().mapNotNull { day ->
            val a = from.week.getValue(day)
            val b = to.week.getValue(day)
            if (a == b) null else DayChange(day, a.limitMinutes, b.limitMinutes, a.startMinute, b.startMinute)
        },
        added = to.allowed - from.allowed,
        removed = from.allowed - to.allowed,
    )

    /** 요청한 설정이 잠금 중 시작 시각을 바꾸는지. 바꾸면 바뀌는 날 하루가 길어진다. */
    fun changesStart(active: Settings, requested: Settings): Boolean =
        DayOfWeek.values().any { active.week.getValue(it).startMinute != requested.week.getValue(it).startMinute }
}
