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

def orig_hd(rows=27):
    """원래 곰(art/out/sprites/bear_green_A.png, 24x32)의 모습 그대로 도트 수만 4배(가로세로 두 번 Scale2x → 96x108)로 늘린다. 앉아 있게 보이도록 아래 5줄(발)은 자른다."""
    import gen_child_hd as G
    src = Image.open(os.path.join(HERE, '..', 'art', 'out', 'sprites', 'bear_green_A.png')).convert('RGBA').crop((0, 0, 24, rows))
    return Image.fromarray(G.scale2x(G.scale2x(np.array(src))), 'RGBA')

HIPS_FROM_BOTTOM = 108 - 82                                              # 엉덩이(앉는 자리)에서 그림 맨 아래까지 도트 수
BEARK = 4.6                                                             # 곰 그림 한 칸이 게임 화면 몇 도트인지(주인공은 약 4.7)
def orig_sit_human():
    """곰: 머리는 원래 곰(bear_green_A) 그대로 도트 수만 늘리고, 몸은 주인공과 같은 사람 몸 모델(어깨가 비스듬히 흘러내리는 스웨터·둥근 팔·다리)로 그린다.
    그네 자세: 팔꿈치를 굽혀 양옆 줄을 두 손으로 잡고, 두 다리를 앞으로 내밀어 둥근 앞발로 끝난다. 원래 곰의 색(연한 초록 윗옷·황갈색 털)을 쓴다."""
    import gen_child_hd as G
    saved = (G.SW_, G.PT_, G.SHO, G.NECKC, G.HANDT, G.RING); G.RING = 0.0                                  # 안쪽 윤곽선을 없애고(조각조각 보이지 않게) 바깥 윤곽선만 나중에 한 번 긋는다
    TAN = (211, 165, 116); TANT = ((232, 188, 140), TAN, (176, 130, 86))
    G.SW_ = ((166, 208, 134), (111, 143, 88), (63, 90, 52)); G.PT_ = ((118, 150, 96), (88, 118, 70), (58, 84, 48)); G.SHO = TANT; G.NECKC = TAN + (255,); G.HANDT = TANT
    Wc, Hc = 72, 108
    pose = {'arm': {-1: ((-13.0, 61.0, 0.0), (-20.5, 70.0, 0.0), (-27.6, 60.0, 0.0)), 1: ((13.0, 61.0, 0.0), (20.5, 70.0, 0.0), (27.6, 60.0, 0.0))},
            'leg': {-1: ((-4.8, 82.0, 0.0), (-5.6, 90.0, 0.0), (-6.2, 97.0, 0.0)), 1: ((4.8, 82.0, 0.0), (5.6, 90.0, 0.0), (6.2, 97.0, 0.0))}}
    try:
        b = G.body(0.0, 0.0, 0.0, pose, (Wc, Hc))
    finally:
        G.SW_, G.PT_, G.SHO, G.NECKC, G.HANDT, G.RING = saved
    # --- 후드티 느낌: 목 둘레에 두툼하게 말린 모자(후드), 가운데 크림색 끈 둘, 앞 주머니(원래 곰의 초록 후드 윗옷)
    SSh = 4; hl = Image.new('RGBA', (Wc * SSh, Hc * SSh), (0, 0, 0, 0)); hd_ = ImageDraw.Draw(hl); cxh = Wc / 2.0
    def E(cx, cy, rx, ry, g=0.0): return [(cx - rx - g) * SSh, (cy - ry - g) * SSh, (cx + rx + g) * SSh, (cy + ry + g) * SSh]
    LTc, MDc, DKc, DDc = (166, 208, 134, 255), (111, 143, 88, 255), (63, 90, 52, 255), (44, 63, 38, 255)
    hd_.ellipse(E(cxh, 61.8, 17.6, 6.4), fill=DKc)                 # 후드 둥근 말림: 윤곽선 → 그늘
    hd_.ellipse(E(cxh - .5, 61.0, 16.6, 5.4), fill=MDc); hd_.ellipse(E(cxh - 2.2, 60.2, 11.5, 3.2), fill=LTc)                  # 보통 → 위쪽 밝은 면
    hd_.ellipse(E(cxh, 60.2, 8.6, 2.6), fill=(204, 156, 108, 255))                                                                              # 목이 들어가는 안쪽
    for sx in (-1, 1):                                                                                                          # 끈: 목 아래에서 가슴으로 늘어지고 끝에 매듭
        hd_.line([((cxh + sx * 4.2) * SSh, 64.5 * SSh), ((cxh + sx * 4.8) * SSh, 76.5 * SSh)], fill=(170, 150, 120, 255), width=int(2.6 * SSh)); hd_.line([((cxh + sx * 4.2) * SSh, 64.5 * SSh), ((cxh + sx * 4.8) * SSh, 76.5 * SSh)], fill=(240, 226, 196, 255), width=int(1.7 * SSh))
        hd_.ellipse(E(cxh + sx * 4.8, 77.4, 1.7, 1.7), fill=(240, 226, 196, 255))
    hd_.rounded_rectangle([(cxh - 14.0) * SSh, 72.5 * SSh, (cxh + 14.0) * SSh, 85.0 * SSh], radius=5 * SSh, fill=(100, 132, 80, 255)); hd_.rounded_rectangle([(cxh - 13.2) * SSh, 73.4 * SSh, (cxh + 13.2) * SSh, 80.5 * SSh], radius=4 * SSh, fill=(126, 160, 98, 255))      # 앞 주머니(윤곽선 없이 면만 살짝 다르게)
    for sx in (-1, 1): hd_.line([((cxh + sx * 11.6) * SSh, 76.0 * SSh), ((cxh + sx * 8.2) * SSh, 82.2 * SSh)], fill=DKc, width=int(1.5 * SSh))                      # 손 넣는 옆 트임
    ha_ = np.array(hl.convert('RGBa').resize((Wc, Hc), Image.LANCZOS).convert('RGBA')); ha_[..., 3] = np.where(ha_[..., 3] >= 128, 255, 0); hood = Image.fromarray(ha_, 'RGBA')
    src = Image.open(os.path.join(HERE, '..', 'art', 'out', 'sprites', 'bear_green_A.png')).convert('RGBA').crop((0, 0, 24, 18))
    head = Image.fromarray(G.scale2x(G.scale2x(np.array(src))), 'RGBA')                                       # 원래 곰 머리를 4배 도트로(96x72)
    head = head.convert('RGBa').resize((54, 40), Image.LANCZOS).convert('RGBA'); ha = np.array(head); ha[..., 3] = np.where(ha[..., 3] >= 128, 255, 0); head = Image.fromarray(ha, 'RGBA')
    out = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); out.alpha_composite(b); out.alpha_composite(hood)
    from PIL import ImageFilter
    am = out.getchannel('A'); ring = am.filter(ImageFilter.MaxFilter(5)); rm = np.array(ring) > 0; rm &= ~(np.array(am) > 0); ol = np.zeros((Hc, Wc, 4), np.uint8); ol[rm] = (26, 22, 32, 255)             # 몸 전체의 바깥 윤곽선 한 번
    final = Image.fromarray(ol, 'RGBA'); final.alpha_composite(out); out = final; out.alpha_composite(head, ((Wc - 54) // 2, 56 - 40))
    bb = out.getbbox(); out = out.crop((0, bb[1], Wc, Hc))                                                    # 위쪽 빈 줄을 잘라 낸다
    return out, out

def orig_sit(hold=False):
    """(hold=True: 양팔을 뻗어 줄을 쥔 버전, 기본값 False: 원래 곰의 팔 그대로 줄을 쥐지 않는 버전) 원래 곰(bear_green_A: 연한 초록 후드 윗옷·황갈색 털)의 도트 그림을 그대로 쓰고 도트 수만 4배(Scale2x 두 번)로 늘린다.
    그네 자세만 손으로 고친다: 몸 옆에 늘어진 소매는 없애고, 어깨 → 팔꿈치(주머니 높이에서 둥글게 굽음) → 손으로 이어지는 팔 하나씩만 두어 양옆 줄을 잡고, 두 다리는 바지가 이어져 앞으로 내민 둥근 앞발로 끝난다."""
    import gen_child_hd as G
    A0, TAN, PINK = (26, 22, 32, 255), (211, 165, 116, 255), (232, 168, 152, 255); LT, MD, DK, DD = (155, 199, 124, 255), (111, 143, 88, 255), (63, 90, 52, 255), (44, 63, 38, 255)
    src = Image.open(os.path.join(HERE, '..', 'art', 'out', 'sprites', 'bear_green_A.png')).convert('RGBA'); Wd, Ht = 32, 38
    cv = Image.new('RGBA', (Wd, Ht), (0, 0, 0, 0)); cv.alpha_composite(src.crop((0, 0, 24, 28)), (4, 0)); px = cv.load()
    for y in (range(20, 28) if hold else ()):                       # 몸 옆에 늘어진 소매·손은 지우고 몸통(10칸 폭)만 남긴 뒤 옆선을 긋는다(팔은 아래에서 하나씩 새로 그린다)
        for x in list(range(3, 11)) + list(range(21, 27)): px[x, y] = (0, 0, 0, 0)
        px[10, y] = A0; px[21, y] = A0
    for x in (range(10, 22) if hold else ()): px[x, 28] = A0
    def arm(sh, el, hd, dirn):                                      # 어깨 → 팔꿈치 → 손: 굵기 같은 소매를 이어 그린다(관절에서 끊기지 않게 원으로 채움)
        pts = []
        for (a, b) in ((sh, el), (el, hd)):
            for i in range(0, 41): pts.append((a[0] + (b[0] - a[0]) * i / 40.0, a[1] + (b[1] - a[1]) * i / 40.0))
        ys, xs = np.mgrid[0:Ht, 0:Wd]; M = np.zeros((Ht, Wd), bool); R_ = 2.0
        for cx_, cy_ in pts: M |= (xs + .5 - cx_) ** 2 + (ys + .5 - cy_) ** 2 <= R_ * R_
        D = np.zeros((Ht, Wd), bool)
        for cx_, cy_ in pts: D |= (xs + .5 - cx_) ** 2 + (ys + .5 - cy_) ** 2 <= (R_ + 1.1) ** 2
        for y in range(Ht):
            for x in range(Wd):
                if D[y, x] and not M[y, x] and px[x, y][3] == 0: px[x, y] = A0
                if D[y, x] and not M[y, x] and px[x, y] in (LT, MD, DK, DD, TAN): px[x, y] = px[x, y]
        P_ = np.array(pts)
        for y in range(Ht):
            for x in range(Wd):
                if not M[y, x]: continue
                d = P_ - np.array([x + .5, y + .5]); k = int(np.argmin((d ** 2).sum(1))); v = -d[k]; n = np.hypot(*v) or 1.0
                s = (v[0] * -.55 + v[1] * -.85) / n                  # 왼쪽 위에서 오는 빛
                px[x, y] = LT if s > .35 else (DK if s < -.45 else MD)
        hx, hy = hd                                                  # 줄을 쥔 앞발(털)
        for y in range(Ht):
            for x in range(Wd):
                r2 = (x + .5 - hx) ** 2 + (y + .5 - hy) ** 2
                if r2 <= 2.4 ** 2: px[x, y] = TAN
                elif r2 <= 3.4 ** 2 and px[x, y] != TAN and (px[x, y][3] == 0 or px[x, y] in (LT, MD, DK)): px[x, y] = A0
        px[int(hx + dirn * -1), int(hy)] = PINK
    if hold:
        ROPE = (150, 128, 92, 255)                                                                   # 그네 줄(장면의 줄과 같은 색): 손 위아래로 곰 그림 안까지 이어 그려 줄이 주먹을 통과하게 한다
        for rx in (4, 28):
            for y in range(4, 27): px[rx - 1, y] = ROPE; px[rx, y] = ROPE
        arm((10.8, 19.8), (6.6, 17.6), (4.0, 13.4), -1); arm((21.2, 19.8), (25.4, 17.6), (28.0, 13.4), 1)                  # 어깨에서 위로 뻗어 뺨 높이에서 줄을 꼭 쥔다(팔꿈치는 살짝 바깥으로)
        for hx in (4, 28):                                                                          # 주먹: 줄을 감아 쥔 손가락 두 줄
            for dx in (-1, 0, 1): px[hx + dx - 0, 13] = (176, 130, 86, 255); px[hx + dx - 0, 15] = (176, 130, 86, 255)
    for y in range(29, Ht):
        for x in range(Wd): px[x, y] = (0, 0, 0, 0)
    for cx in (13, 19):                                             # 앉은 다리: 윗옷 밑단 아래에서 하나로 이어지는 곧은 바지통(무릎에 주름 한 줄) → 앞발. 둥글게 부푼 곳 없이 폭이 거의 같다
        for y in range(28, 34):
            for dx in range(-2, 3):
                edge = abs(dx) == 2; px[cx + dx, y] = A0 if edge else (LT if dx == -1 and y < 32 else (DK if dx == 1 else MD))
        for dx in range(-1, 2): px[cx + dx, 31] = DK                  # 무릎 주름
        for y in range(34, 38):                                     # 앞발: 바지 끝에서 바로 이어지는 발(맨 아래 분홍 발바닥)
            hw = 3 if y < 37 else 2; fx = cx + (-1 if cx < 16 else 1)
            for dx in range(-hw, hw + 1):
                edge = abs(dx) == hw or y == 37; px[fx + dx, y] = A0 if edge else (PINK if y == 36 and abs(dx) <= 1 else ((190, 142, 96, 255) if y == 34 else TAN))
    return Image.fromarray(G.scale2x(G.scale2x(np.array(cv))), 'RGBA'), cv

def swing_sit():
    """그네 타는 곰(참고 그림: 의자에 앉아 두 손으로 양옆 줄을 가슴 높이에서 쥐고, 팔꿈치는 몸 옆에서 굽고, 허벅지는 의자 위, 정강이는 의자 앞으로 늘어뜨림).
    원래 곰(bear_green_A)의 머리·후드·몸통·위팔(늘어진 소매 윗부분)과 표정은 그대로 두고 아래팔·손·다리만 고친 뒤 도트 수만 4배로 늘린다.
    줄은 곰 그림 안에도 그려 손 위아래로 이어지게 한다(장면의 줄과 같은 색·같은 자리)."""
    import gen_child_hd as G
    A0, TAN, PINK = (26, 22, 32, 255), (211, 165, 116, 255), (232, 168, 152, 255); LT, MD, DK, DD = (155, 199, 124, 255), (111, 143, 88, 255), (63, 90, 52, 255), (44, 63, 38, 255)
    CLR = (0, 0, 0, 0); ROPE = (150, 128, 92, 255)
    src = Image.open(os.path.join(HERE, '..', 'art', 'out', 'sprites', 'bear_green_A.png')).convert('RGBA'); Wd, Ht = 32, 38
    cv = Image.new('RGBA', (Wd, Ht), CLR); cv.alpha_composite(src.crop((0, 0, 24, 28)), (4, 0)); px = cv.load()
    # 1) 늘어진 소매의 아랫부분(손 포함)을 지운다: 위팔만 팔꿈치(24줄)까지 남긴다
    for y in range(24, 28):
        for x in list(range(5, 11)) + list(range(21, 27)): px[x, y] = CLR
        px[10, y] = A0; px[21, y] = A0                              # 몸통 옆선
    for x in range(6, 11): px[x, 24] = A0 if x in (6, 10) else px[x, 24]
    for x in list(range(6, 10)): px[x, 24] = A0
    for x in list(range(22, 26)): px[x, 24] = A0
    # 2) 줄(손 위아래로 이어짐)
    # (줄은 장면에 이미 그려져 있다: 곰 그림에는 그리지 않아 두 줄로 겹쳐 보이지 않게 한다)
    # 3) 아래팔: 팔꿈치(몸 옆, 23줄)에서 바깥 위로 줄까지, 끝에 줄을 쥔 앞발
    ys, xs = np.mgrid[0:Ht, 0:Wd]
    def forearm(el, hd, dirn):
        pts = [(el[0] + (hd[0] - el[0]) * i / 30.0, el[1] + (hd[1] - el[1]) * i / 30.0) for i in range(31)]
        M = np.zeros((Ht, Wd), bool); O = np.zeros((Ht, Wd), bool)
        for cx_, cy_ in pts:
            r2 = (xs + .5 - cx_) ** 2 + (ys + .5 - cy_) ** 2; M |= r2 <= 1.55 ** 2; O |= r2 <= 2.55 ** 2
        for y in range(Ht):
            for x in range(Wd):
                if O[y, x] and not M[y, x] and (px[x, y][3] == 0 or px[x, y] == ROPE): px[x, y] = A0
        for y in range(Ht):
            for x in range(Wd):
                if M[y, x]: px[x, y] = LT if (y + .5) < (el[1] + (hd[1] - el[1]) * max(0, min(1, (x + .5 - el[0]) / (hd[0] - el[0] or 1)))) - .3 else (MD if True else DK)
        hx, hy = hd
        for y in range(Ht):
            for x in range(Wd):
                r2 = (x + .5 - hx) ** 2 + (y + .5 - hy) ** 2
                if r2 <= 1.9 ** 2: px[x, y] = TAN
                elif r2 <= 2.9 ** 2 and (px[x, y][3] == 0 or px[x, y] in (ROPE, LT, MD)): px[x, y] = A0
        for dx in (-1, 0, 1): px[int(hx) + dx, int(hy)] = (176, 130, 86, 255)                       # 줄을 감은 손가락 한 줄
    forearm((7.2, 24.4), (2.7, 20.0), -1); forearm((24.6, 24.4), (27.7, 20.0), 1)            # 손 = 화면에서 잰 장면의 줄 자리(곰 가운데 x=139)
    # 4) 다리: 허벅지는 의자 위(짧게, 반바지처럼 한 덩어리), 무릎에서 꺾여 정강이·발이 의자 앞으로 늘어진다
    for y in range(28, Ht):
        for x in range(Wd): px[x, y] = CLR if not (px[x, y] == ROPE and y < 30) else px[x, y]
    for y in (28, 29, 30):                                          # 허벅지(의자 위)
        for x in range(10, 22):
            edge = x in (10, 21) or y == 30
            px[x, y] = A0 if edge else (LT if (y == 28 and x < 15) else (DK if x in (15, 16) else MD))
    for cx in (13, 18):                                             # 정강이(의자 앞으로 늘어뜨림)
        for y in range(31, 35):
            for dx in range(-2, 3): px[cx + dx, y] = A0 if abs(dx) == 2 else (TAN if dx == -1 else (190, 142, 96, 255))
        for y, hw in ((35, 3), (36, 3), (37, 2)):                  # 발(앞발)
            for dx in range(-hw, hw + 1):
                px[cx + dx, y] = A0 if (abs(dx) == hw or y == 37) else ((PINK if (y == 36 and abs(dx) <= 1) else TAN))
    return Image.fromarray(G.scale2x(G.scale2x(np.array(cv))), 'RGBA'), cv

def walk_up():
    """길을 따라 위쪽(화면 안쪽)으로 걸어가는 곰의 뒷모습: 원래 곰(bear_green_A)의 머리·귀·후드 윗옷 모양과 색 그대로, 얼굴 부분만 털로 덮고(뒷머리) 등에는 후드를 그린다.
    걸음: 왼발은 땅을 딛고 오른발은 뒤로 들려(발바닥 분홍이 보임) 한 걸음 내딛는 모양. 도트 수만 4배."""
    import gen_child_hd as G
    A0, TAN, PINK, CREAM = (26, 22, 32, 255), (211, 165, 116, 255), (232, 168, 152, 255), (242, 220, 180, 255)
    LT, MD, DK, DD = (155, 199, 124, 255), (111, 143, 88, 255), (63, 90, 52, 255), (44, 63, 38, 255); CLR = (0, 0, 0, 0)
    src = Image.open(os.path.join(HERE, '..', 'art', 'out', 'sprites', 'bear_green_A.png')).convert('RGBA'); Wd, Ht = 26, 37
    cv = Image.new('RGBA', (Wd, Ht), CLR); cv.alpha_composite(src.crop((0, 0, 24, 28)), (1, 0)); px = cv.load()
    def boundary(x, y):
        return any(not (0 <= x + dx < Wd and 0 <= y + dy < Ht) or px[x + dx, y + dy][3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for y in range(3, 18):                                           # 얼굴(눈·코·입·뺨·주둥이·귀 안쪽)을 털로 덮는다: 뒷머리
        for x in range(Wd):
            c = px[x, y]
            if c in (PINK, CREAM, (90, 70, 54, 255)) or (c == A0 and not boundary(x, y)): px[x, y] = TAN if not (y <= 6 and c == PINK) else (190, 140, 96, 255)
    for y in range(17, 28):                                          # 앞 끈·V 깃(크림색)은 등에는 없다 → 윗옷색
        for x in range(Wd):
            if px[x, y] == CREAM: px[x, y] = MD
    for y in range(24, 27):                                          # 앞 주머니 띠도 없다
        for x in range(8, 18):
            if px[x, y] in (DK, DD): px[x, y] = MD
    for y, (x0, x1) in ((18, (7, 18)), (19, (6, 19)), (20, (7, 18))):   # 등의 후드(목 뒤에 둥글게 처진 모자)
        for x in range(x0, x1 + 1):
            if px[x, y][3]: px[x, y] = LT if y == 18 else (MD if y == 19 else DK)
    for y in range(28, Ht):
        for x in range(Wd): px[x, y] = CLR
    for x in range(8, 19): px[x, 27] = A0 if px[x, 27][3] == 0 else px[x, 27]
    def leg(x0, y0, y1, w=5):                                        # 바지통
        for y in range(y0, y1 + 1):
            for dx in range(w): px[x0 + dx, y] = A0 if dx in (0, w - 1) else (MD if dx < w // 2 + 1 else DK)
    def foot(cx, y0, hw=3, rows=3, sole=False):                      # 곰 발
        for i in range(rows):
            h = hw if i < rows - 1 else hw - 1
            for dx in range(-h, h + 1):
                edge = abs(dx) == h or i == rows - 1; px[cx + dx, y0 + i] = A0 if edge else ((PINK if sole and i == 1 and abs(dx) <= 1 else TAN))
    leg(7, 28, 32); foot(9, 33, 3, 4)                                 # 왼발: 땅을 딛는다(발 맨 아래가 땅)
    leg(14, 28, 30); foot(16, 31, 3, 3, True)                         # 오른발: 뒤로 들려 한 걸음(발바닥이 보인다), 땅에서 두 줄 뜬다
    return Image.fromarray(G.scale2x(G.scale2x(np.array(cv))), 'RGBA'), cv

def pix(im, size=(24, 34), thr=120):
    """네모네모한 도트판(게임 화면 한 칸 단위, 24x34 = 게임 크기 12x17 × 2): 또렷한 네모 도트로 줄인다."""
    a = np.array(im.convert('RGBa').resize(size, Image.BOX).convert('RGBA')); a[..., 3] = np.where(a[..., 3] >= thr, 255, 0); return Image.fromarray(a, 'RGBA')

if __name__ == '__main__':
    im = build(); im.save(OUT); pix(im).save(OUT.replace('bear_hd', 'bear_px')); orig_hd().save(OUT.replace('bear_hd', 'bear_orig_hd')); si, small = walk_up(); si.save(OUT.replace('bear_hd', 'bear_sit_hd')); small.resize((small.width * 8, small.height * 8), Image.NEAREST).save(os.path.join(HERE, '..', 'maps', 'out', 'bear_sit_small.png')); S = 8; sh = Image.new('RGBA', (im.width * S + 20, im.height * S + 20), (44, 48, 64, 255)); sh.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (10, 10))
    sh.save(os.path.join(HERE, '..', 'maps', 'out', 'bear_hd_sheet.png')); print('bear_hd', im.size)
