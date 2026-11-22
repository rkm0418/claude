#!/usr/bin/env python3
"""주인공 고해상도판: 기존 8방향 도트(24x42)를 같은 모양 그대로 4배 촘촘한 도트(56x96, 게임 크기 14x24 × 4)로 부드럽게 만든다.
  1) Scale2x(EPX)를 두 번 — 계단 모서리를 둥글게 다듬어 4배 크기로(96x168)  2) 게임 크기 × 4 로 줄이고 알파는 다시 또렷하게(도트 느낌 유지)
  3) 걷기 네 장 사이 사이에 중간 자세를 섞어 만든 한 장씩을 더해 걷기를 8장으로(더 부드러운 걸음)
출력: art/out/sprites/child_hd/child_<방향>_<idle|w1..w4|m1..m4>.png   사용: python3 tools/gen_child_hd.py"""
import os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'child8'); OUT = os.path.join(HERE, '..', 'art', 'out', 'sprites', 'child_hd')
K = 4; GW, GH = 14, 26; SIZE = (GW * K, GH * K)                  # 14x26: 이전(14x24)보다 키를 키워 납작해 보이지 않게
DIRS = ['d', 'dr', 'r', 'ur', 'u', 'ul', 'l', 'dl']; FR = ['idle', 'w1', 'w2', 'w3', 'w4']

def scale2x(a):
    h, w = a.shape[:2]; p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    P = p[1:-1, 1:-1]; A = p[:-2, 1:-1]; B = p[1:-1, 2:]; C = p[1:-1, :-2]; D = p[2:, 1:-1]
    eq = lambda x, y: np.all(x == y, axis=-1)
    o = np.repeat(np.repeat(P, 2, 0), 2, 1).copy()
    m1 = eq(C, A) & ~eq(C, D) & ~eq(A, B); m2 = eq(A, B) & ~eq(A, C) & ~eq(B, D); m3 = eq(D, C) & ~eq(D, B) & ~eq(C, A); m4 = eq(B, D) & ~eq(B, A) & ~eq(D, C)
    for m, (dy, dx), src in ((m1, (0, 0), A), (m2, (0, 1), B), (m3, (1, 0), C), (m4, (1, 1), D)):
        ys, xs = np.nonzero(m); o[ys * 2 + dy, xs * 2 + dx] = src[ys, xs]
    return o

def hd(im):
    a = np.array(im.convert('RGBA')); a = scale2x(scale2x(a)); big = Image.fromarray(a, 'RGBA')
    small = big.convert('RGBa').resize(SIZE, Image.LANCZOS).convert('RGBA'); s = np.array(small); s[..., 3] = np.where(s[..., 3] >= 128, 255, 0); return Image.fromarray(s, 'RGBA')

# ---------------- 몸: 진짜 옷을 입은 듯 완만한 곡선으로 새로 그린다 ----------------
import math
SS = 4                                                                # 몸은 4배 더 크게 그린 뒤 줄인다(곡선이 매끈하다)
CUT = 55                                                              # 이 줄 위는 기존 머리 그림, 아래는 새 몸
A_ = (26, 22, 32); SKIN, SKIN2 = (242, 220, 180), (211, 165, 116)
SW_ = ((70, 108, 82), (47, 74, 58), (31, 51, 41))                     # 윗옷: 밝은·보통·그늘
PT_ = ((78, 68, 86), (59, 51, 64), (43, 36, 48))                       # 바지
SHO = ((70, 62, 76), (46, 40, 52), (30, 26, 36))                       # 신발
RING = 1.8                                                            # 윤곽선 굵기(기존 머리 윤곽선과 비슷)
CX = GW * K / 2.0

def _tab(pts, y):
    ys = [p[0] for p in pts]; return float(np.interp(y, ys, [p[1] for p in pts]))
HALF = ((52, 4.6), (55, 8.4), (58, 12.6), (61, 14.6), (66, 15.2), (72, 14.8), (78, 15.0), (84.6, 15.8))        # 스웨터 실루엣: 어깨가 비스듬히 흘러내려 소매로 이어지고 밑단으로 갈수록 살짝 넓다   # 몸통 가로 반폭(어깨는 비스듬히, 허리는 살짝 잘록, 밑단은 퍼짐)

def _stamp(draw, pts, rs, fill, dx=0.0):
    """경로를 따라 원을 찍어 굵기가 변하는 둥근 팔다리를 만든다(좌표는 4배 캔버스)."""
    n = 28
    for i in range(n + 1):
        t = i / n; seg = min(len(pts) - 2, int(t * (len(pts) - 1))); u = t * (len(pts) - 1) - seg
        x = pts[seg][0] + (pts[seg + 1][0] - pts[seg][0]) * u + dx; y = pts[seg][1] + (pts[seg + 1][1] - pts[seg][1]) * u; r = rs[0] + (rs[1] - rs[0]) * t
        draw.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)

def _bez(p0, p1, p2, n=3):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]

NECKC = (214, 176, 132, 255); HANDT = ((236, 202, 156), (236, 202, 156), (204, 160, 114))                # 목·손 살색(곰은 털색으로 바꿔 쓴다)
def body(theta_deg, phi, amp, pose=None, canvas_wh=None):
    """한 자세의 몸(머리 아래)을 RGBA(56x104)로. theta: 0 정면, 90 오른쪽, 180 뒷모습(시계 반대는 270 = 왼쪽)."""
    th = math.radians(theta_deg); ct, st = math.cos(th), math.sin(th); W_, H_ = canvas_wh or (GW * K, GH * K); CXL = W_ / 2.0
    canvas = Image.new('RGBA', (W_ * SS, H_ * SS), (0, 0, 0, 0))
    pr = lambda x, z: CXL + x * ct + z * st                            # 몸 옆(x)·앞(z) → 화면 가로
    dep = lambda x, z: z * ct - x * st                                # 클수록 보는 사람에 가깝다
    def put(mask_fill, mask_base, mask_hi, tones, ring_mask):
        """윤곽선 → 그늘색 몸 → 보통색 → 밝은색 순서로 붙인다(모두 같은 실루엣 안에서만)."""
        for m, c in ((ring_mask, A_ + (255,)),): canvas.paste(Image.new('RGBA', canvas.size, c), (0, 0), m)
        sil = mask_fill
        for m, c in ((sil, tones[2]), (mask_base, tones[1]), (mask_hi, tones[0])):
            layer = Image.new('RGBA', canvas.size, c + (255,)); mm = Image.composite(m, Image.new('L', canvas.size, 0), sil) if m is not sil else m; canvas.paste(layer, (0, 0), mm)
    def limb(pts, rs, tones, light=-0.42):
        def mk(r0, r1, shift):
            m = Image.new('L', canvas.size, 0); _stamp(ImageDraw.Draw(m), pts, (r0, r1), 255, shift); return m
        ring = mk(rs[0] + RING, rs[1] + RING, 0); sil = mk(rs[0], rs[1], 0); base = mk(rs[0] * .92, rs[1] * .92, light * rs[0]); hi = mk(rs[0] * .5, rs[1] * .5, light * rs[0] * 1.5)
        put(sil, base, hi, tones, ring)
    parts = []
    # --- 다리: 걸을 때 앞뒤로 휘두르고 나가는 발은 살짝 든다
    for s in (-1, 1):
        ph = phi + (0 if s < 0 else math.pi); sw = amp * math.sin(ph); lift = 2.8 * amp * max(0.0, math.cos(ph))
        hip = (s * 4.6, 81.5, 0.0); ank = (s * 5.0, 97.6 - lift, 6.2 * sw); knee = ((hip[0] + ank[0]) / 2, (hip[1] + ank[1]) / 2 + .5, (hip[2] + ank[2]) / 2 + 1.0 + lift * .9)
        if pose: hip, knee, ank = pose['leg'][s]
        P_ = [(pr(*(hip[0], hip[2])), hip[1]), (pr(knee[0], knee[2]), knee[1]), (pr(ank[0], ank[2]), ank[1])]
        parts.append((dep(ank[0], ank[2]) - .01, 'leg', P_, (pr(ank[0], ank[2]), ank[1]), ank))
    # --- 팔: 같은 쪽 다리와 반대로 흔든다
    for s in (-1, 1):
        ph = phi + (math.pi if s < 0 else 0); sw = amp * math.sin(ph)
        sh = (s * 12.4, 59.6, 0.0); el = (s * 16.8, 67.4, 2.4 * sw + .6); hd_ = (s * 20.0, 75.8, 4.8 * sw)
        if pose: sh, el, hd_ = pose['arm'][s]                 # 소매가 어깨에서 바깥으로 비스듬히 내려온다(A 모양)
        P_ = [(pr(sh[0], sh[2]), sh[1]), (pr(el[0], el[2]), el[1]), (pr(hd_[0], hd_[2]), hd_[1])]
        parts.append((dep(hd_[0], hd_[2]) + (.5 if dep(sh[0], sh[2]) > 0 else -.5), 'arm', P_, (pr(hd_[0], hd_[2]), hd_[1] + 2.0), hd_))
    parts.sort(key=lambda p: p[0])
    drawn_torso = False
    def torso():
        ys = np.arange(52, 85.1, .5); cxs = CXL + 0.9 * st
        wl = []
        for y in ys:
            a = _tab(HALF, y); b = .78 * a; w = math.sqrt((a * ct) ** 2 + (b * st) ** 2); wl.append((y, w))
        left = [(cxs - w, y) for y, w in wl]; right = [(cxs + w, y) for y, w in wl][::-1]; poly = left + right
        def pm(poly, ow=0.0, dx=0.0, shrink=1.0, y0=0, y1=999):
            m = Image.new('L', canvas.size, 0); d = ImageDraw.Draw(m)
            pp = [((cxs + (x - cxs) * shrink + dx) * SS, y * SS) for x, y in poly if y0 <= y <= y1]
            d.polygon(pp, fill=255, outline=255, width=int(ow * SS)); return m
        neck = Image.new('L', canvas.size, 0); ImageDraw.Draw(neck).rectangle([(cxs - 4.4) * SS, 50 * SS, (cxs + 4.4) * SS, 60 * SS], fill=255)
        if ct > .25: canvas.paste(Image.new('RGBA', canvas.size, NECKC), (0, 0), neck)
        ring = pm(poly, ow=RING); sil = pm(poly); base = pm(poly, dx=-2.0 * (ct if abs(ct) > .3 else 1), shrink=.82); hi = pm(poly, dx=-4.2, shrink=.42, y0=0, y1=68)
        put(sil, base, hi, SW_, ring)
        # 밑단: 아래가 살짝 어두운 띠 + 허리 주름
        band = Image.new('L', canvas.size, 0); ImageDraw.Draw(band).rectangle([0, 81.6 * SS, W_ * SS, 85.0 * SS], fill=255); canvas.paste(Image.new('RGBA', canvas.size, SW_[2] + (255,)), (0, 0), Image.composite(band, Image.new('L', canvas.size, 0), sil))
        fm = Image.new('L', canvas.size, 0); fd = ImageDraw.Draw(fm)
        for (x0, y0, x1, y1) in ((-6.2, 58.4, -13.4, 68.0), (6.2, 58.4, 13.4, 68.0), (-5, 75.5, 0, 78), (5.5, 73.0, 9.0, 76.0)):
            fd.line([(pr(x0, 0) * SS, y0 * SS), (pr(x1, 0) * SS, y1 * SS)], fill=255, width=int(1.4 * SS))
        canvas.paste(Image.new('RGBA', canvas.size, SW_[2] + (255,)), (0, 0), Image.composite(fm, Image.new('L', canvas.size, 0), sil))
        # 목둘레(둥근 깃): 앞에서는 안에 살갗, 뒤에서는 깃만
        col = Image.new('L', canvas.size, 0); cd = ImageDraw.Draw(col); rx = max(2.2, _tab(HALF, 57.6) * .66 * math.sqrt(ct * ct + .45 * st * st)); cy = 57.6
        cd.ellipse([(cxs - rx - RING * .6) * SS, (cy - 2.6 - RING * .6) * SS, (cxs + rx + RING * .6) * SS, (cy + 2.6 + RING * .6) * SS], fill=255)
        canvas.paste(Image.new('RGBA', canvas.size, A_ + (255,)), (0, 0), Image.composite(col, Image.new('L', canvas.size, 0), sil))
        c2 = Image.new('L', canvas.size, 0); ImageDraw.Draw(c2).ellipse([(cxs - rx) * SS, (cy - 2.6) * SS, (cxs + rx) * SS, (cy + 2.6) * SS], fill=255)
        canvas.paste(Image.new('RGBA', canvas.size, SW_[2] + (255,)), (0, 0), Image.composite(c2, Image.new('L', canvas.size, 0), sil))
        if ct > .3:
            c3 = Image.new('L', canvas.size, 0); ImageDraw.Draw(c3).ellipse([(cxs - rx * .68) * SS, (cy - 2.0) * SS, (cxs + rx * .68) * SS, (cy + 1.6) * SS], fill=255)
            canvas.paste(Image.new('RGBA', canvas.size, NECKC), (0, 0), Image.composite(c3, Image.new('L', canvas.size, 0), sil))
    def draw_part(kind, pts, tip):
        if kind == 'leg':
            limb(pts, (5.7, 4.7), PT_)
            sx, sy = tip; rxs = 4.9 + 2.6 * abs(st); cxx = sx + 1.8 * st; cyy = sy + 3.1; E = lambda r_, ry_, dx_=0.0: [(cxx - r_ + dx_) * SS, (cyy - ry_) * SS, (cxx + r_ + dx_) * SS, (cyy + ry_) * SS]
            ring = Image.new('L', canvas.size, 0); ImageDraw.Draw(ring).ellipse(E(rxs + RING, 2.9 + RING), fill=255)
            sc = Image.new('L', canvas.size, 0); ImageDraw.Draw(sc).ellipse(E(rxs, 2.9), fill=255)
            b2 = Image.new('L', canvas.size, 0); ImageDraw.Draw(b2).ellipse([(cxx - rxs - .4) * SS, (cyy - 2.9) * SS, (cxx + rxs - .8) * SS, (cyy + 1.6) * SS], fill=255)
            put(sc, b2, Image.new('L', canvas.size, 0), SHO, ring)
        else:
            limb(pts, (5.6, 4.3), SW_)
            cm = Image.new('L', canvas.size, 0); ImageDraw.Draw(cm).ellipse([(pts[2][0] - 3.7) * SS, (pts[2][1] - 3.7) * SS, (pts[2][0] + 3.7) * SS, (pts[2][1] + 3.7) * SS], fill=255)       # 소매 끝(골)
            canvas.paste(Image.new('RGBA', canvas.size, A_ + (255,)), (0, 0), cm); cm2 = Image.new('L', canvas.size, 0); ImageDraw.Draw(cm2).ellipse([(pts[2][0] - 3.3) * SS, (pts[2][1] - 3.3) * SS, (pts[2][0] + 3.3) * SS, (pts[2][1] + 3.3) * SS], fill=255); canvas.paste(Image.new('RGBA', canvas.size, SW_[2] + (255,)), (0, 0), cm2)
            hx, hy = tip; hr = 2.9; hy = hy + 0.7; E = lambda r_, dx_=0.0, dy_=0.0: [(hx - r_ + dx_) * SS, (hy - r_ + dy_) * SS, (hx + r_ + dx_) * SS, (hy + r_ + dy_) * SS]
            hm = Image.new('L', canvas.size, 0); ImageDraw.Draw(hm).ellipse(E(hr), fill=255)
            hb = Image.new('L', canvas.size, 0); ImageDraw.Draw(hb).ellipse(E(hr * .9, -.5, -.3), fill=255)
            ring = Image.new('L', canvas.size, 0); ImageDraw.Draw(ring).ellipse(E(hr + RING), fill=255)
            put(hm, hb, Image.new('L', canvas.size, 0), HANDT, ring)      # 손: 얼굴보다 따뜻한 살색(하얗게 튀지 않게)
    for dp, kind, pts, tip, j in parts:                                       # 다리는 언제나 몸통 아래
        if kind == 'leg': draw_part(kind, pts, tip)
    for dp, kind, pts, tip, j in parts:                                       # 먼 쪽 팔 → 몸통 → 가까운 쪽 팔
        if kind == 'arm' and dp < 0: draw_part(kind, pts, tip)
    torso()
    for dp, kind, pts, tip, j in parts:
        if kind == 'arm' and dp >= 0: draw_part(kind, pts, tip)
    arr = np.array(canvas.convert('RGBa').resize((W_, H_), Image.LANCZOS).convert('RGBA')); arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    return Image.fromarray(arr, 'RGBA')

YAW = {'d': 0, 'dr': 45, 'r': 90, 'ur': 135, 'u': 180, 'ul': 225, 'l': 270, 'dl': 315}
NW = 8                                                                # 걷기 장 수(한 걸음 주기를 8장으로)

HS = 0.88                                                             # 머리를 이 비율로 줄인다(몸이 상대적으로 커져 어린아이 비율에서 벗어난다)
CHIN = 55                                                             # 줄인 머리의 턱 줄(이 아래가 몸)
def small_head(head):
    h = np.array(head).copy(); h[60:] = 0; im = Image.fromarray(h, 'RGBA').crop((0, 0, GW * K, 60)); w, hh = round(GW * K * HS), round(60 * HS)
    s = np.array(im.convert('RGBa').resize((w, hh), Image.LANCZOS).convert('RGBA')); s[..., 3] = np.where(s[..., 3] >= 128, 255, 0)
    out = Image.new('RGBA', (GW * K, GH * K), (0, 0, 0, 0)); out.alpha_composite(Image.fromarray(s, 'RGBA'), (round((GW * K - w) / 2), CHIN - hh)); return np.array(out)

def build():
    os.makedirs(OUT, exist_ok=True); res = {}
    for d in DIRS:
        head = hd(Image.open(os.path.join(SRC, f'child_{d}_idle.png'))); hp = small_head(head)
        def comp(phi, amp, hp=hp):
            b = np.array(body(YAW[d], phi, amp)); out = b.copy(); m = hp[..., 3] > 0; out[m] = hp[m]; return Image.fromarray(out, 'RGBA')
        f = {'idle': comp(0.0, 0.0)}
        for i in range(NW): f[f'w{i + 1}'] = comp(2 * math.pi * i / NW, 1.0)
        if d == 'r':                                                      # 오른쪽 보며 걷는 몸에 고개만 위쪽(lu)·아래쪽(ld)으로 돌린 변형: 컷씬에서 주변을 둘러보는 데 쓴다
            for tag, srcd in (('lu', 'ur'), ('ld', 'dr')):
                h2 = small_head(hd(Image.open(os.path.join(SRC, f'child_{srcd}_idle.png'))))
                f[f'{tag}_idle'] = comp(0.0, 0.0, h2)
                for i in range(NW): f[f'{tag}_w{i + 1}'] = comp(2 * math.pi * i / NW, 1.0, h2)
        for k, im in f.items(): im.save(os.path.join(OUT, f'child_{d}_{k}.png'))
        res[d] = f
    return res

if __name__ == '__main__':
    r = build(); S = 3; names = ['idle'] + [f'w{i + 1}' for i in range(NW)]
    sheet = Image.new('RGBA', (len(names) * (SIZE[0] + 4) * S + 8, len(DIRS) * (SIZE[1] + 4) * S + 8), (44, 48, 64, 255))
    for row, d in enumerate(DIRS):
        for c, k in enumerate(names): sheet.alpha_composite(r[d][k].resize((SIZE[0] * S, SIZE[1] * S), Image.NEAREST), (4 + c * (SIZE[0] + 4) * S, 4 + row * (SIZE[1] + 4) * S))
    sheet.save(os.path.join(HERE, '..', 'maps', 'out', 'child_hd_sheet.png')); print('child_hd', len(DIRS) * (NW + 1))
