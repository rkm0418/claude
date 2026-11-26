package app.harulock.ui

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.app.AlertDialog
import android.app.NotificationManager
import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import app.harulock.R
import app.harulock.admin.Guard
import app.harulock.data.Permissions

/**
 * 설정 안내 다섯 단계와 잠금 시작. 기기 소유자, 사용 정보 접근, 접근성이 모두 되어야 잠금 시작을 누를 수 있다.
 * 알림과 배터리는 권장이다.
 */
class SetupActivity : Activity() {
    private class Step(root: View, title: Int, desc: Int, action: Int, onAction: () -> Unit) {
        val state: ImageView = root.findViewById(R.id.img_state)
        val button: Button = root.findViewById(R.id.btn_action)

        init {
            root.findViewById<TextView>(R.id.tv_title).setText(title)
            root.findViewById<TextView>(R.id.tv_desc).setText(desc)
            button.setText(action)
            button.setOnClickListener { onAction() }
        }

        fun show(done: Boolean) {
            state.setImageResource(if (done) R.drawable.ic_step_done else R.drawable.ic_step_todo)
            button.visibility = if (done) View.GONE else View.VISIBLE
        }
    }

    /** 한 번 확인한 단계 상태. */
    private class Status(
        val owner: Boolean,
        val usage: Boolean,
        val accessibility: Boolean,
        val notification: Boolean,
        val battery: Boolean,
        val armed: Boolean,
    ) {
        val required: Boolean get() = owner && usage && accessibility
    }

    private lateinit var owner: Step
    private lateinit var usage: Step
    private lateinit var accessibility: Step
    private lateinit var notification: Step
    private lateinit var battery: Step
    private lateinit var btnArm: Button

    private var status: Status? = null
    private var busy = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_setup)
        owner = Step(
            findViewById(R.id.step_owner), R.string.step_owner_title, R.string.step_owner_desc, R.string.action_how,
        ) { showOwnerHelp() }
        usage = Step(
            findViewById(R.id.step_usage), R.string.step_usage_title, R.string.step_usage_desc, R.string.action_open,
        ) { openUsage() }
        accessibility = Step(
            findViewById(R.id.step_accessibility), R.string.step_accessibility_title,
            R.string.step_accessibility_desc, R.string.action_open,
        ) { open(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
        notification = Step(
            findViewById(R.id.step_notification), R.string.step_notification_title,
            R.string.step_notification_desc, R.string.action_open,
        ) { openNotification() }
        battery = Step(
            findViewById(R.id.step_battery), R.string.step_battery_title, R.string.step_battery_desc,
            R.string.action_open,
        ) { openBattery() }
        btnArm = findViewById(R.id.btn_arm)
        btnArm.setOnClickListener { confirmArm() }
        show()
    }

    override fun onResume() {
        super.onResume()
        refresh()
    }

    private fun refresh() {
        val ctx = applicationContext
        Work.run(this, {
            Status(
                owner = Guard(ctx).isOwner(),
                usage = Permissions.usage(ctx),
                accessibility = Permissions.accessibility(ctx),
                notification = ctx.getSystemService(NotificationManager::class.java).areNotificationsEnabled(),
                battery = ctx.getSystemService(PowerManager::class.java).isIgnoringBatteryOptimizations(ctx.packageName),
                armed = SettingsEdit.read(ctx).armed,
            )
        }) { result ->
            status = result.getOrNull()
            show()
        }
    }

    private fun show() {
        val s = status
        owner.show(s?.owner == true)
        usage.show(s?.usage == true)
        accessibility.show(s?.accessibility == true)
        notification.show(s?.notification == true)
        battery.show(s?.battery == true)
        btnArm.isEnabled = s != null && s.required && !s.armed && !busy
        btnArm.setText(
            when {
                s?.armed == true -> R.string.arm_running
                s?.required == true -> R.string.arm_start
                else -> R.string.arm_need_steps
            },
        )
    }

    private fun showOwnerHelp() {
        val command = getString(R.string.owner_command)
        AlertDialog.Builder(this)
            .setTitle(R.string.owner_dialog_title)
            .setMessage(getString(R.string.owner_dialog_message, command))
            .setPositiveButton(R.string.action_copy) { _, _ ->
                getSystemService(ClipboardManager::class.java)
                    .setPrimaryClip(ClipData.newPlainText(getString(R.string.owner_dialog_title), command))
                Toast.makeText(this, R.string.copied, Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton(R.string.action_close, null)
            .show()
    }

    /** 이 앱의 사용 정보 접근 화면. 지원하지 않으면 전체 목록. */
    private fun openUsage() {
        open(
            Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS, Uri.parse("package:$packageName")),
            Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS),
        )
    }

    /** 알림 권한을 먼저 묻고, 이미 거절해 다시 물을 수 없으면 앱 알림 설정을 연다. */
    private fun openNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), REQUEST_NOTIFICATION)
        } else {
            openNotificationSettings()
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode != REQUEST_NOTIFICATION) return
        val granted = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
        if (!granted && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            !shouldShowRequestPermissionRationale(Manifest.permission.POST_NOTIFICATIONS)
        ) {
            openNotificationSettings()
        }
        refresh()
    }

    private fun openNotificationSettings() {
        open(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, packageName))
    }

    /** 이 앱만 배터리 최적화에서 빼 달라고 묻는다. 안 되면 전체 목록. */
    @SuppressLint("BatteryLife")
    private fun openBattery() {
        open(
            Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName")),
            Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS),
        )
    }

    /** 차례로 열어 보고, 모두 안 되면 알린다. */
    private fun open(vararg intents: Intent) {
        for (intent in intents) {
            try {
                startActivity(intent)
                return
            } catch (e: ActivityNotFoundException) {
                continue
            } catch (e: SecurityException) {
                continue
            }
        }
        Toast.makeText(this, R.string.open_failed, Toast.LENGTH_LONG).show()
    }

    private fun confirmArm() {
        if (busy || status?.required != true) return
        AlertDialog.Builder(this)
            .setTitle(R.string.arm_confirm_title)
            .setMessage(R.string.arm_confirm_message)
            .setPositiveButton(R.string.arm_start) { _, _ -> arm() }
            .setNegativeButton(R.string.action_cancel, null)
            .show()
    }

    private fun arm() {
        busy = true
        show()
        val ctx = applicationContext
        Work.run(this, { SettingsEdit.arm(ctx) }) { result ->
            busy = false
            if (result.getOrDefault(false)) {
                Toast.makeText(this, R.string.arm_started, Toast.LENGTH_LONG).show()
                finish()
            } else {
                AlertDialog.Builder(this)
                    .setMessage(R.string.arm_failed)
                    .setPositiveButton(R.string.action_ok, null)
                    .show()
                refresh()
            }
        }
    }

    private companion object {
        const val REQUEST_NOTIFICATION = 1
    }
}
