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
STRICT = set()
SEEDOFF = {}                                                                     # 방별 소품 배치 씨앗 보정(render_more가 길이 막히면 바꿔 다시 굽는다)
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
    crack = (np.abs(x % 9) < .8) | (np.abs(d % 9) < .8); gone = nz(np.floor(x / 9), np.floor(d / 9), 6) > .88                 # 폐놀이공원: 바랜 포장, 금, 빠진 타일, 틈으로 올라온 잡초
    return col([(t, (66, 60, 76)), (~t, (58, 52, 68)), (crack, (40, 36, 48)), (gone, (36, 32, 42)), (crack & (nz(x, d, 4) > .8), (52, 74, 56)), (nz(x / 3, d / 3, 2) > .93, (84, 76, 92)), (e > -2, (92, 84, 100))], n)
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

BLOCKED = {                                                                     # 걷는 길 밖의 '막힌 바닥'(허공 대신)
    'woods': lambda x, d, n: col([(nz(x, d, 1) >= 0, (14, 20, 22)), (nz(x / 2, d / 2, 2) > .55, (20, 30, 30)), (nz(x, d, 3) > .9, (30, 48, 42)), (nz(x / 5, d / 2, 4) > .88, (30, 24, 38))], n),
    'reed': lambda x, d, n: col([(nz(x, d, 1) >= 0, (104, 72, 36)), (np.floor(x * 2 + d) % 5 == 0, (150, 108, 48)), (nz(x, d, 3) > .9, (176, 132, 60)), (nz(x / 6, d / 3, 4) > .86, (80, 54, 32))], n),
    'park': lambda x, d, n: col([(nz(x, d, 1) >= 0, (30, 28, 38)), ((np.floor(x / 9) + np.floor(d / 9)) % 2 == 1, (26, 24, 34)), (nz(x / 2, d / 2, 3) > .72, (30, 46, 36)), (nz(x / 4, d / 3, 5) > .9, (40, 60, 44)), (nz(x / 12, d / 7, 4) > .9, (22, 26, 48)), (nz(x, d, 8) > .992, (150, 140, 120))], n),
    'hall': lambda x, d, n: col([(nz(x, d, 1) >= 0, (40, 38, 46)), (np.abs(d % 9) < 1, (30, 28, 36)), ((x % 30 < 13) & (d % 24 < 9), (58, 52, 52)), ((x % 30 < 13) & (d % 24 < 9) & ((x % 30 < 1) | (d % 24 < 1)), (80, 70, 64))], n),
}
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
                 ground=park_ground, face=face_rock((96, 80, 110), (30, 22, 44)), ch=30, sky=((30, 22, 52), (86, 56, 104)), start=(190, 8), box=dict(wall='tent', vig=.62),
                 exits=[dict(at=(190, 3), to='office', spawn_abs=(71, 46)), dict(at=(372, 96), to='reed', spawn=(10, 104))]),
    'reed': dict(H=64, wob=3, shapes=[('circle', 120, 120, 88), ('circle', 250, 150, 98), ('circle', 370, 112, 80), ('path', [(0, 104), (50, 112)], 24), ('path', [(430, 110), (480, 122), (524, 102)], 24)],
                 ground=reed_ground, face=face_rock((120, 86, 50), (44, 26, 30)), ch=34, sky=((84, 50, 70), (236, 150, 80)), start=(10, 104), box=dict(wall='reeds', vig=.3),
                 exits=[dict(at=(4, 104), to='park', spawn=(364, 96)), dict(at=(520, 102), to='woods', spawn=(10, 60))]),
    'woods': dict(H=84, wob=3, shapes=[('path', bez((0, 60), (60, 40), (90, 100), (140, 90)) + bez((140, 90), (200, 80), (230, 40), (300, 66))[1:] + bez((300, 66), (350, 80), (370, 120), (420, 106))[1:] + bez((420, 106), (470, 96), (490, 70), (530, 80))[1:], 28), ('circle', 140, 88, 50), ('circle', 300, 68, 46), ('circle', 420, 106, 58)],
                  ground=woods_ground, face=face_rock((40, 44, 50), (8, 8, 14)), ch=34, sky=((6, 8, 14), (22, 34, 40)), start=(10, 60), box=dict(wall='trunks'),
                  exits=[dict(at=(4, 60), to='reed', spawn=(510, 104)), dict(at=(526, 80), to='ridge', spawn=(10, 38))], chaser=dict(spots=((120, 112), (164, 68), (252, 58), (300, 94), (380, 102), (436, 126), (484, 98)), radius=52)),
    'ridge': dict(H=64, wob=1.5, mood='dark', chase=True, shapes=[('path', P1, 19), ('path', P2, 19), ('path', P3, 19), ('rect', 146, 50, 208, 70), ('rect', 406, 54, 464, 74), ('circle', 92, 52, 32), ('circle', 310, 104, 34), ('circle', 522, 92, 32)],
                  zones=[(('rect', 172, 49, 184, 71), plank_ground), (('rect', 432, 53, 444, 75), plank_ground)],
                  ground=ridge_ground, face=face_rock((132, 92, 62), (36, 20, 30)), ch=46, sky=((40, 22, 48), (170, 70, 60)), start=(10, 38), box=dict(wall='rock', pit=30, floor=(30, 16, 22)),
                  exits=[dict(at=(4, 40), to='woods', spawn=(516, 80)), dict(at=(596, 100), to='roofs', spawn=(10, 36))]),
    'roofs': dict(H=70, shapes=[('rect', 0, 0, 90, 70), ('rect', 84, 24, 124, 44), ('rect', 118, 10, 190, 90), ('rect', 144, 84, 164, 126), ('rect', 110, 120, 230, 180), ('rect', 224, 134, 268, 154), ('rect', 262, 110, 330, 170)],
                  zones=[(('rect', 90, 23, 118, 45), plank_ground), (('rect', 143, 90, 165, 120), plank_ground_v), (('rect', 230, 133, 262, 155), plank_ground)],
                  ground=roof_ground, face=face_building, ch=90, sky=((10, 12, 30), (40, 46, 86)), start=(10, 36), box=dict(wall='facade', pit=44, floor=(12, 13, 26)),
                  exits=[dict(at=(4, 36), to='ridge', spawn=(586, 100)), dict(at=(324, 140), to='hall', spawn=(10, 22))]),
    'hall': dict(H=70, mood='dark', chase=True, shapes=[('rect', 0, 0, 440, 46), ('rect', 392, 46, 440, 150), ('rect', 392, 150, 700, 196)],
                 ground=hall_ground, face=face_rock((70, 76, 70), (10, 8, 14)), ch=26, sky=((8, 6, 12), (20, 16, 26)), start=(10, 22), box=dict(wall='class'),
                 exits=[dict(at=(4, 22), to='roofs', spawn=(314, 140)), dict(at=(694, 172), to=None, endMsg='복도 끝의 문 — 여기서부터는 아직 만들지 않았어요', side='right')]),
}

def props(name, k, tr, inside, rng):
    sc = k.sc; T = lambda x, d: tr((x, d))
    if name == 'park':                                                          # 폐놀이공원: 전부 낡고 꺼져 있고, 불은 몇 군데만 살아 있다
        def ferris():                                                           # 멈춘 관람차: 칸 하나만 불이 켜져 있고, 하나는 떨어져 나갔다
            cx, cy = sc.P(*T(204, 222), 40); R = 34; DK = (44, 40, 56)
            sc.d.line([sc.P(*T(192, 218), 0), (cx, cy)], fill=DK, width=2); sc.d.line([sc.P(*T(218, 218), 0), (cx, cy)], fill=DK, width=2)
            sc.d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(62, 56, 76)); sc.d.ellipse([cx - R + 3, cy - R + 3, cx + R - 3, cy + R - 3], outline=DK)
            for i in range(10):
                a = i * math.tau / 10 + .2; ex, ey = cx + R * math.cos(a), cy + R * math.sin(a); sc.d.line([(cx, cy), (ex, ey)], fill=(50, 46, 62))
                if i == 3: continue
                sc.d.rectangle([ex - 3, ey, ex + 3, ey + 5], fill=(56, 44, 56) if i % 2 else (48, 50, 64)); sc.d.rectangle([ex - 2, ey + 1, ex + 2, ey + 3], fill=(255, 220, 150) if i == 7 else (20, 18, 28))
        sc.jobs.append((400, ferris)); fx, fd = T(204, 222); a7 = 7 * math.tau / 10 + .2; k.glow(fx + 34 * math.cos(a7), fd, 16, (255, 214, 150), .25)
        cx, cd = T(44, 156)                                                     # 회전목마: 꺼져 있다. 바랜 지붕 한쪽이 처지고 말 하나는 쓰러졌다. 전구 하나만 켜짐
        def carousel():
            X, Y = sc.P(cx, cd, 0); sc.d.ellipse([X - 22, Y - 7, X + 22, Y + 7], fill=(70, 56, 66)); sc.d.ellipse([X - 20, Y - 8, X + 20, Y + 4], fill=(92, 80, 80))
            for i in range(-18, 19, 9): sc.d.line([(X + i, Y - 2), (X + i, Y - 30 + (3 if i > 0 else 0))], fill=(120, 110, 90))
            for i, c in ((-12, (130, 128, 132)), (2, (116, 90, 94))): sc.d.rectangle([X + i - 3, Y - 14, X + i + 3, Y - 10], fill=c); sc.d.rectangle([X + i + 2, Y - 17, X + i + 4, Y - 13], fill=c); sc.d.line([(X + i - 2, Y - 10), (X + i - 2, Y - 6)], fill=c); sc.d.line([(X + i + 2, Y - 10), (X + i + 2, Y - 6)], fill=c)
            sc.d.rectangle([X + 9, Y - 5, X + 17, Y - 2], fill=(130, 128, 132)); sc.d.rectangle([X + 16, Y - 7, X + 19, Y - 4], fill=(130, 128, 132))                 # 쓰러진 말
            for j in range(12): c = (110, 52, 60) if j % 2 else (128, 120, 110); sag = 4 if j > 7 else 0; sc.d.polygon([(X, Y - 48), (X - 24 + j * 4, Y - 30 + sag), (X - 20 + j * 4, Y - 30 + sag)], fill=dk(c, 1 - abs(j - 5.5) * .05))
            sc.d.rectangle([X - 24, Y - 31, X + 8, Y - 28], fill=(120, 104, 64)); sc.d.rectangle([X - 1, Y - 53, X + 1, Y - 48], fill=(120, 104, 64)); sc.d.rectangle([X - 13, Y - 28, X - 11, Y - 26], fill=(255, 224, 150))
        sc.jobs.append((cd - 8, carousel)); k.rects.append((cx - 20, cd - 8, 40, 14)); k.glow(cx - 12, cd - 6, 20, (255, 214, 150), .3)
        for n_, (bx, bd, c) in enumerate(((132, 150, (104, 50, 58)), (236, 150, (50, 78, 100)), (140, 62, (120, 100, 60)))):       # 가게: 두 곳은 셔터가 내려가 있고, 한 곳만 안에 불이 켜져 있다
            x, d = T(bx, bd); lit = n_ == 1; k.B(x, d, 18, 10, 16, (104, 98, 96)); k.B(x - 1, d - 2, 20, 13, 3, c, z0=16, solid=False)
            for i in range(0, 18, 4): k.F(x + i, x + i + 2, 0, 9, c, d)
            if lit: k.F(x + 3, x + 15, 10, 15, (255, 214, 140), d); k.F(x + 8.5, x + 9.5, 10, 15, (120, 90, 60), d); k.glow(x + 9, d - 5, 24, (255, 206, 130), .5)
            else:
                k.F(x + 3, x + 15, 10, 15, (58, 56, 62), d)
                for z in (11, 13): k.F(x + 3, x + 15, z, z + .6, (40, 38, 46), d)
                def sign(x=x, d=d, c=c): a = sc.P(x + 2, d - 3, 2); sc.d.polygon([a, (a[0] + 12, a[1] + 3), (a[0] + 12, a[1] + 6), (a[0], a[1] + 3)], fill=dk(c, .8))                   # 떨어진 간판
                sc.jobs.append((d - 3, sign))
        for n_, (lx, ld) in enumerate(((160, 60), (220, 60), (140, 120), (240, 126), (190, 160), (90, 128), (300, 100))):                      # 가로등 7개 중 2개만 켜짐. 하나는 기울었다
            x, d = T(lx, ld); on = n_ in (0, 4)
            if n_ == 5:
                def lean(x=x, d=d): b = sc.P(x + 1, d, 0); sc.d.line([b, (b[0] + 7, b[1] - 18)], fill=(52, 48, 66), width=2); sc.d.rectangle([b[0] + 6, b[1] - 21, b[0] + 9, b[1] - 18], fill=(44, 42, 50))
                sc.jobs.append((d, lean)); k.block.append((x + 1, d + 1, 2)); continue
            k.post(x, d, 20, (60, 54, 76)); k.B(x - 1, d - 1, 4, 4, 3, (255, 226, 160) if on else (48, 46, 54), z0=20, solid=False)
            if on: k.glow(x + 1, d, 34, (255, 214, 150), .6)
        x, d = T(190, 110); k.B(x - 7, d - 5, 14, 10, 4, (76, 70, 86)); k.B(x - 2, d - 1, 4, 3, 10, (88, 82, 98), z0=4, solid=False); k.B(x - 5, d - 3, 3, 2, .6, (120, 80, 50), z0=4, solid=False)   # 마른 분수(낙엽)
        for (bx, bd, c, up) in ((166, 66, (150, 64, 72), True), (212, 132, (120, 104, 60), False), (64, 132, (60, 84, 104), False)):       # 풍선: 하나만 떠 있고 둘은 바람이 빠져 바닥에
            x, d = T(bx, bd)
            def bal(x=x, d=d, c=c, up=up):
                X, Y = sc.P(x, d, 0)
                if up: sc.d.line([(X, Y), (X + 1, Y - 16)], fill=(150, 144, 160)); sc.d.ellipse([X - 3, Y - 24, X + 4, Y - 16], fill=c); sc.d.point((X - 1, Y - 22), fill=(255, 240, 220))
                else: sc.d.ellipse([X - 4, Y - 2, X + 3, Y + 1], fill=dk(c, .7)); sc.d.line([(X + 3, Y), (X + 9, Y + 2)], fill=(110, 104, 120))
            sc.jobs.append((d, bal))
        x, d = T(176, 44); k.post(x, d, 30, (120, 104, 64)); x2, _ = T(202, 44); k.post(x2, d, 26, (120, 104, 64))                                          # 입구 아치: 글자판이 한쪽으로 기울었다
        def arch(x=x, x2=x2, d=d): a = sc.P(x, d, 36); b = sc.P(x2 + 2, d, 31); sc.d.polygon([a, b, (b[0], b[1] + 6), (a[0], a[1] + 6)], fill=(96, 46, 54)); sc.d.polygon([(a[0] + 4, a[1] + 2), (b[0] - 3, b[1] + 2), (b[0] - 3, b[1] + 4), (a[0] + 4, a[1] + 4)], fill=(128, 122, 108))
        sc.jobs.append((d - .2, arch))
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
    BOX = A.get('box'); sc = Scene(W, D, A['H'], pad=(BOX.get('pit', 0) + (6 if name in STRICT else 14)) if BOX else min(A['ch'] + 6, 60)); CW, CH = sc.CW, sc.CH
    YY, XX = np.mgrid[0:CH, 0:CW]; dd = (sc.Y0 - YY - .5) * 2; xx = XX + .5 - sc.X0 - .5 * dd
    e = sd(sh, xx + x0, dd + d0, wob); land = e < 0
    t = (YY / CH)[..., None]; top, bot = np.array(A['sky'][0]), np.array(A['sky'][1]); img = (top + (bot - top) * (np.round(t * 14) / 14)).astype(np.int32)
    rng = random.Random(sum(map(ord, name)) + SEEDOFF.get(name, 0))
    for _ in range(CW * CH // 500):                                             # 허공의 먼지·별
        X, Y = rng.randrange(CW), rng.randrange(CH); img[Y, X] = np.minimum(255, img[Y, X] + 60)
    if BOX:                                                                      # 방 상자(처음 집 형식): 바닥이 상자를 꽉 채우고, 뒷벽·왼쪽 벽이 바닥 가장자리에서 바로 올라간다. pit>0 이면 걷는 땅 밖이 깊은 구덩이
        pit, H_ = BOX.get('pit', 0), A['H']; img[:] = (12, 9, 16); wk = BOX['wall']; fl = np.array(BOX.get('floor', (14, 12, 18)), float)
        df = (sc.Y0 + pit - YY - .5) * 2; xf = XX + .5 - sc.X0 - .5 * df; fm = (xf >= 0) & (xf < W) & (df >= 0) & (df < D)                     # 상자 바닥(z = -pit)
        if pit: fc = np.minimum(255, fl[None, None, :] * (1 + .25 * (nz(xf / 3, df / 3, 4) > .8))[..., None]); img[fm] = fc[fm]
        else: bm = fm & ~land; img[bm] = BLOCKED[name]((xx + x0)[bm], (dd + d0)[bm], int(bm.sum()))
        def wall(u, z, m_, shade, seed):                                          # u: 벽을 따라가는 좌표, z: 높이 -> 테마 무늬
            n_ = nz(u, z, 3 + seed); us = u + seed * 5
            if callable(wk): c = np.asarray(wk(u, z, n_, H_, us, seed, pit), float)                    # 새 테마: 벽 무늬 함수를 그대로 받는다
            elif wk == 'trunks':
                c = np.where((n_ > .86)[..., None], (22, 30, 34), (14, 18, 24)).astype(float); tk = (us % 19 < 6) | ((us + 9) % 31 < 3); c = np.where(tk[..., None], np.where(((us % 19 < 1.2) | (n_ > .9))[..., None], (62, 52, 70), (40, 32, 48)), c)
                lf = z > H_ - (16 + 9 * np.sin(us / 6.0) + 6 * nz(np.floor(us / 3), np.zeros_like(u), 7)); c = np.where(lf[..., None], np.where((n_ > .55)[..., None], (26, 54, 52), (16, 36, 38)), c)
            elif wk == 'reeds':
                c = (np.array((92, 60, 36))[None, None, :] + np.array((60, 40, 14))[None, None, :] * np.clip(z / H_, 0, 1)[..., None]); st = (np.floor(us) % 4 == 0) | (n_ > .93); c = np.where(st[..., None], (186, 140, 58), c)
                ear = (z > H_ - 14 - 6 * nz(np.floor(us / 2), np.zeros_like(u), 5)) & (np.floor(us) % 2 == 0); c = np.where(ear[..., None], (236, 204, 124), c)
            elif wk == 'tent':                                                    # 낡은 천막: 바랜 줄무늬, 찢어진 틈, 처진 주름, 거의 다 꺼진 전구 줄
                c = np.where((us % 18 < 9)[..., None], (78, 34, 44), (104, 94, 90)).astype(float) * (0.5 + .5 * np.clip(z / H_, 0, 1))[..., None] * (1 - .18 * (np.sin(us / 2.6) > .7))[..., None]
                tear = (nz(np.floor(us / 11), np.zeros_like(u), 21 + seed) > .8) & (np.abs(us % 11 - 5 - 2 * np.sin(z / 5.0)) < 1.6) & (z > 10 + 20 * nz(np.floor(us / 11), np.ones_like(u), 22)) & (z < H_ - 12); c = np.where(tear[..., None], (8, 6, 12), c)
                sc_ = z > H_ - 6 - 3 * np.abs(np.sin(us / 9 * np.pi)); c = np.where(sc_[..., None], (112, 92, 54), c)
                bi = np.floor(us / 14); bulb = (np.abs(us % 14 - 7) < 1.3) & (np.abs(z - (H_ - 14 + 3 * np.cos(us / 14 * 2 * np.pi))) < 1.3); on = nz(bi, np.zeros_like(u), 31 + seed) > .9; c = np.where(bulb[..., None], np.where(on[..., None], (255, 220, 140), (50, 46, 44)), c)
                halo = on & (np.hypot(us % 14 - 7, z - (H_ - 14 + 3 * np.cos(us / 14 * 2 * np.pi))) < 3.2) & ~bulb; c = np.where(halo[..., None], c + np.array((46, 34, 12)), c)
            elif wk == 'class':
                c = np.where((z < 14)[..., None], (70, 80, 72), (118, 114, 100)).astype(float); k_ = us % 150
                bd = (k_ > 20) & (k_ < 84) & (z > 18) & (z < 40); c = np.where(bd[..., None], np.where(((k_ < 22) | (k_ > 82) | (z < 20) | (z > 38))[..., None], (120, 92, 60), (30, 52, 46)), c)
                wn = (k_ > 100) & (k_ < 132) & (z > 18) & (z < 42); c = np.where(wn[..., None], np.where(((np.abs(k_ - 116) < 1) | (k_ < 102) | (k_ > 130) | (z < 20) | (z > 40))[..., None], (150, 146, 130), (12, 14, 30)), c)
            elif wk == 'rock':
                c = np.where((np.floor((z + 3 * np.sin(us / 23.0)) / 6) % 2 == 0)[..., None], (112, 60, 50), (94, 48, 44)).astype(float); c = np.where((n_ > .9)[..., None], (140, 84, 62), c) * (.7 + .3 * np.clip(z / H_, 0, 1))[..., None]
            else:                                                                 # facade: 옆 건물 벽, 창 몇 개만 켜짐
                c = np.full(np.shape(u) + (3,), (44, 46, 72), float); wn = (us % 9 > 2) & (us % 9 < 7) & (z % 11 > 3) & (z % 11 < 8); lit = nz(np.floor(us / 9), np.floor(z / 11), 9 + seed) > .9; c = np.where(wn[..., None], np.where(lit[..., None], (255, 214, 140), (20, 22, 42)), c)
            c = np.where((z < 0)[..., None], c * .55, c); c = np.where(((z >= -pit) & (z < -pit + 2.2))[..., None], c * .45, c); img[m_] = (c * shade)[m_]
        xb = XX + .5 - sc.X0 - .5 * D; zb = sc.Y0 - .5 * D - YY - .5; wall(xb, zb, (xb >= 0) & (xb < W) & (zb >= -pit) & (zb < H_), 1.0, 0)        # 뒷벽
        dl = (XX + .5 - sc.X0) * 2; zl = sc.Y0 - .5 * dl - YY - .5; wall(dl, zl, (dl >= 0) & (dl < D) & (zl >= -pit) & (zl < H_), .74, 2)          # 왼쪽 벽(한 단계 어둡게)
        zs_ = sc.Y0 + pit - YY - .5; sf = (XX + .5 - sc.X0 >= 0) & (XX + .5 - sc.X0 < W) & (zs_ < 0) & (zs_ >= -5); img[sf] = (30, 24, 32)                        # 바닥 앞 두께
        dr = (XX + .5 - sc.X0 - W) * 2; zr = sc.Y0 + pit - .5 * dr - YY - .5; sr = (dr >= 0) & (dr < D) & (zr < 0) & (zr >= -5); img[sr] = (20, 16, 24)           # 바닥 오른쪽 두께
    wx, wd, we = (xx + x0)[land], (dd + d0)[land], e[land]; img[land] = A['ground'](wx, wd, we, wx.size)
    for zs, gfn in A.get('zones', []):
        zm = land & (sd([zs], xx + x0, dd + d0) < 0); img[zm] = gfn((xx + x0)[zm], (dd + d0)[zm], e[zm], int(zm.sum()))
    ch = BOX.get('pit', 0) if BOX else A['ch']; painted = land.copy(); face = A['face']                        # 낭떠러지 단면: 땅 가장자리 아래로 곧게 떨어진다
    for kk in range(1, ch + 1):
        sh_ = np.zeros_like(land); sh_[kk:] = land[:-kk]; m_ = sh_ & ~painted
        ys, xs_ = np.nonzero(m_)
        for Y, X in zip(ys, xs_): img[Y, X] = face(int(X), kk, ch)
        painted |= m_
    if BOX:                                                                      # 상자 안은 가장자리로 갈수록 어둡다(빛 웅덩이는 이 뒤에 얹힌다)
        inb = (img != np.array((12, 9, 16))).any(axis=2); cyx = np.argwhere(inb); (y0_, x0_), (y1_, x1_) = cyx.min(0), cyx.max(0); r_ = np.hypot((XX - (x0_ + x1_) / 2) / ((x1_ - x0_) / 2 + 1), (YY - (y0_ + y1_) / 2) / ((y1_ - y0_) / 2 + 1))
        img = np.where(inb[..., None], img * (1 - BOX.get('vig', .42) * np.clip(r_, 0, 1.2)[..., None] ** 2), img).astype(np.int32)
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
    if name in STRICT:                                                           # 가구 몸통(rects)도 엔진처럼 아이 발 여유를 두고 막는다
        for (rx_, rd_, rw_, rp_) in k.rects: ok &= ~((gx > rx_ - 5) & (gx < rx_ + rw_ + 5) & (gd > rd_ - 3.2) & (gd < rd_ + rp_ + 3.2))
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
