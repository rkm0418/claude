package app.harulock.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DeviceSelectTest {
    private val launchers = listOf(
        FoundApp("com.sec.android.app.launcher", true),
        FoundApp("com.android.settings", true),
        FoundApp("third.launcher", false),
    )

    @Test fun homes_nonDefaultThirdPartyLauncherIsNotAHome() = assertEquals(
        setOf("com.sec.android.app.launcher", "com.android.settings"),
        DeviceSelect.homes(launchers, "com.sec.android.app.launcher"))

    @Test fun homes_defaultThirdPartyLauncherIsAHome() = assertEquals(
        setOf("com.sec.android.app.launcher", "com.android.settings", "third.launcher"),
        DeviceSelect.homes(launchers, "third.launcher"))

    @Test fun homes_resolverIsDropped() = assertEquals(
        setOf("com.sec.android.app.launcher", "com.android.settings"),
        DeviceSelect.homes(launchers + FoundApp("android", true), "android"))

    @Test fun homes_noDefault() = assertEquals(
        setOf("com.sec.android.app.launcher", "com.android.settings"),
        DeviceSelect.homes(launchers, null))

    private val imes = listOf(FoundApp("com.samsung.android.honeyboard", true), FoundApp("other.kb", false))

    @Test fun keyboards_defaultThirdPartyIsKept() = assertEquals(
        setOf("com.samsung.android.honeyboard", "other.kb"),
        DeviceSelect.keyboards("other.kb/.Ime", imes))

    @Test fun keyboards_nonDefaultThirdPartyIsDropped() = assertEquals(
        setOf("com.samsung.android.honeyboard"),
        DeviceSelect.keyboards("com.samsung.android.honeyboard/.Ime", imes))

    @Test fun keyboards_noDefault() = assertEquals(
        setOf("com.samsung.android.honeyboard"), DeviceSelect.keyboards(null, imes))

    @Test fun imePackage_parses() {
        assertEquals("a.b", DeviceSelect.imePackage("a.b/a.b.Ime"))
        assertNull(DeviceSelect.imePackage(""))
        assertNull(DeviceSelect.imePackage("noslash"))
        assertNull(DeviceSelect.imePackage("/cls"))
        assertNull(DeviceSelect.imePackage(null))
    }
}
