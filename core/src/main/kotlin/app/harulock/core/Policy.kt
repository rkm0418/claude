package app.harulock.core

/** 기기에 설치된 앱 중 정지 판단에 필요한 패키지 묶음. */
data class DeviceApps(val candidates: Set<String>, val self: String, val homes: Set<String>,
  val dialers: Set<String>, val keyboards: Set<String>)

object Policy {
    private const val SYSTEM_UI = "com.android.systemui"
    private const val SETTINGS = "com.android.settings"

    /** 전화·응급 통화 경로. 정지하면 안 되므로 항상 제외한다. */
    private val PHONE_PATHS = setOf("com.android.phone", "com.android.server.telecom", "com.android.emergency")

    /** 정지하지 않는 패키지: 자기 앱, 홈, 기본 전화앱, 시스템 UI. */
    fun alwaysFree(d: DeviceApps): Set<String> =
        setOf(d.self) + d.homes + d.dialers + SYSTEM_UI

    /** 허용앱, 키보드, 설정, 전화 경로를 뺀 나머지 후보를 정지 대상으로 삼는다. */
    fun suspendTargets(d: DeviceApps, allowed: Set<String>): Set<String> =
        d.candidates - alwaysFree(d) - allowed - d.keyboards - SETTINGS - PHONE_PATHS

    /**
     * 잠금이 무장되어 있고 권한이 정상일 때, 설정 화면에 앱 이름이 보이면 닫는다.
     * 권한이 부족하면 복구를 위해 설정 화면을 그대로 둔다.
     */
    fun shouldCloseSettings(pkg: String, texts: List<String>, appLabel: String, armed: Boolean, permissionsOk: Boolean): Boolean =
        armed && permissionsOk && pkg == SETTINGS && appLabel.isNotEmpty() && texts.any { it.contains(appLabel) }
}
