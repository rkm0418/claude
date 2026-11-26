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

    @Test fun settingsStaysNotFreeWhenItIsAHome() {
        val h = d.copy(homes = setOf("home", "com.android.settings"))
        assertFalse("com.android.settings" in Policy.alwaysFree(h))
        assertFalse("com.android.settings" in Policy.suspendTargets(h, emptySet()))
    }
    @Test fun telecomEmergencySystemUiNeverSuspended() {
        val t = d.copy(candidates = setOf("self","home","dial","kb","com.android.settings","com.android.phone",
          "com.android.server.telecom","com.android.emergency","com.android.systemui","ok","game"))
        assertEquals(setOf("game"), Policy.suspendTargets(t, setOf("ok")))
    }
    @Test fun unarmedNeverClosesSettings() =
      assertFalse(Policy.shouldCloseSettings("com.android.settings", listOf("하루잠금"), "하루잠금", false, true))
    @Test fun storesAndBrowsersNeedConfirm() {
        assertTrue(Policy.needsAllowConfirm("com.android.vending", emptySet()))
        assertTrue(Policy.needsAllowConfirm("com.sec.android.app.samsungapps", emptySet()))
        assertTrue(Policy.needsAllowConfirm("browser", setOf("browser")))
        assertFalse(Policy.needsAllowConfirm("game", setOf("browser")))
    }
}
