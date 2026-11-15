/* 답변 글을 끌어서 고르면 뜨는 도구: 메모에 넣기 · 형광펜 · 형광펜 지우기.
   글을 그리는 쪽(fillRich)이 root.__ctx = { getHl, setHl, addMemo }를 달아 둔 곳에서만 동작 */
let bar = null, timer = null, cur = null; // cur: 지금 선택 {root, ctx, range}

const rootOf = n => (n && (n.nodeType === 1 ? n : n.parentElement))?.closest?.(".rich-root");
const uid = () => "h" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

/** 고른 글을 메모용 글로: 수식은 LaTeX($...$), 줄 끝은 줄바꿈, 공식 번호 칩은 뺌 */
function selectionText(range) {
  const f = range.cloneContents();
  f.querySelectorAll("[data-tex]").forEach(k => k.replaceWith(document.createTextNode(k.dataset.d ? "$$" + k.dataset.tex + "$$" : "$" + k.dataset.tex + "$")));
  f.querySelectorAll(".katex").forEach(k => {
    const a = k.querySelector('annotation[encoding="application/x-tex"]'), tex = a ? a.textContent : k.textContent;
    k.replaceWith(document.createTextNode(k.closest(".katex-display") ? "$$" + tex + "$$" : "$" + tex + "$"));
  });
  f.querySelectorAll(".fchip").forEach(c => c.remove());
  f.querySelectorAll(".tag-out").forEach(t => t.replaceWith(document.createTextNode("[교과 외]")));
  f.querySelectorAll(".ln").forEach(l => l.append("\n"));
  return f.textContent.replace(/[ \t]+\n/g, "\n").replace(/\n{2,}/g, "\n").trim();
}

/** line 안에서 node의 offset 앞에 같은 글(t)이 몇 번 나왔는지 (다시 칠할 때 같은 곳을 찾으려고) */
function occurrenceBefore(line, node, offset, t) {
  const w = document.createTreeWalker(line, NodeFilter.SHOW_TEXT, { acceptNode: n => n.parentElement.closest(".katex") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
  let k = 0;
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const s = n === node ? n.data.slice(0, offset + t.length - 1) : n.data;
    for (let i = s.indexOf(t); i >= 0 && !(n === node && i >= offset); i = s.indexOf(t, i + 1)) k++;
    if (n === node) break;
  }
  return k;
}

function highlight() {
  const { root, ctx, range } = cur, sc = range.startContainer, added = [];
  if (sc === range.endContainer && sc.nodeType === 3 && !sc.parentElement.closest(".katex") && sc.parentElement.closest(".ln")) {
    const line = sc.parentElement.closest(".ln"), t = range.toString();
    if (t.trim()) {
      const id = uid(), k = occurrenceBefore(line, sc, range.startOffset, t), m = document.createElement("mark");
      m.className = "hl"; m.dataset.h = id; range.surroundContents(m);
      added.push({ id, l: line.dataset.lk, t, k });
    }
  } else { // 여러 줄이나 수식이 섞인 선택은 걸친 줄 전체를 칠함
    root.querySelectorAll(".ln").forEach(ln => {
      if (!range.intersectsNode(ln) || ln.classList.contains("hl-line")) return;
      const id = uid(); ln.classList.add("hl-line"); ln.dataset.h = id; added.push({ id, l: ln.dataset.lk, t: "" });
    });
  }
  if (added.length) ctx.setHl([...(ctx.getHl() || []), ...added]);
  return added.length ? "형광펜을 칠했어요" : "";
}

function clearHighlight() {
  const { root, ctx, range } = cur, ids = new Set();
  root.querySelectorAll("mark.hl, .ln.hl-line").forEach(e => { if (range.intersectsNode(e)) ids.add(e.dataset.h) });
  ids.forEach(id => root.querySelectorAll('[data-h="' + id + '"]').forEach(e => {
    if (e.tagName === "MARK") { const p = e.parentNode; e.replaceWith(...e.childNodes); p.normalize() }
    else { e.classList.remove("hl-line"); delete e.dataset.h }
  }));
  ctx.setHl((ctx.getHl() || []).filter(h => !ids.has(h.id)));
  return ids.size ? "형광펜을 지웠어요" : "";
}

function hide() { clearTimeout(timer); bar?.remove(); bar = null; cur = null }

function toast(host, rect, text) {
  host.querySelector(".sel-toast")?.remove();
  const t = document.createElement("div"); t.className = "sel-toast"; t.textContent = text;
  t.style.top = Math.max(8, rect.top - 44) + "px"; t.style.left = Math.max(8, Math.min(innerWidth - 220, rect.left)) + "px";
  host.appendChild(t); setTimeout(() => t.remove(), 1800);
}

function show(root, ctx, range) {
  const host = root.closest("dialog") || document.body; // 대화상자는 맨 위 층이라 그 안에 붙임
  const rect = range.getBoundingClientRect();
  cur = { root, ctx, range: range.cloneRange() };
  const inMark = [...root.querySelectorAll("mark.hl, .ln.hl-line")].some(e => range.intersectsNode(e));
  bar?.remove();
  bar = document.createElement("div"); bar.className = "sel-bar"; bar.setAttribute("role", "toolbar");
  const mk = (label, fn) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = label;
    b.onclick = async () => { const msg = await fn(); const r = rect; getSelection().removeAllRanges(); hide(); if (msg) toast(host, r, msg) };
    bar.appendChild(b);
  };
  mk("메모에 넣기", () => ctx.addMemo(selectionText(cur.range)));
  mk("형광펜", highlight);
  if (inMark) mk("형광펜 지우기", clearHighlight);
  for (const ev of ["pointerdown", "mousedown", "touchstart"]) bar.addEventListener(ev, e => e.preventDefault(), { passive: false });
  host.appendChild(bar);
  const bw = bar.offsetWidth, bh = bar.offsetHeight;
  let top = rect.bottom + 10; if (top + bh > innerHeight - 8) top = Math.max(8, rect.top - bh - 10);
  bar.style.top = top + "px"; bar.style.left = Math.max(8, Math.min(innerWidth - bw - 8, rect.left + rect.width / 2 - bw / 2)) + "px";
}

function update() {
  const sel = getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) { hide(); return }
  const range = sel.getRangeAt(0), root = rootOf(range.commonAncestorContainer);
  if (!root || !root.__ctx || rootOf(range.startContainer) !== root || rootOf(range.endContainer) !== root || !range.toString().trim()) { hide(); return }
  show(root, root.__ctx, range);
}

export function initSelectionTools() {
  document.addEventListener("selectionchange", () => { clearTimeout(timer); timer = setTimeout(update, 250) });
  document.addEventListener("pointerdown", e => { if (bar && !e.target.closest(".sel-bar")) { /* 선택이 풀리면 selectionchange에서 숨김 */ } });
  addEventListener("scroll", () => { if (bar) hide() }, true);
}
