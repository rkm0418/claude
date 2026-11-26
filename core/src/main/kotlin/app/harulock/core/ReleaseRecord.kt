package app.harulock.core

import java.time.Duration
import java.time.Instant
import java.util.zip.CRC32

/**
 * 비상 해제 파일(release.txt)의 내용: 요청 시각(없으면 null)과 비상 해제 화면이 쓰는 시계 기준점.
 * 요청 시각은 기준점보다 늦을 수 없다(요청할 때의 신뢰 시각이 곧 그때의 기준점이고, 기준점은 앞으로만 간다).
 */
data class ReleaseRecord(val requestedAt: Instant?, val anchor: ClockAnchor)

/**
 * [ReleaseRecord]의 저장 형식. 줄 단위 `key=value`, 첫 줄 `v=1`, 마지막 줄은 본문의 CRC32.
 * 어떤 오류든 null이다. 읽지 못하면 요청이 없는 것으로 보므로, 손상은 대기를 줄이지 않고 다시 요청하게 할 뿐이다.
 */
object ReleaseCodec {
    private const val VERSION_LINE = "v=1\n"
    private const val NONE = "-"

    fun encode(r: ReleaseRecord): String {
        val body = buildString {
            append(VERSION_LINE)
            append("requested=").append(r.requestedAt?.toString() ?: NONE).append('\n')
            append("anchor=").append(r.anchor.wall).append(',')
                .append(r.anchor.elapsedMillis).append(',').append(r.anchor.bootCount).append('\n')
        }
        return body + checksumLine(body)
    }

    fun decode(text: String): ReleaseRecord? = runCatching { parse(text) }.getOrNull()

    private fun parse(text: String): ReleaseRecord {
        val body = text.substring(0, text.lastIndexOf('\n') + 1)
        require(text.substring(body.length) == checksumLine(body))
        require(body.startsWith(VERSION_LINE))
        val lines = body.removePrefix(VERSION_LINE).split('\n').dropLast(1)
        require(lines.size == 2)
        val requested = lines[0].removePrefixOrFail("requested=")
        val anchorParts = lines[1].removePrefixOrFail("anchor=").split(',')
        require(anchorParts.size == 3)
        val anchor = ClockAnchor(Instant.parse(anchorParts[0]), anchorParts[1].toLong(), anchorParts[2].toInt())
        require(anchor.elapsedMillis >= 0)
        val requestedAt = if (requested == NONE) null else Instant.parse(requested)
        require(requestedAt == null || requestedAt <= anchor.wall)
        return ReleaseRecord(requestedAt, anchor)
    }

    private fun String.removePrefixOrFail(prefix: String): String {
        require(startsWith(prefix))
        return substring(prefix.length)
    }

    private fun checksumLine(body: String): String {
        val crc = CRC32()
        crc.update(body.toByteArray(Charsets.UTF_8))
        return "crc=%08x".format(crc.value)
    }
}

/** 비상 해제 화면의 상태. */
sealed interface ReleaseView {
    object None : ReleaseView
    data class Waiting(val left: Duration) : ReleaseView
    data class Ready(val left: Duration) : ReleaseView
    object Expired : ReleaseView
    /** 해제를 시작했으나(완료 표시 있음) 아직 기기 소유자다. 다시 시도해야 한다. */
    object Incomplete : ReleaseView
    /** 해제를 마쳤다. */
    object Done : ReleaseView
}

/** 비상 해제 화면의 판단. 파일과 시스템 호출은 앱이 하고, 여기서는 값만 정한다. */
object ReleaseFlow {
    /**
     * 기록의 기준점으로 신뢰 시각을 구한다. 부팅 번호를 읽지 못해 같은 번호로 보이는 재부팅에서도
     * 기준점보다 이른 시각은 내지 않는다. 돌려준 기준점을 저장한다.
     */
    fun clock(record: ReleaseRecord?, wall: Instant, elapsedMillis: Long, bootCount: Int): Pair<Instant, ClockAnchor> {
        val (now, anchor) = TrustedClock.now(record?.anchor, wall, elapsedMillis, bootCount)
        val floor = record?.anchor?.wall ?: return now to anchor
        return if (now < floor) floor to anchor.copy(wall = floor) else now to anchor
    }

    /**
     * 완료 표시([marker])가 있으면 요청 기록과 상관없이 기기 소유자 여부로 완료/미완료를 정한다.
     * 완료 표시는 [Ready]에서 확인한 뒤에만 생기므로 미완료의 재시도는 대기를 건너뛰는 길이 아니다.
     */
    fun view(record: ReleaseRecord?, now: Instant, marker: Boolean, owner: Boolean): ReleaseView {
        if (marker) return if (owner) ReleaseView.Incomplete else ReleaseView.Done
        return when (val s = EmergencyRelease.status(record?.requestedAt, now)) {
            ReleaseStatus.None -> ReleaseView.None
            is ReleaseStatus.Waiting -> ReleaseView.Waiting(s.left)
            is ReleaseStatus.Ready -> ReleaseView.Ready(s.left)
            ReleaseStatus.Expired -> ReleaseView.Expired
        }
    }

    /** 요청이 없거나 만료되었을 때만 [now]로 새 요청을 만든다. 대기 중이거나 확인 가능하면 null(그대로 둔다). */
    fun request(record: ReleaseRecord?, now: Instant, anchor: ClockAnchor): ReleaseRecord? =
        when (EmergencyRelease.status(record?.requestedAt, now)) {
            ReleaseStatus.None, ReleaseStatus.Expired -> ReleaseRecord(now, anchor)
            is ReleaseStatus.Waiting, is ReleaseStatus.Ready -> null
        }

    /** 요청을 지운다. 시계 기준점은 남긴다. */
    fun cancel(anchor: ClockAnchor): ReleaseRecord = ReleaseRecord(null, anchor)

    /** 해제 동작을 시작해도 되는가: 미완료의 재시도이거나, 완료 표시가 없고 지금 [ReleaseStatus.Ready]. */
    fun mayRelease(record: ReleaseRecord?, now: Instant, marker: Boolean, owner: Boolean): Boolean =
        when (view(record, now, marker, owner)) {
            ReleaseView.Incomplete, is ReleaseView.Ready -> true
            else -> false
        }
}
