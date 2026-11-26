package app.harulock.data

import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import app.harulock.core.UsageEvent
import java.time.Instant

/** 시스템 사용 기록을 [UsageEvent]로 바꾼다. 사용자 잠금 해제 전에는 부르지 않는다. */
class UsageReader(ctx: Context) {
    private val usage = ctx.applicationContext.getSystemService(UsageStatsManager::class.java)

    /**
     * 벽시계 `[fromWall, toWall)` 구간의 이벤트를 시각순으로 읽는다.
     * 기록 시각은 벽시계이므로 [shiftMillis](신뢰 시각 - 벽시계)만큼 옮긴다.
     */
    fun read(fromWall: Long, toWall: Long, shiftMillis: Long): List<UsageEvent> {
        if (fromWall >= toWall) return emptyList()
        val events = usage.queryEvents(fromWall, toWall) ?: return emptyList()
        val out = ArrayList<UsageEvent>()
        val e = UsageEvents.Event()
        while (events.hasNextEvent()) {
            if (!events.getNextEvent(e)) break
            map(e, Instant.ofEpochMilli(e.timeStamp + shiftMillis))?.let { out.add(it) }
        }
        return out
    }

    /** ACTIVITY_STOPPED는 쓰지 않는다. 지난 인스턴스의 늦은 STOPPED가 떠 있는 화면을 지울 수 있다. */
    private fun map(e: UsageEvents.Event, at: Instant): UsageEvent? = when (e.eventType) {
        UsageEvents.Event.ACTIVITY_RESUMED -> UsageEvent.Resumed(at, e.packageName.orEmpty(), e.className.orEmpty())
        UsageEvents.Event.ACTIVITY_PAUSED -> UsageEvent.Paused(at, e.packageName.orEmpty(), e.className.orEmpty())
        UsageEvents.Event.SCREEN_INTERACTIVE -> UsageEvent.Screen(at, on = true)
        UsageEvents.Event.SCREEN_NON_INTERACTIVE -> UsageEvent.Screen(at, on = false)
        UsageEvents.Event.KEYGUARD_SHOWN -> UsageEvent.Keyguard(at, shown = true)
        UsageEvents.Event.KEYGUARD_HIDDEN -> UsageEvent.Keyguard(at, shown = false)
        UsageEvents.Event.DEVICE_STARTUP -> UsageEvent.Restart(at)
        UsageEvents.Event.DEVICE_SHUTDOWN -> UsageEvent.Screen(at, on = false)
        else -> null
    }
}
