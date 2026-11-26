package app.harulock.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/** 부팅(잠금 해제 전 포함)과 앱 업데이트 뒤 서비스를 다시 시작한다. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action !in ACTIONS) return
        LockService.start(context)
        // 서비스가 뜨지 못해도 저장된 잠금은 한 번 적용한다.
        tickAsync(context)
    }

    private companion object {
        val ACTIONS = setOf(
            Intent.ACTION_LOCKED_BOOT_COMPLETED,
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_MY_PACKAGE_REPLACED,
        )
    }
}

/** 초기화 시각과 즉시 잠금 종료 시각의 정확한 알람. 화면이 꺼져 있어도 바로 반영한다. */
class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        LockService.start(context)
        tickAsync(context)
    }
}

/** 수신기 시간 제한 안에서 별도 스레드로 tick을 실행한다. 끝날 때까지 기기를 깨워 둔다. */
private fun BroadcastReceiver.tickAsync(context: Context) {
    val app = context.applicationContext
    val pending = goAsync()
    Thread {
        try {
            Controller(app).tick()
        } catch (t: Throwable) {
            Log.w("Receivers", "tick failed", t)
        } finally {
            pending.finish()
        }
    }.start()
}
