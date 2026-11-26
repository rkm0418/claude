package app.harulock.core

import java.time.Duration
import java.time.Instant

/** 비상 해제 요청의 진행 상태. */
sealed interface ReleaseStatus {
    /** 요청이 없다. */
    object None : ReleaseStatus
    /** 해제 가능까지 [left] 남았다. */
    data class Waiting(val left: Duration) : ReleaseStatus
    /** 해제 가능하며, 만료까지 [left] 남았다. */
    data class Ready(val left: Duration) : ReleaseStatus
    /** 해제 가능 기간이 지나 만료되었다. */
    object Expired : ReleaseStatus
}

/** 비상 해제는 요청 후 24시간 뒤부터 48시간 안에만 가능하다. */
object EmergencyRelease {
    private val delay: Duration = Duration.ofHours(24)
    private val window: Duration = Duration.ofHours(48)

    fun status(requestedAt: Instant?, now: Instant): ReleaseStatus {
        if (requestedAt == null) return ReleaseStatus.None
        val elapsed = Duration.between(requestedAt, now)
        return when {
            elapsed < delay -> ReleaseStatus.Waiting(delay - elapsed)
            elapsed < window -> ReleaseStatus.Ready(window - elapsed)
            else -> ReleaseStatus.Expired
        }
    }
}
