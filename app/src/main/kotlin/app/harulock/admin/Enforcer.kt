package app.harulock.admin

import android.app.admin.DevicePolicyManager
import android.content.Context
import android.content.pm.ApplicationInfo
import android.util.Log
import app.harulock.core.Policy
import app.harulock.data.DeviceInfo
import app.harulock.data.deviceApps

/** 앱 정지를 실행한다. 정지를 요청한 패키지를 기억해 두고, 대상에서 빠지면 푼다. */
class Enforcer(ctx: Context) {
    private val context = ctx.applicationContext
    private val dpm = context.getSystemService(DevicePolicyManager::class.java)
    private val admin = AdminReceiver.component(context)
    private val prefs = context.createDeviceProtectedStorageContext()
        .getSharedPreferences("enforcer", Context.MODE_PRIVATE)

    /**
     * 잠겼으면 [Policy.suspendTargets]를 정지하고, 대상이 아니게 된 앱은 푼다. 반복 호출해도 된다.
     * 앱 목록을 읽지 못하면 아무것도 바꾸지 않는다. 전화 앱을 잘못 정지하지 않기 위해서다.
     */
    fun apply(locked: Boolean, allowed: Set<String>) {
        val previous = remembered()
        if (!locked && previous.isEmpty()) return
        runCatching {
            val targets = if (locked) Policy.suspendTargets(deviceApps(context), allowed) else emptySet()
            val installed = DeviceInfo.installed(context)
            // 도중에 프로세스가 죽어도 풀 수 있도록 정지보다 먼저 기록한다.
            remember(previous + targets)

            val alreadySuspended = suspendedIn(installed)
            // 풀지 못했고 아직 정지된 앱만 남겨 두고 다음에 다시 시도한다.
            // 바꿀 수 없는 패키지는 정지된 적도 없으므로 기억에서 빠진다.
            val stuck = setSuspended(previous - targets, false).intersect(alreadySuspended)

            // 이미 정지된 앱은 건너뛴다. 다시 설치되어 정지가 풀린 앱은 여기서 다시 정지된다.
            setSuspended(targets - alreadySuspended, true)

            remember(targets + stuck)
        }.onFailure { Log.w(TAG, "apply failed", it) }
    }

    /**
     * 기억한 목록이 틀렸거나 없어도 풀리도록 설치된 모든 앱의 정지를 해제한다.
     * 앱 목록을 읽었고 정지된 채 남은 앱이 없으면 true. false면 다시 불러야 한다.
     *
     * 시스템은 `android` 같은 바꿀 수 없는 패키지를 항상 실패로 돌려주므로 실패 목록만으로 판단하지 않는다.
     * 실패한 패키지는 상태가 바뀌지 않았으므로 호출 전 목록의 FLAG_SUSPENDED로 아직 정지되었는지 본다.
     */
    fun unsuspendAll(): Boolean {
        val previous = remembered()
        val installed = runCatching { DeviceInfo.installed(context) }
            .onFailure { Log.w(TAG, "cannot list apps", it) }
            .getOrNull()
        val names = installed.orEmpty().mapTo(HashSet()) { it.packageName }
        val failed = setSuspended(previous + names, false)
        if (installed == null) {
            remember(previous.intersect(failed))
            return false
        }
        val stuck = failed.intersect(suspendedIn(installed))
        remember(stuck)
        return stuck.isEmpty()
    }

    private fun suspendedIn(installed: List<ApplicationInfo>): Set<String> = installed
        .filter { it.flags and ApplicationInfo.FLAG_SUSPENDED != 0 }
        .mapTo(HashSet()) { it.packageName }

    /** 바꾸지 못한 패키지를 돌려준다. 호출 자체가 실패하면 전부다. */
    private fun setSuspended(packages: Set<String>, suspended: Boolean): Set<String> {
        if (packages.isEmpty()) return emptySet()
        return runCatching {
            dpm.setPackagesSuspended(admin, packages.toTypedArray(), suspended).toSet()
        }.onFailure { Log.w(TAG, "setPackagesSuspended($suspended) failed", it) }
            .getOrDefault(packages)
    }

    private fun remembered(): Set<String> = prefs.getStringSet(KEY, null)?.toSet() ?: emptySet()

    private fun remember(packages: Set<String>) {
        if (packages != remembered()) prefs.edit().putStringSet(KEY, packages).commit()
    }

    private companion object {
        const val TAG = "Enforcer"
        const val KEY = "suspended"
    }
}
