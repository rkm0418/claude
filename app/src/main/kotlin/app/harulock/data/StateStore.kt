package app.harulock.data

import android.content.Context
import android.util.Log
import app.harulock.core.ClockAnchor
import app.harulock.core.CoreState
import app.harulock.core.StateCodec
import java.time.Instant

sealed interface Loaded {
    data class Ok(val state: CoreState) : Loaded
    /** 저장한 적이 없다. */
    object Empty : Loaded
    /** 저장한 것이 있으나 두 칸 모두 읽을 수 없다. */
    object Corrupt : Loaded
}

/** 재부팅 직후 잠금 해제 전에도 읽을 수 있도록 기기 보호 저장소에 둔다. */
class StateStore(ctx: Context) {
    private val prefs = ctx.applicationContext.createDeviceProtectedStorageContext()
        .getSharedPreferences("state", Context.MODE_PRIVATE)

    fun load(): Loaded {
        if (!prefs.contains(CURRENT) && !prefs.contains(BACKUP)) return Loaded.Empty
        val state = decode(CURRENT) ?: decode(BACKUP)
        return if (state != null) Loaded.Ok(state) else Loaded.Corrupt
    }

    /** 읽을 수 있는 직전 상태를 백업 칸으로 옮기고 새 상태를 쓴다. 손상된 값은 백업을 덮지 않는다. */
    fun save(s: CoreState) {
        val editor = prefs.edit()
        if (decode(CURRENT) != null) editor.putString(BACKUP, text(CURRENT))
        editor.putString(CURRENT, StateCodec.encode(s))
        if (!editor.commit()) Log.w(TAG, "state not saved")
    }

    /** 신뢰 시계의 기준점. 없거나 읽을 수 없으면 null. */
    var anchor: ClockAnchor?
        get() = text(ANCHOR)?.let { stored ->
            runCatching {
                val (wall, elapsed, boot) = stored.split(',')
                ClockAnchor(Instant.parse(wall), elapsed.toLong(), boot.toInt())
            }.getOrNull()
        }
        set(value) {
            val editor = prefs.edit()
            if (value == null) {
                editor.remove(ANCHOR)
            } else {
                editor.putString(ANCHOR, "${value.wall},${value.elapsedMillis},${value.bootCount}")
            }
            if (!editor.commit()) Log.w(TAG, "anchor not saved")
        }

    private fun text(key: String): String? = runCatching { prefs.getString(key, null) }.getOrNull()

    private fun decode(key: String): CoreState? = text(key)?.let { StateCodec.decode(it) }

    private companion object {
        const val TAG = "StateStore"
        const val CURRENT = "current"
        const val BACKUP = "backup"
        const val ANCHOR = "anchor"
    }
}
