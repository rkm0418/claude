package app.harulock.core

/** 기기 조회 결과의 한 항목: 패키지 이름과 시스템 앱 여부. */
data class FoundApp(val pkg: String, val system: Boolean)

/** 기기에서 조회한 값으로 홈과 키보드 패키지를 고른다. 조회는 앱이 하고 여기서는 값만 정한다. */
object DeviceSelect {
    /** 기본 홈이 정해지지 않았을 때 시스템이 돌려주는 고르기 화면의 패키지. */
    private const val RESOLVER = "android"

    /**
     * 시스템 홈 앱과 지금의 기본 홈. 홈을 선언한 다른 앱은 기본 홈일 때만 든다(R18).
     * 그렇지 않으면 홈을 선언하기만 한 앱이 시간을 쓰지 않고 정지되지도 않는다.
     */
    fun homes(handlers: Collection<FoundApp>, defaultHome: String?): Set<String> =
        (handlers.filter { it.system }.map { it.pkg } + listOfNotNull(defaultHome)).toSet() - RESOLVER

    /** 기본 입력기와 사용 설정된 시스템 입력기. 다른 입력기는 기본일 때만 든다. */
    fun keyboards(defaultIme: String?, enabled: Collection<FoundApp>): Set<String> =
        (enabled.filter { it.system }.map { it.pkg } + listOfNotNull(imePackage(defaultIme))).toSet()

    /** `패키지/클래스` 꼴의 입력기 이름에서 패키지. 비었거나 꼴이 다르면 null. */
    fun imePackage(flattened: String?): String? {
        val text = flattened?.trim() ?: return null
        val slash = text.indexOf('/')
        if (slash <= 0) return null
        return text.substring(0, slash)
    }
}
