package app.harulock.ui

import android.app.Activity
import android.app.AlertDialog
import android.app.TimePickerDialog
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import app.harulock.R
import app.harulock.core.DayRule
import app.harulock.core.Defaults
import app.harulock.core.Display
import app.harulock.core.Settings
import java.time.DayOfWeek

/**
 * 요일별 한도와 시작 시각. 대기 중인 설정(없으면 지금 설정) 위에서 고치고, 저장할 때 요일 부분만 바꿔
 * [app.harulock.service.Controller.requestSettings]에 넘긴다(R19).
 */
class SettingsActivity : Activity() {
    private class Row(root: View) {
        val day: TextView = root.findViewById(R.id.tv_day)
        val limit: EditText = root.findViewById(R.id.input_limit)
        val start: Button = root.findViewById(R.id.btn_start_time)
        val error: TextView = root.findViewById(R.id.tv_error)
    }

    private lateinit var rows: List<Row>
    private lateinit var tvPendingNotice: TextView
    private lateinit var btnSave: Button

    /** 요일 순서(월~일)대로의 시작 시각(분). */
    private val starts = IntArray(DAYS.size) { Defaults.START_MINUTE }

    /** 처음 읽은 바탕의 시작 시각. 이번에 시작 시각을 바꿨는지 알아내는 데 쓴다. */
    private var baseStarts: IntArray? = null
    private var armed = false
    private var loaded = false
    private var busy = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        tvPendingNotice = findViewById(R.id.tv_pending_notice)
        btnSave = findViewById(R.id.btn_save)
        rows = ROW_IDS.map { Row(findViewById(it)) }
        rows.forEachIndexed { i, row ->
            row.day.text = Texts.dayName(this, DAYS[i])
            // 일곱 칸이 같은 ID라 시스템 자동 저장은 서로 덮어쓴다. 직접 저장한다.
            row.limit.isSaveEnabled = false
            row.start.setOnClickListener { pickStart(i) }
            row.error.visibility = View.GONE
        }
        findViewById<Button>(R.id.btn_allowed_apps).setOnClickListener {
            startActivity(Intent(this, AllowedAppsActivity::class.java))
        }
        btnSave.setOnClickListener { save() }

        val restored = savedInstanceState?.takeIf { it.getBoolean(KEY_LOADED) }
        if (restored != null) {
            restore(restored)
        } else {
            load()
        }
    }

    override fun onResume() {
        super.onResume()
        // 허용앱 화면에서 바뀌었을 수 있다. 입력칸은 건드리지 않고 안내만 다시 읽는다.
        if (loaded) refreshNotice()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putBoolean(KEY_LOADED, loaded)
        if (!loaded) return
        outState.putStringArray(KEY_LIMITS, rows.map { it.limit.text.toString() }.toTypedArray())
        outState.putIntArray(KEY_STARTS, starts)
        baseStarts?.let { outState.putIntArray(KEY_BASE_STARTS, it) }
        outState.putBoolean(KEY_ARMED, armed)
    }

    private fun restore(b: Bundle) {
        val limits = b.getStringArray(KEY_LIMITS)
        val saved = b.getIntArray(KEY_STARTS)
        if (limits == null || saved == null || limits.size != DAYS.size || saved.size != DAYS.size) {
            load()
            return
        }
        rows.forEachIndexed { i, row -> row.limit.setText(limits[i]) }
        saved.copyInto(starts)
        baseStarts = b.getIntArray(KEY_BASE_STARTS)
        armed = b.getBoolean(KEY_ARMED)
        rows.indices.forEach { showStart(it) }
        loaded = true
        btnSave.isEnabled = true
        refreshNotice()
    }

    private fun load() {
        btnSave.isEnabled = false
        Work.run(this, { SettingsEdit.read(this) }) { result ->
            result.onSuccess { snapshot ->
                val week = snapshot.base.week
                DAYS.forEachIndexed { i, day ->
                    val rule = week.getValue(day)
                    rows[i].limit.setText(rule.limitMinutes.toString())
                    starts[i] = rule.startMinute
                    showStart(i)
                }
                baseStarts = starts.copyOf()
                armed = snapshot.armed
                loaded = true
                btnSave.isEnabled = true
                showNotice(snapshot)
            }.onFailure {
                showMessage(R.string.save_failed)
            }
        }
    }

    private fun refreshNotice() {
        Work.run(this, { SettingsEdit.read(this) }) { result ->
            result.onSuccess { snapshot ->
                armed = snapshot.armed
                showNotice(snapshot)
            }
        }
    }

    private fun showNotice(snapshot: Snapshot) {
        val text = snapshot.state?.takeIf { it.armed }?.let { Texts.pendingNotice(this, it) }
        tvPendingNotice.text = text ?: ""
        tvPendingNotice.visibility = if (text != null) View.VISIBLE else View.GONE
    }

    private fun pickStart(i: Int) {
        TimePickerDialog(
            this,
            { _, hour, minute ->
                starts[i] = (hour * 60 + minute).coerceIn(Display.START_RANGE)
                showStart(i)
            },
            starts[i] / 60,
            starts[i] % 60,
            true,
        ).show()
    }

    private fun showStart(i: Int) {
        rows[i].start.text = Texts.startTime(this, starts[i])
    }

    /** 칸마다 1~1440을 확인하고 틀린 칸에 [Row.error]를 보인다. 모두 맞으면 요일 설정. */
    private fun readWeek(): Map<DayOfWeek, DayRule>? {
        var ok = true
        val week = HashMap<DayOfWeek, DayRule>()
        rows.forEachIndexed { i, row ->
            val limit = Display.parseMinutes(row.limit.text.toString())
            row.error.visibility = if (limit == null) View.VISIBLE else View.GONE
            if (limit == null) {
                ok = false
            } else {
                week[DAYS[i]] = DayRule(limit, starts[i])
            }
        }
        return if (ok) week else null
    }

    private fun save() {
        if (!loaded || busy) return
        val week = readWeek()
        if (week == null) {
            Toast.makeText(this, R.string.error_fix_inputs, Toast.LENGTH_LONG).show()
            return
        }
        // 잠금 중 시작 시각을 바꾸면 바뀌는 날의 하루가 길어진다(48시간 가까이). 먼저 알린다.
        val startChanged = baseStarts?.let { !it.contentEquals(starts) } ?: false
        if (armed && startChanged) {
            AlertDialog.Builder(this)
                .setTitle(R.string.confirm_start_title)
                .setMessage(R.string.confirm_start_message)
                .setPositiveButton(R.string.action_save) { _, _ -> request(week) }
                .setNegativeButton(R.string.action_cancel, null)
                .show()
        } else {
            request(week)
        }
    }

    private fun request(week: Map<DayOfWeek, DayRule>) {
        setBusy(true)
        Work.run(this, { SettingsEdit.request(this) { base -> Settings(week, base.allowed) } }) { result ->
            setBusy(false)
            val saved = result.getOrNull()
            if (saved?.change == null) {
                showMessage(R.string.save_failed)
            } else {
                baseStarts = starts.copyOf()
                armed = saved.after.armed
                showNotice(saved.after)
                Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setBusy(value: Boolean) {
        busy = value
        btnSave.isEnabled = !value && loaded
    }

    private fun showMessage(text: Int) {
        AlertDialog.Builder(this)
            .setMessage(text)
            .setPositiveButton(R.string.action_ok, null)
            .show()
    }

    private companion object {
        val DAYS = listOf(
            DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY,
            DayOfWeek.FRIDAY, DayOfWeek.SATURDAY, DayOfWeek.SUNDAY,
        )
        val ROW_IDS = listOf(
            R.id.day_mon, R.id.day_tue, R.id.day_wed, R.id.day_thu, R.id.day_fri, R.id.day_sat, R.id.day_sun,
        )
        const val KEY_LOADED = "loaded"
        const val KEY_LIMITS = "limits"
        const val KEY_STARTS = "starts"
        const val KEY_BASE_STARTS = "baseStarts"
        const val KEY_ARMED = "armed"
    }
}
