package app.harulock.admin

import android.app.admin.DevicePolicyManager
import android.content.Context
import android.os.UserManager
import android.util.Log
import app.harulock.BuildConfig

/**
 * 잠금을 우회하지 못하게 하는 기기 제한. [harden]이 거는 것은 모두 [relax]가 되돌린다.
 * 한 호출이 실패해도 나머지는 계속한다.
 */
class Guard(ctx: Context) {
    private val context = ctx.applicationContext
    private val dpm = context.getSystemService(DevicePolicyManager::class.java)
    private val admin = AdminReceiver.component(context)

    /** [harden] 전의 자동 시간 설정. 비상 해제 프로세스도 읽으므로 commit으로 쓴다. */
    private val before = context.createDeviceProtectedStorageContext()
        .getSharedPreferences("guard", Context.MODE_PRIVATE)

    fun isOwner(): Boolean = dpm.isDeviceOwnerApp(context.packageName)

    fun harden() {
        if (!isOwner()) return
        attempt("block uninstall") { dpm.setUninstallBlocked(admin, context.packageName, true) }
        attempt("disable user control") {
            dpm.setUserControlDisabledPackages(admin, listOf(context.packageName))
        }
        attempt("remember auto time") { remember(AUTO_TIME) { dpm.getAutoTimeEnabled(admin) } }
        attempt("enable auto time") { dpm.setAutoTimeEnabled(admin, true) }
        attempt("remember auto time zone") { remember(AUTO_TIME_ZONE) { dpm.getAutoTimeZoneEnabled(admin) } }
        attempt("enable auto time zone") { dpm.setAutoTimeZoneEnabled(admin, true) }
        RESTRICTIONS.forEach { key -> attempt(key) { dpm.addUserRestriction(admin, key) } }
        // 정식판만 USB 디버깅을 막는다. 시험판은 PC로 해제할 수 있어야 한다.
        if (BuildConfig.FINAL_GUARD) {
            attempt(UserManager.DISALLOW_DEBUGGING_FEATURES) {
                dpm.addUserRestriction(admin, UserManager.DISALLOW_DEBUGGING_FEATURES)
            }
        }
    }

    /**
     * 제한, 사용자 제어, 삭제 막기를 모두 되돌렸으면(또는 기기 소유자가 아니어서 할 것이 없으면) true.
     * false면 다시 불러야 한다. 자동 시간과 자동 시간대 복원은 실패해도 기록만 한다. 그것 때문에
     * 비상 해제가 기기 소유자를 끝내 해제하지 못하면 안 되기 때문이다.
     */
    fun relax(): Boolean {
        if (!isOwner()) return true
        // 디버깅 제한은 빌드 종류와 상관없이 항상 푼다.
        val results = (RESTRICTIONS + UserManager.DISALLOW_DEBUGGING_FEATURES).map { key ->
            attempt(key) { dpm.clearUserRestriction(admin, key) }
        } + listOf(
            attempt("enable user control") { dpm.setUserControlDisabledPackages(admin, emptyList()) },
            attempt("unblock uninstall") { dpm.setUninstallBlocked(admin, context.packageName, false) },
        )
        // 결과에 넣지 않는다(R24). 실패하면 기록이 남아, 다음 relax가 있으면(정리 재시도, 해제 재시도) 그때 다시 시도한다.
        // 비상 해제가 성공하면 기기 소유자가 풀리므로 다음 relax는 없고 자동 시간 설정이 켜진 채 남을 수 있다.
        attempt("restore auto time") { restore(AUTO_TIME) { dpm.setAutoTimeEnabled(admin, it) } }
        attempt("restore auto time zone") { restore(AUTO_TIME_ZONE) { dpm.setAutoTimeZoneEnabled(admin, it) } }
        return results.all { it }
    }

    /** 처음 한 번만 기록한다. 다시 [harden]해도 원래 값이 덮이지 않는다. */
    private fun remember(key: String, current: () -> Boolean) {
        if (!before.contains(key)) before.edit().putBoolean(key, current()).commit()
    }

    private fun restore(key: String, set: (Boolean) -> Unit) {
        if (!before.contains(key)) return
        set(before.getBoolean(key, true))
        before.edit().remove(key).commit()
    }

    private fun attempt(what: String, call: () -> Unit): Boolean =
        runCatching(call).onFailure { Log.w(TAG, "failed: $what", it) }.isSuccess

    private companion object {
        const val TAG = "Guard"
        const val AUTO_TIME = "autoTime"
        const val AUTO_TIME_ZONE = "autoTimeZone"

        val RESTRICTIONS = listOf(
            UserManager.DISALLOW_SAFE_BOOT,
            UserManager.DISALLOW_FACTORY_RESET,
            UserManager.DISALLOW_CONFIG_DATE_TIME,
            UserManager.DISALLOW_ADD_USER,
            UserManager.DISALLOW_ADD_MANAGED_PROFILE,
        )
    }
}
