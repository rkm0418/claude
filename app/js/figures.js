/* 문제 그림 추출 + 손글씨 자동 제거 */

/** 색 펜 제거 + 종이 그늘(배경) 보정 + 대비 올리기 */
function processFig(cv0, rmColor) {
  const w = cv0.width, h = cv0.height, g = cv0.getContext("2d"), im = g.getImageData(0, 0, w, h), d = im.data;
  // 배경 밝기는 작게 줄였다 키워서 추정
  const sw = Math.max(2, Math.round(w / 14)), sh = Math.max(2, Math.round(h / 14));
  const sm = document.createElement("canvas"); sm.width = sw; sm.height = sh; sm.getContext("2d").drawImage(cv0, 0, 0, sw, sh);
  const bg = document.createElement("canvas"); bg.width = w; bg.height = h;
  const bgc = bg.getContext("2d"); bgc.imageSmoothingEnabled = true; bgc.drawImage(sm, 0, 0, w, h);
  const bd = bgc.getImageData(0, 0, w, h).data;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i], gg = d[i + 1], b = d[i + 2], mx = Math.max(r, gg, b), mn = Math.min(r, gg, b);
    if (rmColor && mx - mn > 48) { d[i] = d[i + 1] = d[i + 2] = 255; continue }
    const lum = .3 * r + .59 * gg + .11 * b, bl = Math.max(60, .3 * bd[i] + .59 * bd[i + 1] + .11 * bd[i + 2]);
    let v = Math.min(255, lum * 255 / bl);
    v = Math.max(0, Math.min(255, (v - 95) * 255 / (215 - 95)));
    d[i] = d[i + 1] = d[i + 2] = v;
  }
  g.putImageData(im, 0, 0);
  return cv0;
}

/** Claude가 알려준 비율 좌표(figures)대로 사진에서 그림만 오려 JPEG 데이터 주소 목록으로 */
export function makeFigures(list, srcCanvas, rect, rmColor) {
  if (!Array.isArray(list) || !srcCanvas || !rect) return [];
  const out = [];
  for (const b of list.slice(0, 4)) {
    let { x, y, w, h } = b || {};
    x = +x; y = +y; w = +w; h = +h;
    if (![x, y, w, h].every(Number.isFinite) || w < .04 || h < .04) continue;
    const pad = .02;
    x = Math.max(0, x - pad); y = Math.max(0, y - pad); w = Math.min(1 - x, w + pad * 2); h = Math.min(1 - y, h + pad * 2);
    const sx = rect.x + x * rect.w, sy = rect.y + y * rect.h, sw = w * rect.w, sh = h * rect.h, k = Math.min(1, 760 / Math.max(sw, sh));
    const c = document.createElement("canvas");
    c.width = Math.max(8, Math.round(sw * k)); c.height = Math.max(8, Math.round(sh * k));
    c.getContext("2d").drawImage(srcCanvas, sx, sy, sw, sh, 0, 0, c.width, c.height);
    processFig(c, rmColor);
    out.push(c.toDataURL("image/jpeg", .85));
  }
  return out;
}
