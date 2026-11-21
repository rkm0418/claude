#!/usr/bin/env python3
"""곰 조력자(그네에 앉아 있는 모습): 주인공과 같은 방식(4배 크기로 그려 줄이기 · 같은 굵기의 윤곽선 · 밝은/보통/그늘 세 톤 · 같은 초록 윗옷)으로 새로 그린다.
기존 곰(art/out/sprites/bear_green_*.png: 황갈색 털, 분홍 귀 안쪽·뺨, 크림색 주둥이, 초록 윗옷)의 모습을 이어받는다.
출력: art/out/sprites/bear_hd.png (56x80, 게임 크기 약 12x17)   사용: python3 tools/gen_bear_hd.py"""
import os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'bear_hd.png')
W, H, SS = 56, 80, 4; RING = 1.8
A_ = (26, 22, 32)
FUR = ((206, 160, 112), (186, 138, 92), (150, 104, 68)); EARIN = ((236, 176, 170), (220, 150, 150), (184, 118, 122)); MUZ = ((250, 228, 194), (240, 214, 176), (214, 184, 144))
JK = ((70, 108, 82), (47, 74, 58), (31, 51, 41)); PT = ((78, 68, 86), (59, 51, 64), (43, 36, 48)); SHOE = ((110, 78, 58), (84, 58, 44), (58, 40, 32))

def build():
    cv = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    def m_ellipse(cx, cy, rx, ry, g=0.0, dx=0.0, dy=0.0, k=1.0):
        m = Image.new('L', cv.size, 0); ImageDraw.Draw(m).ellipse([(cx + dx - rx * k - g) * SS, (cy + dy - ry * k - g) * SS, (cx + dx + rx * k + g) * SS, (cy + dy + ry * k + g) * SS], fill=255); return m
    def m_rrect(x0, y0, x1, y1, r, g=0.0, dx=0.0, dy=0.0, k=1.0):
        m = Image.new('L', cv.size, 0); cx, cy = (x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy; hw, hh = (x1 - x0) / 2 * k, (y1 - y0) / 2 * k
        ImageDraw.Draw(m).rounded_rectangle([(cx - hw - g) * SS, (cy - hh - g) * SS, (cx + hw + g) * SS, (cy + hh + g) * SS], radius=(r + g) * SS, fill=255); return m
    def m_cap(pts, r0, r1, g=0.0, dx=0.0):
        m = Image.new('L', cv.size, 0); d = ImageDraw.Draw(m); n = 24
        for i in range(n + 1):
            t = i / n; x = pts[0][0] + (pts[1][0] - pts[0][0]) * t + dx; y = pts[0][1] + (pts[1][1] - pts[0][1]) * t; r = r0 + (r1 - r0) * t + g
            d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=255)
        return m
    def paint(m, col, clip=None):
        if clip is not None: m = Image.composite(m, Image.new('L', cv.size, 0), clip)
        cv.paste(Image.new('RGBA', cv.size, col + (255,)), (0, 0), m)
    def shape(mk, tones, hi=True):
        """mk(g, dx, dy, k) -> 마스크. 윤곽선 → 그늘 → 보통(왼쪽 위로 치우쳐) → 밝은 점 순서(모두 같은 실루엣 안에서만)."""
        sil = mk(0, 0, 0, 1.0); paint(mk(RING, 0, 0, 1.0), A_); paint(sil, tones[2])
        paint(mk(0, -.9, -.9, .92), tones[1], sil)
        if hi: paint(mk(0, -2.2, -2.4, .5), tones[0], sil)
        return sil
    E = lambda cx, cy, rx, ry: (lambda g, dx, dy, k: m_ellipse(cx, cy, rx, ry, g, dx, dy, k))
    # --- 뒤에서부터: 다리(앉아서 아래로 늘어뜨림) → 몸통 → 팔 → 귀 → 머리 → 얼굴
    for sx in (21, 35):                                                  # 다리: 바지 + 신발
        shape(lambda g, dx, dy, k, sx=sx: m_cap(((sx, 58), (sx, 71)), 5.0, 4.4, g, dx), PT)
        shape(E(sx + (-.6 if sx < 28 else .6), 74.6, 6.4, 3.8), SHOE)
    shape(lambda g, dx, dy, k: m_rrect(14, 41, 42, 62, 8, g, dx, dy, k), JK)                          # 윗옷 몸통
    for x0, x1 in ((19, 15), (37, 41)):                                                                # 래글런 선
        d = ImageDraw.Draw(cv); d.line([(x0 * SS, 44.5 * SS), (x1 * SS, 53.5 * SS)], fill=JK[2] + (255,), width=int(1.3 * SS))
    d = ImageDraw.Draw(cv); d.polygon([(22 * SS, 42 * SS), (34 * SS, 42 * SS), (28 * SS, 50 * SS)], fill=(240, 226, 196, 255))             # 안에 입은 셔츠(V 목)
    d.polygon([(20.5 * SS, 42 * SS), (23.5 * SS, 42 * SS), (28 * SS, 50.5 * SS), (26 * SS, 50.5 * SS)], fill=JK[2] + (255,)); d.polygon([(35.5 * SS, 42 * SS), (32.5 * SS, 42 * SS), (28 * SS, 50.5 * SS), (30 * SS, 50.5 * SS)], fill=JK[2] + (255,))
    d.line([(15 * SS, 59 * SS), (41 * SS, 59 * SS)], fill=JK[2] + (255,), width=int(2.2 * SS))                                           # 밑단 띠
    for sx, hx in ((1, 12.2), (-1, 43.8)):                                                              # 팔: 소매 + 앞발(털)
        shape(lambda g, dx, dy, k, sx=sx: m_cap(((15.5 if sx > 0 else 40.5, 45.5), (hx + (.8 if sx > 0 else -.8), 55.5)), 5.0, 4.0, g, dx), JK)
        shape(E(hx, 58.0, 3.4, 3.2), FUR)
    for cx in (11.5, 44.5):                                                                              # 귀
        shape(E(cx, 10.5, 7.4, 7.2), FUR); paint(m_ellipse(cx, 11.2, 3.8, 3.6), EARIN[1]); paint(m_ellipse(cx, 11.6, 2.6, 2.4, 0, -.6, -.6, .8), EARIN[0])
    shape(E(28, 25.5, 22, 18.4), FUR)                                                                    # 머리
    shape(E(28, 34.6, 9.6, 6.2), MUZ)                                                                    # 주둥이
    for cx in (11.2, 44.8): paint(m_ellipse(cx, 31.0, 4.2, 2.7), (236, 166, 152))                         # 뺨
    paint(m_ellipse(28, 31.6, 3.0, 2.0), (66, 44, 40)); paint(m_ellipse(27.2, 30.9, 1.0, .6), (150, 120, 104))   # 코
    d = ImageDraw.Draw(cv)
    for a, b in (((28, 33.4), (28, 35.6)), ((28, 35.6), (25.4, 37.0)), ((28, 35.6), (30.6, 37.0))): d.line([(a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS)], fill=A_ + (255,), width=int(1.2 * SS))   # 입
    for cx in (17.8, 38.2): paint(m_ellipse(cx, 23.6, 2.1, 2.6), A_); paint(m_ellipse(cx - .7, 22.5, .75, .85), (252, 246, 232))        # 눈 + 반짝임
    arr = np.array(cv.convert('RGBa').resize((W, H), Image.LANCZOS).convert('RGBA')); arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    return Image.fromarray(arr, 'RGBA')

def pix(im, size=(24, 34), thr=120):
    """네모네모한 도트판(게임 화면 한 칸 단위, 24x34 = 게임 크기 12x17 × 2): 또렷한 네모 도트로 줄인다."""
    a = np.array(im.convert('RGBa').resize(size, Image.BOX).convert('RGBA')); a[..., 3] = np.where(a[..., 3] >= thr, 255, 0); return Image.fromarray(a, 'RGBA')

if __name__ == '__main__':
    im = build(); im.save(OUT); pix(im).save(OUT.replace('bear_hd', 'bear_px')); S = 8; sh = Image.new('RGBA', (im.width * S + 20, im.height * S + 20), (44, 48, 64, 255)); sh.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (10, 10))
    sh.save(os.path.join(HERE, '..', 'maps', 'out', 'bear_hd_sheet.png')); print('bear_hd', im.size)
