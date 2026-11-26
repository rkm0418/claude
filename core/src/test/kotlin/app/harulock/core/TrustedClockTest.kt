package app.harulock.core

import java.time.Duration
import org.junit.Assert.assertEquals
import org.junit.Test

class TrustedClockTest {
    private val a = ClockAnchor(at("2026-11-26T10:00"), 1_000_000, 3)

    @Test fun sameBoot_ignoresWallChange() = assertEquals(at("2026-11-26T10:01"),
        TrustedClock.now(a, at("2027-01-01T00:00"), 1_060_000, 3).first)

    @Test fun reboot_neverGoesBack() = assertEquals(a.wall,
        TrustedClock.now(a, at("2026-11-26T09:00"), 5_000, 4).first)

    @Test fun reboot_movesForward() = assertEquals(at("2026-11-26T12:00"),
        TrustedClock.now(a, at("2026-11-26T12:00"), 5_000, 4).first)

    @Test fun noAnchor_usesWall() = assertEquals(at("2026-11-26T12:00"),
        TrustedClock.now(null, at("2026-11-26T12:00"), 5_000, 4).first)

    @Test fun returnedAnchor_isBasedOnResultTime() = assertEquals(
        ClockAnchor(at("2026-11-26T10:01"), 1_060_000, 3),
        TrustedClock.now(a, at("2027-01-01T00:00"), 1_060_000, 3).second)

    @Test fun rebootAnchor_isBasedOnResultTime() = assertEquals(
        ClockAnchor(at("2026-11-26T12:00"), 5_000, 4),
        TrustedClock.now(a, at("2026-11-26T12:00"), 5_000, 4).second)
}
