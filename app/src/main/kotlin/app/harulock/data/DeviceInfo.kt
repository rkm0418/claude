package app.harulock.data

import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.net.Uri
import android.os.Build
import android.telecom.TelecomManager
import android.view.inputmethod.InputMethodManager
import app.harulock.core.DeviceApps

fun deviceApps(ctx: Context): DeviceApps = DeviceApps(
    candidates = DeviceInfo.candidates(ctx),
    self = ctx.packageName,
    homes = DeviceInfo.homes(ctx),
    dialers = DeviceInfo.dialers(ctx),
    keyboards = DeviceInfo.keyboards(ctx),
)

/** 설치된 앱 조회. 전체를 보려면 `QUERY_ALL_PACKAGES`가 필요하다. */
object DeviceInfo {
    /** 기본 전화 앱이 아니어도 긴급 신고에 쓰이므로 정지하지 않는 안전 앱. */
    private val SAFETY_APPS = setOf("com.google.android.apps.safetyhub", "com.sec.android.app.safetyassurance")

    /** 사용자 잠금 해제 전에는 기본값이 direct boot 지원 구성요소만 찾으므로 둘 다 지정한다. */
    private const val ANY_BOOT_STATE =
        PackageManager.MATCH_DIRECT_BOOT_AWARE or PackageManager.MATCH_DIRECT_BOOT_UNAWARE

    fun installed(ctx: Context): List<ApplicationInfo> {
        val pm = ctx.packageManager
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pm.getInstalledApplications(PackageManager.ApplicationInfoFlags.of(0L))
        } else {
            @Suppress("DEPRECATION")
            pm.getInstalledApplications(0)
        }
    }

    /** 정지 후보: 실행 아이콘이 있는 앱과 사용자가 설치한 앱. */
    fun candidates(ctx: Context): Set<String> {
        val launchable = handlers(ctx, Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER))
            .map { it.activityInfo.packageName }
        val userInstalled = installed(ctx)
            .filter { it.flags and ApplicationInfo.FLAG_SYSTEM == 0 }
            .map { it.packageName }
        return (launchable + userInstalled).toSet()
    }

    fun homes(ctx: Context): Set<String> =
        handlers(ctx, Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME))
            .map { it.activityInfo.packageName }
            .toSet()

    /** 현재 기본 전화 앱, 다이얼 화면을 여는 시스템 앱, 안전 앱. */
    fun dialers(ctx: Context): Set<String> {
        val default = ctx.getSystemService(TelecomManager::class.java)?.defaultDialerPackage
        // 번호가 있는 다이얼만 받는 앱도 찾는다.
        val system = listOf(Intent(Intent.ACTION_DIAL), Intent(Intent.ACTION_DIAL, Uri.parse("tel:")))
            .flatMap { handlers(ctx, it) }
            .filter { it.activityInfo.applicationInfo.flags and ApplicationInfo.FLAG_SYSTEM != 0 }
            .map { it.activityInfo.packageName }
        return (listOfNotNull(default) + system).toSet() + SAFETY_APPS
    }

    /** 사용 설정된 입력기. */
    fun keyboards(ctx: Context): Set<String> =
        ctx.getSystemService(InputMethodManager::class.java)
            .enabledInputMethodList
            .map { it.packageName }
            .toSet()

    private fun handlers(ctx: Context, intent: Intent): List<ResolveInfo> {
        val pm = ctx.packageManager
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pm.queryIntentActivities(intent, PackageManager.ResolveInfoFlags.of(ANY_BOOT_STATE.toLong()))
        } else {
            @Suppress("DEPRECATION")
            pm.queryIntentActivities(intent, ANY_BOOT_STATE)
        }
    }
}
