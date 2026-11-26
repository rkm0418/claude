package app.harulock.core

import java.time.DayOfWeek.FRIDAY
import java.time.DayOfWeek.SATURDAY
import java.time.DayOfWeek.THURSDAY
import java.time.DayOfWeek.WEDNESDAY
import org.junit.Assert.assertEquals
import org.junit.Test

class DayClockTest {
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
}
