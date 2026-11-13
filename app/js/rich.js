/* 글 속 수식($...$, $$...$$)을 KaTeX로 그리기 */
function tokenize(t) {
  t = String(t || "").replace(/\\\[([\s\S]+?)\\\]/g, "$$$$$1$$$$").replace(/\\\(([\s\S]+?)\\\)/g, "$$$1$$");
  const out = [], re = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;
  let last = 0, m;
  while ((m = re.exec(t))) {
    if (m.index > last) out.push({ v: t.slice(last, m.index) });
    out.push({ m: (m[1] ?? m[2]).trim(), d: m[1] !== undefined });
    last = re.lastIndex;
  }
  if (last < t.length) out.push({ v: t.slice(last) });
  return out;
}

function mathNode(tk) {
  const sp = document.createElement("span");
  try {
    sp.innerHTML = window.katex.renderToString(tk.m, { displayMode: tk.d, throwOnError: false, output: "html" });
  } catch {
    sp.textContent = (tk.d ? "$$" : "$") + tk.m + (tk.d ? "$$" : "$");
  }
  if (tk.d) { sp.style.display = "block"; sp.style.textAlign = "center" }
  return sp;
}

/** 글 조각 안의 (공식N)은 번호 칩으로, [교과 외]는 작은 표시로 */
const MARK = /\(공식(\d+)\)|\[교과 외\]/g;
function addText(el, v) {
  let last = 0, m;
  MARK.lastIndex = 0;
  while ((m = MARK.exec(v))) {
    if (m.index > last) el.append(v.slice(last, m.index));
    if (m[1]) {
      const b = document.createElement("button");
      b.type = "button"; b.className = "fchip"; b.dataset.f = m[1]; b.textContent = m[1];
      b.title = "공식 " + m[1] + " 사용한 곳 보기"; b.setAttribute("aria-label", "공식 " + m[1] + " 사용한 곳 보기");
      el.appendChild(b);
    } else {
      const t = document.createElement("span"); t.className = "tag-out"; t.textContent = "교과 외"; el.appendChild(t);
    }
    last = MARK.lastIndex;
  }
  if (last < v.length) el.append(v.slice(last));
}

function addTokens(el, text) {
  tokenize(text).forEach(tk => { if (tk.m !== undefined) el.appendChild(mathNode(tk)); else addText(el, tk.v) });
}

/** 공식 표시가 있는 글은 줄 단위로 나눠서 "사용한 곳"을 줄 전체로 강조할 수 있게 함 (1775 수식이 여러 줄이면 한 줄로 묶음) */
function addBody(el, text, force) {
  if (!force && !/\(공식\d+\)/.test(text)) { addTokens(el, text); return }
  const lines = []; let buf = "";
  for (const ln of String(text).split("\n")) {
    buf = buf ? buf + "\n" + ln : ln;
    if ((buf.match(/\$\$/g) || []).length % 2 === 0) { if (buf.trim()) lines.push(buf); buf = "" }
  }
  if (buf.trim()) lines.push(buf);
  for (const l of lines) { const d = document.createElement("div"); d.className = "ln"; addTokens(d, l); el.appendChild(d) }
}

const CHEV_L = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>';
const CHEV_R = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';

/** 구역을 칸(카드)으로 나눠 한 칸씩 보여줌: 위쪽 제목 칩으로 이동, 아래 화살표나 좌우로 밀어서 이동 */
function buildPager(el, secs) {
  const root = document.createElement("div"); root.className = "pager";
  const tabs = document.createElement("div"); tabs.className = "pg-tabs"; tabs.setAttribute("role", "tablist");
  const stage = document.createElement("div"); stage.className = "pg-stage";
  const nav = document.createElement("div"); nav.className = "pg-nav";
  const prev = document.createElement("button"), next = document.createElement("button"), count = document.createElement("span");
  prev.type = next.type = "button"; prev.className = next.className = "pg-btn";
  prev.setAttribute("aria-label", "이전 칸"); next.setAttribute("aria-label", "다음 칸");
  prev.innerHTML = CHEV_L; next.innerHTML = CHEV_R; count.className = "pg-count";
  nav.append(prev, count, next);
  const tabEls = [], cards = [];
  let cur = 0;
  function show(i, focus) {
    cur = Math.max(0, Math.min(secs.length - 1, i));
    cards.forEach((c, k) => { c.hidden = k !== cur; tabEls[k].classList.toggle("on", k === cur); tabEls[k].setAttribute("aria-selected", k === cur) });
    prev.disabled = cur === 0; next.disabled = cur === secs.length - 1;
    count.textContent = (cur + 1) + " / " + secs.length;
    if (focus !== false) tabEls[cur].scrollIntoView?.({ inline: "center", block: "nearest" });
  }
  secs.forEach((s, i) => {
    const t = document.createElement("button");
    t.type = "button"; t.className = "pg-tab"; t.textContent = s.h; t.setAttribute("role", "tab");
    t.onclick = () => show(i);
    tabs.appendChild(t); tabEls.push(t);
    const c = document.createElement("div"); c.className = "pg-card"; addBody(c, s.body, true);
    stage.appendChild(c); cards.push(c);
  });
  // 좌우로 밀어서 이동
  let sx = null, sy = 0;
  stage.addEventListener("pointerdown", e => { if (e.target.closest("button")) return; sx = e.clientX; sy = e.clientY });
  stage.addEventListener("pointerup", e => {
    if (sx === null) return;
    const dx = e.clientX - sx, dy = e.clientY - sy; sx = null;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) show(cur + (dx < 0 ? 1 : -1));
  });
  stage.addEventListener("pointercancel", () => { sx = null });
  prev.onclick = () => show(cur - 1); next.onclick = () => show(cur + 1);
  root.append(tabs, stage, nav);
  root.__go = show; root.__cards = cards; root.__tabs = tabEls; root.__cur = () => cur;
  el.appendChild(root);
  show(0, false);
}

const SECTION = /^\[(사용된 개념|조건 해석|풀이 방향|풀이|빠른 풀이|검산|자주 하는 실수|한 줄 정리)\][ 	]*$/m;

/** 수식을 그려 넣고, [사용된 개념]·[조건 해석]·[풀이]처럼 제목만 있는 줄은 구역으로 나눠 보여줌.
    [빠른 풀이]는 접어 두고 따로 펼쳐 볼 수 있게 함 */
export function fillRich(el, text, opts = {}) {
  el.textContent = ""; el.classList.add("rich-root");
  const parts = String(text || "").split(new RegExp(SECTION.source, "gm"));
  if (parts.length < 3) { addBody(el, String(text || "")); return }
  if (opts.pager && parts.length >= 5) {
    const secs = [];
    if (parts[0].trim()) secs.push({ h: "요약", body: parts[0].trim() });
    for (let i = 1; i < parts.length; i += 2) secs.push({ h: parts[i], body: (parts[i + 1] || "").trim() });
    buildPager(el, secs); return;
  }
  if (parts[0].trim()) { const pre = document.createElement("div"); addBody(pre, parts[0].trim()); el.appendChild(pre) }
  for (let i = 1; i < parts.length; i += 2) {
    const b = document.createElement("div"); b.className = "sec-b"; addBody(b, (parts[i + 1] || "").trim());
    if (parts[i] === "빠른 풀이") {
      const d = document.createElement("details"), s = document.createElement("summary");
      d.className = "sec-fast";
      s.innerHTML = '<span class="sec-h"></span><span class="note"> 눌러서 보기 (교과 외 공식이 있을 수 있어요)</span>';
      s.firstChild.textContent = "빠른 풀이";
      d.append(s, b); el.appendChild(d);
    } else {
      const h = document.createElement("div"); h.className = "sec-h"; h.textContent = parts[i];
      el.append(h, b);
    }
  }
}

/** 공식 번호 칩을 누르면 그 공식을 쓴 줄이 모두 강조됨 (다시 누르면 해제). 접힌 빠른 풀이도 펼침 */
export function initChips() {
  document.addEventListener("click", e => {
    const c = e.target.closest?.(".fchip");
    if (!c) return;
    const scope = c.closest(".rich-root") || document, on = !c.classList.contains("on");
    scope.querySelectorAll('.fchip[data-f="' + c.dataset.f + '"]').forEach(x => {
      x.classList.toggle("on", on);
      x.closest(".ln")?.classList.toggle("hl", on);
      if (on) x.closest("details")?.setAttribute("open", "");
    });
    // 칸으로 나뉜 답: 강조된 줄이 있는 칸의 제목에 점을 찍고, 켰을 때 다른 칸의 첫 사용처로 이동
    scope.querySelectorAll(".pager").forEach(pg => {
      pg.__cards.forEach((card, k) => pg.__tabs[k].classList.toggle("has-hl", !!card.querySelector(".ln.hl")));
      if (on) { // 켜면 이 공식을 쓴 다른 칸으로 이동 (현재 칸 뒤쪽 우선)
        const here = pg.__cur(), n = pg.__cards.length, sel = '.ln.hl .fchip[data-f="' + c.dataset.f + '"]';
        for (let k = 1; k < n; k++) { const i = (here + k) % n; if (pg.__cards[i].querySelector(sel)) { pg.__go(i); break } }
      }
    });
  });
}
