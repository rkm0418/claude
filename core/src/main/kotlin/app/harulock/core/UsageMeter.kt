package app.harulock.core

import java.time.Instant

sealed interface UsageEvent {
    val at: Instant

    data class Resumed(override val at: Instant, val pkg: String, val activity: String) : UsageEvent
    data class Paused(override val at: Instant, val pkg: String, val activity: String) : UsageEvent
    data class Screen(override val at: Instant, val on: Boolean) : UsageEvent
    data class Keyguard(override val at: Instant, val shown: Boolean) : UsageEvent
    data class Restart(override val at: Instant) : UsageEvent
}

/** [countedUntil]까지 센 결과. [resumed]는 앞에 떠 있는 화면("pkg/activity"). */
data class MeterState(
    val countedUntil: Instant,
    val usedMillis: Long = 0,
    val resumed: Set<String> = emptySet(),
    val screenOn: Boolean = true,
    val keyguard: Boolean = false,
)

object UsageMeter {
    /**
     * [until]까지의 사용 시간을 더한다. 이미 반영한 이벤트를 시각순 뒷부분 그대로 다시 넘겨도 결과가 같다.
     * [free] 패키지만 떠 있는 동안은 세지 않는다.
     */
    fun advance(state: MeterState, events: List<UsageEvent>, until: Instant, free: Set<String>): MeterState {
        // 과거로 되돌리면 이벤트 일부만 다시 반영되어 상태가 어긋나고 같은 구간을 두 번 센다.
        if (until < state.countedUntil) return state

        var countedUntil = state.countedUntil
        var used = state.usedMillis
        val resumed = state.resumed.toMutableSet()
        var screenOn = state.screenOn
        var keyguard = state.keyguard

        fun moveTo(t: Instant, count: Boolean) {
            if (t <= countedUntil) return
            if (count && screenOn && !keyguard && resumed.any { it.substringBefore('/') !in free }) {
                used += t.toEpochMilli() - countedUntil.toEpochMilli()
            }
            countedUntil = t
        }

        for (event in events.filter { it.at <= until }.sortedBy { it.at }) {
            // 재시작 직전 구간은 기기가 꺼져 있었을 수 있으므로 세지 않는다.
            moveTo(event.at, count = event !is UsageEvent.Restart)
            when (event) {
                is UsageEvent.Resumed -> resumed.add("${event.pkg}/${event.activity}")
                is UsageEvent.Paused -> resumed.remove("${event.pkg}/${event.activity}")
                is UsageEvent.Screen -> screenOn = event.on
                is UsageEvent.Keyguard -> keyguard = event.shown
                is UsageEvent.Restart -> {
                    resumed.clear()
                    screenOn = false
                }
            }
        }
        moveTo(until, count = true)

        return MeterState(countedUntil, used, resumed, screenOn, keyguard)
    }
}
