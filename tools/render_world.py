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
BODY = Image.open(os.path.join(SPR, 'chaser.png')).convert('RGBA').crop((0, 30, 30, 64))

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
def woods_ground(x, d, e, n):
    q = nz(x / 2, d / 2, 7)
    return col([(q >= 0, (34, 46, 48)), (q > .5, (40, 54, 54)), (q > .86, (52, 70, 62)), (nz(x / 6, d / 4, 3) > .84, (28, 36, 42)), (nz(x, d, 11) > .975, (120, 130, 110)), (e > -2, (62, 80, 72))], n)
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
    'park': dict(H=70, shapes=[('circle', 190, 110, 78), ('rect', 164, 0, 216, 50), ('path', [(130, 110), (60, 124), (44, 150)], 24), ('circle', 44, 150, 40), ('path', [(250, 110), (320, 92), (376, 96)], 24), ('path', [(190, 170), (200, 200)], 26), ('circle', 204, 206, 44)],
                 ground=park_ground, face=face_rock((96, 80, 110), (30, 22, 44)), ch=30, sky=((30, 22, 52), (86, 56, 104)), start=(190, 8), box=dict(kind='hills', sil=(44, 32, 66), floor=(26, 20, 40)),
                 exits=[dict(at=(190, 3), to='office', spawn_abs=(71, 46)), dict(at=(372, 96), to='reed', spawn=(10, 104))]),
    'reed': dict(H=64, wob=3, shapes=[('circle', 120, 120, 88), ('circle', 250, 150, 98), ('circle', 370, 112, 80), ('path', [(0, 104), (50, 112)], 24), ('path', [(430, 110), (480, 122), (524, 102)], 24)],
                 ground=reed_ground, face=face_rock((120, 86, 50), (44, 26, 30)), ch=34, sky=((84, 50, 70), (236, 150, 80)), start=(10, 104), box=dict(kind='hills', sil=(140, 92, 54), floor=(60, 40, 40)),
                 exits=[dict(at=(4, 104), to='park', spawn=(364, 96)), dict(at=(520, 102), to='woods', spawn=(10, 60))]),
    'woods': dict(H=84, wob=3, shapes=[('path', bez((0, 60), (60, 40), (90, 100), (140, 90)) + bez((140, 90), (200, 80), (230, 40), (300, 66))[1:] + bez((300, 66), (350, 80), (370, 120), (420, 106))[1:] + bez((420, 106), (470, 96), (490, 70), (530, 80))[1:], 28), ('circle', 140, 88, 50), ('circle', 300, 68, 46), ('circle', 420, 106, 58)],
                  ground=woods_ground, face=face_rock((40, 44, 50), (8, 8, 14)), ch=34, sky=((6, 8, 14), (22, 34, 40)), start=(10, 60), box=dict(kind='trees'),
                  exits=[dict(at=(4, 60), to='reed', spawn=(510, 104)), dict(at=(526, 80), to='ridge', spawn=(10, 38))], chaser=dict(spots=((120, 112), (164, 68), (252, 58), (300, 94), (380, 102), (436, 126), (484, 98)), radius=52)),
    'ridge': dict(H=64, wob=1.5, mood='dark', chase=True, shapes=[('path', P1, 19), ('path', P2, 19), ('path', P3, 19), ('rect', 146, 50, 208, 70), ('rect', 406, 54, 464, 74), ('circle', 92, 52, 32), ('circle', 310, 104, 34), ('circle', 522, 92, 32)],
                  zones=[(('rect', 172, 49, 184, 71), plank_ground), (('rect', 432, 53, 444, 75), plank_ground)],
                  ground=ridge_ground, face=face_rock((132, 92, 62), (36, 20, 30)), ch=46, sky=((40, 22, 48), (170, 70, 60)), start=(10, 38), box=dict(kind='hills', sil=(74, 36, 46), floor=(34, 20, 30)),
                  exits=[dict(at=(4, 40), to='woods', spawn=(516, 80)), dict(at=(596, 100), to='roofs', spawn=(10, 36))]),
    'roofs': dict(H=70, shapes=[('rect', 0, 0, 90, 70), ('rect', 84, 24, 124, 44), ('rect', 118, 10, 190, 90), ('rect', 144, 84, 164, 126), ('rect', 110, 120, 230, 180), ('rect', 224, 134, 268, 154), ('rect', 262, 110, 330, 170)],
                  zones=[(('rect', 90, 23, 118, 45), plank_ground), (('rect', 143, 90, 165, 120), plank_ground_v), (('rect', 230, 133, 262, 155), plank_ground)],
                  ground=roof_ground, face=face_building, ch=90, sky=((10, 12, 30), (40, 46, 86)), start=(10, 36), box=dict(kind='city', sil=(20, 22, 44), floor=(14, 16, 32)),
                  exits=[dict(at=(4, 36), to='ridge', spawn=(586, 100)), dict(at=(324, 140), to='hall', spawn=(10, 22))]),
    'hall': dict(H=70, mood='dark', chase=True, shapes=[('rect', 0, 0, 440, 46), ('rect', 392, 46, 440, 150), ('rect', 392, 150, 700, 196)],
                 ground=hall_ground, face=face_rock((70, 76, 70), (10, 8, 14)), ch=26, sky=((8, 6, 12), (20, 16, 26)), start=(10, 22), box=dict(kind='none', floor=(14, 12, 18)),
                 exits=[dict(at=(4, 22), to='roofs', spawn=(314, 140)), dict(at=(694, 172), to=None, endMsg='복도 끝의 문 — 여기서부터는 아직 만들지 않았어요', side='right')]),
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
        for (x, d) in ((130, 130), (250, 190), (350, 96)): k.desk(*T(x, d))
        for (x, d) in ((60, 118), (190, 110), (440, 118)): k.rock(*T(x, d), 4, (150, 120, 90))
    elif name == 'woods':
        def dtree(x, d, h):                                                     # 어두운 숲의 나무: 한 그루씩 다르게. 사람 형상을 닮은 줄기(갈라진 뿌리, 늘어진 가지, 옹이구멍), 몇 그루는 잎이 없다
            r = random.Random(int(x * 7 + d * 131)); w = r.choice((2, 2, 3)); lean = r.choice((-3, -2, 0, 0, 2, 3)); top = r.choice('CCCCBBS'); legs = r.random() < .6; arms = r.choice((0, 1, 1, 2)); knot = r.random() < .45; fl = r.choice((-1, 1))
            DK, MD, LT = (40, 34, 48), (62, 54, 70), (96, 86, 102)
            def f():
                X, Y = sc.P(x, d, 0); D_ = sc.d; tx = lambda z: X + round(lean * (z / h) ** 2)
                sc.d.ellipse([X - 5, Y - 1, X + 5, Y + 1], fill=(22, 28, 32))
                z0 = 0
                if legs:                                                        # 밑동이 두 갈래 뿌리로 갈라져 선다
                    z0 = r.choice((7, 9, 12)); D_.line([(X - w - 2, Y), (X - 1, Y - z0)], fill=DK, width=2); D_.line([(X + w + 2, Y), (X + 1, Y - z0)], fill=DK, width=2); D_.point((X - w - 2, Y - 1), fill=MD)
                for z in range(z0, h):                                           # 줄기: 위로 갈수록 가늘고, 껍질 결
                    ww = w if z < h * .7 else max(1, w - 1); cx = tx(z); D_.line([(cx - ww, Y - z), (cx + ww, Y - z)], fill=DK)
                    if (z * 7 + int(x)) % 5 == 0: D_.point((cx - ww + 1, Y - z), fill=MD)
                    if (z * 3 + int(d)) % 11 == 0: D_.point((cx + ww - 1, Y - z), fill=LT)
                sh = int(h * r.uniform(.56, .7))
                for a_ in range(arms):                                          # 어깨 높이에서 아래로 늘어진 가지
                    sd_ = fl if a_ == 0 else -fl; ax = tx(sh) + sd_ * w; ln = r.randint(12, 22); ex = ax + sd_ * r.randint(4, 7)
                    D_.line([(ax, Y - sh), (ex, Y - sh + 3)], fill=DK, width=2); D_.line([(ex, Y - sh + 3), (ex + sd_, Y - sh + ln)], fill=DK); D_.point((ex, Y - sh + ln // 2), fill=MD)
                    if r.random() < .5: D_.line([(ex + sd_, Y - sh + ln), (ex + sd_ * 2, Y - sh + ln + 3)], fill=MD)
                if knot: kz = int(h * .5); cx = tx(kz); D_.rectangle([cx - 1, Y - kz - 2, cx + 1, Y - kz + 1], fill=(14, 12, 20)); D_.point((cx - 1, Y - kz - 3), fill=LT); D_.point((cx + 1, Y - kz - 3), fill=LT)
                cx = tx(h)
                if top == 'C':                                                  # 수관
                    for (ox, oy, rr, c) in ((0, 0, h * .26, (16, 30, 34)), (-h * .17, h * .1, h * .2, (22, 40, 42)), (h * .16, -h * .03, h * .2, (22, 40, 42)), (r.choice((-3, 0, 3)), -h * .15, h * .16, (30, 52, 52))): D_.ellipse([cx + ox - rr, Y - h + oy - rr * .75, cx + ox + rr, Y - h + oy + rr * .75], fill=c)
                elif top == 'B':                                                # 잎 없는 가지 끝
                    for (bx_, by_) in ((-7, -9), (6, -11), (-2, -14), (9, -5), (-10, -4)): D_.line([(cx, Y - h + 2), (cx + bx_, Y - h + by_)], fill=DK); D_.line([(cx + bx_, Y - h + by_), (cx + bx_ + (2 if bx_ > 0 else -2), Y - h + by_ - 4)], fill=MD)
                else: D_.polygon([(cx - w, Y - h), (cx + w, Y - h), (cx + w, Y - h - 3), (cx, Y - h - 1), (cx - w, Y - h - 5)], fill=DK); D_.point((cx - w, Y - h - 5), fill=LT)   # 부러진 그루터기 끝
            sc.jobs.append((d, f)); k.block.append((x, d, 3))
        pts = [T(*q) for q in AREAS['woods']['chaser']['spots']]; k.block += [(a, b, 4) for a, b in pts]                                                     # 진짜가 설 자리(엔진이 그린다): 몸통이 줄기처럼 보이고 머리는 어두운 수관에 가려져 있다
        tr_ = list(pts)
        for _ in range(3000):
            x, d = rng.uniform(0, 540), rng.uniform(10, 170); e = inside(x, d)
            lx, ld = T(x, d)
            if -11 < e < -4 and (inside(x, d - 16) < 0 or rng.random() < .22) and all(math.hypot(lx - a, (ld - b) * 1.6) > 26 for a, b in tr_): tr_.append((lx, ld)); dtree(lx, ld, rng.choice((38, 44, 50, 50, 56, 62)))
        for (x, d) in ((140, 88), (300, 68), (420, 106)): k.glow(*T(x, d), 44, (150, 190, 200), .16)
        for (x, d) in ((70, 56), (212, 70), (360, 98), (500, 82)): k.rock(*T(x, d), 3, (60, 66, 72))
    elif name == 'ridge':
        for (x, d, h) in ((84, 66, 34), (104, 44, 28), (298, 120, 36), (326, 96, 28), (514, 106, 34), (536, 84, 28)): k.atree(*T(x, d), h, pal=((150, 60, 44), (196, 96, 50), (104, 40, 44)))
        for (x, d) in ((171, 48), (171, 70), (184, 48), (184, 70), (431, 52), (431, 74), (444, 52), (444, 74)): k.post(*T(x, d), 9)
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
        wall(0, 392, 46, 1); wall(392, 700, 196, 2)
        x, d0 = T(392, 46); _, d1 = T(392, 150); k.L(d0, d1, 0, 46, dk(WALL, .86), x); k.L(d0, d1, 0, 14, dk(WD, .86), x); k.L(d0, d1, 44, 46, (80, 86, 78), x)
        for (x, d) in ((60, 22), (200, 22), (340, 22), (416, 96), (480, 172), (620, 172)): k.glow(*T(x, d), 34, (220, 236, 200), .34)
        for (x, d) in ((150, 36), (300, 8), (420, 70), (560, 186)):               # 실내화, 넘어진 의자
            xx, dd = T(x, d); k.B(xx, dd, 3, 2, 1, (240, 240, 240), solid=False); k.B(xx + 4, dd + 1, 3, 2, 1, (240, 240, 240), solid=False)
        xx, dd = T(686, 160); k.B(xx, dd, 12, 3, 30, (120, 92, 70), solid=False); k.F(xx + 2, xx + 10, 3, 27, (255, 232, 180), dd); k.glow(xx + 6, dd - 4, 30, (255, 226, 170), .5)   # 끝의 문

def build(name):
    A = AREAS[name]; sh = A['shapes']; xs, ds = [], []
    for s in sh:
        if s[0] == 'rect': xs += [s[1], s[3]]; ds += [s[2], s[4]]
        elif s[0] == 'circle': xs += [s[1] - s[3], s[1] + s[3]]; ds += [s[2] - s[3], s[2] + s[3]]
        else: xs += [p[0] - s[2] for p in s[1]] + [p[0] + s[2] for p in s[1]]; ds += [p[1] - s[2] for p in s[1]] + [p[1] + s[2] for p in s[1]]
    m = 8; x0, d0 = min(xs) - m, min(ds) - m; W, D = int(max(xs) + m - x0), int(max(ds) + m - d0); wob = A.get('wob', 0)
    tr = lambda p: (p[0] - x0, p[1] - d0)
    BOX = A.get('box'); sc = Scene(W, D, A['H'], pad=min(A['ch'] + 6, 60) + (10 if BOX else 0)); CW, CH = sc.CW, sc.CH
    YY, XX = np.mgrid[0:CH, 0:CW]; dd = (sc.Y0 - YY - .5) * 2; xx = XX + .5 - sc.X0 - .5 * dd
    e = sd(sh, xx + x0, dd + d0, wob); land = e < 0
    t = (YY / CH)[..., None]; top, bot = np.array(A['sky'][0]), np.array(A['sky'][1]); img = (top + (bot - top) * (np.round(t * 14) / 14)).astype(np.int32)
    rng = random.Random(hash(name) % 1000 if False else sum(map(ord, name)))
    for _ in range(CW * CH // 500):                                             # 허공의 먼지·별
        X, Y = rng.randrange(CW), rng.randrange(CH); img[Y, X] = np.minimum(255, img[Y, X] + 60)
    if BOX:                                                                      # 꿈 상자: 땅을 뒷벽·왼쪽 벽·바닥판이 있는 상자 안에 넣는다(앞과 오른쪽은 뚫려 있다). 하늘은 벽에 그린 그림이 된다
        ch_, H_ = min(A['ch'], 50), A['H']; kind = BOX.get('kind', 'trees'); img[:] = BOX.get('out', (12, 9, 16)); top3, bot3 = np.array(A['sky'][0], float), np.array(A['sky'][1], float); sil = np.array(BOX.get('sil', (12, 20, 24)), float); fl = np.array(BOX.get('floor', (20, 24, 30)), float)
        df = (sc.Y0 + ch_ - YY - .5) * 2; xf = XX + .5 - sc.X0 - .5 * df; fm = (xf >= 0) & (xf < W) & (df >= 0) & (df < D)                     # 바닥판(z = -ch)
        grid = (np.abs(xf % 16) < 1) | (np.abs(df % 16) < 1); fog = np.clip(1 - np.hypot((xf - W / 2) / (W / 2), (df - D / 2) / (D / 2)), 0, 1)[..., None]
        fc = fl + (np.array((40, 52, 56)) - fl) * fog * .5; fc = np.where(grid[..., None], fc * 1.18, fc); img[fm] = fc[fm]
        def wall(u, z, m_, shade, seed):                                          # u: 벽을 따라가는 좌표, z: 높이
            k = np.clip(z / H_, 0, 1)[..., None]; c = bot3 + (top3 - bot3) * (np.round(k * 12) / 12)
            hgt = (15 + 8 * np.sin(u / 9.0 + seed) + 6 * np.sin(u / 3.7 + 1 + seed) + 3 * np.sin(u / 1.9)) if kind == 'trees' else (12 + 9 * np.sin(u / 41.0 + seed) + 5 * np.sin(u / 17.0 + 2 * seed)) if kind == 'hills' else (10 + 26 * nz(np.floor(u / 13), np.zeros_like(u), 3 + seed)) if kind == 'city' else np.full(np.shape(u), -1.0); c = np.where(((z >= 0) & (z < hgt))[..., None], sil[None, None, :], c)   # 벽에 그린 먼 숲의 윤곽
            trunk_ = (np.abs((u + seed * 7) % 13) < 1.2) & (z >= 0) & (z < hgt + 6) & (kind == 'trees'); c = np.where(trunk_[..., None], (sil * .8)[None, None, :], c)
            if kind == 'city': lit = (np.abs(u % 13 - 6) < 4) & (np.floor(u) % 3 == 0) & (np.floor(z) % 5 == 2) & (z > 2) & (z < hgt - 2) & (nz(np.floor(u / 3), np.floor(z / 5), 9) > .72); c = np.where(lit[..., None], np.array((255, 214, 140))[None, None, :] * .8, c)
            below = z < 0; c = np.where(below[..., None], sil[None, None, :] * (1 - .35 * np.clip(-z / ch_, 0, 1))[..., None] + fl[None, None, :] * .35 * np.clip(-z / ch_, 0, 1)[..., None], c)
            st = (nz(u * 1.3 + seed * 50, z * 1.7, 5) > .985) & (z > hgt + 8); c = np.where(st[..., None], np.minimum(255, c + 70), c)
            c = c * shade; img[m_] = c[m_]
        xb = XX + .5 - sc.X0 - .5 * D; zb = sc.Y0 - .5 * D - YY - .5; wall(xb, zb, (xb >= 0) & (xb < W) & (zb >= -ch_) & (zb < H_), 1.0, 0)        # 뒷벽
        dl = (XX + .5 - sc.X0) * 2; zl = sc.Y0 - .5 * dl - YY - .5; wall(dl, zl, (dl >= 0) & (dl < D) & (zl >= -ch_) & (zl < H_), .78, 2)          # 왼쪽 벽(한 단계 어둡게)
        zs_ = sc.Y0 + ch_ - YY - .5; sf = (XX + .5 - sc.X0 >= 0) & (XX + .5 - sc.X0 < W) & (zs_ < 0) & (zs_ >= -6); img[sf] = (fl * .7)[None, :]                  # 바닥판 앞 두께
        dr = (XX + .5 - sc.X0 - W) * 2; zr = sc.Y0 + ch_ - .5 * dr - YY - .5; sr = (dr >= 0) & (dr < D) & (zr < 0) & (zr >= -6); img[sr] = (fl * .5)[None, :]      # 바닥판 오른쪽 두께
    wx, wd, we = (xx + x0)[land], (dd + d0)[land], e[land]; img[land] = A['ground'](wx, wd, we, wx.size)
    for zs, gfn in A.get('zones', []):
        zm = land & (sd([zs], xx + x0, dd + d0) < 0); img[zm] = gfn((xx + x0)[zm], (dd + d0)[zm], e[zm], int(zm.sum()))
    ch = min(A['ch'], 50) if BOX else A['ch']; painted = land.copy(); face = A['face']                        # 낭떠러지 단면: 땅 가장자리 아래로 곧게 떨어진다
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
    if A.get('chaser'): c = A['chaser']; meta['chaser'] = {'spots': [tr(q) for q in c['spots']], 'radius': c['radius']}
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
