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

export function fillRich(el, text) {
  el.textContent = "";
  tokenize(text).forEach(tk => el.appendChild(tk.m !== undefined ? mathNode(tk) : document.createTextNode(tk.v)));
}
