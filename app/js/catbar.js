/* 오답노트 분류 선택: 빨간 동그라미 아이콘(빈 것 하나, 찬 것 1~4개) 아래에 이름을 쓴 버튼 5개 (눌러서 선택) */
import { CATS, ORDER, catDots } from "./cats.js";

/** 아이콘 아래에 쓰는 짧은 이름 (저장 번호 기준) */
export const CAT_SHORT = { 4: "시간", 1: "얻음", 0: "애매", 2: "개념", 3: "어려움" };

/** value: 처음 선택(없으면 null), showCount: 분류별 문제 수 표시, onChange(cat): 눌렀을 때 */
export function categoryBar({ value = null, showCount = false, onChange }) {
  const el = document.createElement("div");
  el.className = "catbar"; el.setAttribute("role", "radiogroup"); el.setAttribute("aria-label", "오답노트 분류");
  const btns = new Map(), counts = new Map();
  ORDER.forEach(cat => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "cat-btn"; b.setAttribute("role", "radio"); b.title = CATS[cat];
    const name = document.createElement("span"); name.className = "cat-name"; name.textContent = CAT_SHORT[cat];
    b.append(catDots(cat), name);
    if (showCount) { const n = document.createElement("span"); n.className = "cat-cnt"; n.textContent = "0"; b.appendChild(n); counts.set(cat, n) }
    b.onclick = () => { select(cat); onChange?.(cat) };
    el.appendChild(b); btns.set(cat, b);
  });
  function select(cat) { btns.forEach((b, c) => { b.classList.toggle("on", c === cat); b.setAttribute("aria-checked", c === cat) }) }
  select(value);
  return { el, select, setCounts(map) { counts.forEach((n, c) => { n.textContent = map[c] ?? 0 }) } };
}
