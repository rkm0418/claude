package app.harulock.core

import java.time.DayOfWeek
import kotlin.math.min

/** 설정 변경 요청의 결과. [active]는 지금 적용되는 설정, [pending]은 잠금 중 대기하는 요청(없으면 null). */
data class Change(val active: Settings, val pending: Settings?)

object SettingsRules {
    /**
     * 잠금 시작 전([armed] = false)에는 요청을 즉시 전부 적용한다.
     * 잠금 후에는 요일별 한도의 작은 값, 기존 시작 시각, 허용앱 교집합만 즉시 적용하고,
     * 요청이 그 결과와 다르면 요청 전체를 [Change.pending]에 대기시킨다.
     */
    fun request(active: Settings, requested: Settings, armed: Boolean): Change {
        if (!armed) return Change(requested, null)

        val immediate = Settings(
            week = DayOfWeek.values().associateWith { day ->
                DayRule(
                    limitMinutes = min(active.week.getValue(day).limitMinutes, requested.week.getValue(day).limitMinutes),
                    startMinute = active.week.getValue(day).startMinute,
                )
            },
            allowed = active.allowed intersect requested.allowed,
        )
        return Change(immediate, if (requested == immediate) null else requested)
    }
}
