package app.harulock.core

import java.time.Duration
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ReleaseRecordTest {
    private val anchor = ClockAnchor(at("2026-11-26T10:00"), 1_000_000, 3)
    private val requested = ReleaseRecord(at("2026-11-26T09:00"), anchor)
    private val empty = ReleaseRecord(null, anchor)

    @Test fun roundTrip_withRequest() = assertEquals(requested, ReleaseCodec.decode(ReleaseCodec.encode(requested)))

    @Test fun roundTrip_withoutRequest() = assertEquals(empty, ReleaseCodec.decode(ReleaseCodec.encode(empty)))

    @Test fun decode_rejectsChangedText() {
        val text = ReleaseCodec.encode(requested).replace("T00:00:00Z", "T00:00:01Z")
        assertNull(ReleaseCodec.decode(text))
    }

    @Test fun decode_rejectsEveryTruncation() {
        val text = ReleaseCodec.encode(requested)
        for (n in 0 until text.length) assertNull("length $n", ReleaseCodec.decode(text.substring(0, n)))
    }

    @Test fun decode_rejectsTrailingNewline() = assertNull(ReleaseCodec.decode(ReleaseCodec.encode(requested) + "\n"))

    @Test fun decode_rejectsGarbage() {
        assertNull(ReleaseCodec.decode(""))
        assertNull(ReleaseCodec.decode("\u0000\u0000"))
        assertNull(ReleaseCodec.decode("v=1\nrequested=-\n"))
    }

    @Test fun decode_rejectsRequestAfterAnchor() {
        val bad = ReleaseRecord(at("2026-11-26T11:00"), anchor)
        assertNull(ReleaseCodec.decode(ReleaseCodec.encode(bad)))
    }

    @Test fun decode_rejectsNegativeElapsed() {
        val bad = ReleaseRecord(null, anchor.copy(elapsedMillis = -1))
        assertNull(ReleaseCodec.decode(ReleaseCodec.encode(bad)))
    }

    @Test fun decode_rejectsOtherVersion() {
        val text = ReleaseCodec.encode(requested)
        val body = "v=2\n" + text.substringAfter("v=1\n").substringBeforeLast("crc=")
        assertNull(ReleaseCodec.decode(body + "crc=00000000"))
    }

    @Test fun clock_sameBootUsesElapsed() = assertEquals(at("2026-11-26T10:01"),
        ReleaseFlow.clock(empty, at("2030-01-01T00:00"), 1_060_000, 3).first)

    @Test fun clock_neverBeforeAnchor_evenWithSameBootCount() {
        val (now, next) = ReleaseFlow.clock(empty, at("2026-11-26T08:00"), 5_000, 3)
        assertEquals(anchor.wall, now)
        assertEquals(ClockAnchor(anchor.wall, 5_000, 3), next)
    }

    @Test fun clock_rebootWithClockBehindKeepsAnchor() = assertEquals(anchor.wall,
        ReleaseFlow.clock(empty, at("2026-11-26T08:00"), 5_000, 4).first)

    @Test fun clock_noRecordUsesWall() = assertEquals(at("2026-11-26T12:00"),
        ReleaseFlow.clock(null, at("2026-11-26T12:00"), 5_000, 4).first)

    @Test fun view_statesFromRequest() {
        val t = requested.requestedAt!!
        assertEquals(ReleaseView.None, ReleaseFlow.view(null, t, marker = false, owner = true))
        assertEquals(ReleaseView.None, ReleaseFlow.view(empty, t, marker = false, owner = true))
        assertEquals(ReleaseView.Waiting(Duration.ofHours(1)),
            ReleaseFlow.view(requested, t.plus(Duration.ofHours(23)), marker = false, owner = true))
        assertEquals(ReleaseView.Ready(Duration.ofHours(24)),
            ReleaseFlow.view(requested, t.plus(Duration.ofHours(24)), marker = false, owner = true))
        assertEquals(ReleaseView.Expired,
            ReleaseFlow.view(requested, t.plus(Duration.ofHours(48)), marker = false, owner = true))
    }

    @Test fun view_markerDecidesDoneOrIncomplete() {
        val t = requested.requestedAt!!
        assertEquals(ReleaseView.Incomplete, ReleaseFlow.view(null, t, marker = true, owner = true))
        assertEquals(ReleaseView.Done, ReleaseFlow.view(requested, t, marker = true, owner = false))
    }

    @Test fun mayRelease_onlyWhenReadyOrRetrying() {
        val t = requested.requestedAt!!
        assertFalse(ReleaseFlow.mayRelease(null, t, marker = false, owner = true))
        assertFalse(ReleaseFlow.mayRelease(requested, t.plus(Duration.ofMinutes(1439)), marker = false, owner = true))
        assertTrue(ReleaseFlow.mayRelease(requested, t.plus(Duration.ofMinutes(1440)), marker = false, owner = true))
        assertFalse(ReleaseFlow.mayRelease(requested, t.plus(Duration.ofHours(48)), marker = false, owner = true))
        assertTrue(ReleaseFlow.mayRelease(null, t, marker = true, owner = true))
        assertFalse(ReleaseFlow.mayRelease(null, t, marker = true, owner = false))
    }

    private fun req(record: ReleaseRecord?, now: java.time.Instant, a: ClockAnchor = anchor) =
        ReleaseFlow.request(record, now, a, network = null, networkRequired = false)

    @Test fun request_onlyFromNoneOrExpired() {
        val t = requested.requestedAt!!
        val later = anchor.copy(wall = t.plus(Duration.ofHours(48)))
        assertEquals(RequestResult.New(ReleaseRecord(t, anchor)), req(null, t))
        assertEquals(RequestResult.New(ReleaseRecord(t, anchor)), req(empty, t))
        assertEquals(RequestResult.Unchanged, req(requested, t.plus(Duration.ofHours(1))))
        assertEquals(RequestResult.Unchanged, req(requested, t.plus(Duration.ofHours(30))))
        assertEquals(RequestResult.New(ReleaseRecord(later.wall, later)), req(requested, later.wall, later))
    }

    @Test fun request_networkLaterThanClock_usesNetworkForRequestAndAnchor() {
        // 잠금 전에 시계를 23시간 뒤로 돌려 둔 경우: 요청 시각이 실제 시각이 되어 대기가 줄지 않는다.
        val now = anchor.wall
        val network = now.plus(Duration.ofHours(23))
        val r = ReleaseFlow.request(null, now, anchor, network, networkRequired = true)
        assertEquals(RequestResult.New(ReleaseRecord(network, anchor.copy(wall = network))), r)
        val saved = (r as RequestResult.New).record
        // 재부팅 뒤 실제 시각으로 1시간이 지나도 아직 23시간을 기다려야 한다.
        val after = ReleaseFlow.clock(saved, network.plus(Duration.ofHours(1)), 5_000, 9).first
        assertEquals(ReleaseView.Waiting(Duration.ofHours(23)), ReleaseFlow.view(saved, after, marker = false, owner = true))
    }

    @Test fun request_networkEarlierThanClock_keepsClock() {
        val now = anchor.wall
        val r = ReleaseFlow.request(null, now, anchor, now.minus(Duration.ofHours(5)), networkRequired = true)
        assertEquals(RequestResult.New(ReleaseRecord(now, anchor)), r)
    }

    @Test fun request_withoutNetworkTime_isRefusedWhenRequired() {
        assertEquals(RequestResult.NeedNetwork, ReleaseFlow.request(null, anchor.wall, anchor, null, networkRequired = true))
        assertEquals(RequestResult.NeedNetwork, ReleaseFlow.request(empty, anchor.wall, anchor, null, networkRequired = true))
    }

    @Test fun request_alreadyWaiting_needsNoNetwork() {
        val t = requested.requestedAt!!
        assertEquals(RequestResult.Unchanged,
            ReleaseFlow.request(requested, t.plus(Duration.ofHours(1)), anchor, null, networkRequired = true))
    }

    @Test fun request_networkNeverMovesAnExistingRequest() {
        val t = requested.requestedAt!!
        val far = t.plus(Duration.ofDays(10))
        assertEquals(RequestResult.Unchanged,
            ReleaseFlow.request(requested, t.plus(Duration.ofHours(25)), anchor, far, networkRequired = true))
    }

    @Test fun cancel_keepsAnchor() = assertEquals(empty, ReleaseFlow.cancel(anchor))
}
