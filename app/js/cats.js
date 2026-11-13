/* 오답노트 분류 (저장되는 번호는 고정, 화면 순서만 ORDER) */
export const CATS = ["풀 수 있는데 이해 안 됨", "풀 수 있는데 얻은 것 있음", "개념을 몰라서 못 품", "어려워서 못 품", "시간이 부족해서 못 품"];
export const CATS_S = ["이해 안 됨", "얻은 것 있음", "개념 몰라서", "어려워서", "시간"];

/** 화면 순서(왼쪽부터): 시간 → 얻음 → 애매 → 개념 → 어려움 */
export const ORDER = [4, 1, 0, 2, 3];

/** 분류 아이콘: 맨 왼쪽(시간)은 빈 빨간 동그라미 하나, 그다음부터 속이 찬 빨간 동그라미 1~4개 */
export function catDots(cat) {
  const idx = ORDER.indexOf(cat), s = document.createElement("span");
  s.className = "dots"; s.setAttribute("aria-hidden", "true");
  for (let i = 0; i < Math.max(1, idx); i++) { const d = document.createElement("i"); if (idx === 0) d.className = "hollow"; s.appendChild(d) }
  return s;
}
