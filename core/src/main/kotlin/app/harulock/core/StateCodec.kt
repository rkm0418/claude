package app.harulock.core

import java.time.DayOfWeek
import java.time.Instant
import java.util.zip.CRC32

/**
 * [CoreState]의 저장 형식. 줄 단위 `key=value`이며 첫 줄은 버전, 마지막 줄은 그 앞 본문의 CRC32.
 * 집합은 원소마다 한 줄이고, 값의 줄바꿈과 역슬래시는 `\n`, `\\`로 쓴다.
 */
object StateCodec {
    private const val VERSION_LINE = "v=1\n"

    fun encode(s: CoreState): String {
        val body = buildString {
            fun line(key: String, value: Any) {
                append(key).append('=').append(escape(value.toString())).append('\n')
            }

            fun settings(prefix: String, settings: Settings) {
                for (day in DayOfWeek.values()) {
                    val rule = settings.week.getValue(day)
                    line("$prefix.week.$day", "${rule.limitMinutes},${rule.startMinute}")
                }
                settings.allowed.forEach { line("$prefix.allowed", it) }
            }

            append(VERSION_LINE)
            line("armed", s.armed)
            line("instantUntil", s.instantUntil ?: "")
            line("period.day", s.period.day)
            line("period.start", s.period.start)
            line("period.end", s.period.end)
            line("meter.countedUntil", s.meter.countedUntil)
            line("meter.usedMillis", s.meter.usedMillis)
            line("meter.screenOn", s.meter.screenOn)
            line("meter.keyguard", s.meter.keyguard)
            s.meter.resumed.forEach { line("meter.resumed", it) }
            settings("settings", s.settings)
            line("pending", s.pending != null)
            s.pending?.let { settings("pending", it) }
        }
        return body + checksumLine(body)
    }

    /** 손상되었거나 알 수 없는 형식이면 예외 없이 null. */
    fun decode(text: String): CoreState? = runCatching { parse(text) }.getOrNull()

    private fun parse(text: String): CoreState {
        val body = text.substring(0, text.lastIndexOf('\n') + 1)
        require(text.substring(body.length) == checksumLine(body))
        require(body.startsWith(VERSION_LINE))

        // 읽은 키는 지운다. 끝까지 남은 키가 있으면 알 수 없는 형식이다.
        val fields = body.removePrefix(VERSION_LINE).split('\n').dropLast(1)
            .onEach { require('=' in it) }
            .groupByTo(mutableMapOf(), { it.substringBefore('=') }, { unescape(it.substringAfter('=')) })

        fun one(key: String): String = fields.remove(key)!!.single()
        fun many(key: String): Set<String> = fields.remove(key).orEmpty().toSet()
        fun instant(key: String): Instant = Instant.parse(one(key))
        fun boolean(key: String): Boolean = one(key).toBooleanStrictOrNull()!!

        fun settings(prefix: String): Settings = Settings(
            week = DayOfWeek.values().associateWith { day ->
                val (limit, start) = one("$prefix.week.$day").split(',').also { require(it.size == 2) }
                DayRule(limit.toInt(), start.toInt())
            },
            allowed = many("$prefix.allowed"),
        )

        val state = CoreState(
            settings = settings("settings"),
            pending = if (boolean("pending")) settings("pending") else null,
            armed = boolean("armed"),
            period = Period(DayOfWeek.valueOf(one("period.day")), instant("period.start"), instant("period.end")),
            meter = MeterState(
                countedUntil = instant("meter.countedUntil"),
                usedMillis = one("meter.usedMillis").toLong(),
                resumed = many("meter.resumed"),
                screenOn = boolean("meter.screenOn"),
                keyguard = boolean("meter.keyguard"),
            ),
            instantUntil = one("instantUntil").takeIf { it.isNotEmpty() }?.let { Instant.parse(it) },
        )
        require(fields.isEmpty())
        return state
    }

    private fun checksumLine(body: String): String {
        val crc = CRC32().apply { update(body.toByteArray(Charsets.UTF_8)) }
        return "crc=" + crc.value.toString(16)
    }

    private fun escape(value: String): String = value.replace("\\", "\\\\").replace("\n", "\\n")

    private fun unescape(value: String): String = buildString {
        var i = 0
        while (i < value.length) {
            val c = value[i++]
            if (c != '\\') {
                append(c)
                continue
            }
            append(
                when (value[i++]) {
                    '\\' -> '\\'
                    'n' -> '\n'
                    else -> throw IllegalArgumentException("bad escape: $value")
                },
            )
        }
    }
}
