/* PDF 내보내기
   - 모의고사: 명조체 2단 시험지, 한 단에 두 문제씩(풀이 칸 없음) + 정답 및 해설
   - 변형 모의고사: 저장한 문제를 Claude가 변형한 문제로 같은 모양의 시험지
   - 오답노트: 1단 카드 */
import { loadScript, shuffle, saveFile } from "./util.js";
import { notes } from "./db.js";
import { fillRich, parseSections, fixNl } from "./rich.js";
import { CATS, CATS_S } from "./cats.js";
import { makeVariants } from "./claude.js";

const mk = (cls, html) => { const e = document.createElement("div"); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e };
const text = (cls, t) => { const e = mk(cls); e.textContent = t; return e };
const openAll = el => { el.querySelectorAll("details").forEach(d => { d.open = true }); return el };

/** 문제 글 + 그림. 글을 못 옮겼으면 원본 사진으로 대신함 */
/** 모의고사에는 보기(①~⑤ 선택지)를 넣지 않음 */
const stripChoices = t => { const s = String(t || ""), i = s.indexOf("①"); return i >= 0 && s.indexOf("②", i) > 0 ? s.slice(0, i).trimEnd() : s };

function problemParts(n, noChoices) {
  const body = noChoices ? stripChoices(fixNl(n.tr || n.text || "")) : (n.tr || n.text || "");
  const t = mk("t"); fillRich(t, body || (n.img && !n.figs?.length ? "(문제 글을 옮기지 못해 원본 사진을 넣었어요)" : ""));
  const imgs = [];
  if (n.figs?.length) n.figs.forEach(f => { const im = new Image(); im.src = f; imgs.push(im) });
  else if (!body && n.img) { const im = new Image(); im.src = n.img; imgs.push(im) }
  return { t, imgs };
}

const strip = s => String(s || "").replace(/\(공식\d+\)/g, "").replace(/[ \t]+$/gm, "");

/** 답지용 풀이: 내가 고른(저장한) 칸의 내용만, 제목 없이 이어서 */
function keyBody(n) {
  const parts = [];
  (n.qa || []).forEach(x => {
    const { pre, secs } = parseSections(x.a);
    if (secs.length) { if (pre) parts.push(pre); secs.forEach(s => parts.push(s.body)) } else parts.push(x.a);
  });
  return strip(parts.join("\n")).trim();
}

/** 답지용 답: 저장된 답, 없으면 [풀이]의 마지막 줄 */
function keyAnswer(n) {
  if (n.ans) return strip(n.ans).trim();
  for (const x of n.qa || []) {
    const s = parseSections(x.a).secs.find(s => s.h === "풀이");
    const last = s && s.body.split("\n").map(l => l.trim()).filter(Boolean).pop();
    if (last) return strip(last).trim();
  }
  return "";
}

/** 질문과 답 (검산 구역은 fillRich가 알아서 뺌) */
function qaInto(n, box) {
  (n.qa || []).forEach(x => {
    if (x.q) box.appendChild(text("qq", "Q. " + x.q));
    const a = mk("aa"); fillRich(a, x.a); box.appendChild(openAll(a));
  });
}

export async function exportPdf(mode, { scope, cat, setMsg, busy, ids }) {
  const variant = mode === "variant", exam = mode !== "note";
  let list = await notes.all();
  list = ids ? list.filter(x => ids.has(x.id)).sort((a, b) => a.t - b.t) // 꾹 눌러 고른 문제들만
    : scope === "cat" ? list.filter(x => x.cat === cat).sort((a, b) => a.t - b.t) : shuffle(list.slice());
  if (!list.length) { setMsg("내보낼 문제가 없어요."); return }
  busy(true); setMsg(variant ? "변형 문제를 만드는 중…" : "만드는 중…");
  const root = mk("pdf-root"); document.body.appendChild(root);
  try {
    let items = list;
    if (variant) { // 글로 옮겨진 문제만 변형 (그림이 필요한 문제는 글로 조건을 풀어 쓴 변형)
      const withText = list.filter(n => (n.tr || n.text || "").trim());
      if (!withText.length) { setMsg("글로 옮겨진 문제가 없어요. 문제를 질문해서 저장하면 변형할 수 있어요."); return }
      const vs = await makeVariants(withText.map(n => n.tr || n.text));
      items = withText.map((n, i) => vs[i] && { tr: vs[i].problem, figs: [], qa: [], answer: vs[i].answer, solution: vs[i].solution }).filter(Boolean);
      if (!items.length) { setMsg("변형 문제를 만들지 못했어요. 다시 시도해 주세요."); return }
      setMsg("만드는 중…");
    }
    await Promise.all([loadScript("vendor/jspdf.umd.min.js"), loadScript("vendor/html2canvas.min.js")]);
    await document.fonts.ready;
    if (exam) await Promise.all([document.fonts.load('15px "Myeongjo"'), document.fonts.load('700 15px "Myeongjo"')]);
    const label = ids ? "선택한 문제" : scope === "cat" ? CATS[cat] : "전체 · 섞어서", today = new Date().toLocaleDateString("ko-KR");
    const title = variant ? "변형 모의고사" : exam ? "오답 모의고사" : "오답노트", pages = [];

    const newPage = (first, { single = false, slots = false } = {}) => {
      const pg = mk("pg" + (single ? " single" : "") + (exam ? " serif" : "") + (slots ? " slots" : ""));
      if (first) {
        const top = mk("top", '<div class="tag"></div><div class="mid"><div class="ttl"></div><div class="sub"></div></div>' + "");
        top.querySelector(".tag").textContent = variant ? "변형" : exam ? "모의고사" : "오답노트";
        top.querySelector(".ttl").textContent = title;
        if (exam) top.querySelector(".sub").remove(); // 모의고사는 제목만
        else top.querySelector(".sub").textContent = `${label} · 총 ${items.length}문항 · ${today}`;
        pg.append(top, mk("rule"));
      } else pg.append(text("mini", exam ? title : title + " · " + label), mk("rule thin"));
      const cols = mk("cols"), c1 = mk("col"), c2 = mk("col");
      cols.append(c1, c2); pg.appendChild(cols);
      pg.appendChild(mk("foot", `<span>${title}</span><span class="pn"></span>`));
      root.appendChild(pg); pages.push(pg);
      return [c1, c2];
    };
    const decoded = el => Promise.all([...el.querySelectorAll("img")].map(i => i.decode().catch(() => {})));
    const over = c => c.scrollHeight > c.clientHeight + 1;

    let single = !exam, cols, ci = 0, slot = 0;
    /* 해설·카드: 쪽이 넘치면 다음 단 또는 다음 쪽으로 */
    const add = async el => {
      cols[ci].appendChild(el); await decoded(el);
      if (over(cols[ci]) && cols[ci].children.length > 1) {
        cols[ci].removeChild(el);
        if (ci === 0 && !single) { ci = 1; cols[1].appendChild(el) }
        else { cols = newPage(false, { single }); ci = 0; cols[0].appendChild(el) }
      }
    };
    /* 문제: 한 단에 두 문제씩. 넘치면 글자를 줄여 맞추고, 그래도 안 되면 한 단을 다 씀 */
    const advance = () => { slot = 0; if (ci === 0) ci = 1; else { cols = newPage(false, { slots: true }); ci = 0 } };
    const fit = async q => { for (const s of [1, .94, .88, .82, .76]) { q.style.fontSize = (15 * s) + "px"; if (q.scrollHeight <= q.clientHeight + 1) return true } return false };
    const place = async q => {
      if (slot >= 2) advance();
      cols[ci].appendChild(q); await decoded(q);
      if (await fit(q)) { slot++; return }
      if (slot === 1) { cols[ci].removeChild(q); advance(); cols[ci].appendChild(q) }
      q.style.flex = "0 0 100%"; q.style.height = "100%"; await fit(q); slot = 2;
    };

    if (exam) {
      cols = newPage(true, { slots: true });
      for (let i = 0; i < items.length; i++) {
        const q = mk("q"), qh = mk("qh"), { t, imgs } = problemParts(items[i], true);
        qh.append(text("n", (i + 1) + "."), t); q.appendChild(qh);
        imgs.forEach(im => q.appendChild(im));
        await place(q);
      }
      cols = newPage(false); ci = 0; // 정답 및 해설은 새 쪽에서
      await add(mk(null, "<h3>정답 및 해설</h3>"));
      for (let i = 0; i < items.length; i++) { // 답지: 답 / 풀이만
        const it = items[i], e = mk("ex"), hd = mk("ak"), nb = document.createElement("b"), av = document.createElement("span");
        const ans = variant ? it.answer : keyAnswer(it), sol = variant ? it.solution : keyBody(it);
        nb.textContent = (i + 1) + ". 답 "; fillRich(av, ans || "-"); hd.append(nb, av); e.appendChild(hd);
        if (sol) { const body = mk("aa"); fillRich(body, sol); e.append(text("sl", "풀이"), openAll(body)) }
        await add(e);
      }
    } else {
      cols = newPage(true, { single });
      for (let i = 0; i < items.length; i++) {
        const n = items[i], e = mk("card"), nh = mk("nh", '<span class="chip"></span><span></span><b></b>');
        nh.children[0].textContent = CATS_S[n.cat]; nh.children[1].textContent = new Date(n.t).toLocaleDateString("ko-KR"); nh.children[2].textContent = "No. " + (i + 1);
        const { t, imgs } = problemParts(n); t.className = "pt";
        e.append(nh, t); imgs.forEach(im => e.appendChild(im));
        qaInto(n, e); e.appendChild(text("memo", "내 메모"));
        await add(e);
      }
    }

    pages.forEach((pg, i) => { pg.querySelector(".pn").textContent = `${i + 1} / ${pages.length}` });
    const pdf = new window.jspdf.jsPDF({ unit: "mm", format: "a4", orientation: "p" });
    for (let i = 0; i < pages.length; i++) {
      setMsg(`만드는 중 (${i + 1}/${pages.length})…`);
      const cv = await window.html2canvas(pages[i], { scale: 2, backgroundColor: "#ffffff", useCORS: true, logging: false });
      if (i) pdf.addPage();
      pdf.addImage(cv.toDataURL("image/jpeg", .88), "JPEG", 0, 0, 210, 297);
    }
    const kind = variant ? "변형모의고사_" : exam ? "오답모의고사_" : "오답노트_";
    await saveFile(kind + (ids ? "선택" : scope === "cat" ? CATS_S[cat].replace(/\s+/g, "") : "전체") + "_" + new Date().toISOString().slice(0, 10) + ".pdf", pdf.output("blob"));
    setMsg("PDF를 만들었어요.");
  } catch (e) {
    setMsg("PDF를 만들지 못했어요: " + (e.message || e));
  } finally {
    root.remove(); busy(false);
  }
}
