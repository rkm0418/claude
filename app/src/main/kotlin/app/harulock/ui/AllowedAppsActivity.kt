package app.harulock.ui

import android.app.Activity
import android.app.AlertDialog
import android.graphics.drawable.Drawable
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageView
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import app.harulock.R
import app.harulock.core.Policy
import app.harulock.data.DeviceInfo
import app.harulock.data.deviceApps
import java.text.Collator
import java.util.Locale

/**
 * 허용앱 고르기. 대기 중인 설정(없으면 지금 설정)의 허용앱에서 시작해, 완료하면 허용앱 부분만 바꿔
 * 요청한다(R19). 브라우저나 앱 스토어를 고르면 한 번 더 묻는다.
 */
class AllowedAppsActivity : Activity() {
    private class App(val pkg: String, val label: String, val icon: Drawable?)

    private class Data(val apps: List<App>, val allowed: Set<String>, val browsers: Set<String>)

    private lateinit var input: EditText
    private lateinit var list: ListView
    private lateinit var tvEmpty: TextView
    private lateinit var btnDone: Button

    private var all: List<App> = emptyList()
    private var shown: List<App> = emptyList()
    private val selected = HashSet<String>()
    private var original: Set<String> = emptySet()
    private var browsers: Set<String> = emptySet()
    private var restored: Set<String>? = null
    private var loaded = false
    private var busy = false

    private val adapter = object : BaseAdapter() {
        override fun getCount(): Int = shown.size
        override fun getItem(position: Int): Any = shown[position]
        override fun getItemId(position: Int): Long = position.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
            val view = convertView ?: LayoutInflater.from(parent.context).inflate(R.layout.item_app, parent, false)
            val app = shown[position]
            view.findViewById<ImageView>(R.id.img_icon).setImageDrawable(app.icon)
            view.findViewById<TextView>(R.id.tv_app_name).text = app.label
            view.findViewById<CheckBox>(R.id.cb_allowed).apply {
                // 줄 전체가 눌리도록 체크 상자는 누름을 받지 않는다.
                isClickable = false
                isFocusable = false
                isChecked = app.pkg in selected
            }
            return view
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_allowed_apps)
        input = findViewById(R.id.input_search)
        list = findViewById(R.id.list_apps)
        tvEmpty = findViewById(R.id.tv_empty)
        btnDone = findViewById(R.id.btn_done)

        tvEmpty.setText(R.string.allowed_loading)
        list.emptyView = tvEmpty
        list.adapter = adapter
        list.setOnItemClickListener { _, _, position, _ -> shown.getOrNull(position)?.let { toggle(it) } }
        input.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) = Unit
            override fun afterTextChanged(s: Editable?) = filter()
        })
        btnDone.setOnClickListener { done() }
        restored = savedInstanceState?.getStringArrayList(KEY_SELECTED)?.toSet()
        load()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        if (loaded) outState.putStringArrayList(KEY_SELECTED, ArrayList(selected))
    }

    private fun load() {
        btnDone.isEnabled = false
        val ctx = applicationContext
        Work.run(this, {
            val base = SettingsEdit.read(ctx).base
            val device = deviceApps(ctx)
            val infos = DeviceInfo.installed(ctx).associateBy { it.packageName }
            val pm = ctx.packageManager
            // 정지 대상이 되는 앱과, 이미 허용한 앱 중 설치된 것.
            val packages = Policy.suspendTargets(device, emptySet()) + (base.allowed intersect infos.keys)
            val collator = Collator.getInstance(Locale.KOREAN)
            val apps = packages.mapNotNull { pkg ->
                val info = infos[pkg] ?: return@mapNotNull null
                val label = runCatching { info.loadLabel(pm).toString() }.getOrDefault(pkg)
                App(pkg, label, runCatching { info.loadIcon(pm) }.getOrNull())
            }.sortedWith(compareBy(collator) { it.label })
            Data(apps, base.allowed, DeviceInfo.browsers(ctx))
        }) { result ->
            result.onSuccess { data ->
                all = data.apps
                original = data.allowed
                browsers = data.browsers
                selected.clear()
                selected += restored ?: data.allowed
                loaded = true
                btnDone.isEnabled = true
                filter()
            }.onFailure {
                tvEmpty.setText(R.string.load_failed)
            }
        }
    }

    private fun filter() {
        val query = input.text.toString().trim().lowercase(Locale.ROOT)
        shown = if (query.isEmpty()) {
            all
        } else {
            all.filter { it.label.lowercase(Locale.ROOT).contains(query) || it.pkg.contains(query) }
        }
        // 목록이 비었을 때: 검색어가 있으면 검색 결과 없음, 없으면 고를 앱이 없음.
        if (loaded) tvEmpty.setText(if (query.isEmpty()) R.string.allowed_none else R.string.allowed_empty)
        adapter.notifyDataSetChanged()
    }

    private fun toggle(app: App) {
        if (busy) return
        if (app.pkg in selected) {
            selected -= app.pkg
            adapter.notifyDataSetChanged()
            return
        }
        if (!Policy.needsAllowConfirm(app.pkg, browsers)) {
            selected += app.pkg
            adapter.notifyDataSetChanged()
            return
        }
        AlertDialog.Builder(this)
            .setTitle(R.string.confirm_risky_title)
            .setMessage(getString(R.string.confirm_risky_message, app.label))
            .setPositiveButton(R.string.action_allow) { _, _ ->
                selected += app.pkg
                adapter.notifyDataSetChanged()
            }
            .setNegativeButton(R.string.action_cancel, null)
            .show()
    }

    private fun done() {
        if (busy) return
        if (!loaded || selected == original) {
            finish()
            return
        }
        val chosen = selected.toSet()
        setBusy(true)
        val ctx = applicationContext
        Work.run(this, { SettingsEdit.request(ctx) { base -> base.copy(allowed = chosen) } }) { result ->
            setBusy(false)
            val saved = result.getOrNull()
            val change = saved?.change
            val pending = change?.pending
            val state = saved?.after?.state
            when {
                change == null -> AlertDialog.Builder(this)
                    .setMessage(R.string.save_failed)
                    .setPositiveButton(R.string.action_ok, null)
                    .show()
                state != null && state.armed && pending != null &&
                    (pending.allowed - change.active.allowed).isNotEmpty() -> AlertDialog.Builder(this)
                    .setMessage(getString(R.string.allowed_saved_pending, Texts.dateTime(this, state.period.end)))
                    .setPositiveButton(R.string.action_ok) { _, _ -> finish() }
                    .setOnCancelListener { finish() }
                    .show()
                else -> {
                    Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show()
                    finish()
                }
            }
        }
    }

    private fun setBusy(value: Boolean) {
        busy = value
        btnDone.isEnabled = !value && loaded
        input.isEnabled = !value
    }

    private companion object {
        const val KEY_SELECTED = "selected"
    }
}
