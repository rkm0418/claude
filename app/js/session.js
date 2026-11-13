/* 질문 세션: 문제 올림 → 궁금한 점 묻기(자동 풀이 없음) → 끝내기 */
import { $, blobToDataUrl } from "./util.js";
import { fillRich } from "./rich.js";
import { callClaude, imageBlock, parseFirst, cleanReply, ApiError } from "./claude.js";
import { resetDrawer } from "./drawer.js";
import { makeFigures } from "./figures.js";
import { saveNote } from "./notes.js";
import { CATS, ORDER, levelDots } from "./cats.js";
import { createPicker } from "./picker.js";
import { openSettings } from "./settings.js";

let S = null;      // 지금 세션: {problem, qa, transcript, figs, noteId}
let ctl = null;    // 진행 중인 요청 취소용
let endTimer = null;

const asking = () => !!S;
const setAskMode = on => { document.body.classList.toggle("ask-mode", on); $("compose").inert = on; $("dock").inert = !on };

/* ── 화면 부품 ── */
function addMsg(cls, t) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  if (cls === "a") fillRich(d, t); else d.textContent = t;
  const m = $("msgs"); m.appendChild(d); m.scrollTop = m.scrollHeight;
  return d;
}

/** 저장 선택기: 위아래로 쓸어서 고르면 바로 오답노트에 저장(바꾸면 분류만 바뀜).
    빨간 동그라미 1~4개: 얻은 것 있음 → 이해 안 됨 → 개념 몰라서 → 어려워서 */
let saveTimer = null;
function makeSaveBar() {
  const bar = $("saveBar"); bar.textContent = "";
  const pk = createPicker({
    render: levelDots, label: "오답노트 분류 (위아래로 쓸어서 선택)",
    onChange: lv => { clearTimeout(saveTimer); const mine = S; saveTimer = setTimeout(() => { if (S === mine) persist(ORDER[lv - 1]) }, 350) },
  });
  bar.appendChild(pk.el);
}

async function persist(cat) {
  S.noteId ||= "n" + Date.now();
  await saveNote({ id: S.noteId, t: S.t, cat, text: S.problem.blob ? "" : (S.qa[0]?.q || ""), tr: S.transcript, img: S.problem.blob ? await blobToDataUrl(S.problem.blob) : "", qa: S.qa, figs: S.figs });
}

/* ── 시작 / 끝 ── */
export function startSession(problem) {
  S = { problem, qa: [], transcript: "", figs: [], noteId: null, t: Date.now() };
  $("msgs").textContent = ""; $("saveBar").classList.add("hide"); makeSaveBar();
  resetEndButton();
  setAskMode(true);
  setTimeout(() => $("askText").focus(), 400);
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
      if (S.problem.blob && o.problem) S.transcript = String(o.problem);
      S.figs = S.problem.blob ? makeFigures(o.figures, S.problem.src, S.problem.rect, S.problem.rmColor) : [];
    }
    reply = cleanReply(reply);
    S.qa.push({ q, a: reply });
    wait.remove(); addMsg("a", reply);
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
