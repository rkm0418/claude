package app.harulock.core

import app.harulock.core.ReleaseStatus.Expired
import app.harulock.core.ReleaseStatus.None
import app.harulock.core.ReleaseStatus.Ready
import app.harulock.core.ReleaseStatus.Waiting
import java.time.Duration
import org.junit.Assert.assertEquals
import org.junit.Test

class EmergencyReleaseTest {
    private val t = at("2026-11-26T10:00")
    private fun st(min: Long) = EmergencyRelease.status(t, t.plus(Duration.ofMinutes(min)))

    @Test fun waiting() = assertEquals(Waiting(Duration.ofMinutes(1)), st(1439))
    @Test fun ready() = assertEquals(Ready(Duration.ofHours(24)), st(1440))
    @Test fun expired() = assertEquals(Expired, st(2880))
    @Test fun none() = assertEquals(None, EmergencyRelease.status(null, t))
    @Test fun waitingAtRequestInstant() = assertEquals(Waiting(Duration.ofHours(24)), st(0))
    @Test fun readyJustBeforeExpiry() = assertEquals(Ready(Duration.ofMinutes(1)), st(2879))
}
