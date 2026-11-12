/* PDF 내보내기: 모의고사(2단 시험지 + 질문·해설 쪽) / 오답노트(1단 카드) */
import { loadScript, shuffle } from "./util.js";
import { notes } from "./db.js";
import { fillRich } from "./rich.js";
import { CATS, CATS_S } from "./cats.js";

const mk = (cls, html) => { const e = document.createElement("div"); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e };
const text = (cls, t) => { const e = mk(cls); e.textContent = t; return e };

/** 문제 글 + 그림. 글을 못 옮겼으면 원본 사진으로 대신함 */
function problemParts(n) {
  const body = n.tr || n.text || "", parts = [];
  const t = mk("t"); fillRich(t, body || (n.img && !n.figs?.length ? "(문제 글을 옮기지 못해 원본 사진을 넣었어요)" : ""));
  const imgs = [];
  if (n.figs?.length) n.figs.forEach(f => { const im = new Image(); im.src = f; imgs.push(im) });
  else if (!body && n.img) { const im = new Image(); im.src = n.img; imgs.push(im) }
  return { t, imgs };
}

function qaInto(n, box) {
  (n.qa || []).forEach(x => { box.appendChild(text("qq", "Q. " + x.q)); const a = mk("aa"); fillRich(a, x.a); box.appendChild(a) });
}

export async function exportPdf(mode, { scope, cat, setMsg, busy }) {
  const exam = mode === "exam";
  let list = await notes.all();
  list = scope === "cat" ? list.filter(x => x.cat === cat).sort((a, b) => a.t - b.t) : shuffle(list.slice());
  if (!list.length) { setMsg("내보낼 문제가 없어요."); return }
  busy(true); setMsg("만드는 중…");
  const root = mk("pdf-root"); document.body.appendChild(root);
  try {
    await Promise.all([loadScript("vendor/jspdf.umd.min.js"), loadScript("vendor/html2canvas.min.js")]);
    await document.fonts.ready;
    const label = scope === "cat" ? CATS[cat] : "전체 · 섞어서", today = new Date().toLocaleDateString("ko-KR");
    const title = exam ? "오답 모의고사" : "오답노트", pages = [];

    const newPage = (first, single) => {
      const pg = mk("pg" + (single ? " single" : ""));
      if (first) {
        const top = mk("top", '<div class="tag"></div><div class="mid"><div class="ttl"></div><div class="sub"></div></div>' + (exam ? '<div class="who"><div>성명 <u></u></div><div>수험번호 <u></u></div></div>' : ""));
        top.querySelector(".tag").textContent = exam ? "모의고사" : "오답노트";
        top.querySelector(".ttl").textContent = title;
        top.querySelector(".sub").textContent = `${label} · 총 ${list.length}문항 · ${today}`;
        pg.append(top, mk("rule"));
      } else pg.append(text("mini", title + " · " + label), mk("rule thin"));
      const cols = mk("cols"), c1 = mk("col"), c2 = mk("col");
      cols.append(c1, c2); pg.appendChild(cols);
      pg.appendChild(mk("foot", `<span>${title}</span><span class="pn"></span>`));
      root.appendChild(pg); pages.push(pg);
      return [c1, c2];
    };

    // 쪽이 넘치면 다음 칸(단) 또는 다음 쪽으로
    let single = !exam, cols = newPage(true, single), ci = 0;
    const over = c => c.scrollHeight > c.clientHeight + 1;
    const add = async el => {
      cols[ci].appendChild(el);
      await Promise.all([...el.querySelectorAll("img")].map(i => i.decode().catch(() => {})));
      if (over(cols[ci]) && cols[ci].children.length > 1) {
        cols[ci].removeChild(el);
        if (ci === 0 && !single) { ci = 1; cols[1].appendChild(el) }
        else { cols = newPage(false, single); ci = 0; cols[0].appendChild(el) }
      }
    };

    if (exam) {
      for (let i = 0; i < list.length; i++) {
        const q = mk("q"), qh = mk("qh"), { t, imgs } = problemParts(list[i]);
        qh.append(text("n", (i + 1) + "."), t); q.appendChild(qh);
        imgs.forEach(im => q.appendChild(im));
        q.appendChild(mk("sp", "<i>풀이</i>"));
        await add(q);
      }
      cols = newPage(false, false); ci = 0; // 질문·해설은 새 쪽에서
      await add(mk(null, "<h3>정답 및 해설</h3>"));
      for (let i = 0; i < list.length; i++) {
        const e = mk("ex"), hd = document.createElement("b"); hd.textContent = (i + 1) + ". 질문과 해설";
        e.appendChild(hd); qaInto(list[i], e);
        await add(e);
      }
    } else {
      for (let i = 0; i < list.length; i++) {
        const n = list[i], e = mk("card"), nh = mk("nh", '<span class="chip"></span><span></span><b></b>');
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
    const name = (exam ? "오답모의고사_" : "오답노트_") + (scope === "cat" ? CATS_S[cat].replace(/\s+/g, "") : "전체") + "_" + new Date().toISOString().slice(0, 10) + ".pdf";
    download(name, pdf.output("blob"));
    setMsg("PDF를 만들었어요.");
  } catch (e) {
    setMsg("PDF를 만들지 못했어요: " + (e.message || e));
  } finally {
    root.remove(); busy(false);
  }
}

function download(name, blob) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name;
  a.style.display = "none"; document.body.appendChild(a); a.click();
  setTimeout(() => { a.remove(); URL.revokeObjectURL(a.href) }, 10000);
}
