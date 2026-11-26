package app.harulock.core

import app.harulock.core.UsageEvent.Resumed
import java.time.DayOfWeek
import java.time.DayOfWeek.FRIDAY
import java.time.DayOfWeek.MONDAY
import java.time.DayOfWeek.THURSDAY
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DisplayTest {
    private fun armed(t: String, limit: Int = 120) = Engine.arm(Settings(week(limit), emptySet()), at(t), SEOUL)
    private fun used(s: CoreState, minutes: Long) = s.copy(meter = s.meter.copy(usedMillis = minutes * 60_000))
    private fun state(s: CoreState?, t: String, ok: Boolean = true) = Display.homeState(s, at(t), ok)

    @Test fun notArmed() {
        assertEquals(HomeState.NOT_ARMED, state(null, "2026-11-26T10:00"))
        assertEquals(HomeState.NOT_ARMED, state(armed("2026-11-26T10:00").copy(armed = false), "2026-11-26T10:00"))
    }

    @Test fun usingThenLowAtTenMinutes() {
        val s = armed("2026-11-26T10:00")
        assertEquals(HomeState.USING, state(used(s, 109), "2026-11-26T10:00"))
        assertEquals(HomeState.LOW, state(used(s, 110), "2026-11-26T10:00"))
    }

    @Test fun limitLocked() = assertEquals(HomeState.LIMIT_LOCKED, state(used(armed("2026-11-26T10:00"), 120), "2026-11-26T10:00"))

    @Test fun instantLocked() {
        val s = Engine.startInstantLock(armed("2026-11-26T10:00"), 30, at("2026-11-26T10:00"))
        assertEquals(HomeState.INSTANT_LOCKED, state(s, "2026-11-26T10:10"))
        assertEquals(HomeState.USING, state(s, "2026-11-26T10:30"))
    }

    @Test fun permissionFirst() {
        val s = Engine.startInstantLock(used(armed("2026-11-26T10:00"), 120), 30, at("2026-11-26T10:00"))
        assertEquals(HomeState.PERMISSION_LOCKED, state(s, "2026-11-26T10:10", ok = false))
    }

    @Test fun limitAndInstant_showsLaterEnd() {
        val s = used(armed("2026-11-26T10:00"), 120)
        // 기간은 다음 날 05:00에 끝난다.
        val short = Engine.startInstantLock(s, 60, at("2026-11-26T10:00"))
        assertEquals(HomeState.LIMIT_LOCKED, state(short, "2026-11-26T10:10"))
        val long = Engine.startInstantLock(s, 1440, at("2026-11-26T10:00"))
        assertEquals(HomeState.INSTANT_LOCKED, state(long, "2026-11-26T10:10"))
    }

    @Test fun ceilMinutes() {
        assertEquals(0, Display.ceilMinutes(0))
        assertEquals(0, Display.ceilMinutes(-5))
        assertEquals(1, Display.ceilMinutes(1))
        assertEquals(1, Display.ceilMinutes(60_000))
        assertEquals(2, Display.ceilMinutes(60_001))
    }

    @Test fun parseMinutes() {
        assertEquals(1, Display.parseMinutes("1"))
        assertEquals(1440, Display.parseMinutes(" 1440 "))
        assertNull(Display.parseMinutes("0"))
        assertNull(Display.parseMinutes("1441"))
        assertNull(Display.parseMinutes(""))
        assertNull(Display.parseMinutes("abc"))
        assertNull(Display.parseMinutes("99999999999"))
    }

    @Test fun defaultsAreR20() {
        assertEquals(7, Defaults.SETTINGS.week.size)
        assertTrue(Defaults.SETTINGS.week.values.all { it == DayRule(120, 300) })
        assertTrue(Defaults.SETTINGS.allowed.isEmpty())
    }

    @Test fun diff_listsOnlyChangedDaysAndApps() {
        val a = Settings(week(), setOf("x", "y"))
        val b = Settings(week() + (MONDAY to DayRule(180, 300)) + (FRIDAY to DayRule(120, 240)), setOf("y", "z"))
        val d = Display.diff(a, b)
        assertEquals(
            listOf(DayChange(MONDAY, 120, 180, 300, 300), DayChange(FRIDAY, 120, 120, 300, 240)),
            d.days,
        )
        assertEquals(setOf("z"), d.added)
        assertEquals(setOf("x"), d.removed)
        assertFalse(d.isEmpty)
        assertTrue(Display.diff(a, a).isEmpty)
    }

    @Test fun changesStart() {
        val a = Settings(week(), emptySet())
        assertFalse(Display.changesStart(a, Settings(week(200), setOf("x"))))
        assertTrue(Display.changesStart(a, Settings(week() + (DayOfWeek.SUNDAY to DayRule(120, 0)), emptySet())))
    }

    @Test fun nextPeriod_noPending_isNextDay() {
        val s = armed("2026-11-26T10:00")
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-28T05:00")), Engine.nextPeriod(s, SEOUL))
    }

    @Test fun nextPeriod_earlierStart_nearly48h_andMatchesStep() {
        val s = armed("2026-11-26T10:00").copy(pending = Settings(week(120, 240), emptySet()))
        val next = Engine.nextPeriod(s, SEOUL)
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-29T04:00")), next)
        val stepped = Engine.step(s, emptyList(), at("2026-11-27T05:00"), SEOUL, emptySet())
        assertEquals(next, stepped.period)
    }

    @Test fun nextPeriod_limitOnlyPending_isNextDay() {
        val s = armed("2026-11-26T10:00").copy(pending = Settings(week(300), emptySet()))
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-28T05:00")), Engine.nextPeriod(s, SEOUL))
        assertEquals(THURSDAY, s.period.day)
    }

    @Test fun usageStillCountsInLowState() {
        val s = armed("2026-11-26T10:00", 11)
        val r = Engine.step(s, listOf(Resumed(at("2026-11-26T10:00"), "game", "A")), at("2026-11-26T10:02"), SEOUL, emptySet())
        assertEquals(HomeState.LOW, state(r, "2026-11-26T10:02"))
    }
}
