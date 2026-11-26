package app.harulock.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import app.harulock.R

/** 화면이 켜진 동안 1초마다 [Controller.tick]을 실행하는 상시 서비스. */
class LockService : Service() {
    private lateinit var thread: HandlerThread
    private lateinit var handler: Handler
    private lateinit var controller: Controller
    private lateinit var power: PowerManager

    private val loop = object : Runnable {
        override fun run() {
            if (tickOnce() && power.isInteractive) handler.postDelayed(this, TICK_MILLIS)
        }
    }

    private val once = Runnable { tickOnce() }

    private val screen = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                Intent.ACTION_SCREEN_ON -> restartLoop()
                Intent.ACTION_SCREEN_OFF -> {
                    handler.removeCallbacks(loop)
                    handler.post(once)
                }
                Intent.ACTION_USER_UNLOCKED -> {
                    // 잠금 해제 전에는 일부 앱이 보이지 않았을 수 있다.
                    Controller.packagesChanged()
                    handler.post(once)
                }
                else -> handler.post(once)
            }
        }
    }

    private val packages = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            Controller.packagesChanged()
            handler.post(once)
        }
    }

    override fun onCreate() {
        super.onCreate()
        power = getSystemService(PowerManager::class.java)
        controller = Controller(this)
        thread = HandlerThread("lock-tick").also { it.start() }
        handler = Handler(thread.looper)
        register(
            screen,
            IntentFilter().apply {
                addAction(Intent.ACTION_SCREEN_ON)
                addAction(Intent.ACTION_SCREEN_OFF)
                addAction(Intent.ACTION_USER_PRESENT)
                addAction(Intent.ACTION_USER_UNLOCKED)
            },
        )
        register(
            packages,
            IntentFilter(Intent.ACTION_PACKAGE_ADDED).apply { addDataScheme("package") },
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // startForegroundService 뒤에는 멈추더라도 먼저 전경으로 올려야 한다.
        runCatching { goForeground() }.onFailure { Log.w(TAG, "startForeground failed", it) }
        if (Controller.released(this)) {
            stopSelf()
            return START_NOT_STICKY
        }
        restartLoop()
        return START_STICKY
    }

    override fun onDestroy() {
        runCatching { unregisterReceiver(screen) }
        runCatching { unregisterReceiver(packages) }
        handler.removeCallbacksAndMessages(null)
        thread.quitSafely()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun restartLoop() {
        handler.removeCallbacks(loop)
        handler.post(loop)
    }

    /** 비상 해제가 끝났으면 멈추고 false. */
    private fun tickOnce(): Boolean {
        runCatching { controller.tick() }.onFailure { Log.w(TAG, "tick failed", it) }
        if (!Controller.released(this)) return true
        handler.removeCallbacks(loop)
        stopSelf()
        return false
    }

    private fun goForeground() {
        val notification = Notices(this).running()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    /** 시스템 방송만 받는다. 다른 앱은 보낼 수 없다. */
    private fun register(receiver: BroadcastReceiver, filter: IntentFilter) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(receiver, filter)
        }
    }

    companion object {
        private const val TAG = "LockService"
        private const val TICK_MILLIS = 1_000L
        private const val NOTIFICATION_ID = 1

        /** 서비스를 시작한다. 비상 해제가 끝났거나 시작할 수 없으면 false. */
        fun start(ctx: Context): Boolean {
            if (Controller.released(ctx)) return false
            return runCatching {
                ctx.startForegroundService(Intent(ctx, LockService::class.java))
                true
            }.onFailure { Log.w(TAG, "cannot start service", it) }.getOrDefault(false)
        }
    }
}

/** 상시 알림, 예고 알림, 재설정 안내. 알림 권한이 없으면 시스템이 조용히 버린다. */
internal class Notices(ctx: Context) {
    private val context = ctx.applicationContext
    private val manager = context.getSystemService(NotificationManager::class.java)

    /** 남은 시간을 넣지 않는다. */
    fun running(): Notification {
        channels()
        return Notification.Builder(context, CHANNEL_RUNNING)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentText(context.getString(R.string.notif_running))
            .setOngoing(true)
            .setShowWhen(false)
            .setCategory(Notification.CATEGORY_SERVICE)
            .setContentIntent(openApp())
            .build()
    }

    fun warning(minutes: Int) = post(ID_WARNING, CHANNEL_WARNING, context.getString(R.string.notif_warning, minutes))

    fun setupAgain() = post(ID_SETUP, CHANNEL_SETUP, context.getString(R.string.notif_setup_again))

    private fun post(id: Int, channel: String, text: String) {
        runCatching {
            channels()
            val notification = Notification.Builder(context, channel)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(context.getString(R.string.app_name))
                .setContentText(text)
                .setStyle(Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true)
                .setContentIntent(openApp())
                .build()
            manager.notify(id, notification)
        }.onFailure { Log.w(TAG, "notify failed", it) }
    }

    private fun channels() {
        manager.createNotificationChannels(
            listOf(
                NotificationChannel(
                    CHANNEL_RUNNING,
                    context.getString(R.string.channel_running),
                    NotificationManager.IMPORTANCE_LOW,
                ),
                NotificationChannel(
                    CHANNEL_WARNING,
                    context.getString(R.string.channel_warning),
                    NotificationManager.IMPORTANCE_HIGH,
                ),
                NotificationChannel(
                    CHANNEL_SETUP,
                    context.getString(R.string.channel_setup),
                    NotificationManager.IMPORTANCE_DEFAULT,
                ),
            ),
        )
    }

    /** 실행 화면이 없으면(Task 11 전) 누를 곳 없이 둔다. */
    private fun openApp(): PendingIntent? =
        context.packageManager.getLaunchIntentForPackage(context.packageName)?.let {
            PendingIntent.getActivity(context, 0, it, PendingIntent.FLAG_IMMUTABLE)
        }

    private companion object {
        const val TAG = "Notices"
        const val CHANNEL_RUNNING = "running"
        const val CHANNEL_WARNING = "warning"
        const val CHANNEL_SETUP = "setup"
        const val ID_WARNING = 2
        const val ID_SETUP = 3
    }
}
