package app.harulock.ui

import android.app.Activity
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import app.harulock.R
import app.harulock.core.Change
import app.harulock.core.CoreState
import app.harulock.core.Defaults
import app.harulock.core.Display
import app.harulock.core.Engine
import app.harulock.core.Settings
import app.harulock.core.TrustedClock
import app.harulock.data.Loaded
import app.harulock.data.StateStore
import app.harulock.service.Controller
import java.time.DayOfWeek
import java.time.Duration
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import java.util.concurrent.Executors
import android.provider.Settings.Global as GlobalSettings

/** 저장 상태와 화면 갱신은 메인 스레드 밖에서 하고, 결과는 화면이 살아 있을 때만 메인 스레드로 돌려준다. */
internal object Work {
    private const val TAG = "Work"
    private val executor = Executors.newCachedThreadPool()
    private val main = Handler(Looper.getMainLooper())

    fun <T> run(activity: Activity, task: () -> T, done: (Result<T>) -> Unit) {
        executor.execute {
            val result = runCatching(task).onFailure { Log.w(TAG, "background task failed", it) }
            main.post { if (!activity.isFinishing && !activity.isDestroyed) done(result) }
        }
    }
}

/** 화면이 읽는 저장 상태. */
internal class Snapshot(loaded: Loaded) {
    /** 저장한 적이 없거나 읽을 수 없으면 null. */
    val state: CoreState? = (loaded as? Loaded.Ok)?.state

    /** 저장한 것이 있으나 읽을 수 없다. */
    val unreadable: Boolean = loaded is Loaded.Corrupt

    val armed: Boolean get() = state?.armed == true

    /** 화면이 고칠 바탕(R19): 대기 중인 설정, 없으면 지금 설정, 처음이면 기본값(R20). */
    val base: Settings = state?.let { it.pending ?: it.settings } ?: Defaults.SETTINGS
}

/** 설정 화면들의 읽기와 저장. */
internal object SettingsEdit {
    class Saved(val change: Change?, val after: Snapshot)

    /** 디스크를 읽으므로 메인 스레드 밖에서 부른다. */
    fun read(ctx: Context): Snapshot = Snapshot(StateStore(ctx).load())

    /**
     * 저장 상태를 다시 읽어 바탕에서 [part]가 바꾸는 부분(요일 또는 허용앱)만 바꿔 요청한다(R19).
     * 읽기와 요청을 한 번에 해서 그 사이 다른 변경이 끼지 않게 한다. 메인 스레드 밖에서 부른다.
     */
    fun request(ctx: Context, part: (Settings) -> Settings): Saved = Controller.exclusive(ctx) {
        val change = Controller(ctx).requestSettings(part(read(ctx).base))
        Saved(change, read(ctx))
    }

    /** 지금 바탕 설정으로 잠금을 시작한다. 메인 스레드 밖에서 부른다. */
    fun arm(ctx: Context): Boolean = Controller.exclusive(ctx) {
        Controller(ctx).arm(read(ctx).base)
    }
}

/** 화면 글자 만들기. 문장은 모두 strings.xml에 있다. */
internal object Texts {
    private val DAY_NAMES = mapOf(
        DayOfWeek.MONDAY to R.string.day_mon,
        DayOfWeek.TUESDAY to R.string.day_tue,
        DayOfWeek.WEDNESDAY to R.string.day_wed,
        DayOfWeek.THURSDAY to R.string.day_thu,
        DayOfWeek.FRIDAY to R.string.day_fri,
        DayOfWeek.SATURDAY to R.string.day_sat,
        DayOfWeek.SUNDAY to R.string.day_sun,
    )

    fun zone(): ZoneId = ZoneId.systemDefault()

    fun dayName(ctx: Context, day: DayOfWeek): String = ctx.getString(DAY_NAMES.getValue(day))

    /** 남은 시간. 분으로 올려 센다. */
    fun remaining(ctx: Context, millis: Long): String {
        val minutes = Display.ceilMinutes(millis)
        val hours = minutes / 60
        return if (hours > 0) {
            ctx.getString(R.string.remaining_hours_minutes, hours.toInt(), (minutes % 60).toInt())
        } else {
            ctx.getString(R.string.remaining_minutes, minutes.toInt())
        }
    }

    fun dateTime(ctx: Context, t: Instant): String =
        DateTimeFormatter.ofPattern(ctx.getString(R.string.format_date_time), Locale.KOREAN)
            .format(t.atZone(zone()))

    fun startTime(ctx: Context, minute: Int): String =
        ctx.getString(R.string.format_start_time, minute / 60, minute % 60)

    /** 홈의 다음 초기화부터 바뀌는 내용. 대기 중인 변경이 없으면 null. */
    fun pendingChange(ctx: Context, s: CoreState): String? {
        val pending = s.pending ?: return null
        val diff = Display.diff(s.settings, pending)
        val lines = ArrayList<String>()
        lines += ctx.getString(R.string.pending_change_title, dateTime(ctx, s.period.end))
        diff.days.forEach { d ->
            val name = dayName(ctx, d.day)
            if (d.limitFrom != d.limitTo) {
                lines += ctx.getString(R.string.pending_day_limit, name, d.limitFrom, d.limitTo)
            }
            if (d.startFrom != d.startTo) {
                lines += ctx.getString(
                    R.string.pending_day_start, name, startTime(ctx, d.startFrom), startTime(ctx, d.startTo),
                )
            }
        }
        if (diff.added.isNotEmpty()) lines += ctx.getString(R.string.pending_allowed_added, diff.added.size)
        if (diff.removed.isNotEmpty()) lines += ctx.getString(R.string.pending_allowed_removed, diff.removed.size)
        stretch(ctx, s)?.let { lines += it }
        return lines.joinToString("\n")
    }

    /** 설정 화면의 대기 안내. 대기 중인 변경이 없으면 null. */
    fun pendingNotice(ctx: Context, s: CoreState): String? {
        if (s.pending == null) return null
        val notice = ctx.getString(R.string.pending_notice, dateTime(ctx, s.period.end))
        return listOfNotNull(notice, stretch(ctx, s)).joinToString("\n")
    }

    /** 대기 중인 변경이 시작 시각을 바꾸면 길어지는 다음 하루. 그렇지 않으면 null. */
    private fun stretch(ctx: Context, s: CoreState): String? {
        val pending = s.pending ?: return null
        if (!Display.changesStart(s.settings, pending)) return null
        val next = Engine.nextPeriod(s, zone())
        val hours = (Duration.between(next.start, next.end).toMinutes() + 30) / 60
        return ctx.getString(R.string.pending_stretch, dateTime(ctx, next.start), dateTime(ctx, next.end), hours.toInt())
    }
}

/**
 * 화면에 보일 신뢰 시각. [Controller]와 같은 방법으로 구하되 기준점은 저장하지 않는다.
 * 메인 스레드 밖에서 부른다.
 */
internal fun trustedNow(ctx: Context): Instant {
    val boot = GlobalSettings.getInt(ctx.contentResolver, GlobalSettings.BOOT_COUNT, 0)
    return TrustedClock.now(StateStore(ctx).anchor, Instant.now(), SystemClock.elapsedRealtime(), boot).first
}
