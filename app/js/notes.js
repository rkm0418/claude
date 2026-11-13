/* 오답노트: 4분류 저장, 목록, 그림 지우개 */
import { $, showDialog, closeDialog, loadImage } from "./util.js";
import { notes } from "./db.js";
import { fillRich } from "./rich.js";
import { exportPdf } from "./pdf.js";
import { CATS } from "./cats.js";
import { swipeSelect } from "./picker.js";
import { categoryBar } from "./catbar.js";


let curCat = 1; // 처음엔 "얻은 것 있음"
let catbar = null;
export const currentCat = () => curCat;

/** 문제 글 + 그림 + 질문/답을 저장 (원본 사진은 목록에서만 보임). 같은 id면 분류만 바뀜 */
export async function saveNote(n) {
  await notes.put({ id: n.id, t: n.t, cat: n.cat, text: n.text, tr: n.tr, img: n.img, qa: n.qa.map(x => ({ q: x.q, a: x.a })), figs: n.figs.slice(), figs0: n.figs.slice() });
}

/* ── 그림 지우개 ── */
let figEdit = null;
const fcv = () => $("figCv");

async function openFigEdit(note, i) {
  figEdit = { note, i };
  const im = await loadImage(note.figs[i]), c = fcv();
  c.width = im.width; c.height = im.height; c.getContext("2d").drawImage(im, 0, 0);
  showDialog($("figDlg"));
}

function initFigEditor() {
  const c = fcv(); let last = null;
  const pos = e => { const b = c.getBoundingClientRect(); return { x: (e.clientX - b.left) * c.width / b.width, y: (e.clientY - b.top) * c.height / b.height } };
  const line = (a, b) => {
    const g = c.getContext("2d");
    g.strokeStyle = "#fff"; g.lineCap = g.lineJoin = "round"; g.lineWidth = +$("brush").value * c.width / 320;
    g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
  };
  c.onpointerdown = e => { c.setPointerCapture(e.pointerId); last = pos(e); line(last, last) };
  c.onpointermove = e => { if (!last) return; const p = pos(e); line(last, p); last = p };
  c.onpointerup = c.onpointercancel = () => { last = null };
  $("figReset").onclick = async () => { if (figEdit) fcv().getContext("2d").drawImage(await loadImage(figEdit.note.figs0[figEdit.i]), 0, 0) };
  $("figCancel").onclick = () => closeDialog($("figDlg"));
  $("figDone").onclick = async () => {
    if (!figEdit) return;
    figEdit.note.figs[figEdit.i] = fcv().toDataURL("image/jpeg", .88);
    await notes.put(figEdit.note);
    closeDialog($("figDlg")); renderNotes();
  };
}

/* ── 목록 ── */
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e };

/** 수정 화면: 문제 글, 질문, 답을 고치거나 지울 수 있음 (비우면 그 부분이 빠짐) */
function editCard(n, c) {
  c.textContent = "";
  const ta = (value, rows) => { const t = el("textarea", "ed"); t.value = value; t.rows = rows; t.addEventListener("input", () => { t.style.height = "auto"; t.style.height = t.scrollHeight + "px" }); return t };
  const body = ta(n.tr || n.text || "", 3), qas = (n.qa || []).map(x => ({ q: ta(x.q, 1), a: ta(x.a, 6) }));
  c.append(el("div", "note", "문제"), body);
  qas.forEach(x => c.append(el("div", "note", "질문"), x.q, el("div", "note", "답 ([제목] 줄로 칸이 나뉘어요)"), x.a));
  const row = el("div", "row end mt"), cancel = el("button", "btn", "취소"), ok = el("button", "btn pri", "저장");
  cancel.type = ok.type = "button"; cancel.onclick = () => renderNotes();
  ok.onclick = async () => {
    if (n.tr) n.tr = body.value.trim(); else n.text = body.value.trim();
    n.qa = qas.map(x => ({ q: x.q.value.trim(), a: x.a.value.trim() })).filter(x => x.q || x.a);
    await notes.put(n); renderNotes();
  };
  row.append(cancel, ok); c.appendChild(row);
  c.querySelectorAll("textarea").forEach(t => { t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 360) + "px" });
}

function card(n) {
  const c = el("div", "nc"), top = el("div", "top", new Date(n.t).toLocaleDateString("ko-KR", { month: "long", day: "numeric" }));
  const del = el("button", "x", "×"); del.type = "button"; del.setAttribute("aria-label", "삭제");
  del.onclick = async () => { await notes.del(n.id); renderNotes() };
  const edit = el("button", "x", ""); edit.type = "button"; edit.setAttribute("aria-label", "수정");
  edit.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9a2.1 2.1 0 0 0-3-3L5 17z"/><path d="M14.5 7.5l3 3"/></svg>';
  edit.onclick = () => editCard(n, c);
  const acts = el("span", "acts"); acts.append(edit, del); top.appendChild(acts); c.appendChild(top);
  const pt = el("div", "pt"); fillRich(pt, n.tr || n.text || (n.img ? "(사진 문제)" : "")); c.appendChild(pt);

  const dt = el("details"); dt.appendChild(el("summary", null, "자세히"));
  if (n.figs?.length) {
    const fw = el("div", "figs");
    n.figs.forEach((f, i) => {
      const w = el("span"), im = new Image(); im.alt = "문제 그림"; im.src = f; w.appendChild(im);
      const eb = el("button", "lk", "지우개"); eb.type = "button"; eb.onclick = () => openFigEdit(n, i); w.appendChild(eb);
      fw.appendChild(w);
    });
    dt.appendChild(fw);
  }
  (n.qa || []).forEach(x => { dt.appendChild(el("div", "q", "Q. " + x.q)); const a = el("div"); fillRich(a, x.a, { pager: true }); dt.appendChild(a) });
  if (n.img) {
    const od = el("div", "note orig", "원본 사진 (PDF에는 안 들어가요)"), im = new Image(); im.alt = "원본 사진"; im.src = n.img; od.appendChild(im); dt.appendChild(od);
  }
  c.appendChild(dt);
  return c;
}

async function renderNotes() {
  const all = (await notes.all()).sort((a, b) => b.t - a.t);
  const cnt = {}; all.forEach(x => { cnt[x.cat] = (cnt[x.cat] || 0) + 1 }); catbar.setCounts(cnt);
  const list = $("noteList"), mine = all.filter(x => x.cat === curCat);
  list.textContent = "";
  if (!mine.length) list.appendChild(el("div", "note", "저장된 문제가 없어요."));
  else mine.forEach(n => list.appendChild(card(n)));
}

export function initNotes() {
  initFigEditor();
  // 분류 선택: 아이콘 아래 이름이 있는 버튼 (눌러서 선택)
  catbar = categoryBar({ value: curCat, showCount: true, onChange: cat => { curCat = cat; renderNotes() } });
  $("noteTabs").replaceChildren(catbar.el);
  swipeSelect($("pdfScope"), "PDF 범위 (위아래로 쓸어서 선택)");
  $("btnNote").onclick = async () => { $("pdfMsg").textContent = ""; await renderNotes(); showDialog($("noteDlg")) };
  $("noteClose").onclick = () => closeDialog($("noteDlg"));
  const run = mode => exportPdf(mode, { scope: $("pdfScope").value, cat: curCat, setMsg: t => { $("pdfMsg").textContent = t }, busy: b => { $("pdfExam").disabled = $("pdfNote").disabled = $("pdfVar").disabled = b } });
  $("pdfExam").onclick = () => run("exam");
  $("pdfNote").onclick = () => run("note");
  $("pdfVar").onclick = () => run("variant");
}
