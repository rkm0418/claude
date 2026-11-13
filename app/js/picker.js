/* 위아래로 쓸어서 고르는 선택기 (터치 스와이프, 마우스 드래그·휠, 방향키).
   위로 쓸면 단계가 올라가고 아래로 쓸면 내려감. 값은 0(선택 안 함) 또는 1~levels */
const CHEV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 15l6-6 6 6"/></svg>';
const STEP = 26; // 한 단계로 치는 이동 거리(px)

export function createPicker({ levels = 4, value = 0, render, showCount = false, onChange, label = "", className = "" }) {
  const el = document.createElement("div");
  el.className = "picker " + className; el.tabIndex = 0; el.setAttribute("role", "slider");
  el.setAttribute("aria-orientation", "vertical"); el.setAttribute("aria-label", label);
  el.setAttribute("aria-valuemin", "1"); el.setAttribute("aria-valuemax", String(levels));
  el.innerHTML = CHEV + '<div class="pk-face"></div>' + (showCount ? '<div class="pk-count">0</div>' : "") + CHEV.replace("M6 15l6-6 6 6", "M6 9l6 6 6-6");
  const face = el.querySelector(".pk-face"), cnt = el.querySelector(".pk-count");
  let v = value;

  function paint(dir) {
    face.textContent = ""; face.appendChild(render(v));
    el.setAttribute("aria-valuenow", String(v));
    if (dir) { face.classList.remove("up", "down"); void face.offsetWidth; face.classList.add(dir > 0 ? "up" : "down") }
  }
  /** delta 단계만큼 이동 (처음 선택 전 아래로 쓸면 무시) */
  function move(delta) {
    const n = Math.min(levels, Math.max(v ? 1 : 1, v + delta));
    if (!v && delta < 0) return;
    if (n === v) return;
    const dir = n > v ? 1 : -1; v = n; paint(dir); onChange?.(v);
  }

  let st = null;
  el.addEventListener("pointerdown", e => { st = { id: e.pointerId, y: e.clientY }; try { el.setPointerCapture(e.pointerId) } catch {} });
  el.addEventListener("pointermove", e => {
    if (!st || e.pointerId !== st.id) return;
    const steps = Math.trunc((st.y - e.clientY) / STEP);
    if (steps) { move(steps); st.y -= steps * STEP }
  });
  const end = e => { if (st && e.pointerId === st.id) st = null };
  el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
  let acc = 0;
  el.addEventListener("wheel", e => { e.preventDefault(); acc += e.deltaY; if (Math.abs(acc) >= 40) { move(acc < 0 ? 1 : -1); acc = 0 } }, { passive: false });
  el.addEventListener("keydown", e => {
    if (e.key === "ArrowUp") { e.preventDefault(); move(1) }
    else if (e.key === "ArrowDown") { e.preventDefault(); move(-1) }
  });

  paint(0);
  return {
    el, get: () => v,
    setCount(n) { if (cnt) cnt.textContent = n },
  };
}

/** <select>를 숨기고 같은 선택지를 위아래로 쓸어서 고르는 선택기로 바꿈 (select 값은 그대로 유지·change 발생) */
export function swipeSelect(select, label = "") {
  const opts = [...select.options];
  const idx = Math.max(0, opts.findIndex(o => o.value === select.value));
  const pk = createPicker({
    levels: opts.length, value: idx + 1, label, className: "text",
    render: l => document.createTextNode(opts[l - 1].textContent),
    onChange: l => { select.value = opts[l - 1].value; select.dispatchEvent(new Event("change", { bubbles: true })) },
  });
  select.hidden = true; select.after(pk.el);
  return pk;
}
