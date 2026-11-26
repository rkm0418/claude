package app.harulock.ui

import android.app.Activity
import android.app.ActivityManager
import android.app.AlertDialog
import android.app.admin.DevicePolicyManager
import android.content.Context
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import app.harulock.R
import app.harulock.admin.Enforcer
import app.harulock.admin.Guard
import app.harulock.core.ClockAnchor
import app.harulock.core.Display
import app.harulock.core.ReleaseFlow
import app.harulock.core.ReleaseRecord
import app.harulock.core.ReleaseView
import app.harulock.data.ReleaseFiles
import app.harulock.service.Controller
import java.time.Duration
import java.time.Instant
import android.provider.Settings.Global as GlobalSettings

/**
 * 비상 해제. PC 없이 잠금에서 나오는 유일한 길이므로 메인 프로세스와 저장 상태가 망가져도 동작하도록
 * 별도 프로세스(":release")에서 `release.txt`와 `released` 두 파일만으로 판단한다. [app.harulock.data.StateStore]는 쓰지 않는다.
 * 요청 뒤 24시간이 지나야 하고, 그 뒤 24시간 안에만 풀 수 있다.
 */
class ReleaseActivity : Activity() {
    private lateinit var tvState: TextView
    private lateinit var tvRemaining: TextView
    private lateinit var btnRequest: Button
    private lateinit var btnCancel: Button
    private lateinit var btnConfirm: Button

    private val main = Handler(Looper.getMainLooper())
    private var opened: ReleaseOps.Opened? = null
    private var busy = false
    private var dialog: AlertDialog? = null

    /** 1초마다 남은 시간을 다시 그린다. 시각은 연 순간의 신뢰 시각에 그 뒤 부팅 경과 시간을 더한다. */
    private val refresh = object : Runnable {
        override fun run() {
            show()
            main.postDelayed(this, REFRESH_MILLIS)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_release)
        tvState = findViewById(R.id.tv_release_state)
        tvRemaining = findViewById(R.id.tv_release_remaining)
        btnRequest = findViewById(R.id.btn_request)
        btnCancel = findViewById(R.id.btn_cancel_request)
        btnConfirm = findViewById(R.id.btn_confirm)
        btnRequest.setOnClickListener { act { ctx -> ReleaseOps.request(ctx) } }
        btnCancel.setOnClickListener { act { ctx -> ReleaseOps.cancel(ctx) } }
        btnConfirm.setOnClickListener { confirm() }
        show()
    }

    override fun onResume() {
        super.onResume()
        load()
        main.removeCallbacks(refresh)
        main.post(refresh)
    }

    override fun onPause() {
        main.removeCallbacks(refresh)
        super.onPause()
    }

    override fun onDestroy() {
        dialog?.dismiss()
        dialog = null
        super.onDestroy()
    }

    /** 열 때마다 파일을 다시 읽고 기준점을 갱신한다. */
    private fun load() {
        val ctx = applicationContext
        Work.run(this, { ReleaseOps.open(ctx) }) { result ->
            result.onSuccess { opened = it }.onFailure { toast(R.string.load_failed) }
            show()
        }
    }

    private fun current(): ReleaseView? {
        val o = opened ?: return null
        val now = o.now.plusMillis((SystemClock.elapsedRealtime() - o.elapsed).coerceAtLeast(0))
        return ReleaseFlow.view(o.record, now, o.marker, o.owner)
    }

    private fun show() {
        val view = current()
        tvState.text = when (view) {
            null -> ""
            ReleaseView.None -> getString(R.string.release_state_none)
            is ReleaseView.Waiting -> getString(R.string.release_state_waiting)
            is ReleaseView.Ready -> getString(R.string.release_state_ready)
            ReleaseView.Expired -> getString(R.string.release_state_expired)
            ReleaseView.Incomplete -> getString(R.string.release_failed)
            ReleaseView.Done -> getString(R.string.release_state_done)
        }
        val left = when (view) {
            is ReleaseView.Waiting -> getString(R.string.release_waiting_left, duration(view.left))
            is ReleaseView.Ready -> getString(R.string.release_ready_left, duration(view.left))
            else -> null
        }
        tvRemaining.text = left ?: ""
        tvRemaining.visibility = if (left != null) View.VISIBLE else View.GONE

        val canRequest = view == ReleaseView.None || view == ReleaseView.Expired
        val canCancel = view is ReleaseView.Waiting || view is ReleaseView.Ready
        val canConfirm = view is ReleaseView.Ready || view == ReleaseView.Incomplete
        show(btnRequest, canRequest)
        show(btnCancel, canCancel)
        show(btnConfirm, canConfirm)
    }

    private fun show(button: Button, visible: Boolean) {
        button.visibility = if (visible) View.VISIBLE else View.GONE
        button.isEnabled = visible && !busy
    }

    private fun duration(left: Duration): String {
        val minutes = Display.ceilMinutes(left.toMillis())
        return getString(R.string.release_left_format, (minutes / 60).toInt(), (minutes % 60).toInt())
    }

    /** 처음 해제는 확인 창을 거친다. 도중에 멈춘 해제를 다시 하는 것은 이미 확인했으므로 바로 한다. */
    private fun confirm() {
        if (busy) return
        when (current()) {
            ReleaseView.Incomplete -> release()
            is ReleaseView.Ready -> {
                if (dialog?.isShowing == true) return
                dialog = AlertDialog.Builder(this)
                    .setTitle(R.string.release_confirm_title)
                    .setMessage(R.string.release_confirm_message)
                    .setPositiveButton(R.string.action_release_confirm) { _, _ -> release() }
                    .setNegativeButton(R.string.action_cancel, null)
                    .show()
            }
            else -> Unit
        }
    }

    private fun release() {
        if (busy) return
        busy = true
        show()
        val ctx = applicationContext
        Work.run(this, { ReleaseOps.release(ctx) }) { result -> released(result.getOrDefault(ReleaseOps.Outcome.FAILED)) }
    }

    private fun released(outcome: ReleaseOps.Outcome) {
        busy = false
        when (outcome) {
            ReleaseOps.Outcome.DONE -> load()
            ReleaseOps.Outcome.NOT_READY, ReleaseOps.Outcome.FAILED -> {
                toast(R.string.release_failed)
                load()
            }
            ReleaseOps.Outcome.STALE -> {
                // 이 프로세스가 기억한 정지 목록과 제한 기록이 낡았다. 프로세스를 끝내 다음에 열 때 새로 읽게 한다.
                toast(R.string.release_failed)
                finish()
                main.postDelayed({ Process.killProcess(Process.myPid()) }, RESTART_DELAY_MILLIS)
            }
        }
    }

    /** 요청과 취소. 저장하지 못하면 알리고, 끝나면 다시 읽는다. */
    private fun act(task: (Context) -> Boolean) {
        if (busy) return
        busy = true
        show()
        val ctx = applicationContext
        Work.run(this, { task(ctx) }) { result ->
            busy = false
            if (!result.getOrDefault(false)) toast(R.string.save_failed)
            load()
        }
    }

    private fun toast(text: Int) = Toast.makeText(this, text, Toast.LENGTH_LONG).show()

    private companion object {
        const val REFRESH_MILLIS = 1_000L
        const val RESTART_DELAY_MILLIS = 500L
    }
}

/**
 * 비상 해제 프로세스의 파일 처리와 해제 동작. 모두 [Controller.exclusive] 안에서 하므로 메인 프로세스의 동작과 겹치지 않는다.
 * 메인 스레드 밖에서 부른다.
 */
internal object ReleaseOps {
    private const val TAG = "Release"

    /** 연 순간의 값. [now]는 신뢰 시각, [elapsed]는 그때의 부팅 경과 시간. */
    class Opened(
        val record: ReleaseRecord?,
        val now: Instant,
        val elapsed: Long,
        val marker: Boolean,
        val owner: Boolean,
    )

    enum class Outcome {
        /** 모두 풀고 기기 소유자를 해제했다(또는 이미 해제되어 있다). */
        DONE,
        /** 지금은 해제할 수 있는 때가 아니다. */
        NOT_READY,
        /** 일부를 풀지 못했다. 완료 표시가 남아 있으면 화면에서 다시 시도한다. */
        FAILED,
        /** 이 프로세스가 읽어 둔 SharedPreferences가 낡았을 수 있다. 새 프로세스에서 다시 해야 한다. */
        STALE,
    }

    /**
     * 이 프로세스에서 [Enforcer]와 [Guard]의 SharedPreferences를 읽었을 때의 완료 표시 표식.
     * SharedPreferences는 프로세스마다 한 번 읽고 기억하므로, 그 뒤 완료 표시가 바뀌었다면(다시 잠금을 시작해
     * 지워졌다면) 메인 프로세스가 그사이 값을 바꿨을 수 있다. 완료 표시가 그대로면 메인 프로세스는 아무것도 쓰지 않는다.
     */
    @Volatile private var loadedWith: String? = null

    /** 기록을 읽고 기준점을 갱신해 저장한다. */
    fun open(ctx: Context): Opened = Controller.exclusive(ctx) {
        val f = fresh(ctx)
        Opened(f.record, f.now, f.elapsed, f.files.markerToken() != null, isOwner(ctx))
    }

    /** 요청이 없거나 만료되었으면 지금으로 요청한다. 이미 요청 중이면 그대로 둔다. 저장하지 못하면 false. */
    fun request(ctx: Context): Boolean = Controller.exclusive(ctx) {
        val f = fresh(ctx)
        if (f.files.markerToken() != null) return@exclusive true
        val next = ReleaseFlow.request(f.record, f.now, f.anchor) ?: return@exclusive true
        f.files.writeRecord(next)
    }

    /** 요청을 지운다. 기준점은 남긴다. 저장하지 못하면 false. */
    fun cancel(ctx: Context): Boolean = Controller.exclusive(ctx) {
        val f = fresh(ctx)
        if (f.files.markerToken() != null) return@exclusive true
        f.files.writeRecord(ReleaseFlow.cancel(f.anchor))
    }

    /**
     * 확인 가능 기간이면 완료 표시 생성 → 모든 정지 해제 → 기기 제한 해제 → 기기 소유자 해제.
     * 완료 표시가 생기면 메인 프로세스는 더 이상 정지나 제한을 걸지 않는다. 앞의 둘이 모두 성공해야만
     * 기기 소유자를 해제한다(해제 뒤에는 남은 정지와 제한을 풀 권한이 없다). 실패하거나 도중에 프로세스가
     * 죽으면 완료 표시가 남으므로 화면에서 다시 시도할 수 있다.
     */
    fun release(ctx: Context): Outcome {
        var started = false
        val outcome = runCatching {
            Controller.exclusive(ctx) {
                val f = fresh(ctx)
                val owner = isOwner(ctx)
                var token = f.files.markerToken()
                if (!ReleaseFlow.mayRelease(f.record, f.now, token != null, owner)) {
                    return@exclusive if (token != null) Outcome.DONE else Outcome.NOT_READY
                }
                val loaded = loadedWith
                if (loaded != null && loaded != token) return@exclusive Outcome.STALE
                if (token == null) token = f.files.createMarker() ?: return@exclusive Outcome.FAILED
                started = true
                // 기기 소유자가 아니면 풀 권한도, 이 앱이 건 정지와 제한도 없다.
                if (!owner) return@exclusive Outcome.DONE
                loadedWith = token
                // 여기서 처음 만들어야 SharedPreferences를 완료 표시가 생긴 뒤(메인 프로세스가 멈춘 뒤) 읽는다.
                val unsuspended = Enforcer(ctx).unsuspendAll()
                val relaxed = Guard(ctx).relax()
                if (!unsuspended || !relaxed) {
                    Log.w(TAG, "release incomplete: unsuspended=$unsuspended relaxed=$relaxed")
                    return@exclusive Outcome.FAILED
                }
                clearOwner(ctx)
                if (isOwner(ctx)) Outcome.FAILED else Outcome.DONE
            }
        }.onFailure { Log.w(TAG, "release failed", it) }.getOrDefault(Outcome.FAILED)
        // 메인 프로세스가 기억한 SharedPreferences는 이 프로세스가 바꿔 낡았다. 끝내서 새로 읽게 한다.
        // 완료 표시가 있으므로 다시 떠도 아무것도 걸지 않는다.
        if (started) endOtherProcesses(ctx)
        return outcome
    }

    private class Fresh(
        val files: ReleaseFiles,
        val record: ReleaseRecord?,
        val now: Instant,
        val anchor: ClockAnchor,
        val elapsed: Long,
    )

    /** 파일을 읽어 신뢰 시각을 구하고 새 기준점을 저장한다. 저장에 실패해도 읽은 값으로 계속한다. */
    private fun fresh(ctx: Context): Fresh {
        val files = ReleaseFiles(ctx)
        val stored = files.readRecord()
        val elapsed = SystemClock.elapsedRealtime()
        val boot = GlobalSettings.getInt(ctx.contentResolver, GlobalSettings.BOOT_COUNT, 0)
        val (now, anchor) = ReleaseFlow.clock(stored, Instant.now(), elapsed, boot)
        val record = ReleaseRecord(stored?.requestedAt, anchor)
        files.writeRecord(record)
        return Fresh(files, record, now, anchor, elapsed)
    }

    private fun isOwner(ctx: Context): Boolean =
        ctx.getSystemService(DevicePolicyManager::class.java).isDeviceOwnerApp(ctx.packageName)

    @Suppress("DEPRECATION")
    private fun clearOwner(ctx: Context) {
        runCatching { ctx.getSystemService(DevicePolicyManager::class.java).clearDeviceOwnerApp(ctx.packageName) }
            .onFailure { Log.w(TAG, "clearDeviceOwnerApp failed", it) }
    }

    /** 이 앱의 다른 프로세스(메인)를 끝낸다. 서비스는 시스템이 다시 띄우고, 화면은 돌아갈 때 다시 만든다. */
    private fun endOtherProcesses(ctx: Context) {
        runCatching {
            val me = Process.myPid()
            ctx.getSystemService(ActivityManager::class.java).runningAppProcesses.orEmpty()
                .filter { it.pid != me && it.uid == Process.myUid() }
                .forEach { Process.killProcess(it.pid) }
        }.onFailure { Log.w(TAG, "cannot end other processes", it) }
    }
}
