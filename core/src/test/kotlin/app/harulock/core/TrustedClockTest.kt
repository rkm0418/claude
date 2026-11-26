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

    @Test fun sameBootCount_elapsedWentBack_isTreatedAsReboot() {
        val (now, next) = TrustedClock.now(a, at("2026-11-26T12:00"), 5_000, 3)
        assertEquals(at("2026-11-26T12:00"), now)
        assertEquals(ClockAnchor(at("2026-11-26T12:00"), 5_000, 3), next)
    }

    @Test fun sameBootCount_elapsedWentBack_neverGoesBack() = assertEquals(a.wall,
        TrustedClock.now(a, at("2026-11-26T09:00"), 5_000, 3).first)

    @Test fun sameBoot_equalElapsed_keepsAnchorTime() = assertEquals(a.wall,
        TrustedClock.now(a, at("2027-01-01T00:00"), 1_000_000, 3).first)
}
