/* 질문 세션: 문제 올림 → 궁금한 점 묻기(자동 풀이 없음) → 끝내기 */
import { $, blobToDataUrl } from "./util.js";
import { fillRich, joinSections, parseSections } from "./rich.js";
import { callClaude, imageBlock, parseFirst, cleanReply, ApiError } from "./claude.js";
import { resetDrawer } from "./drawer.js";
import { makeFigures } from "./figures.js";
import { saveNote } from "./notes.js";

import { categoryBar } from "./catbar.js";
import { openSettings } from "./settings.js";

let S = null;      // 지금 세션: {problem, qa, transcript, figs, noteId}
let ctl = null;    // 진행 중인 요청 취소용
let endTimer = null;

const asking = () => !!S;
const setAskMode = on => { document.body.classList.toggle("ask-mode", on); $("compose").inert = on; $("dock").inert = !on };

/* ── 화면 부품 ── */
function addMsg(cls, t, entry) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  if (cls === "a") fillRich(d, t, entry ? { pager: true, selectable: true, skip: entry.skip, onToggle: () => { if (S?.noteId) persist(S.cat) } } : { pager: true });
  else d.textContent = t;
  // 칸으로 나뉘지 않는 답(추가 질문 등)도 체크해서 담음 (처음엔 해제)
  if (cls === "a" && entry && !d.querySelector(".pager")) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "pg-pick msg-pick";
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="4"/><path d="M8 12.5l3 3 5-6"/></svg>';
    const paint = () => { const on = !entry.skip.has("전체"); b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); b.setAttribute("aria-label", on ? "오답노트에 담김 (누르면 뺌)" : "오답노트에 안 담김 (누르면 담음)") };
    b.onclick = () => { if (entry.skip.has("전체")) entry.skip.delete("전체"); else entry.skip.add("전체"); paint(); if (S?.noteId) persist(S.cat) };
    paint(); d.appendChild(b);
  }
  const m = $("msgs"); m.appendChild(d);
  // 긴 답은 처음부터 읽을 수 있게 말풍선 위쪽에 맞추고, 내 질문은 맨 아래로
  if (cls === "a") m.scrollTop += d.getBoundingClientRect().top - m.getBoundingClientRect().top - 8; else m.scrollTop = m.scrollHeight;
  return d;
}

/** 저장 선택: 빨간 동그라미 아이콘 아래에 이름을 쓴 버튼 4개 (얻음 · 애매 · 개념 · 어려움).
    누르면 바로 오답노트에 저장하고, 다른 버튼을 누르면 분류만 바뀜 */
function makeSaveBar() {
  const bar = $("saveBar"); bar.textContent = "";
  bar.appendChild(categoryBar({ onChange: cat => persist(cat) }).el);
}

/** 오답노트에는 내가 담은 칸만 저장 (칸이 없는 짧은 답은 그대로) */
async function persist(cat) {
  S.noteId ||= "n" + Date.now(); S.cat = cat;
  const qa = S.qa.map(x => {
    const sectioned = parseSections(x.a).secs.length > 0;
    return { q: x.q, a: sectioned ? joinSections(x.a, x.skip).trim() : (x.skip.has("전체") ? "" : x.a) };
  }).filter(x => x.a);
  await saveNote({ id: S.noteId, t: S.t, cat, text: S.transcript ? "" : (S.problem.blob ? "" : (S.qa[0]?.q || "")), tr: S.transcript, ans: S.ans, img: S.problem.blob ? await blobToDataUrl(S.problem.blob) : "", qa, figs: S.figs });
}

/* ── 시작 / 끝 ── */
export function startSession(problem) {
  S = { problem, qa: [], transcript: "", ans: "", figs: [], noteId: null, t: Date.now() };
  $("msgs").textContent = ""; $("saveBar").classList.add("hide"); makeSaveBar();
  resetEndButton();
  setAskMode(true);
  setTimeout(() => $("askText").focus(), 400);
  if (problem.blob) setTimeout(() => { if (S && !S.qa.length) ask(AUTO_Q) }, 450); // 사진이 있으면 바로 풀이 시작
}

function resetEndButton() {
  clearTimeout(endTimer);
  $("btnEnd").textContent = "끝내기"; $("btnEnd").classList.remove("warn");
}

/** 저장 안 한 질문이 있으면 한 번 더 눌러야 끝남 */
export function endSession(force) {
  if (!S) return;
  const btn = $("btnEnd");
  if (!force && S.qa.length && !S.noteId && !btn.classList.contains("warn")) {
    btn.textContent = "저장 안 하고 끝내기"; btn.classList.add("warn");
    clearTimeout(endTimer); endTimer = setTimeout(resetEndButton, 4000);
    return;
  }
  ctl?.abort(); ctl = null;
  resetEndButton(); S = null;
  resetDrawer(); $("msgs").textContent = ""; $("saveBar").classList.add("hide");
  setAskMode(false);
}

/* ── 질문 ── */
/** 지금까지의 대화를 API 메시지로. 사진은 전사 전(=첫 질문)에만 보냄 */
async function buildMessages(newQ) {
  const { problem, transcript, qa } = S;
  const head = `[문제]\n${problem.blob ? "(사진 참고)" : "(질문에 함께 적음)"}${transcript ? "\n\n[문제 전사]\n" + transcript : ""}\n\n[질문]\n`;
  const useImg = !!problem.blob && !transcript;
  const first = qa.length ? qa[0].q : newQ;
  const content = [];
  if (useImg) content.push(await imageBlock(problem.blob));
  content.push({ type: "text", text: head + first });
  const msgs = [{ role: "user", content }];
  qa.forEach((x, i) => { msgs.push({ role: "assistant", content: x.a }); if (qa[i + 1]) msgs.push({ role: "user", content: qa[i + 1].q }) });
  if (qa.length) msgs.push({ role: "user", content: newQ });
  return msgs;
}

const AUTO_Q = "이 문제를 풀어 주세요.";

async function ask(q) {
  const isFirst = S.qa.length === 0;
  addMsg("u", q);
  const wait = addMsg("a", "…");
  $("askSend").disabled = true;
  const mine = S;
  try {
    ctl = new AbortController();
    const text = await callClaude(await buildMessages(q), ctl.signal);
    if (S !== mine) return;
    let reply = text;
    if (isFirst) {
      const o = parseFirst(text); reply = o.reply;
      if (o.answer) S.ans = String(o.answer);
      if (o.problem) S.transcript = String(o.problem); // 사진이 없어도 글에서 문제 부분만 따로 저장
      S.figs = S.problem.blob ? makeFigures(o.figures, S.problem.src, S.problem.rect, S.problem.rmColor) : [];
    }
    reply = cleanReply(reply);
    // 처음에는 모든 칸이 선택 해제 상태: 오답노트에 넣을 칸만 체크해서 담음
    const ps = parseSections(reply), skip = new Set(ps.secs.length ? [...(ps.pre ? ["요약"] : []), ...ps.secs.map(s => s.h)] : ["전체"]);
    const entry = { q, a: reply, skip }; S.qa.push(entry);
    if (S.noteId) persist(S.cat); // 이미 저장한 문제면 새 답도 같이 저장
    wait.remove(); addMsg("a", reply, entry);
    $("saveBar").classList.remove("hide");
  } catch (e) {
    if (S !== mine || e.name === "AbortError") return;
    wait.remove(); addMsg("err", e.message || "문제가 생겼어요.");
    if (e instanceof ApiError && e.code === "no_key") openSettings();
  } finally {
    if (S === mine) { $("askSend").disabled = false; $("askText").focus() }
  }
}

export function initSession() {
  $("btnEnd").onclick = () => endSession(false);
  $("askForm").onsubmit = e => {
    e.preventDefault();
    const q = $("askText").value.trim();
    if (!q || !asking() || $("askSend").disabled) return;
    $("askText").value = ""; ask(q);
  };
}
