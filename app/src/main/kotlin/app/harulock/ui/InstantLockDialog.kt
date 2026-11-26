package app.harulock.ui

import android.app.Activity
import android.app.Dialog
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.view.Window
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import app.harulock.R
import app.harulock.core.Display
import app.harulock.service.Controller

/**
 * 즉시 잠금 작은 창. 경고를 늘 보여 주고, 빠른 선택 버튼은 입력칸만 채운다(R22).
 * 시작 버튼만 [Controller.instantLock]을 부른다. 잠금이 시작되면 [onLocked]를 부른다.
 */
class InstantLockDialog(
    private val owner: Activity,
    private val onLocked: () -> Unit,
) : Dialog(owner) {
    private lateinit var input: EditText
    private lateinit var tvError: TextView
    private lateinit var buttons: List<Button>
    private var busy = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestWindowFeature(Window.FEATURE_NO_TITLE)
        setContentView(R.layout.dialog_instant_lock)
        input = findViewById(R.id.input_minutes)
        tvError = findViewById(R.id.tv_error)
        findViewById<TextView>(R.id.tv_warning).visibility = View.VISIBLE

        val startButton = findViewById<Button>(R.id.btn_start)
        val cancel = findViewById<Button>(R.id.btn_cancel)
        val presets = listOf(
            findViewById<Button>(R.id.btn_30m) to 30,
            findViewById<Button>(R.id.btn_1h) to 60,
            findViewById<Button>(R.id.btn_2h) to 120,
        )
        presets.forEach { (button, minutes) ->
            button.setOnClickListener {
                input.setText(minutes.toString())
                input.setSelection(input.text.length)
                hideError()
            }
        }
        startButton.setOnClickListener { begin() }
        cancel.setOnClickListener { if (!busy) dismiss() }
        buttons = presets.map { it.first } + startButton + cancel
    }

    override fun onStart() {
        super.onStart()
        window?.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
    }

    private fun begin() {
        if (busy) return
        val minutes = Display.parseMinutes(input.text.toString())
        if (minutes == null) {
            showError(R.string.instant_error_range)
            return
        }
        hideError()
        setBusy(true)
        val app = owner.applicationContext
        Work.run(owner, { Controller(app).instantLock(minutes) }) { result ->
            setBusy(false)
            if (result.getOrDefault(false)) {
                Toast.makeText(owner, owner.getString(R.string.instant_started, minutes), Toast.LENGTH_LONG).show()
                dismiss()
                onLocked()
            } else {
                showError(R.string.instant_failed)
            }
        }
    }

    private fun setBusy(value: Boolean) {
        busy = value
        setCancelable(!value)
        buttons.forEach { it.isEnabled = !value }
        input.isEnabled = !value
    }

    private fun showError(text: Int) {
        tvError.setText(text)
        tvError.visibility = View.VISIBLE
    }

    private fun hideError() {
        tvError.visibility = View.GONE
    }
}
