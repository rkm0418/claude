package app.harulock.core

import java.time.DayOfWeek
import java.time.Instant

/** 요일 하나의 규칙. [startMinute]는 하루가 시작하는 시각(자정 기준 분). */
data class DayRule(val limitMinutes: Int, val startMinute: Int) {
    init {
        require(limitMinutes in 1..1440) { "limitMinutes out of range: $limitMinutes" }
        require(startMinute in 0..1439) { "startMinute out of range: $startMinute" }
    }
}

data class Settings(val week: Map<DayOfWeek, DayRule>, val allowed: Set<String>) {
    init {
        require(week.size == DayOfWeek.values().size) { "week must have all 7 days: ${week.keys}" }
    }
}

/** 하루 한 번의 사용 기간 `[start, end)`. [day]는 적용되는 요일. */
data class Period(val day: DayOfWeek, val start: Instant, val end: Instant)
