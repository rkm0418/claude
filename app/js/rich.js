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

function addTokens(el, text) {
  tokenize(text).forEach(tk => el.appendChild(tk.m !== undefined ? mathNode(tk) : document.createTextNode(tk.v)));
}

const SECTION = /^\[(사용된 개념|조건 해석|풀이)\][ 	]*$/m;

/** 수식을 그려 넣고, [사용된 개념]·[조건 해석]·[풀이] 제목 줄은 구역으로 나눠 보여줌 */
export function fillRich(el, text) {
  el.textContent = "";
  const parts = String(text || "").split(new RegExp(SECTION.source, "gm"));
  if (parts.length < 3) { addTokens(el, text); return }
  if (parts[0].trim()) { const pre = document.createElement("div"); addTokens(pre, parts[0].trim()); el.appendChild(pre) }
  for (let i = 1; i < parts.length; i += 2) {
    const h = document.createElement("div"); h.className = "sec-h"; h.textContent = parts[i];
    const b = document.createElement("div"); b.className = "sec-b"; addTokens(b, (parts[i + 1] || "").trim());
    el.append(h, b);
  }
}
