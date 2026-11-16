#!/usr/bin/env python3
"""모험 구역(불규칙 지형): 네모 상자가 아니라 땅 모양 자체가 제각각인 공간. 땅 밖은 허공이고 가장자리는 낭떠러지 단면으로 떨어진다.
 park  폐 놀이공원 광장(큰 공간, 여러 갈래)      — 현실: 부모님과 갔던 나들이의 기억
 reed  황금 갈대밭(화면보다 훨씬 큰 들판)          — 현실: 학교 운동장·하굣길의 수군거림. 첫 조우: 나무인 줄 알았던 것이 일어난다
 ridge 낭떠러지 능선 길(길고 좁은 추격 길, 널다리) — 현실: 쫓기듯 뛰어 돌아오던 하굣길
 roofs 밤 도시 옥상들(네모 섬 + 널빤지)            — 현실: 아파트 베란다·난간(추락 지점)
 hall  허공에 뜬 학교 복도(긴 ㄱ자 추격 복도)       — 현실: 학교 복도와 사물함
사용: python3 tools/render_world.py -> maps/out/world_<이름>.png, _depth.png, _walk.png, world_nav.json"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT
from render_dream_area import bez, CELL
SPR = os.path.join(HERE, '..', 'art', 'out', 'sprites')
CROWN = Image.open(os.path.join(SPR, 'chaser.png')).convert('RGBA').crop((0, 0, 30, 30))   # 추격자의 나무 머리(수관+목): 가짜 나무도 똑같이 생겼다
PAD = 34

def mixa(a, b, f): return tuple(int(a[i] + (b[i] - a[i]) * max(0, min(1, f))) for i in range(3))
def nz(x, d, s=0):                                                              # 격자 잡음(배열)
    v = (np.floor(x).astype(np.int64) * 73856093) ^ (np.floor(d).astype(np.int64) * 19349663) ^ (s * 83492791); return ((v * 2654435761) >> 9) % 100 / 100.0
def col(mask_list, n):                                                          # [(조건, 색)...] 뒤의 것이 덮는다
    out = np.zeros((n, 3), np.int32)
    for m, c in mask_list: out[m] = c
    return out
def sd(shapes, x, d, wob=0):
    out = np.full(np.shape(x), 1e9)
    for s in shapes:
        if s[0] == 'rect': v = np.maximum(np.maximum(s[1] - x, x - s[3]), np.maximum(s[2] - d, d - s[4]))
        elif s[0] == 'circle': v = np.hypot(x - s[1], d - s[2]) - s[3] + wob * np.sin(d / 6.0 + x / 8.0)
        else:
            v = np.full(np.shape(x), 1e9)
            for (ax, ad), (bx, bd) in zip(s[1], s[1][1:]):
                dx, dd = bx - ax, bd - ad; t = np.clip(((x - ax) * dx + (d - ad) * dd) / (dx * dx + dd * dd or 1), 0, 1); v = np.minimum(v, np.hypot(x - (ax + dx * t), d - (ad + dd * t)))
            v = v - s[2] + wob * np.sin(d / 6.0 + x / 8.0)
        out = np.minimum(out, v)
    return out

# ---------------- 소품 ----------------
class K:
    def __init__(s, sc, rng): s.sc, s.rng, s.rects, s.block = sc, rng, [], []
    def B(s, x, d, w, dp, h, c, z0=0, sh=(.84, .68), solid=True):
        if solid and z0 < 20: s.rects.append((round(x, 1), round(d, 1), round(w, 1), round(dp, 1)))
        s.sc.jobs.append((d, lambda: s.sc.box(x, d, w, dp, h, c, dk(c, sh[0]), dk(c, sh[1]), z0=z0)))
    def F(s, x0, x1, z0, z1, c, d, back=False): s.sc.jobs.append((d + (.3 if back else -.3), lambda: s.sc.poly([(x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)], c)))
    def L(s, d0, d1, z0, z1, c, x): s.sc.jobs.append((max(d0, d1) + .3, lambda: s.sc.poly([(x, d0, z0), (x, d1, z0), (x, d1, z1), (x, d0, z1)], c)))
    def pale_tree(s, x, d):
        def f(): X, Y = s.sc.P(x, d, 0); s.sc.img.paste(CROWN, (X - 15, Y - 29), CROWN); s.sc.d.ellipse([X - 4, Y - 1, X + 4, Y + 1], fill=(40, 34, 44))
        s.sc.jobs.append((d, f)); s.block.append((x, d, 4))
    def reed(s, x, d, h):
        r = s.rng; st = [(r.randint(-4, 4), r.randint(-3, 3), r.random()) for _ in range(6)]
        def f():
            X, Y = s.sc.P(x, d, 0)
            for dx, dh, q in st:
                c = (222, 178, 76) if q > .5 else (186, 140, 54); s.sc.d.line([(X + dx, Y), (X + dx + (1 if q > .7 else 0), Y - h - dh)], fill=c)
                s.sc.d.line([(X + dx + (1 if q > .7 else 0), Y - h - dh), (X + dx + 1, Y - h - dh - 3)], fill=(246, 222, 150))
        s.sc.jobs.append((d, f))
    def rock(s, x, d, r, c=(120, 112, 120)):
        def f(): X, Y = s.sc.P(x, d, 0); s.sc.d.ellipse([X - r, Y - r, X + r, Y + r // 3], fill=dk(c, .7)); s.sc.d.ellipse([X - r + 1, Y - r, X + r - 2, Y - 1], fill=c); s.sc.d.line([(X - r + 3, Y - r + 2), (X, Y - r + 1)], fill=dk(c, 1.25))
        s.sc.jobs.append((d, f)); s.block.append((x, d, r))
    def atree(s, x, d, h, pal=((214, 110, 50), (236, 150, 60), (176, 76, 44))):
        def f():
            X, Y = s.sc.P(x, d, 0); s.sc.d.rectangle([X - 2, Y - h // 2, X + 1, Y], fill=(84, 58, 46)); s.sc.d.line([(X + 1, Y - h // 2), (X + 1, Y)], fill=(60, 40, 34))
            for (ox, oy, rr, c) in ((0, -h * .62, h * .3, pal[2]), (-h * .2, -h * .56, h * .22, pal[0]), (h * .18, -h * .66, h * .22, pal[0]), (-h * .04, -h * .8, h * .2, pal[1])): s.sc.d.ellipse([X + ox - rr, Y + oy - rr * .8, X + ox + rr, Y + oy + rr * .8], fill=c)
            for _ in range(8): px_ = X + s.rng.randint(-int(h * .36), int(h * .36)); py_ = Y - int(h * s.rng.uniform(.45, .9)); s.sc.d.point((px_, py_), fill=pal[1])
        s.sc.jobs.append((d, f)); s.block.append((x, d, 3))
    def desk(s, x, d):                                                         # 학교 책상과 의자(갈대에 반쯤 묻힘)
        for (lx, ld) in ((x, d), (x + 8, d), (x, d + 5), (x + 8, d + 5)): s.B(lx, ld, 1, 1, 8, (110, 110, 124), solid=False)
        s.B(x - 1, d - 1, 11, 8, 1.6, (196, 150, 96), z0=8); s.B(x + 2, d - 8, 6, 5, 5, (150, 110, 76)); s.B(x + 2, d - 4.4, 6, 1, 6, (150, 110, 76), z0=5, solid=False)
    def post(s, x, d, h=12, c=(120, 92, 70)): s.B(x, d, 2, 2, h, c, solid=False); s.block.append((x + 1, d + 1, 2))
    def glow(s, x, d, r, c, p): s.sc.glow(x, d, r, col=c, power=p)

# ---------------- 구역 정의 ----------------
def park_ground(x, d, e, n):
    t = (np.floor(x / 9) + np.floor(d / 9)) % 2 == 0
    return col([(t, (122, 104, 132)), (~t, (108, 92, 122)), (nz(x / 3, d / 3, 2) > .9, (150, 130, 150)), (e > -2, (176, 150, 170))], n)
def reed_ground(x, d, e, n):
    q = nz(x / 2, d / 2, 5)
    return col([(q >= 0, (150, 112, 52)), (q > .45, (170, 128, 58)), (q > .82, (196, 152, 70)), (nz(x / 7, d / 5, 9) > .86, (128, 94, 48)), (e > -2, (206, 166, 86))], n)
def ridge_ground(x, d, e, n):
    q = nz(x / 2, d / 2, 3); leaf = nz(x, d, 8)
    return col([(q >= 0, (150, 110, 78)), (q > .5, (164, 122, 84)), (leaf > .9, (226, 130, 56)), (leaf > .96, (240, 176, 70)), (e > -2, (190, 150, 104))], n)
def plank_ground(x, d, e, n):
    return col([(np.floor(x / 5) % 2 == 0, (150, 108, 70)), (np.floor(x / 5) % 2 == 1, (132, 94, 62)), (np.abs(x % 5) < .8, (84, 58, 42))], n)
def plank_ground_v(x, d, e, n):
    return col([(np.floor(d / 5) % 2 == 0, (150, 108, 70)), (np.floor(d / 5) % 2 == 1, (132, 94, 62)), (np.abs(d % 5) < .8, (84, 58, 42))], n)
def roof_ground(x, d, e, n):
    q = nz(x / 3, d / 3, 4)
    return col([(q >= 0, (70, 74, 100)), (q > .6, (78, 82, 108)), ((np.abs(x % 24) < .8) | (np.abs(d % 24) < .8), (56, 58, 84)), (e > -3, (112, 114, 140)), (e > -1.2, (150, 150, 172))], n)
def hall_ground(x, d, e, n):
    t = (np.floor(x / 10) + np.floor(d / 10)) % 2 == 0
    return col([(t, (150, 160, 140)), (~t, (128, 140, 124)), (nz(x / 2, d / 2, 6) > .93, (110, 120, 108)), (e > -1.2, (190, 196, 176))], n)

def face_rock(c0, c1):
    def f(X, k, ch): return mixa(c0 if (k // 4 + X // 9) % 2 else dk(c0, .88), c1, (k / ch) ** 1.1)
    return f
def face_building(X, k, ch):                                                    # 옥상 아래는 건물 벽: 불 꺼진 창 사이로 몇 개만 켜져 있다
    if k < 3: return (40, 42, 66)
    wx, wy = (X // 7), (k - 3) // 9; inwin = (X % 7) in (2, 3, 4) and ((k - 3) % 9) in (2, 3, 4, 5)
    base = mixa((58, 60, 88), (20, 20, 40), k / ch)
    if inwin: lit = (wx * 7 + wy * 13) % 11 == 0; return mixa((255, 214, 140) if lit else (30, 32, 54), (20, 20, 40), (k / ch) ** 1.6)
    return base

P1 = bez((0, 40), (60, 20), (90, 70), (150, 60)); P2 = bez((204, 60), (240, 56), (250, 110), (310, 104)) + bez((310, 104), (350, 100), (360, 60), (410, 64))[1:]; P3 = bez((460, 64), (500, 60), (520, 110), (600, 100))
AREAS = {
    'park': dict(H=70, shapes=[('circle', 190, 110, 68), ('rect', 176, 0, 204, 50), ('path', [(130, 110), (60, 124), (44, 150)], 13), ('circle', 44, 150, 30), ('path', [(250, 110), (320, 92), (376, 96)], 12), ('path', [(190, 170), (200, 200)], 15), ('circle', 204, 206, 34)],
                 ground=park_ground, face=face_rock((96, 80, 110), (30, 22, 44)), ch=30, sky=((30, 22, 52), (86, 56, 104)), start=(190, 8),
                 exits=[dict(at=(190, 3), to='office', spawn_abs=(71, 46)), dict(at=(372, 96), to='reed', spawn=(10, 104))]),
    'reed': dict(H=64, wob=3, shapes=[('circle', 120, 120, 88), ('circle', 250, 150, 98), ('circle', 370, 112, 80), ('path', [(0, 104), (50, 112)], 12), ('path', [(430, 110), (480, 122), (524, 102)], 11)],
                 ground=reed_ground, face=face_rock((120, 86, 50), (44, 26, 30)), ch=34, sky=((84, 50, 70), (236, 150, 80)), start=(10, 104),
                 exits=[dict(at=(4, 104), to='park', spawn=(364, 96)), dict(at=(520, 102), to='ridge', spawn=(10, 38))], chaser=dict(x=296, d=176, radius=72)),
    'ridge': dict(H=64, wob=1.5, mood='dark', chase=True, shapes=[('path', P1, 10), ('path', P2, 10), ('path', P3, 10), ('rect', 146, 54, 208, 66), ('rect', 406, 58, 464, 70), ('circle', 92, 52, 22), ('circle', 310, 104, 24), ('circle', 522, 92, 22)],
                  zones=[(('rect', 158, 55, 196, 65), plank_ground), (('rect', 418, 59, 452, 69), plank_ground)],
                  ground=ridge_ground, face=face_rock((132, 92, 62), (36, 20, 30)), ch=46, sky=((40, 22, 48), (170, 70, 60)), start=(10, 38),
                  exits=[dict(at=(4, 40), to='reed', spawn=(510, 104)), dict(at=(596, 100), to='roofs', spawn=(10, 36))]),
    'roofs': dict(H=70, shapes=[('rect', 0, 0, 90, 70), ('rect', 84, 28, 124, 40), ('rect', 118, 10, 190, 90), ('rect', 148, 84, 160, 126), ('rect', 110, 120, 230, 180), ('rect', 224, 138, 268, 150), ('rect', 262, 110, 330, 170)],
                  zones=[(('rect', 90, 27, 118, 41), plank_ground), (('rect', 147, 90, 161, 120), plank_ground_v), (('rect', 230, 137, 262, 151), plank_ground)],
                  ground=roof_ground, face=face_building, ch=90, sky=((10, 12, 30), (40, 46, 86)), start=(10, 36),
                  exits=[dict(at=(4, 36), to='ridge', spawn=(586, 100)), dict(at=(324, 140), to='hall', spawn=(10, 14))]),
    'hall': dict(H=70, mood='dark', chase=True, shapes=[('rect', 0, 0, 420, 28), ('rect', 392, 28, 420, 150), ('rect', 392, 150, 700, 178)],
                 ground=hall_ground, face=face_rock((70, 76, 70), (10, 8, 14)), ch=26, sky=((8, 6, 12), (20, 16, 26)), start=(10, 14),
                 exits=[dict(at=(4, 14), to='roofs', spawn=(314, 140)), dict(at=(694, 164), to=None, endMsg='복도 끝의 문 — 여기서부터는 아직 만들지 않았어요', side='right')]),
}

def props(name, k, tr, inside, rng):
    sc = k.sc; T = lambda x, d: tr((x, d))
    if name == 'park':
        def ferris():                                                           # 멈춘 관람차(뒤쪽 하늘에 크게)
            cx, cy = sc.P(*T(204, 222), 58); R = 44
            sc.d.line([sc.P(*T(190, 216), 0), (cx, cy)], fill=(96, 84, 120), width=2); sc.d.line([sc.P(*T(222, 216), 0), (cx, cy)], fill=(96, 84, 120), width=2)
            sc.d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(150, 130, 170)); sc.d.ellipse([cx - R + 3, cy - R + 3, cx + R - 3, cy + R - 3], outline=(96, 84, 120))
            for i in range(10):
                a = i * math.tau / 10 + .2; ex, ey = cx + R * math.cos(a), cy + R * math.sin(a); sc.d.line([(cx, cy), (ex, ey)], fill=(110, 96, 136))
                c = ((214, 90, 100), (240, 200, 110), (110, 160, 200), (150, 110, 170))[i % 4]; sc.d.rectangle([ex - 3, ey, ex + 3, ey + 5], fill=dk(c, .8 if i % 3 else .45)); sc.d.rectangle([ex - 2, ey + 1, ex + 2, ey + 3], fill=(40, 34, 60) if i % 3 else (255, 220, 150))
        sc.jobs.append((400, ferris))
        cx, cd = T(44, 156)                                                     # 회전목마: 줄무늬 지붕, 기둥, 멈춘 말
        def carousel():
            X, Y = sc.P(cx, cd, 0); sc.d.ellipse([X - 22, Y - 7, X + 22, Y + 7], fill=(150, 110, 130)); sc.d.ellipse([X - 20, Y - 8, X + 20, Y + 4], fill=(196, 160, 150))
            for i in range(-18, 19, 9): sc.d.line([(X + i, Y - 2), (X + i, Y - 30)], fill=(240, 220, 160))
            for i, c in ((-12, (240, 240, 240)), (2, (214, 150, 150)), (13, (240, 240, 240))): sc.d.rectangle([X + i - 3, Y - 14, X + i + 3, Y - 10], fill=c); sc.d.rectangle([X + i + 2, Y - 17, X + i + 4, Y - 13], fill=c); sc.d.line([(X + i - 2, Y - 10), (X + i - 2, Y - 6)], fill=c); sc.d.line([(X + i + 2, Y - 10), (X + i + 2, Y - 6)], fill=c)
            for j in range(12): c = (214, 90, 100) if j % 2 else (244, 232, 210); sc.d.polygon([(X, Y - 48), (X - 24 + j * 4, Y - 30), (X - 20 + j * 4, Y - 30)], fill=dk(c, 1 - abs(j - 5.5) * .04))
            sc.d.rectangle([X - 24, Y - 31, X + 24, Y - 28], fill=(250, 214, 120)); sc.d.rectangle([X - 1, Y - 53, X + 1, Y - 48], fill=(250, 214, 120))
        sc.jobs.append((cd - 8, carousel)); k.rects.append((cx - 20, cd - 8, 40, 14))
        for (bx, bd, c) in ((132, 150, (214, 90, 100)), (236, 150, (90, 150, 190)), (140, 62, (240, 200, 110))):       # 줄무늬 가게
            x, d = T(bx, bd); k.B(x, d, 18, 10, 16, (236, 220, 200)); k.B(x - 1, d - 2, 20, 13, 3, c, z0=16, solid=False)
            for i in range(0, 18, 4): k.F(x + i, x + i + 2, 0, 9, c, d)
            k.F(x + 3, x + 15, 10, 15, (40, 34, 60), d)
        for (lx, ld) in ((160, 60), (220, 60), (140, 120), (240, 126), (190, 160), (90, 128), (300, 100)):
            x, d = T(lx, ld); k.post(x, d, 20, (96, 84, 120)); k.B(x - 1, d - 1, 4, 4, 3, (255, 226, 160), z0=20, solid=False); k.glow(x + 1, d, 26, (255, 214, 150), .4)
        x, d = T(190, 110); k.B(x - 7, d - 5, 14, 10, 4, (150, 130, 160)); k.B(x - 2, d - 1, 4, 3, 10, (176, 156, 186), z0=4, solid=False)   # 마른 분수
        for (bx, bd, c) in ((176, 84, (214, 90, 100)), (212, 132, (240, 200, 110)), (64, 132, (110, 160, 200))):         # 줄 끊긴 풍선
            x, d = T(bx, bd)
            def bal(x=x, d=d, c=c): X, Y = sc.P(x, d, 0); sc.d.line([(X, Y), (X + 1, Y - 16)], fill=(200, 190, 210)); sc.d.ellipse([X - 3, Y - 24, X + 4, Y - 16], fill=c); sc.d.point((X - 1, Y - 22), fill=(255, 255, 255))
            sc.jobs.append((d, bal))
        x, d = T(176, 44); k.post(x, d, 30, (250, 214, 120)); x2, _ = T(202, 44); k.post(x2, d, 30, (250, 214, 120)); k.F(x, x2 + 2, 30, 36, (214, 90, 100), d); k.F(x + 4, x2 - 2, 31.5, 34.5, (250, 240, 200), d)   # 입구 아치
    elif name == 'reed':
        pts = []
        for _ in range(4000):
            x, d = rng.uniform(0, 530), rng.uniform(20, 250)
            if inside(x, d) < -5 and all(abs(x - a) > 11 or abs(d - b) > 7 for a, b in pts): pts.append((x, d))
            if len(pts) > 230: break
        for (x, d) in pts: k.reed(*T(x, d), rng.choice((9, 11, 13, 16)))
        for (x, d) in ((96, 150), (150, 84), (196, 200), (262, 96), (296, 176), (372, 160), (404, 76), (166, 176)):
            if (x, d) != (296, 176): k.pale_tree(*T(x, d))                      # (296,176) 자리는 진짜: 엔진이 그린다
        for (x, d) in ((130, 130), (250, 190), (350, 96)): k.desk(*T(x, d))
        for (x, d) in ((60, 118), (190, 110), (440, 118)): k.rock(*T(x, d), 4, (150, 120, 90))
    elif name == 'ridge':
        for (x, d, h) in ((84, 66, 34), (104, 44, 28), (298, 120, 36), (326, 96, 28), (514, 106, 34), (536, 84, 28)): k.atree(*T(x, d), h, pal=((150, 60, 44), (196, 96, 50), (104, 40, 44)))
        for (x, d) in ((158, 53), (158, 65), (196, 53), (196, 65), (418, 57), (418, 69), (452, 57), (452, 69)): k.post(*T(x, d), 9)
        for (x, d) in ((60, 34), (240, 72), (360, 76), (470, 60), (570, 104)): k.rock(*T(x, d), 3, (130, 104, 96))
        for (x, d) in ((92, 52), (310, 104), (522, 92)): k.glow(*T(x, d), 30, (255, 150, 90), .22)
    elif name == 'roofs':
        x, d = T(128, 66); k.B(x, d, 16, 14, 4, (60, 62, 86)); k.B(x + 1, d + 1, 14, 12, 18, (110, 104, 120), z0=4, solid=False); k.B(x, d, 16, 14, 2, (84, 80, 100), z0=22, solid=False)      # 물탱크
        for (x, d) in ((60, 52), (170, 30), (206, 160), (290, 152)): xx, dd = T(x, d); k.B(xx, dd, 10, 7, 7, (150, 154, 170)); k.F(xx + 2, xx + 8, 2, 5, (60, 62, 86), dd)                       # 실외기
        x, d = T(120, 162); k.B(x, d, 22, 14, 26, (96, 98, 124)); k.F(x + 7, x + 15, 0, 20, (40, 42, 66), d); k.F(x + 8, x + 14, 0, 19, (255, 206, 130), d); k.glow(x + 11, d - 6, 26, (255, 200, 120), .5)   # 계단실(불 켜진 문)
        for (x, d, sd_) in ((20, 60, 1), (200, 130, 1), (276, 160, 1)): sc.lamp(*T(x, d), h=34, side=sd_); k.block.append((*T(x, d), 2))
        x, d = T(30, 12); k.post(x, d, 26, (58, 62, 88)); x2, _ = T(72, 12); k.post(x2, d, 26, (58, 62, 88))
        def line(x=x, x2=x2, d=d):
            a = sc.P(x + 1, d, 26); b = sc.P(x2 + 1, d, 26); sc.d.line([a, b], fill=(150, 150, 172))
            for i, c in enumerate(((230, 230, 236), (150, 90, 100), (220, 220, 230))): X = a[0] + 8 + i * 11; sc.d.rectangle([X, a[1] + 1, X + 6, a[1] + 9], fill=c)
        sc.jobs.append((d, line))
        for (x, d) in ((84, 6), (186, 86), (326, 114)): xx, dd = T(x, d); k.post(xx, dd, 22, (70, 74, 100))
    elif name == 'hall':
        WALL, WD = (176, 170, 150), (120, 130, 116)
        def wall(x0, x1, d, seed):
            a, _ = T(x0, d); b, dd = T(x1, d); k.F(a, b, 0, 46, WALL, dd, back=True); k.F(a, b, 0, 14, WD, dd, back=True); k.F(a, b, 44, 46, (90, 96, 88), dd, back=True); r = random.Random(seed); x = a + 6
            while x < b - 20:
                kind = r.choice('LLDW')
                if kind == 'L':                                                 # 사물함 줄
                    for i in range(4): k.F(x + i * 5, x + i * 5 + 4.4, 1, 30, (96, 124, 140) if (i + seed) % 3 else (120, 96, 100), dd, back=True); k.F(x + i * 5 + 1, x + i * 5 + 3.4, 24, 26, (40, 50, 60), dd, back=True)
                    x += 26
                elif kind == 'D': k.F(x, x + 13, 0, 36, (70, 60, 56), dd, back=True); k.F(x + 1, x + 12, 0, 35, (120, 92, 70), dd, back=True); k.F(x + 3, x + 10, 22, 32, (24, 26, 40), dd, back=True); x += 22
                else: k.F(x, x + 20, 18, 36, (210, 206, 186), dd, back=True); k.F(x + 1, x + 19, 19, 35, (14, 16, 34), dd, back=True); k.F(x + 9.6, x + 10.4, 19, 35, (210, 206, 186), dd, back=True); x += 30
                x += r.choice((6, 10, 16))
        wall(0, 392, 28, 1); wall(392, 700, 178, 2)
        x, d0 = T(392, 28); _, d1 = T(392, 150); k.L(d0, d1, 0, 46, dk(WALL, .86), x); k.L(d0, d1, 0, 14, dk(WD, .86), x); k.L(d0, d1, 44, 46, (80, 86, 78), x)
        for (x, d) in ((60, 14), (200, 14), (340, 14), (406, 90), (480, 164), (620, 164)): k.glow(*T(x, d), 34, (220, 236, 200), .34)
        for (x, d) in ((150, 22), (300, 6), (410, 60), (560, 172)):               # 실내화, 넘어진 의자
            xx, dd = T(x, d); k.B(xx, dd, 3, 2, 1, (240, 240, 240), solid=False); k.B(xx + 4, dd + 1, 3, 2, 1, (240, 240, 240), solid=False)
        xx, dd = T(686, 152); k.B(xx, dd, 12, 3, 30, (120, 92, 70), solid=False); k.F(xx + 2, xx + 10, 3, 27, (255, 232, 180), dd); k.glow(xx + 6, dd - 4, 30, (255, 226, 170), .5)   # 끝의 문

def build(name):
    A = AREAS[name]; sh = A['shapes']; xs, ds = [], []
    for s in sh:
        if s[0] == 'rect': xs += [s[1], s[3]]; ds += [s[2], s[4]]
        elif s[0] == 'circle': xs += [s[1] - s[3], s[1] + s[3]]; ds += [s[2] - s[3], s[2] + s[3]]
        else: xs += [p[0] - s[2] for p in s[1]] + [p[0] + s[2] for p in s[1]]; ds += [p[1] - s[2] for p in s[1]] + [p[1] + s[2] for p in s[1]]
    m = 8; x0, d0 = min(xs) - m, min(ds) - m; W, D = int(max(xs) + m - x0), int(max(ds) + m - d0); wob = A.get('wob', 0)
    tr = lambda p: (p[0] - x0, p[1] - d0)
    sc = Scene(W, D, A['H'], pad=min(A['ch'] + 6, 60)); CW, CH = sc.CW, sc.CH
    YY, XX = np.mgrid[0:CH, 0:CW]; dd = (sc.Y0 - YY - .5) * 2; xx = XX + .5 - sc.X0 - .5 * dd
    e = sd(sh, xx + x0, dd + d0, wob); land = e < 0
    t = (YY / CH)[..., None]; top, bot = np.array(A['sky'][0]), np.array(A['sky'][1]); img = (top + (bot - top) * (np.round(t * 14) / 14)).astype(np.int32)
    rng = random.Random(hash(name) % 1000 if False else sum(map(ord, name)))
    for _ in range(CW * CH // 500):                                             # 허공의 먼지·별
        X, Y = rng.randrange(CW), rng.randrange(CH); img[Y, X] = np.minimum(255, img[Y, X] + 60)
    wx, wd, we = (xx + x0)[land], (dd + d0)[land], e[land]; img[land] = A['ground'](wx, wd, we, wx.size)
    for zs, gfn in A.get('zones', []):
        zm = land & (sd([zs], xx + x0, dd + d0) < 0); img[zm] = gfn((xx + x0)[zm], (dd + d0)[zm], e[zm], int(zm.sum()))
    ch = A['ch']; painted = land.copy(); face = A['face']                        # 낭떠러지 단면: 땅 가장자리 아래로 곧게 떨어진다
    for kk in range(1, ch + 1):
        sh_ = np.zeros_like(land); sh_[kk:] = land[:-kk]; m_ = sh_ & ~painted
        ys, xs_ = np.nonzero(m_)
        for Y, X in zip(ys, xs_): img[Y, X] = face(int(X), kk, ch)
        painted |= m_
    sc.img = Image.fromarray(img.astype(np.uint8), 'RGB'); sc.d = ImageDraw.Draw(sc.img); sc.px = sc.img.load()
    inside = lambda x, d: float(sd(sh, np.array(x, float), np.array(d, float), wob))
    k = K(sc, rng); props(name, k, tr, inside, rng)
    ex = []
    for E in A['exits']:
        lx, ld = tr(E['at']); sc.glow(lx, ld, 18, col=(255, 255, 255), power=.3)
        ex.append({'zone': (lx - 5, lx + 5, ld - 5, ld + 5), 'to': E['to'], 'spawn': E.get('spawn_abs'), 'spawn_w': E.get('spawn'), 'endMsg': E.get('endMsg'), 'side': E.get('side')})
    dep = Image.new('L', sc.img.size, 255)
    for depth, f in sorted(sc.jobs, key=lambda j: -j[0]):
        before = sc.img.copy(); f()
        if depth < 390:
            diff = ImageChops.difference(sc.img, before).convert('L').point(lambda v: 255 if v else 0); dep.paste(int(max(0, min(254, round((depth + 2) * 3)))) if depth < 82 else 254, (0, 0), diff)
    gw, gh = math.ceil(W / CELL), math.ceil(D / CELL); gx, gd = np.meshgrid((np.arange(gw) + .5) * CELL, (np.arange(gh) + .5) * CELL)
    ok = sd(sh, gx + x0, gd + d0, wob) < -2.6
    for (bx, bd, br) in k.block: ok &= ~((np.abs(gx - bx) < br + 1) & (np.abs(gd - bd) < br))
    for E in ex: z = E['zone']; ok |= (np.hypot(gx - (z[0] + z[1]) / 2, gd - (z[2] + z[3]) / 2) < 6) & (sd(sh, gx + x0, gd + d0, wob) < 1)
    mask = Image.fromarray((ok * 255).astype(np.uint8), 'L')
    meta = {'W': W, 'D': D, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': CW, 'CH': CH, 'rects': k.rects, 'exits': ex, 'start': tr(A['start']), 'origin': (x0, d0), 'open': True}
    if A.get('mood'): meta['mood'] = A['mood']
    if A.get('chase'): meta['chase'] = True
    if A.get('chaser'): c = A['chaser']; cx, cd = tr((c['x'], c['d'])); meta['chaser'] = {'x': cx, 'd': cd, 'radius': c['radius']}
    return sc.img, dep, mask, meta

def main():
    nav = {}; only = sys.argv[1:]
    for name in AREAS:
        im, dep, mask, meta = build(name); nav[name] = meta
        im.save(os.path.join(OUT, 'world_%s.png' % name)); dep.save(os.path.join(OUT, 'world_%s_depth.png' % name)); mask.save(os.path.join(OUT, 'world_%s_walk.png' % name)); im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(OUT, 'world_%s_x2.png' % name))
        print(name, im.size)
    for name, meta in nav.items():
        for e in meta['exits']:
            w = e.pop('spawn_w', None)
            if w and e['to'] in nav: o = nav[e['to']]['origin']; e['spawn'] = (round(w[0] - o[0], 1), round(w[1] - o[1], 1))
    json.dump(nav, open(os.path.join(OUT, 'world_nav.json'), 'w'), ensure_ascii=False)
if __name__ == '__main__': main()
