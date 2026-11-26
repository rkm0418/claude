package app.harulock.core

import java.time.DayOfWeek.FRIDAY
import java.time.DayOfWeek.MONDAY
import java.time.DayOfWeek.TUESDAY
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SettingsRulesTest {
    private val base = Settings(week(120), setOf("a", "b"))

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
        assertEquals(base, c.active)
        assertEquals(240, c.pending!!.week[MONDAY]!!.startMinute)
    }

    @Test fun unarmed_isImmediate() {
        val req = Settings(week(600), setOf("z"))
        assertEquals(Change(req, null), SettingsRules.request(base, req, false))
    }

    @Test fun limitIsMinimumPerWeekday() {
        val active = Settings(week(120) + (FRIDAY to DayRule(90, 300)), setOf("a"))
        val req = Settings(week(60) + (TUESDAY to DayRule(200, 300)), setOf("a"))
        val c = SettingsRules.request(active, req, true)
        assertEquals(60, c.active.week[MONDAY]!!.limitMinutes)
        assertEquals(60, c.active.week[FRIDAY]!!.limitMinutes)
        assertEquals(120, c.active.week[TUESDAY]!!.limitMinutes)
        assertEquals(req, c.pending)
    }

    @Test fun allowedIsIntersection_evenWhenEmpty() {
        val req = Settings(week(120), setOf("c"))
        val c = SettingsRules.request(base, req, true)
        assertEquals(emptySet<String>(), c.active.allowed)
        assertEquals(req, c.pending)
    }

    @Test fun equalToResult_isNotPending() {
        val req = Settings(week(120), setOf("a"))
        val c = SettingsRules.request(base, req, true)
        assertEquals(Change(req, null), c)
        assertNull(c.pending)
    }

    @Test fun armedStrictAndLooserMixed_appliesStricterNowQueuesRest() {
        val req = Settings(week(120) + (MONDAY to DayRule(30, 300)) + (TUESDAY to DayRule(200, 300)), setOf("a", "b"))
        val c = SettingsRules.request(base, req, true)
        assertEquals(30, c.active.week[MONDAY]!!.limitMinutes)
        assertEquals(120, c.active.week[TUESDAY]!!.limitMinutes)
        assertEquals(req, c.pending)
    }
}
