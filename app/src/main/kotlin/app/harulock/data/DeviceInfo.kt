package app.harulock.data

import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.telecom.TelecomManager
import android.view.inputmethod.InputMethodManager
import app.harulock.core.DeviceApps
import app.harulock.core.DeviceSelect
import app.harulock.core.FoundApp

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

    /**
     * 시스템 홈 앱과 지금의 기본 홈(R18). 다른 홈 앱은 기본 홈일 때만 자유이고, 기본에서 빠지면
     * 다음 30초 재계산부터 정지 대상이 된다.
     */
    fun homes(ctx: Context): Set<String> {
        val intent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
        val found = handlers(ctx, intent).map { FoundApp(it.activityInfo.packageName, isSystem(it)) }
        return DeviceSelect.homes(found, defaultHome(ctx, intent))
    }

    /** 기본 홈 패키지. 정해지지 않았으면 고르기 화면("android")이 나오며, [DeviceSelect.homes]가 뺀다. */
    private fun defaultHome(ctx: Context, intent: Intent): String? {
        val pm = ctx.packageManager
        val flags = PackageManager.MATCH_DEFAULT_ONLY or ANY_BOOT_STATE
        val resolved = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pm.resolveActivity(intent, PackageManager.ResolveInfoFlags.of(flags.toLong()))
        } else {
            @Suppress("DEPRECATION")
            pm.resolveActivity(intent, flags)
        }
        return resolved?.activityInfo?.packageName
    }

    /** 현재 기본 전화 앱, 다이얼 화면을 여는 시스템 앱, 안전 앱. */
    fun dialers(ctx: Context): Set<String> {
        val default = ctx.getSystemService(TelecomManager::class.java)?.defaultDialerPackage
        // 번호가 있는 다이얼만 받는 앱도 찾는다.
        val system = listOf(Intent(Intent.ACTION_DIAL), Intent(Intent.ACTION_DIAL, Uri.parse("tel:")))
            .flatMap { handlers(ctx, it) }
            .filter { isSystem(it) }
            .map { it.activityInfo.packageName }
        return (listOfNotNull(default) + system).toSet() + SAFETY_APPS
    }

    /** 기본 입력기와 사용 설정된 시스템 입력기. 다른 입력기는 기본 입력기일 때만 정지하지 않는다. */
    fun keyboards(ctx: Context): Set<String> {
        val enabled = ctx.getSystemService(InputMethodManager::class.java)
            .enabledInputMethodList
            .map { FoundApp(it.packageName, it.serviceInfo.applicationInfo.flags and ApplicationInfo.FLAG_SYSTEM != 0) }
        val default = Settings.Secure.getString(ctx.contentResolver, Settings.Secure.DEFAULT_INPUT_METHOD)
        return DeviceSelect.keyboards(default, enabled)
    }

    /** 아무 웹 주소나 여는 앱(브라우저). 특정 주소만 여는 앱은 들지 않는다. 시스템 거르기 없이 전부 찾는다. */
    fun browsers(ctx: Context): Set<String> {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://example.com/"))
            .addCategory(Intent.CATEGORY_BROWSABLE)
        val flags = ANY_BOOT_STATE or PackageManager.MATCH_ALL
        val pm = ctx.packageManager
        val found = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pm.queryIntentActivities(intent, PackageManager.ResolveInfoFlags.of(flags.toLong()))
        } else {
            @Suppress("DEPRECATION")
            pm.queryIntentActivities(intent, flags)
        }
        return found.map { it.activityInfo.packageName }.toSet()
    }

    private fun isSystem(info: ResolveInfo): Boolean =
        info.activityInfo.applicationInfo.flags and ApplicationInfo.FLAG_SYSTEM != 0

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
