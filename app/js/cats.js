/* 오답노트 분류 (저장되는 번호는 고정, 화면 순서만 ORDER) */
export const CATS = ["풀 수 있는데 이해 안 됨", "풀 수 있는데 얻은 것 있음", "개념을 몰라서 못 품", "어려워서 못 품"];
export const CATS_S = ["이해 안 됨", "얻은 것 있음", "개념 몰라서", "어려워서"];

/** 화면 순서: 얻은 것 있음 → 이해 안 됨 → 개념 몰라서 → 어려워서 */
export const ORDER = [1, 0, 2, 3];

/** 빨간 동그라미 level개 (글씨 없음). level 0이면 4개 모두 빈 동그라미 */
export function levelDots(level) {
  const s = document.createElement("span");
  s.className = "dots"; s.setAttribute("aria-hidden", "true");
  for (let i = 1; i <= (level || 4); i++) { const d = document.createElement("i"); if (!level) d.className = "empty"; s.appendChild(d) }
  return s;
}
