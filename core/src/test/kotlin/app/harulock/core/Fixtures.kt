package app.harulock.core

import java.time.DayOfWeek
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId

val SEOUL: ZoneId = ZoneId.of("Asia/Seoul")

/** "2026-11-26T05:00" 형식의 서울 현지 시각. */
fun at(local: String): Instant = LocalDateTime.parse(local).atZone(SEOUL).toInstant()

fun week(limit: Int = 120, start: Int = 300): Map<DayOfWeek, DayRule> =
    DayOfWeek.values().associateWith { DayRule(limit, start) }
