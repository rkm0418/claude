package app.harulock.core

import java.time.DayOfWeek
import java.time.DayOfWeek.MONDAY
import java.time.DayOfWeek.THURSDAY
import java.time.Instant
import java.util.zip.CRC32
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class StateCodecTest {
    private val full = CoreState(
        settings = Settings(week(120, 300) + (MONDAY to DayRule(1, 0)), setOf("com.a", "com.b")),
        pending = Settings(week(1440, 1439), setOf("com.c")),
        armed = true,
        period = Period(THURSDAY, at("2026-11-26T05:00"), at("2026-11-27T05:00")),
        meter = MeterState(
            countedUntil = at("2026-11-26T10:00").plusNanos(123_456_789),
            usedMillis = 3_600_001,
            resumed = setOf("com.game/com.game.Main\$Inner"),
            screenOn = false,
            keyguard = true,
        ),
        instantUntil = at("2026-11-26T11:00"),
    )

    private val bare = full.copy(
        settings = Settings(week(), emptySet()),
        pending = null,
        armed = false,
        meter = MeterState(Instant.EPOCH),
        instantUntil = null,
    )

    private fun assertRoundTrip(s: CoreState) = assertEquals(s, StateCodec.decode(StateCodec.encode(s)))

    /** [full]의 본문을 [change]로 바꾸고 CRC를 다시 맞춘다. CRC 검사를 통과한 뒤의 검증을 시험한다. */
    private fun resealed(change: (String) -> String): String {
        val body = StateCodec.encode(full).substringBeforeLast('\n') + "\n"
        val changed = change(body)
        val crc = CRC32().apply { update(changed.toByteArray()) }.value
        return changed + "crc=" + crc.toString(16)
    }

    private fun replaceLine(key: String, line: String): (String) -> String = { body ->
        val old = body.split('\n').first { it.startsWith("$key=") }
        body.replace("$old\n", if (line.isEmpty()) "" else "$line\n")
    }

    @Test fun roundTrip() = assertRoundTrip(full)

    @Test fun garbage_isNull() = assertNull(StateCodec.decode("garbage"))

    @Test fun truncated_isNull() = assertNull(StateCodec.decode(StateCodec.encode(full).dropLast(20)))

    @Test fun tampered_isNull() = assertNull(StateCodec.decode(StateCodec.encode(full).replace("v=1", "v=2")))

    @Test fun roundTrip_nullsAndEmptySets() = assertRoundTrip(bare)

    @Test fun roundTrip_emptyPending() = assertRoundTrip(bare.copy(pending = Settings(week(), emptySet())))

    @Test fun roundTrip_manyResumedWithSpecialNames() = assertRoundTrip(
        full.copy(
            meter = full.meter.copy(
                resumed = setOf("a.b/a.b.C\$D\$1", "a.b/.Relative", "x/y=z", "x/", "p/q,r s", "앱/화면"),
                screenOn = true,
                keyguard = false,
            ),
        ))

    @Test fun roundTrip_lineBreaksAndBackslashes() = assertRoundTrip(
        full.copy(
            settings = Settings(week(), setOf("", "a\nb", "a\\nb", "a\r", "tail\\")),
            meter = full.meter.copy(resumed = setOf("p/a\ncrc=0", "p/\\\n")),
        ))

    @Test fun format_versionFirstCrcLast() {
        val lines = StateCodec.encode(full).split('\n')
        assertEquals("v=1", lines.first())
        val body = lines.dropLast(1).joinToString("") { "$it\n" }
        val crc = CRC32().apply { update(body.toByteArray()) }.value
        assertEquals("crc=" + crc.toString(16), lines.last())
        assertEquals(emptyList<String>(), lines.filter { '=' !in it })
    }

    @Test fun empty_isNull() {
        for (text in listOf("", "\n", "v=1", "v=1\n", "crc=0", "\ncrc=0")) assertNull(text, StateCodec.decode(text))
    }

    @Test fun everyTruncation_isNull() {
        val text = StateCodec.encode(full)
        for (n in 0 until text.length) assertNull("length $n", StateCodec.decode(text.take(n)))
    }

    @Test fun everySingleCharChange_isNull() {
        val text = StateCodec.encode(full)
        for (i in text.indices) {
            val changed = text.substring(0, i) + (if (text[i] == '1') '2' else '1') + text.substring(i + 1)
            assertNull("index $i", StateCodec.decode(changed))
        }
    }

    @Test fun trailingData_isNull() = assertNull(StateCodec.decode(StateCodec.encode(full) + "\n"))

    @Test fun resealedUnchanged_decodes() = assertEquals(full, StateCodec.decode(resealed { it }))

    @Test fun otherVersionWithValidCrc_isNull() =
        assertNull(StateCodec.decode(resealed { it.replace("v=1\n", "v=2\n") }))

    @Test fun everyMissingLineWithValidCrc_isNull() {
        // 집합 원소 줄은 빠져도 형식에 맞으므로 제외한다.
        val keys = StateCodec.encode(full).split('\n').dropLast(1).map { it.substringBefore('=') }
            .filterNot { it.endsWith("allowed") || it.endsWith("resumed") }
        for (key in keys) assertNull(key, StateCodec.decode(resealed(replaceLine(key, ""))))
    }

    @Test fun invalidValuesWithValidCrc_isNull() {
        val day = DayOfWeek.MONDAY.name
        val bad = listOf(
            "armed" to "armed=yes",
            "instantUntil" to "instantUntil=soon",
            "pending" to "pending=",
            "pending" to "pending=false",
            "period.day" to "period.day=FUNDAY",
            "period.start" to "period.start=",
            "meter.usedMillis" to "meter.usedMillis=99999999999999999999",
            "meter.screenOn" to "meter.screenOn=1",
            "settings.week.$day" to "settings.week.$day=0,300",
            "settings.week.$day" to "settings.week.$day=120,1440",
            "settings.week.$day" to "settings.week.$day=120",
            "settings.week.$day" to "settings.week.$day=120,300,1",
            "pending.week.$day" to "pending.week.$day=x,300",
        )
        for ((key, line) in bad) assertNull(line, StateCodec.decode(resealed(replaceLine(key, line))))
    }

    @Test fun badEscapeWithValidCrc_isNull() {
        for (value in listOf("a\\", "a\\x")) {
            assertNull(value, StateCodec.decode(resealed { it + "settings.allowed=$value\n" }))
        }
    }

    @Test fun extraLinesWithValidCrc_isNull() {
        for (line in listOf("armed=false", "unknown=1", "noequals", "")) {
            assertNull(line, StateCodec.decode(resealed { "$it$line\n" }))
        }
    }
}
