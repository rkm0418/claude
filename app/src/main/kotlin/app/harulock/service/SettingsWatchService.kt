package app.harulock.service

import android.accessibilityservice.AccessibilityService
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import app.harulock.R
import app.harulock.core.Policy
import app.harulock.data.Loaded
import app.harulock.data.Permissions
import app.harulock.data.StateStore

/**
 * 잠금 중에 설정 앱 화면에 앱 이름이 보이면 홈으로 나간다. 이 앱을 끄거나 권한을 빼는 화면을 닫기 위해서다.
 * 닫을지는 [Policy.shouldCloseSettings]가 정한다. 화면 글자는 그 자리에서 비교만 하고 모으거나 저장하거나 기록하지 않는다.
 * 잠금 해제 전에도 동작하도록 기기 보호 저장소만 읽는다.
 */
class SettingsWatchService : AccessibilityService() {
    private val handler = Handler(Looper.getMainLooper())
    private val store by lazy { StateStore(this) }
    private val check = Runnable { inspect() }

    /** 마지막 이벤트 뒤 화면이 자리 잡은 다음 한 번 더 보는 확인. 바로 한 확인은 이전 화면이나 빈 화면을 볼 수 있다. */
    private val settle = Runnable { inspect() }

    /** 다음 확인을 할 수 있는 가장 이른 시각(uptime). */
    private var notBefore = 0L

    /** 홈으로 나간 뒤 화면이 넘어가는 동안은 확인하지 않는다(uptime). */
    private var closedUntil = 0L

    /**
     * 이벤트가 몰려도 확인은 간격을 두고 한다. 마지막 이벤트 [SETTLE_MILLIS] 뒤에 한 번 더 본다.
     */
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event?.packageName?.toString() != SETTINGS) return
        handler.removeCallbacks(settle)
        handler.postDelayed(settle, SETTLE_MILLIS)
        if (handler.hasCallbacks(check)) return
        handler.postDelayed(check, (notBefore - SystemClock.uptimeMillis()).coerceAtLeast(0))
    }

    override fun onInterrupt() = Unit

    override fun onDestroy() {
        handler.removeCallbacks(check)
        handler.removeCallbacks(settle)
        super.onDestroy()
    }

    /** 잠금 중이고 권한이 정상일 때만 화면을 읽는다. 그 밖에는 복구와 설정을 위해 그대로 둔다. */
    private fun inspect() {
        val now = SystemClock.uptimeMillis()
        // 홈을 누른 직후의 화면 전환 중에는 다시 누르지 않는다. 그 뒤에 한 번 다시 본다.
        if (now < closedUntil) {
            handler.removeCallbacks(settle)
            handler.postDelayed(settle, closedUntil - now)
            return
        }
        notBefore = now + CHECK_EVERY_MILLIS
        runCatching {
            val armed = armed()
            if (!armed) return
            val permissionsOk = Permissions.all(this)
            if (!permissionsOk) return
            val root = rootInActiveWindow ?: return
            // 그사이 다른 앱이 앞에 왔으면 그 화면은 읽지 않는다.
            val pkg = root.packageName?.toString()
            if (pkg != SETTINGS) return
            val label = getString(R.string.app_name)
            val found = anyVisibleText(root) { text ->
                Policy.shouldCloseSettings(pkg, listOf(text), label, armed, permissionsOk)
            }
            if (found) {
                performGlobalAction(GLOBAL_ACTION_HOME)
                // 화면이 넘어가는 동안의 이벤트로 홈을 거듭 누르지 않는다.
                closedUntil = SystemClock.uptimeMillis() + AFTER_CLOSE_MILLIS
                notBefore = closedUntil
            }
        }.onFailure { Log.w(TAG, "check failed: ${it.javaClass.name}") }
    }

    /** 비상 해제가 끝났거나 저장 상태를 읽을 수 없으면 false. */
    private fun armed(): Boolean =
        !Controller.released(this) && (store.load() as? Loaded.Ok)?.state?.armed == true

    /** 화면에 보이는 글자나 설명 중 [match]에 맞는 것이 있는지. 노드는 [MAX_NODES]개까지만 본다. */
    private fun anyVisibleText(root: AccessibilityNodeInfo, match: (String) -> Boolean): Boolean {
        val queue = ArrayDeque<AccessibilityNodeInfo>()
        queue.add(root)
        var requested = 1
        while (queue.isNotEmpty()) {
            val node = queue.removeFirst()
            if (node.isVisibleToUser) {
                if (node.text?.let { match(it.toString()) } == true) return true
                if (node.contentDescription?.let { match(it.toString()) } == true) return true
            }
            var child = 0
            while (child < node.childCount && requested < MAX_NODES) {
                node.getChild(child)?.let { queue.add(it) }
                child++
                requested++
            }
        }
        return false
    }

    private companion object {
        const val TAG = "SettingsWatch"
        const val SETTINGS = "com.android.settings"
        const val CHECK_EVERY_MILLIS = 200L
        const val AFTER_CLOSE_MILLIS = 700L
        const val SETTLE_MILLIS = 400L
        const val MAX_NODES = 600
    }
}
