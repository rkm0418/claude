package app.harulock.data

import android.content.Context
import android.util.Log
import app.harulock.core.ReleaseCodec
import app.harulock.core.ReleaseRecord
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

/**
 * 비상 해제의 두 파일(R5). 기기 보호 저장소의 `release.txt`(요청 시각과 시계 기준점)와 완료 표시 `released`.
 * SharedPreferences를 쓰지 않으므로 프로세스마다 따로 기억하는 값이 없다. 쓰기는 [app.harulock.service.Controller.exclusive] 안에서 한다.
 */
class ReleaseFiles(ctx: Context) {
    private val dir: File = ctx.applicationContext.createDeviceProtectedStorageContext().filesDir
    private val record = File(dir, RECORD)
    private val marker = File(dir, MARKER)

    /** 없거나 읽을 수 없으면 null. 읽지 못하면 요청이 없는 것으로 본다. */
    fun readRecord(): ReleaseRecord? {
        if (!record.exists()) return null
        return runCatching { ReleaseCodec.decode(record.readText(Charsets.UTF_8)) }
            .onFailure { Log.w(TAG, "cannot read $RECORD", it) }
            .getOrNull()
    }

    /** 성공하면 true. 임시 파일에 써서 디스크에 내린 뒤 이름을 바꾼다. */
    fun writeRecord(r: ReleaseRecord): Boolean = writeAtomically(record, ReleaseCodec.encode(r))

    /** 완료 표시가 있으면 그 안의 표식(읽지 못하면 빈 문자열), 없으면 null. */
    fun markerToken(): String? {
        if (!marker.exists()) return null
        return runCatching { marker.readText(Charsets.UTF_8) }.getOrDefault("")
    }

    /** 새 표식으로 완료 표시를 만든다. 실패하면 null. */
    fun createMarker(): String? {
        val token = UUID.randomUUID().toString()
        return if (writeAtomically(marker, token)) token else null
    }

    /** 요청 기록을 지운다. 없으면 true. */
    fun deleteRecord(): Boolean = delete(record)

    /** 완료 표시를 지운다. 없으면 true. */
    fun deleteMarker(): Boolean = delete(marker)

    private fun delete(file: File): Boolean {
        runCatching { File(dir, file.name + TMP).delete() }
        return !file.exists() || file.delete() || !file.exists()
    }

    private fun writeAtomically(target: File, text: String): Boolean = runCatching {
        val tmp = File(dir, target.name + TMP)
        FileOutputStream(tmp).use { out ->
            out.write(text.toByteArray(Charsets.UTF_8))
            out.fd.sync()
        }
        check(tmp.renameTo(target)) { "rename failed" }
        true
    }.onFailure { Log.w(TAG, "cannot write ${target.name}", it) }.getOrDefault(false)

    companion object {
        private const val TAG = "ReleaseFiles"
        private const val RECORD = "release.txt"
        private const val MARKER = "released"
        private const val TMP = ".tmp"

        /** 완료 표시가 있는가. 디스크를 매번 확인하므로 프로세스 사이에 늦은 값이 없다. */
        fun released(ctx: Context): Boolean =
            File(ctx.applicationContext.createDeviceProtectedStorageContext().filesDir, MARKER).exists()
    }
}
