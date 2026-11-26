package app.harulock.core

import java.time.DayOfWeek
import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId

/** 요일별 시작 시각으로 하루의 경계를 정한다. */
object DayClock {
    /** [now]가 속한 기간. 그날의 시작 시각 전이면 전날에 속한다. */
    fun periodAt(now: Instant, week: Map<DayOfWeek, DayRule>, zone: ZoneId): Period {
        // 시간대 전환으로 날짜가 되돌아가는 경우까지 포함하도록 하루 뒤부터 거슬러 찾는다.
        var date = now.atZone(zone).toLocalDate().plusDays(1)
        while (startOf(date, week, zone) > now) date = date.minusDays(1)
        return Period(date.dayOfWeek, startOf(date, week, zone), startOf(date.plusDays(1), week, zone))
    }

    /** [t]와 같거나 그 뒤에 오는 첫 시작 시각. */
    fun firstStartAtOrAfter(t: Instant, week: Map<DayOfWeek, DayRule>, zone: ZoneId): Instant {
        var date = t.atZone(zone).toLocalDate().minusDays(1)
        while (startOf(date, week, zone) < t) date = date.plusDays(1)
        return startOf(date, week, zone)
    }

    private fun startOf(date: LocalDate, week: Map<DayOfWeek, DayRule>, zone: ZoneId): Instant {
        val minute = week.getValue(date.dayOfWeek).startMinute
        return date.atTime(LocalTime.of(minute / 60, minute % 60)).atZone(zone).toInstant()
    }
}
