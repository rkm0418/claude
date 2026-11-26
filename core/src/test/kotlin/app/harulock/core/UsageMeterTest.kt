package app.harulock.core

import app.harulock.core.UsageEvent.Keyguard
import app.harulock.core.UsageEvent.Paused
import app.harulock.core.UsageEvent.Restart
import app.harulock.core.UsageEvent.Resumed
import app.harulock.core.UsageEvent.Screen
import java.time.Duration
import java.time.Instant
import org.junit.Assert.assertEquals
import org.junit.Test

class UsageMeterTest {
    private val t0 = at("2026-11-26T10:00")
    private fun m(n: Long): Instant = t0.plus(Duration.ofMinutes(n))
    private fun r(n: Long, pkg: String, activity: String = "A") = Resumed(m(n), pkg, activity)
    private fun p(n: Long, pkg: String, activity: String = "A") = Paused(m(n), pkg, activity)

    private fun used(vararg e: UsageEvent, free: Set<String> = emptySet()) =
        UsageMeter.advance(MeterState(t0), e.toList(), m(10), free).usedMillis

    @Test fun countsForeground() = assertEquals(600_000, used(r(0, "game")))

    @Test fun freeApp_notCounted() = assertEquals(0, used(r(0, "home"), free = setOf("home")))

    @Test fun screenOff_stops() = assertEquals(300_000, used(r(0, "game"), Screen(m(5), false)))

    @Test fun keyguard_stops() = assertEquals(120_000, used(r(0, "game"), Keyguard(m(2), true)))

    @Test fun splitScreen_counts() =
        assertEquals(600_000, used(r(0, "ok"), r(0, "game"), free = setOf("ok")))

    @Test fun restartGap_notCounted() = assertEquals(0, UsageMeter.advance(
        MeterState(t0, resumed = setOf("game/A")), listOf(Restart(m(120))), m(120), emptySet()).usedMillis)

    @Test fun replayedEvents_notDoubleCounted() {
        val ev = listOf(r(0, "game"))
        val a = UsageMeter.advance(MeterState(t0), ev, m(5), emptySet())
        assertEquals(600_000, UsageMeter.advance(a, ev, m(10), emptySet()).usedMillis)
    }

    @Test fun paused_stops() = assertEquals(180_000, used(r(0, "game"), p(3, "game")))

    @Test fun otherActivityStillResumed_keepsCounting() =
        assertEquals(600_000, used(r(0, "game", "A"), r(2, "game", "B"), p(3, "game", "A")))

    @Test fun unsortedEvents_processedInTimeOrder() =
        assertEquals(180_000, used(p(5, "game"), r(2, "game")))

    @Test fun eventsAfterUntil_ignored() = assertEquals(
        MeterState(m(10), 600_000, setOf("game/A")),
        UsageMeter.advance(MeterState(t0),
            listOf(r(0, "game"), Screen(m(11), false), Restart(m(12))), m(10), emptySet()))

    @Test fun eventBeforeCountedUntil_changesStateOnly() = assertEquals(
        MeterState(m(10), 300_000, setOf("game/A")),
        UsageMeter.advance(MeterState(m(5)), listOf(r(1, "game")), m(10), emptySet()))

    @Test fun restart_dropsOnlyPrecedingInterval_andResetsState() = assertEquals(
        // 0~2분은 세고, 2분~재시작 구간은 세지 않는다.
        MeterState(m(10), 120_000, emptySet(), screenOn = false),
        UsageMeter.advance(MeterState(t0),
            listOf(r(0, "game"), Keyguard(m(2), false), Restart(m(7))), m(10), emptySet()))

    @Test fun countingResumesAfterRestart() =
        assertEquals(180_000, used(Restart(m(5)), Screen(m(6), true), r(7, "game")))

    @Test fun earlierUntil_leavesStateUnchanged() {
        val ev = listOf(r(1, "game"), p(5, "game"))
        val a = UsageMeter.advance(MeterState(t0), ev, m(8), emptySet())
        assertEquals(a, UsageMeter.advance(a, ev, m(3), emptySet()))
    }

    @Test fun replayingAppliedSuffix_changesNothing() {
        val ev = listOf(
            r(0, "game"), Screen(m(1), false), Keyguard(m(1), true), Screen(m(3), true),
            Keyguard(m(4), false), r(5, "chat"), p(5, "game"), Restart(m(8)),
            Screen(m(9), true), r(10, "game"), p(12, "game"), r(13, "chat"))
        for (split in 0L..15L) {
            val (applied, fresh) = ev.partition { it.at <= m(split) }
            val first = UsageMeter.advance(MeterState(t0), applied, m(split), emptySet())
            val expected = UsageMeter.advance(first, fresh, m(15), emptySet())
            for (from in 0..applied.size) {
                val overlap = applied.drop(from) + fresh
                assertEquals("split=$split from=$from",
                    expected, UsageMeter.advance(first, overlap, m(15), emptySet()))
            }
        }
    }
}
