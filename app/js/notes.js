/* 오답노트: 4분류 저장, 목록, 그림 지우개 */
import { $, showDialog, loadImage } from "./util.js";
import { notes } from "./db.js";
import { fillRich } from "./rich.js";
import { exportPdf } from "./pdf.js";
import { CATS, ORDER, dotsEl } from "./cats.js";


let curCat = 1; // 처음엔 "얻은 것 있음"
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
  $("figCancel").onclick = () => $("figDlg").close();
  $("figDone").onclick = async () => {
    if (!figEdit) return;
    figEdit.note.figs[figEdit.i] = fcv().toDataURL("image/jpeg", .88);
    await notes.put(figEdit.note);
    $("figDlg").close(); renderNotes();
  };
}

/* ── 목록 ── */
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e };

function card(n) {
  const c = el("div", "nc"), top = el("div", "top", new Date(n.t).toLocaleDateString("ko-KR", { month: "long", day: "numeric" }));
  const del = el("button", "x", "×"); del.type = "button"; del.setAttribute("aria-label", "삭제");
  del.onclick = async () => { await notes.del(n.id); renderNotes() };
  top.appendChild(del); c.appendChild(top);
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
  (n.qa || []).forEach(x => { dt.appendChild(el("div", "q", "Q. " + x.q)); const a = el("div"); fillRich(a, x.a); dt.appendChild(a) });
  if (n.img) {
    const od = el("div", "note orig", "원본 사진 (PDF에는 안 들어가요)"), im = new Image(); im.alt = "원본 사진"; im.src = n.img; od.appendChild(im); dt.appendChild(od);
  }
  c.appendChild(dt);
  return c;
}

async function renderNotes() {
  const all = (await notes.all()).sort((a, b) => b.t - a.t), tabs = $("noteTabs");
  tabs.textContent = "";
  ORDER.forEach(i => {
    const b = el("button", i === curCat ? "on" : ""); b.type = "button"; b.title = CATS[i]; b.setAttribute("aria-label", CATS[i]);
    b.append(dotsEl(i), el("span", "cnt", all.filter(x => x.cat === i).length));
    b.onclick = () => { curCat = i; renderNotes() };
    tabs.appendChild(b);
  });
  const list = $("noteList"), mine = all.filter(x => x.cat === curCat);
  list.textContent = "";
  if (!mine.length) list.appendChild(el("div", "note", "저장된 문제가 없어요."));
  else mine.forEach(n => list.appendChild(card(n)));
}

export function initNotes() {
  initFigEditor();
  $("btnNote").onclick = async () => { $("pdfMsg").textContent = ""; await renderNotes(); showDialog($("noteDlg")) };
  $("noteClose").onclick = () => $("noteDlg").close();
  const run = mode => exportPdf(mode, { scope: $("pdfScope").value, cat: curCat, setMsg: t => { $("pdfMsg").textContent = t }, busy: b => { $("pdfExam").disabled = $("pdfNote").disabled = b } });
  $("pdfExam").onclick = () => run("exam");
  $("pdfNote").onclick = () => run("note");
}
