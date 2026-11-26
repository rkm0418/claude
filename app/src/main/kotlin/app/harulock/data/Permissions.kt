package app.harulock.data

import android.app.AppOpsManager
import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.os.Process
import android.provider.Settings

/** 잠금 판단에 필요한 권한. 하나라도 없으면 잠근다(설정 화면은 열어 둔다). */
object Permissions {
    /** Task 10의 접근성 서비스. 클래스가 생기기 전에도 쓰도록 이름으로 둔다. */
    const val WATCH_SERVICE = "app.harulock.service.SettingsWatchService"

    fun all(ctx: Context): Boolean = usage(ctx) && accessibility(ctx)

    /** 사용 정보 접근. 앱 작업 기본값이면 권한 부여 여부로 판단한다. */
    fun usage(ctx: Context): Boolean = runCatching {
        val ops = ctx.getSystemService(AppOpsManager::class.java)
        val mode = ops.unsafeCheckOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), ctx.packageName)
        if (mode == AppOpsManager.MODE_DEFAULT) {
            ctx.checkSelfPermission(android.Manifest.permission.PACKAGE_USAGE_STATS) == PackageManager.PERMISSION_GRANTED
        } else {
            mode == AppOpsManager.MODE_ALLOWED
        }
    }.getOrDefault(false)

    /** 접근성 목록에 설정 감시 서비스가 켜져 있는지. */
    fun accessibility(ctx: Context): Boolean = runCatching {
        val enabled = Settings.Secure.getString(ctx.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
            ?: return@runCatching false
        val mine = ComponentName(ctx.packageName, WATCH_SERVICE)
        enabled.split(':').any { ComponentName.unflattenFromString(it.trim()) == mine }
    }.getOrDefault(false)
}
