package app.harulock.core

import app.harulock.core.LockReason.INSTANT
import app.harulock.core.LockReason.LIMIT
import app.harulock.core.LockReason.PERMISSION_MISSING
import app.harulock.core.UsageEvent.Restart
import app.harulock.core.UsageEvent.Resumed
import app.harulock.core.UsageEvent.Screen
import java.time.DayOfWeek.FRIDAY
import java.time.DayOfWeek.MONDAY
import java.time.DayOfWeek.SATURDAY
import java.time.DayOfWeek.SUNDAY
import java.time.DayOfWeek.THURSDAY
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class EngineTest {
    private fun s(t: String, limit: Int = 120) = Engine.arm(Settings(week(limit), emptySet()), at(t), SEOUL)
    private fun step(st: CoreState, t: String, vararg e: UsageEvent) =
        Engine.step(st, e.toList(), at(t), SEOUL, emptySet())
    private fun game(t: String) = Resumed(at(t), "game", "A")

    @Test fun usageAcrossBoundary_splits() {
        val r = step(s("2026-11-26T04:50"), "2026-11-26T05:10", game("2026-11-26T04:50"))
        assertEquals(THURSDAY, r.period.day)
        assertEquals(600_000, r.meter.usedMillis)
    }

    @Test fun startChange_nextPeriodAtLeast24h() {
        val st = s("2026-11-26T06:00").copy(pending = Settings(week(120, 240), emptySet()))
        val r = step(st, "2026-11-27T05:00")
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-29T04:00")), r.period)
    }

    @Test fun offForDays_resetsOnceAndAppliesPending() {
        val st = s("2026-11-26T06:00").copy(pending = Settings(week(180), emptySet()))
        val r = step(st, "2026-11-30T12:00")
        assertEquals(180, r.settings.week[MONDAY]!!.limitMinutes)
        assertNull(r.pending)
        assertEquals(0, r.meter.usedMillis)
        assertEquals(at("2026-11-30T05:00"), r.period.start)
    }

    @Test fun limitReached_locks() {
        val r = step(s("2026-11-26T10:00", 1), "2026-11-26T10:01", game("2026-11-26T10:00"))
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

    @Test fun arm_startsArmedWithNothingCounted() = assertEquals(
        CoreState(
            settings = Settings(week(120), emptySet()),
            pending = null,
            armed = true,
            period = Period(THURSDAY, at("2026-11-26T05:00"), at("2026-11-27T05:00")),
            meter = MeterState(at("2026-11-26T10:00")),
            instantUntil = null,
        ),
        s("2026-11-26T10:00"))

    @Test fun beforeBoundary_keepsUsageAndPending() {
        val pending = Settings(week(180), emptySet())
        val st = s("2026-11-26T10:00").copy(pending = pending)
        val r = step(st, "2026-11-27T04:59", game("2026-11-26T10:00"))
        assertEquals(st.period, r.period)
        assertEquals(pending, r.pending)
        assertEquals(st.settings, r.settings)
        assertEquals(68_340_000, r.meter.usedMillis)
    }

    @Test fun reset_withoutPending_keepsSettingsAndAppState() {
        val a = step(s("2026-11-26T10:00"), "2026-11-26T10:30", game("2026-11-26T10:00"))
        val r = step(a, "2026-11-27T05:07")
        assertEquals(a.settings, r.settings)
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-28T05:00")), r.period)
        assertEquals(setOf("game/A"), r.meter.resumed)
        assertEquals(420_000, r.meter.usedMillis)
    }

    @Test fun offForDays_eventsWhileAway_onlyUpdateAppState() {
        val st = step(s("2026-11-26T10:00"), "2026-11-26T10:05", game("2026-11-26T10:00"))
        val r = step(st, "2026-11-30T12:00",
            Restart(at("2026-11-30T11:50")), Screen(at("2026-11-30T11:50"), true), game("2026-11-30T11:55"))
        assertEquals(300_000, r.meter.usedMillis)
        assertEquals(at("2026-11-30T12:00"), r.meter.countedUntil)
    }

    @Test fun offForDays_shutdownBeforePeriodStart_staysOff() {
        val st = step(s("2026-11-26T10:00"), "2026-11-26T10:05", game("2026-11-26T10:00"))
        val r = step(st, "2026-11-30T12:00", Screen(at("2026-11-27T08:00"), false))
        assertEquals(0, r.meter.usedMillis)
        assertEquals(false, r.meter.screenOn)
    }

    @Test fun overlappingEventsAfterReset_notDoubleCounted() {
        val ev = game("2026-11-27T04:59")
        val a = step(s("2026-11-26T10:00"), "2026-11-27T05:05", ev)
        val r = step(a, "2026-11-27T05:10", ev)
        assertEquals(600_000, r.meter.usedMillis)
    }

    @Test fun newlyAllowedApp_freeOnlyAfterReset() {
        val st = s("2026-11-26T10:00").copy(pending = Settings(week(120), setOf("game")))
        val before = step(st, "2026-11-26T10:10", game("2026-11-26T10:00"))
        assertEquals(600_000, before.meter.usedMillis)
        assertEquals(0, step(before, "2026-11-27T06:00").meter.usedMillis)
    }

    @Test fun allowedAndAlwaysFreeApps_notCounted() {
        val st = Engine.arm(Settings(week(), setOf("ok")), at("2026-11-26T10:00"), SEOUL)
        val events = listOf(Resumed(at("2026-11-26T10:00"), "ok", "A"), Resumed(at("2026-11-26T10:00"), "home", "A"))
        val r = Engine.step(st, events, at("2026-11-26T10:10"), SEOUL, setOf("home"))
        assertEquals(0, r.meter.usedMillis)
    }

    @Test fun startChange_noNewBudgetAtEarlierNewStart() {
        val st = s("2026-11-26T06:00").copy(pending = Settings(week(120, 240), emptySet()))
        val a = step(st, "2026-11-27T05:00")
        val b = step(a, "2026-11-28T04:00", game("2026-11-28T03:50"))
        val c = step(b, "2026-11-29T03:59", Screen(at("2026-11-28T04:00"), false))
        assertEquals(a.period, c.period)
        assertEquals(600_000, c.meter.usedMillis)

        val d = step(c, "2026-11-29T04:00")
        assertEquals(Period(SUNDAY, at("2026-11-29T04:00"), at("2026-11-30T04:00")), d.period)
        assertEquals(0, d.meter.usedMillis)
    }

    @Test fun startChange_laterStart_extendsToNewStart() {
        val st = s("2026-11-26T06:00").copy(pending = Settings(week(120, 360), emptySet()))
        val r = step(st, "2026-11-27T05:00")
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-28T06:00")), r.period)
    }

    @Test fun startChange_onOtherWeekdayOnly_stillHolds24h() {
        val newWeek = week() + (SATURDAY to DayRule(120, 240))
        val st = s("2026-11-26T06:00").copy(pending = Settings(newWeek, emptySet()))
        val r = step(st, "2026-11-27T05:00")
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-29T05:00")), r.period)
    }

    @Test fun startChange_lateStep_countsFromBoundary() {
        val st = s("2026-11-26T06:00").copy(pending = Settings(week(120, 240), emptySet()))
        val r = step(st, "2026-11-28T12:00", game("2026-11-28T11:00"))
        assertEquals(Period(FRIDAY, at("2026-11-27T05:00"), at("2026-11-29T04:00")), r.period)
        assertEquals(3_600_000, r.meter.usedMillis)
    }

    @Test fun startChange_offPastStretchedEnd_usesCurrentPeriod() {
        val st = s("2026-11-26T06:00").copy(pending = Settings(week(120, 240), emptySet()))
        val r = step(st, "2026-11-29T04:00")
        assertEquals(Period(SUNDAY, at("2026-11-29T04:00"), at("2026-11-30T04:00")), r.period)
        assertEquals(at("2026-11-29T04:00"), r.meter.countedUntil)
    }

    @Test fun stretchedPeriod_usesBoundaryWeekdayLimit() {
        val newWeek = week(120, 240) + (FRIDAY to DayRule(30, 240))
        val st = s("2026-11-26T06:00").copy(pending = Settings(newWeek, emptySet()))
        val r = step(st, "2026-11-28T12:00")
        assertEquals(1_800_000, Engine.remainingMillis(r))
    }

    @Test fun clockEarlierThanPeriodStart_changesNothing() {
        val st = step(s("2026-11-26T10:00"), "2026-11-26T10:10", game("2026-11-26T10:00"))
            .copy(pending = Settings(week(180), emptySet()))
        assertEquals(st, step(st, "2026-11-20T10:00", game("2026-11-20T09:00")))
    }

    @Test fun clockSetBackAfterReset_doesNotResetAgain() {
        val a = step(s("2026-11-26T10:00"), "2026-11-27T05:10", game("2026-11-27T05:00"))
        val b = step(a, "2026-11-27T04:00")
        assertEquals(a, b)
        assertEquals(a, step(b, "2026-11-27T05:10"))
    }

    @Test fun longerInstantLock_extends() {
        val now = at("2026-11-26T10:00")
        val a = Engine.startInstantLock(s("2026-11-26T10:00"), 10, now)
        assertEquals(at("2026-11-26T11:00"), Engine.startInstantLock(a, 60, now).instantUntil)
    }

    @Test fun instantLock_acceptsOnly1To1440Minutes() {
        val st = s("2026-11-26T10:00")
        val now = at("2026-11-26T10:00")
        assertEquals(at("2026-11-26T10:01"), Engine.startInstantLock(st, 1, now).instantUntil)
        assertEquals(at("2026-11-27T10:00"), Engine.startInstantLock(st, 1440, now).instantUntil)
        for (minutes in listOf(Int.MIN_VALUE, -1, 0, 1441, Int.MAX_VALUE)) {
            assertThrows(IllegalArgumentException::class.java) { Engine.startInstantLock(st, minutes, now) }
        }
    }

    @Test fun unarmed_neverLocks() {
        val now = at("2026-11-26T10:00")
        val st = Engine.startInstantLock(s("2026-11-26T10:00", 1), 60, now)
            .copy(armed = false, meter = MeterState(now, usedMillis = 60_000))
        assertTrue(Engine.lockReasons(st, now, false).isEmpty())
    }

    @Test fun allReasons_reportedTogether() {
        val now = at("2026-11-26T10:00")
        val st = Engine.startInstantLock(s("2026-11-26T10:00", 1), 60, now)
            .copy(meter = MeterState(now, usedMillis = 60_000))
        assertEquals(setOf(LIMIT, INSTANT, PERMISSION_MISSING), Engine.lockReasons(st, now, false))
    }

    @Test fun remaining_countsDownAndStopsAtZero() {
        val st = s("2026-11-26T10:00", 1)
        fun used(ms: Long) = st.copy(meter = st.meter.copy(usedMillis = ms))
        assertEquals(1, Engine.remainingMillis(used(59_999)))
        assertTrue(Engine.lockReasons(used(59_999), at("2026-11-26T10:00"), true).isEmpty())
        assertEquals(0, Engine.remainingMillis(used(90_000)))
    }

    @Test fun warning_firesOnceAtEachThreshold() {
        assertEquals(5, Engine.dueWarning(300_001, 300_000))
        assertEquals(1, Engine.dueWarning(61_000, 60_000))
        assertNull(Engine.dueWarning(600_000, 599_000))
        assertNull(Engine.dueWarning(60_000, 0))
        assertNull(Engine.dueWarning(0, 7_200_000))
    }
}
