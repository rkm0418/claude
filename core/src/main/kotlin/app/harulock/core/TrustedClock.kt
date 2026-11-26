package app.harulock.core

import java.time.Instant

/** 마지막으로 확인한 벽시계 시각과 그때의 부팅 경과 시간 및 부팅 번호. */
data class ClockAnchor(val wall: Instant, val elapsedMillis: Long, val bootCount: Int)

/** 벽시계를 믿지 않고 같은 부팅 안에서는 경과 시간으로, 재부팅 뒤에는 뒤로 가지 않도록 시각을 잡는다. */
object TrustedClock {
    /** 현재 신뢰 시각과, 그 시각을 기준으로 한 새 앵커를 돌려준다. */
    fun now(anchor: ClockAnchor?, wall: Instant, elapsedMillis: Long, bootCount: Int): Pair<Instant, ClockAnchor> {
        val time = when {
            anchor == null -> wall
            anchor.bootCount == bootCount -> anchor.wall.plusMillis(elapsedMillis - anchor.elapsedMillis)
            else -> if (wall.isAfter(anchor.wall)) wall else anchor.wall
        }
        return time to ClockAnchor(time, elapsedMillis, bootCount)
    }
}
