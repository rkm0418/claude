package app.harulock.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PolicyTest {
    val d = DeviceApps(setOf("self","home","dial","kb","com.android.settings","com.android.phone","ok","game"),
      "self", setOf("home"), setOf("dial"), setOf("kb"))
    @Test fun onlyOrdinaryAppsSuspended() = assertEquals(setOf("game"), Policy.suspendTargets(d, setOf("ok")))
    @Test fun newDialerIsProtected() =
      assertFalse("game" in Policy.suspendTargets(d.copy(dialers = setOf("game")), emptySet()))
    @Test fun settingsNotFree() = assertFalse("com.android.settings" in Policy.alwaysFree(d))
    fun close(pkg: String, ok: Boolean) = Policy.shouldCloseSettings(pkg, listOf("하루잠금"), "하루잠금", true, ok)
    @Test fun closesOwnSettingsPage() = assertTrue(close("com.android.settings", true))
    @Test fun leavesOpenForRepair() = assertFalse(close("com.android.settings", false))
    @Test fun ignoresOtherApps() = assertFalse(close("game", true))
}
