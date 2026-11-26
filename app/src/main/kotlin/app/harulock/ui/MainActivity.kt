package app.harulock.ui

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.Button
import android.widget.TextView
import app.harulock.R
import app.harulock.admin.Guard
import app.harulock.core.Display
import app.harulock.core.Engine
import app.harulock.core.HomeState
import app.harulock.data.Permissions
import app.harulock.service.Controller
import app.harulock.service.LockService
import java.time.Instant

/** 홈. 남은 시간, 상태, 다음 초기화, 대기 중인 변경을 1초마다 저장 상태에서 다시 읽어 보여 준다. */
class MainActivity : Activity() {
    private lateinit var tvStatus: TextView
    private lateinit var tvRemaining: TextView
    private lateinit var tvNextReset: TextView
    private lateinit var tvPendingChange: TextView
    private lateinit var btnInstantLock: Button

    private val main = Handler(Looper.getMainLooper())
    private var loading = false
    private var serviceChecked = false
    private var dialog: InstantLockDialog? = null

    private val refresh = object : Runnable {
        override fun run() {
            load()
            main.postDelayed(this, REFRESH_MILLIS)
        }
    }

    /** 한 번 읽은 화면 값. [owner]는 비상 해제 뒤에만 읽는다(완료인지 도중에 멈췄는지). */
    private class Home(val snapshot: Snapshot, val now: Instant, val permissionsOk: Boolean, val owner: Boolean)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        tvStatus = findViewById(R.id.tv_status)
        tvRemaining = findViewById(R.id.tv_remaining)
        tvNextReset = findViewById(R.id.tv_next_reset)
        tvPendingChange = findViewById(R.id.tv_pending_change)
        btnInstantLock = findViewById(R.id.btn_instant_lock)

        btnInstantLock.setOnClickListener { openInstantLock() }
        findViewById<Button>(R.id.btn_settings).setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        findViewById<Button>(R.id.btn_setup).setOnClickListener {
            startActivity(Intent(this, SetupActivity::class.java))
        }
        findViewById<Button>(R.id.btn_release).setOnClickListener {
            startActivity(Intent(this, ReleaseActivity::class.java))
        }
    }

    override fun onResume() {
        super.onResume()
        serviceChecked = false
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

    private fun openInstantLock() {
        if (dialog?.isShowing == true) return
        dialog = InstantLockDialog(this) { load() }.also { it.show() }
    }

    private fun load() {
        if (loading) return
        loading = true
        val startService = !serviceChecked
        serviceChecked = true
        Work.run(this, {
            val snapshot = SettingsEdit.read(this)
            // 잠금 중인데 서비스가 멈춰 있으면 다시 띄운다. 이미 돌고 있으면 한 번 더 tick할 뿐이다.
            if (startService && snapshot.armed && !Controller.released(this)) LockService.start(this)
            val owner = snapshot.released && Guard(this).isOwner()
            Home(snapshot, trustedNow(this), Permissions.all(this), owner)
        }) { result ->
            loading = false
            result.onSuccess { show(it) }
        }
    }

    private fun show(h: Home) {
        val s = h.snapshot.state?.takeIf { it.armed }
        val state = Display.homeState(s, h.now, h.permissionsOk)

        tvRemaining.text = if (s != null) Texts.remaining(this, Engine.remainingMillis(s)) else getString(R.string.remaining_none)
        tvRemaining.setTextColor(
            getColor(
                when (state) {
                    HomeState.NOT_ARMED, HomeState.USING -> R.color.status_normal
                    HomeState.LOW -> R.color.status_warning
                    HomeState.LIMIT_LOCKED, HomeState.INSTANT_LOCKED, HomeState.PERMISSION_LOCKED -> R.color.status_locked
                },
            ),
        )
        tvStatus.text = when (state) {
            HomeState.NOT_ARMED -> getString(
                when {
                    // 비상 해제 뒤: 완료면 완료 안내, 도중에 멈췄으면 비상 해제 화면에서 다시 하도록 실패 안내.
                    h.snapshot.released && h.owner -> R.string.release_failed
                    h.snapshot.released -> R.string.release_state_done
                    h.snapshot.unreadable -> R.string.status_unreadable
                    else -> R.string.status_not_armed
                },
            )
            HomeState.USING -> getString(R.string.status_using)
            HomeState.LOW -> getString(R.string.status_low)
            HomeState.LIMIT_LOCKED -> getString(R.string.status_limit_locked)
            HomeState.INSTANT_LOCKED ->
                getString(R.string.status_instant_locked, s?.instantUntil?.let { Texts.dateTime(this, it) } ?: "")
            HomeState.PERMISSION_LOCKED -> getString(R.string.status_permission_locked)
        }

        if (s != null) {
            tvNextReset.text = getString(R.string.next_reset, Texts.dateTime(this, s.period.end))
            tvNextReset.visibility = View.VISIBLE
        } else {
            tvNextReset.visibility = View.GONE
        }

        val pending = s?.let { Texts.pendingChange(this, it) }
        tvPendingChange.text = pending ?: ""
        tvPendingChange.visibility = if (pending != null) View.VISIBLE else View.GONE

        btnInstantLock.isEnabled = s != null
    }

    private companion object {
        const val REFRESH_MILLIS = 1_000L
    }
}
