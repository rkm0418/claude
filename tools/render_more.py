#!/usr/bin/env python3
"""테마마다 작은 직사각 상자 공간 10개씩(눈·호수·놀이공원·갈대·숲·능선·옥상·복도·통나무집·도서관·매표소·나무집).
공간은 화면 하나에 틀 전체가 들어오는 크기(약 200x125 이하)이고, 넘어갈 때는 페이드로 이어진다.
공간마다 레이아웃(복도·ㄱ자·지그재그·광장·갈림길·고리·섬과 널다리·계단식·곡선·빗살·아령·십자·T·대각선·다리)과 소품 조합이 다르다.
사용: python3 tools/render_more.py [테마 ...]  -> maps/out/world_<이름>.png/_depth/_walk, more_nav.json (export_web 이 읽는다)"""
import json, math, os, random, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_world as W
from render_world import nz, col, face_rock, plank_ground, OUT, K
from render_dream_area import bez, CELL, fir2
import render_dream_lake as RDL

N_PER = 10
MORE = {}                                                                       # 이름 -> 방 사양

# ---------------- 바닥·벽 무늬 ----------------
def snow_ground(x, d, e, n):
    q = nz(x / 2, d / 2, 5)
    return col([(q >= 0, (234, 240, 250)), (q > .55, (224, 232, 246)), (q > .92, (208, 220, 240)), (nz(x / 6, d / 4, 8) > .9, (246, 249, 255)), (e > -2, (196, 210, 234))], n)
def ice_ground(x, d, e, n):
    q = nz(x / 2, d / 2, 6); crack = (np.abs((x * .6 + d) % 19) < .6) | (np.abs((x - d * .8) % 27) < .6)
    return col([(q >= 0, (150, 198, 228)), (q > .6, (172, 212, 238)), (crack, (232, 246, 255)), (nz(x / 5, d / 5, 3) > .93, (120, 170, 210)), (e > -2, (214, 236, 250))], n)
def wood_ground(x, d, e, n):
    pl = np.floor(d / 6) % 2 == 0; seam = np.abs(d % 6) < .7; knot = nz(x / 3, d / 3, 7) > .96
    return col([(pl, (152, 106, 66)), (~pl, (134, 92, 58)), (seam, (84, 56, 36)), (np.abs((x + 17 * np.floor(d / 6)) % 40) < .6, (96, 66, 44)), (knot, (100, 68, 44)), (e > -1.5, (176, 128, 84))], n)
def parquet_ground(x, d, e, n):
    t = (np.floor(x / 8) + np.floor(d / 8)) % 2 == 0; seam = (np.abs(x % 8) < .6) | (np.abs(d % 8) < .6)
    return col([(t, (104, 70, 48)), (~t, (90, 60, 42)), (seam, (54, 34, 26)), (nz(x / 2, d / 2, 4) > .93, (118, 84, 58)), (e > -1.5, (132, 96, 66))], n)
def lino_ground(x, d, e, n):
    t = (np.floor(x / 10) + np.floor(d / 10)) % 2 == 0
    return col([(t, (176, 178, 150)), (~t, (150, 158, 134)), (nz(x / 2, d / 2, 5) > .92, (134, 140, 120)), (e > -1.5, (206, 206, 176))], n)
def bark_ground(x, d, e, n):
    ring = np.sin(np.hypot(x - 40, (d - 20) * 1.6) / 3.2) > .55; q = nz(x / 2, d / 2, 8)
    return col([(q >= 0, (160, 112, 66)), (ring, (142, 98, 58)), (q > .9, (180, 130, 80)), (nz(x / 5, d / 5, 2) > .94, (96, 150, 80)), (e > -1.5, (196, 150, 96))], n)
def dark_blocked(c0, c1):
    return lambda x, d, n: col([(nz(x, d, 1) >= 0, c0), (nz(x / 3, d / 3, 2) > .7, c1), (nz(x, d, 5) > .94, tuple(min(255, v + 18) for v in c1))], n)

def w_snow(u, z, n_, H_, us, seed, pit):                                          # 눈 하늘: 옅은 하늘색 아래로 먼 전나무 숲 그림자, 눈송이
    t = np.clip(z / H_, 0, 1)[..., None]; c = np.array((218, 230, 250)) * (1 - t) + np.array((246, 248, 255)) * t
    hgt = 10 + 7 * np.abs(np.sin(us / 5.0)) + 6 * nz(np.floor(us / 4), np.zeros_like(u), 7); sil = z < hgt; c = np.where(sil[..., None], np.where((z > hgt - 2)[..., None], (150, 176, 196), (98, 132, 150)), c)
    return np.where((n_ > .965)[..., None] & ~sil[..., None], (255, 255, 255), c)
def w_night(u, z, n_, H_, us, seed, pit):                                         # 호수 밤하늘: 달, 별, 먼 마른 나무 그림자
    t = np.clip(z / H_, 0, 1)[..., None]; c = np.array((70, 78, 134)) * (1 - t) + np.array((18, 22, 56)) * t
    mx = 40 + 22 * (seed % 3); moon = np.hypot(us - mx, (z - (H_ - 13)) * 1.0) < 6.5; c = np.where(moon[..., None], (232, 232, 252), c)
    c = np.where(((n_ > .955) & (z > 14))[..., None], (240, 244, 255), c); tr_ = (us % 23 < 1.4) & (z < 16 + 8 * nz(np.floor(us / 23), np.zeros_like(u), 4)); return np.where(tr_[..., None], (16, 18, 40), c)
def w_logs(u, z, n_, H_, us, seed, pit):                                          # 통나무 벽: 가로 통나무, 모서리 이음, 달빛 드는 창
    row = np.floor(z / 6); c = np.where((row % 2 == 0)[..., None], (128, 84, 50), (112, 72, 42)).astype(float); c = np.where(((z % 6) > 4.2)[..., None], (150, 104, 66), c); c = np.where(((z % 6) < .8)[..., None], (70, 44, 30), c)
    c = np.where((nz(np.floor(us / 7) + row, np.zeros_like(u), 3 + seed) > .92)[..., None], (96, 62, 38), c)
    win = (us % 90 > 30) & (us % 90 < 56) & (z > 16) & (z < 34); fr = win & ((us % 90 < 32) | (us % 90 > 54) | (z < 18) | (z > 32) | (np.abs(us % 90 - 43) < 1)); c = np.where(win[..., None], np.where(fr[..., None], (64, 42, 28), (255, 214, 150)), c)
    return c
def w_shelves(u, z, n_, H_, us, seed, pit):                                       # 도서관: 책장이 벽 전체를 덮는다
    pal = np.array([(150, 50, 50), (60, 90, 130), (200, 170, 70), (70, 110, 80), (120, 70, 120), (190, 190, 170), (210, 120, 60)], float)
    c = np.full(np.shape(u) + (3,), (60, 38, 30), float); sh = (z % 13) < 1.6; row = np.floor(z / 13); idx = (nz(np.floor(us / 2) + 3 * row, np.zeros_like(u), 5 + seed) * 7).astype(int) % 7
    top = 3 + 8 * nz(np.floor(us / 2) + 3 * row, np.zeros_like(u), 9); book = ((z % 13) >= 1.6) & ((z % 13) < 1.6 + top) & (nz(np.floor(us / 2) + 3 * row, np.zeros_like(u), 2) > .12)
    c = np.where(book[..., None], pal[idx], c); c = np.where(sh[..., None], (104, 70, 48), c); return c * (.8 + .2 * np.clip(z / H_, 0, 1))[..., None]
def w_office(u, z, n_, H_, us, seed, pit):                                        # 매표소: 아래는 초록 징두리, 위는 바랜 베이지 벽, 창과 벽보
    c = np.where((z < 15)[..., None], (74, 112, 100), (208, 200, 172)).astype(float); c = np.where(((z > 14.5) & (z < 16.5))[..., None], (150, 150, 128), c)
    c = np.where(((nz(np.floor(us / 5), np.floor(z / 5), 6) > .93) & (z > 16))[..., None], (190, 180, 150), c)
    win = (us % 76 > 26) & (us % 76 < 52) & (z > 22) & (z < 40); fr = win & ((us % 76 < 28) | (us % 76 > 50) | (np.abs(us % 76 - 39) < 1) | (z < 24) | (z > 38) | (np.abs(z - 31) < 1)); c = np.where(win[..., None], np.where(fr[..., None], (120, 120, 100), (140, 170, 196)), c)
    post = (us % 76 > 60) & (us % 76 < 70) & (z > 20) & (z < 36); c = np.where(post[..., None], np.where(((us % 76 < 61.5) | (z < 21.5))[..., None], (120, 90, 60), (200, 120, 100)), c); return c
def w_bark(u, z, n_, H_, us, seed, pit):                                          # 나무집 안쪽: 줄기 속 나뭇결, 옹이, 불 켜진 구멍, 위쪽엔 잎
    c = np.where(((us % 9) < 2.2)[..., None], (74, 48, 32), (104, 70, 44)).astype(float); c = np.where((n_ > .9)[..., None], (126, 88, 56), c)
    hole = (np.hypot((us % 80 - 40) * 1.0, (z - 24) * 1.3) < 7); c = np.where(hole[..., None], (255, 218, 150), c); c = np.where((np.hypot((us % 80 - 40), (z - 24) * 1.3) > 6.4)[..., None] & hole[..., None], (50, 32, 22), c)
    lf = z > H_ - 7 - 4 * np.abs(np.sin(us / 5.0)); return np.where(lf[..., None], np.where((n_ > .5)[..., None], (50, 96, 58), (36, 74, 46)), c)

# ---------------- 소품 ----------------
def flat(k, x, d, rx, ry, c):                                                   # 바닥에 깔리는 무늬(가장 먼저 그려진다)
    def f(): X, Y = k.sc.P(x, d, 0); k.sc.d.ellipse([X - rx, Y - ry, X + rx, Y + ry], fill=c)
    k.sc.jobs.append((399, f))
def job(k, x, d, fn, blk=0):
    k.sc.jobs.append((d, lambda: fn(*k.sc.P(x, d, 0), k.sc.d)))
    if blk: k.block.append((x, d, blk))
def snowtop(k, x, d, w, dp, z): k.B(x - .6, d - .6, w + 1.2, dp + 1.2, 1.4, (244, 248, 255), z0=z, solid=False)
WHITE = (240, 246, 255)

def p_fir(k, x, d, r): fir2(k.sc, x, d, r.choice((56, 64, 72, 82))); k.block.append((x, d, 4))
def p_stump(k, x, d, r): k.B(x, d, 5, 5, 5, (124, 92, 70)); snowtop(k, x, d, 5, 5, 5)
def p_log(k, x, d, r): k.B(x, d, 15, 4, 4, (116, 84, 62)); snowtop(k, x, d, 15, 4, 4)
def p_mound(k, x, d, r): k.rock(x, d, r.choice((3, 4, 5)), (238, 244, 252))
def p_lantern(k, x, d, r): RDL.lantern(k.sc, x, d); k.block.append((x, d, 2))
def p_sign(k, x, d, r): k.post(x, d, 13, (120, 92, 70)); k.B(x - 4, d - .5, 10, 1.4, 5, (158, 126, 88), z0=8, solid=False)
def p_snowman(k, x, d, r):
    def f(X, Y, g):
        g.ellipse([X - 5, Y - 8, X + 5, Y], fill=WHITE); g.ellipse([X - 3, Y - 14, X + 3, Y - 7], fill=WHITE); g.line([(X - 4, Y - 6), (X - 8, Y - 10)], fill=(110, 80, 60)); g.line([(X + 4, Y - 6), (X + 8, Y - 9)], fill=(110, 80, 60))
        g.point((X - 1, Y - 12), fill=(30, 30, 40)); g.point((X + 1, Y - 12), fill=(30, 30, 40)); g.line([(X, Y - 11), (X + 2, Y - 10)], fill=(230, 130, 50)); g.point((X, Y - 5), fill=(60, 60, 70)); g.point((X, Y - 3), fill=(60, 60, 70))
    job(k, x, d, f, 5)
def p_icepatch(k, x, d, r): flat(k, x, d, r.randint(5, 9), r.randint(2, 4), (176, 206, 236))
def p_bush(k, x, d, r):
    def f(X, Y, g):
        for dx in (-4, -1, 2, 5): g.line([(X + dx, Y), (X + dx + r.choice((-2, 0, 2)), Y - r.randint(5, 9))], fill=(86, 70, 74))
        g.point((X - 4, Y - 6), fill=WHITE); g.point((X + 5, Y - 7), fill=WHITE)
    job(k, x, d, f)
def p_deadtree(k, x, d, r): RDL.dead_tree(k.sc, x, d, r.choice((58, 70, 82))); k.block.append((x, d, 3))
def p_hole(k, x, d, r): flat(k, x, d, 7, 3, (210, 232, 248)); flat(k, x, d, 5, 2, (14, 30, 62))
def p_bucket(k, x, d, r):
    k.B(x, d, 4, 4, 5, (150, 152, 166)); job(k, x + 8, d, lambda X, Y, g: (g.line([(X, Y), (X + 6, Y - 14)], fill=(110, 90, 70)), g.line([(X + 6, Y - 14), (X + 2, Y - 3)], fill=(220, 220, 230))))
def p_shard(k, x, d, r):
    def f(X, Y, g): g.polygon([(X - 3, Y), (X, Y - 11), (X + 3, Y)], fill=(206, 232, 252)); g.line([(X, Y - 11), (X, Y - 2)], fill=(255, 255, 255))
    job(k, x, d, f, 3)
def p_boat(k, x, d, r): k.B(x, d, 16, 6, 3, (112, 78, 56)); k.B(x + 1.5, d + 1.2, 13, 3.6, 1, (70, 48, 36), z0=2.6, solid=False); k.B(x + 13, d + 2, 3, 2, 1.5, (112, 78, 56), z0=3, solid=False)
def p_stones(k, x, d, r): k.rock(x, d, 4, (150, 160, 172)); k.rock(x + 1, d, 3, (170, 178, 188)); k.sc.d  # 쌓은 돌

def p_lamp(on):
    def f(k, x, d, r):
        k.post(x, d, 32, (60, 54, 76)); k.B(x - 1, d - 1, 4, 4, 3, (255, 226, 160) if on else (48, 46, 54), z0=32, solid=False)
        if on: k.glow(x + 1, d, 40, (255, 214, 150), .6)
    return f
def p_bench(k, x, d, r): k.B(x, d, 14, 4, 4, (112, 84, 66)); k.B(x, d + 3.4, 14, 1, 7, (96, 70, 56), solid=False)
def p_balloon(k, x, d, r):
    c = r.choice(((150, 64, 72), (120, 104, 60), (60, 84, 104)))
    def f(X, Y, g): g.line([(X, Y), (X + 1, Y - 16)], fill=(150, 144, 160)); g.ellipse([X - 3, Y - 24, X + 4, Y - 16], fill=c); g.point((X - 1, Y - 22), fill=(255, 240, 220))
    job(k, x, d, f)
def p_kiosk(k, x, d, r):
    c = r.choice(((104, 50, 58), (50, 78, 100), (120, 100, 60))); lit = r.random() < .3; k.B(x, d, 16, 9, 20, (104, 98, 96)); k.B(x - 1, d - 2, 18, 12, 3, c, z0=20, solid=False)
    for i in range(0, 16, 4): k.F(x + i, x + i + 2, 0, 9, c, d)
    k.F(x + 3, x + 13, 9, 13, (255, 214, 140) if lit else (58, 56, 62), d)
    if lit: k.glow(x + 8, d - 5, 22, (255, 206, 130), .5)
def p_cart(k, x, d, r): k.B(x, d, 12, 7, 6, (150, 60, 60)); k.B(x - 1, d - 1, 14, 9, 2, (226, 214, 190), z0=6, solid=False); k.B(x + 1, d + 7, 3, 1, 3, (60, 60, 70), solid=False); k.B(x + 8, d + 7, 3, 1, 3, (60, 60, 70), solid=False)
def p_bumper(k, x, d, r):
    c = r.choice(((200, 70, 70), (70, 120, 200), (210, 180, 70))); k.B(x, d, 10, 6, 3, tuple(int(v * .55) for v in c)); k.B(x + 1, d + 1, 8, 4, 3, c, z0=3, solid=False)
def p_bin(k, x, d, r): k.B(x, d, 4, 4, 7, (84, 92, 96)); k.B(x - .4, d - .4, 4.8, 4.8, 1, (110, 118, 122), z0=7, solid=False)
def p_fence(k, x, d, r):
    for i in range(3): k.post(x + i * 6, d, 9, (110, 84, 66))
    k.B(x, d, 13, .8, .8, (120, 94, 74), z0=6, solid=False); k.B(x, d, 13, .8, .8, (120, 94, 74), z0=3, solid=False)
def p_horse(k, x, d, r):
    def f(X, Y, g): g.rectangle([X - 5, Y - 9, X + 3, Y - 5], fill=(130, 128, 132)); g.rectangle([X + 2, Y - 13, X + 5, Y - 8], fill=(130, 128, 132)); g.line([(X - 4, Y - 5), (X - 4, Y)], fill=(110, 108, 114)); g.line([(X + 2, Y - 5), (X + 2, Y)], fill=(110, 108, 114)); g.line([(X, Y - 20), (X, Y)], fill=(200, 180, 100))
    job(k, x, d, f, 3)

def p_reedc(k, x, d, r):
    for _ in range(5): k.reed(x + r.uniform(-4, 4), d + r.uniform(-2, 2), r.choice((16, 19, 22, 26)))
def p_desk(k, x, d, r): k.desk(x, d); k.block.append((x + 5, d - 2, 6))
def p_rock(k, x, d, r): k.rock(x, d, r.choice((3, 4, 5)), (150, 120, 90))
def p_scarecrow(k, x, d, r):
    def f(X, Y, g): g.line([(X, Y), (X, Y - 22)], fill=(110, 84, 60), width=2); g.line([(X - 8, Y - 16), (X + 8, Y - 16)], fill=(110, 84, 60), width=2); g.rectangle([X - 3, Y - 28, X + 3, Y - 22], fill=(220, 190, 120)); g.polygon([(X - 6, Y - 28), (X + 6, Y - 28), (X, Y - 34)], fill=(90, 66, 50)); g.rectangle([X - 5, Y - 15, X + 5, Y - 8], fill=(150, 90, 70))
    job(k, x, d, f, 3)
def p_hay(k, x, d, r): k.B(x, d, 10, 8, 7, (214, 176, 84)); k.B(x + 1, d + 1, 8, 6, 3, (230, 196, 110), z0=7, solid=False)
def p_puddle(k, x, d, r): flat(k, x, d, 8, 3, (96, 70, 44)); flat(k, x, d, 6, 2, (150, 130, 110))

def p_dtree(k, x, d, r):
    h = r.choice((62, 74, 88)); w = r.choice((3, 3, 4)); lean = r.choice((-3, 0, 0, 3)); crown = r.random() < .65; knot = r.random() < .4
    def f(X, Y, g):
        g.ellipse([X - 5, Y - 1, X + 5, Y + 1], fill=(22, 28, 32))
        for z in range(h):
            cx = X + round(lean * (z / h) ** 2); g.line([(cx - w, Y - z), (cx + w, Y - z)], fill=(40, 34, 48))
            if (z * 7 + int(x)) % 5 == 0: g.point((cx - w + 1, Y - z), fill=(62, 54, 70))
        cx = X + lean
        if knot: g.rectangle([cx - 1, Y - h // 2 - 2, cx + 1, Y - h // 2 + 1], fill=(14, 12, 20))
        if crown:
            for (ox, oy, rr, c) in ((0, 0, h * .26, (16, 30, 34)), (-h * .17, h * .1, h * .2, (22, 40, 42)), (h * .16, -h * .03, h * .2, (22, 40, 42))): g.ellipse([cx + ox - rr, Y - h + oy - rr * .75, cx + ox + rr, Y - h + oy + rr * .75], fill=c)
        else:
            for (bx_, by_) in ((-7, -9), (6, -11), (-2, -14), (9, -5)): g.line([(cx, Y - h + 2), (cx + bx_, Y - h + by_)], fill=(40, 34, 48))
    job(k, x, d, f, 3)
def p_wstump(k, x, d, r): k.B(x, d, 5, 5, 4, (54, 44, 56)); k.B(x - .5, d - .5, 6, 6, 1, (72, 60, 70), z0=4, solid=False)
def p_shroom(k, x, d, r):
    def f(X, Y, g):
        for dx, hh in ((-3, 4), (0, 7), (3, 5)): g.line([(X + dx, Y), (X + dx, Y - hh)], fill=(150, 170, 160)); g.ellipse([X + dx - 2, Y - hh - 2, X + dx + 2, Y - hh], fill=(110, 200, 190))
    job(k, x, d, f); k.glow(x, d, 16, (110, 220, 200), .3)
def p_wlog(k, x, d, r): k.B(x, d, 16, 4, 4, (50, 40, 50)); k.B(x, d, 16, 4, .6, (30, 52, 44), z0=4, solid=False)
def p_wrock(k, x, d, r): k.rock(x, d, 3, (60, 66, 72))

def p_atree(k, x, d, r): k.atree(x, d, r.choice((46, 54, 60)), pal=((150, 60, 44), (196, 96, 50), (104, 40, 44)))
def p_cairn(k, x, d, r): k.rock(x, d, 4, (130, 104, 96)); k.rock(x, d - .5, 3, (150, 122, 110)); k.rock(x, d - 1, 2, (170, 140, 126))
def p_redshroom(k, x, d, r):
    def f(X, Y, g): g.line([(X, Y), (X, Y - 5)], fill=(210, 200, 180)); g.ellipse([X - 3, Y - 9, X + 3, Y - 4], fill=(200, 60, 50)); g.point((X - 1, Y - 7), fill=(255, 240, 230))
    job(k, x, d, f)
def p_planks(k, x, d, r): k.B(x, d, 12, 3, 1.4, (150, 108, 70)); k.B(x + 1, d + 3, 12, 3, 1.4, (132, 94, 62)); k.B(x + 2, d + 6, 10, 3, 1.4, (150, 108, 70))
def p_boulder(k, x, d, r): k.rock(x, d, 6, (130, 104, 96))

def p_tank(k, x, d, r): k.B(x, d, 14, 12, 4, (60, 62, 86)); k.B(x + 1, d + 1, 12, 10, 16, (110, 104, 120), z0=4, solid=False); k.B(x, d, 14, 12, 2, (84, 80, 100), z0=20, solid=False)
def p_ac(k, x, d, r): k.B(x, d, 10, 7, 7, (150, 154, 170)); k.F(x + 2, x + 8, 2, 5, (60, 62, 86), d)
def p_hut(k, x, d, r): k.B(x, d, 20, 13, 24, (96, 98, 124)); k.F(x + 6, x + 14, 0, 18, (40, 42, 66), d); k.F(x + 7, x + 13, 0, 17, (255, 206, 130), d); k.glow(x + 10, d - 5, 24, (255, 200, 120), .5)
def p_line(k, x, d, r):
    k.post(x, d, 24, (58, 62, 88)); k.post(x + 30, d, 24, (58, 62, 88))
    def f(X, Y, g):
        a = (X + 1, Y - 24); b = (X + 31, Y - 24); g.line([a, b], fill=(150, 150, 172))
        for i, c in enumerate(((230, 230, 236), (150, 90, 100), (220, 220, 230))): q = a[0] + 6 + i * 9; g.rectangle([q, a[1] + 1, q + 5, a[1] + 8], fill=c)
    job(k, x, d - .2, f)
def p_antenna(k, x, d, r):
    k.post(x, d, 44, (130, 134, 150)); job(k, x, d, lambda X, Y, g: [g.line([(X - 7, Y - h), (X + 7, Y - h)], fill=(150, 154, 170)) for h in (34, 40)])
def p_skylight(k, x, d, r): flat(k, x, d, 9, 4, (60, 62, 90)); flat(k, x, d, 7, 3, (255, 220, 150)); k.glow(x, d, 22, (255, 210, 140), .3)
def p_vent(k, x, d, r): k.B(x, d, 3, 3, 9, (120, 124, 140)); k.B(x - .6, d - .6, 4.2, 4.2, 1.2, (150, 154, 170), z0=9, solid=False)
def p_planter(k, x, d, r): k.B(x, d, 10, 4, 4, (110, 84, 66)); k.B(x + 1, d + .5, 8, 3, 3, (60, 100, 66), z0=4, solid=False)
def p_roofl(k, x, d, r): k.sc.lamp(x, d, h=46, side=1); k.block.append((x, d, 2))
def p_chimney(k, x, d, r): k.B(x, d, 6, 6, 22, (90, 70, 66)); k.B(x - .6, d - .6, 7.2, 7.2, 1.5, (60, 50, 50), z0=22, solid=False)
def p_spool(k, x, d, r): k.B(x, d, 7, 7, 6, (150, 110, 70)); k.B(x - 1, d - 1, 9, 9, 1, (120, 84, 56), z0=6, solid=False)

def p_hlocker(k, x, d, r):
    for i in range(3): k.B(x + i * 5, d, 4.6, 4, 24, (96, 124, 140) if (i + int(x)) % 3 else (120, 96, 100)); k.F(x + i * 5 + 1, x + i * 5 + 3.6, 16, 18, (40, 50, 60), d)
def p_hmop(k, x, d, r): k.B(x, d, 5, 5, 4, (140, 144, 150)); job(k, x + 6, d, lambda X, Y, g: g.line([(X, Y), (X + 4, Y - 20)], fill=(150, 120, 80)))
def p_trophy(k, x, d, r): k.B(x, d, 12, 5, 16, (110, 88, 66)); k.F(x + 1, x + 11, 5, 15, (150, 190, 200), d); k.F(x + 4, x + 8, 7, 12, (230, 200, 90), d - .1)
def p_hbench(k, x, d, r): k.B(x, d, 14, 4, 4, (150, 112, 76)); k.B(x, d, 14, 1, 8, (130, 96, 64), solid=False)
def p_shoes(k, x, d, r): k.B(x, d, 3, 2, 1, (240, 240, 240), solid=False); k.B(x + 4, d + 1, 3, 2, 1, (240, 240, 240), solid=False)
def p_chair(k, x, d, r): k.B(x, d, 5, 5, 6, (150, 110, 76)); k.B(x, d + 4, 5, 1, 12, (130, 96, 64), solid=False)

def p_table(k, x, d, r): k.B(x, d, 14, 9, 1.6, (176, 128, 84), z0=8); [k.B(lx, ld, 1.2, 1.2, 8, (120, 84, 56), solid=False) for lx, ld in ((x + 1, d + 1), (x + 12, d + 1), (x + 1, d + 7), (x + 12, d + 7))]; k.block.append((x + 7, d + 4, 7))
def p_bed(k, x, d, r): k.B(x, d, 20, 11, 5, (120, 84, 56)); k.B(x + 1, d + 1, 18, 9, 3, r.choice(((150, 80, 80), (80, 110, 140), (110, 130, 90))), z0=5, solid=False); k.B(x + 1, d + 1, 5, 9, 2, (230, 224, 210), z0=5, solid=False)
def p_fire(k, x, d, r): k.B(x, d, 18, 7, 24, (110, 100, 96)); k.F(x + 5, x + 13, 0, 10, (30, 20, 20), d); k.F(x + 7, x + 11, 1, 6, (255, 170, 70), d - .1); k.glow(x + 9, d - 6, 34, (255, 170, 90), .6)
def p_rug(k, x, d, r): flat(k, x, d, 14, 5, r.choice(((130, 54, 54), (60, 90, 120), (90, 110, 70)))); flat(k, x, d, 10, 3, (196, 170, 120))
def p_crate(k, x, d, r): k.B(x, d, 8, 7, 7, (150, 112, 70)); k.B(x + 8, d + 1, 6, 6, 5, (130, 96, 60)); k.B(x + 1, d + 1, 7, 6, 5, (166, 124, 80), z0=7, solid=False)
def p_shelf(k, x, d, r): k.B(x, d, 14, 4, 28, (112, 76, 50)); [k.F(x + 1, x + 13, z, z + .8, (80, 54, 36), d) for z in (9, 18)]; k.F(x + 2, x + 6, 10, 15, (190, 150, 90), d); k.F(x + 8, x + 12, 19, 24, (150, 170, 190), d)
def p_barrel(k, x, d, r): k.B(x, d, 6, 6, 8, (130, 90, 56)); k.B(x - .4, d - .4, 6.8, 6.8, .8, (96, 64, 42), z0=3, solid=False)
def p_stool(k, x, d, r): k.B(x, d, 4, 4, 5, (150, 110, 70)); k.B(x - .6, d - .6, 5.2, 5.2, 1, (176, 132, 86), z0=5, solid=False)
def p_stove(k, x, d, r): k.B(x, d, 9, 8, 12, (60, 60, 68)); k.B(x + 3, d + 8, 3, 2, 14, (50, 50, 56), z0=12, solid=False); k.glow(x + 4, d, 16, (255, 150, 80), .25)
def p_hlantern(k, x, d, r): k.post(x, d, 18, (90, 66, 46)); k.B(x - 1.4, d - 1.4, 4.8, 4.8, 4, (255, 220, 150), z0=18, solid=False); k.glow(x + 1, d, 30, (255, 210, 140), .5)

def p_bookcase(k, x, d, r):
    k.B(x, d, 16, 5, 30, (78, 52, 38)); pal = ((150, 50, 50), (60, 90, 130), (200, 170, 70), (70, 110, 80), (120, 70, 120), (190, 190, 170))
    for z in (4, 13, 22):
        i = 0.0
        while i < 14: wd = r.choice((1, 1.5, 2)); k.F(x + 1 + i, x + 1 + i + wd - .2, z, z + r.randint(5, 8), r.choice(pal), d); i += wd
def p_readtable(k, x, d, r): p_table(k, x, d, r); k.B(x + 5, d + 3, 3, 3, 4, (220, 200, 150), z0=9.6, solid=False); k.glow(x + 6, d + 4, 22, (255, 220, 150), .35)
def p_ladder(k, x, d, r): k.B(x, d, 1, 1, 26, (150, 112, 70), solid=False); k.B(x + 6, d, 1, 1, 26, (150, 112, 70), solid=False); [k.F(x, x + 7, z, z + 1, (176, 132, 86), d) for z in range(3, 24, 5)]; k.block.append((x + 3, d, 4))
def p_globe(k, x, d, r): k.B(x, d, 1.2, 1.2, 8, (150, 112, 70), solid=False); job(k, x + .6, d, lambda X, Y, g: (g.ellipse([X - 4, Y - 16, X + 4, Y - 8], fill=(70, 110, 150)), g.line([(X - 2, Y - 14), (X + 1, Y - 11)], fill=(90, 150, 90)))); k.block.append((x, d, 3))
def p_books(k, x, d, r): k.B(x, d, 6, 5, 2, (150, 50, 50)); k.B(x + .5, d + .5, 5, 4, 2, (60, 90, 130), z0=2, solid=False); k.B(x + 1, d + .8, 4, 3.4, 2, (200, 170, 70), z0=4, solid=False)
def p_cart2(k, x, d, r): k.B(x, d, 12, 6, 2, (110, 84, 60), z0=4); k.B(x, d, 12, 6, 6, (90, 66, 48), z0=0, solid=False); k.B(x + 1, d + 1, 10, 4, 4, (150, 60, 60), z0=6, solid=False)
def p_sofa(k, x, d, r): k.B(x, d, 18, 8, 6, (110, 60, 66)); k.B(x, d + 6.6, 18, 1.6, 12, (96, 50, 56), solid=False)
def p_cabinet(k, x, d, r): k.B(x, d, 12, 6, 16, (112, 84, 60)); [k.F(x + 1, x + 11, z, z + 3, (84, 60, 42), d) for z in (2, 6, 10)]; [k.F(x + 5, x + 7, z + 1, z + 2, (220, 200, 140), d - .1) for z in (2, 6, 10)]
def p_flamp(k, x, d, r): k.post(x, d, 22, (110, 88, 60)); k.B(x - 2, d - 2, 6, 6, 4, (255, 224, 160), z0=22, solid=False); k.glow(x + 1, d, 34, (255, 214, 150), .5)

def p_counter(k, x, d, r): k.B(x, d, 26, 6, 10, (130, 100, 72)); k.B(x - .6, d - .6, 27.2, 7.2, 1.4, (176, 140, 100), z0=10, solid=False); k.F(x + 3, x + 23, 11, 24, (150, 190, 210), d - .3); k.F(x + 2, x + 4, 11, 24, (96, 76, 56), d - .4); k.F(x + 22, x + 24, 11, 24, (96, 76, 56), d - .4)
def p_odesk(k, x, d, r): p_table(k, x, d, r); k.B(x + 4, d + 2, 6, 4, 3, (230, 226, 210), z0=9.6, solid=False); p_chair(k, x + 4, d - 7, r)
def p_filecab(k, x, d, r): k.B(x, d, 8, 6, 20, (96, 108, 112)); [k.F(x + 1, x + 7, z, z + .8, (60, 70, 76), d) for z in (6, 12)]; k.F(x + 3, x + 5, 3, 4, (210, 210, 200), d - .1)
def p_safe(k, x, d, r): k.B(x, d, 10, 8, 12, (60, 66, 70)); k.F(x + 2, x + 8, 3, 10, (82, 90, 96), d); job(k, x + 5, d, lambda X, Y, g: g.ellipse([X - 2, Y - 8, X + 2, Y - 5], fill=(200, 180, 90)))
def p_coat(k, x, d, r): k.post(x, d, 26, (110, 84, 60)); job(k, x, d, lambda X, Y, g: (g.line([(X, Y - 24), (X + 6, Y - 20)], fill=(110, 84, 60)), g.rectangle([X + 3, Y - 20, X + 8, Y - 10], fill=(90, 70, 90))))
def p_machine(k, x, d, r): k.B(x, d, 8, 6, 15, (130, 56, 56)); k.F(x + 2, x + 6, 8, 12, (230, 210, 150), d); k.F(x + 3, x + 5, 3, 4, (30, 30, 36), d - .1); k.glow(x + 4, d, 14, (255, 220, 150), .2)

def p_root(k, x, d, r):
    def f(X, Y, g):
        for s in (-1, 1): g.line([(X, Y - 4), (X + s * 10, Y)], fill=(80, 54, 36), width=3); g.line([(X + s * 10, Y), (X + s * 14, Y + 1)], fill=(66, 44, 30), width=2)
    job(k, x, d, f, 3)
def p_tshroom(k, x, d, r):
    def f(X, Y, g): g.line([(X, Y), (X, Y - 8)], fill=(220, 210, 180), width=2); g.ellipse([X - 6, Y - 14, X + 6, Y - 6], fill=r.choice(((200, 70, 60), (220, 170, 70)))); g.point((X - 2, Y - 11), fill=(255, 250, 240)); g.point((X + 2, Y - 9), fill=(255, 250, 240))
    job(k, x, d, f, 4)
def p_jar(k, x, d, r): k.B(x, d, 4, 4, 6, (190, 220, 200)); k.B(x + 1, d + 1, 2, 2, 4, (255, 232, 150), z0=1, solid=False); k.glow(x + 2, d + 1, 22, (255, 232, 150), .45)
def p_hammock(k, x, d, r): flat(k, x, d, 12, 3, (170, 120, 90)); flat(k, x, d, 9, 2, (200, 150, 110)); k.post(x - 13, d, 14, (96, 66, 44)); k.post(x + 13, d, 14, (96, 66, 44))
def p_pots(k, x, d, r): k.B(x, d, 4, 4, 5, (200, 150, 70)); k.B(x + 5, d + 1, 4, 4, 4, (180, 120, 60)); k.B(x + 2, d - 4, 3, 3, 3, (210, 160, 80))
def p_acorns(k, x, d, r): k.B(x, d, 8, 6, 3, (150, 100, 56), solid=False); [k.rock(x + 1 + i * 2, d + 1, 2, (176, 120, 70)) for i in range(3)]
def p_tstump(k, x, d, r): k.B(x, d, 7, 7, 6, (140, 96, 60)); k.B(x - .6, d - .6, 8.2, 8.2, 1, (180, 130, 84), z0=6, solid=False)

def D(name, fn, mode, rng, gap): return (name, fn, mode, rng, gap)
THEMES = {
 'snow': dict(label='눈 숲길', ground=snow_ground, face=face_rock((176, 196, 224), (70, 84, 120)), H=64, walls=[w_snow], pits=[0], floor=(196, 212, 238), blocked=dark_blocked((200, 212, 232), (190, 204, 228)), vig=.16, wob=1,
   props=[D('fir', p_fir, 'edge', (3, 6), 12), D('stump', p_stump, 'any', (1, 3), 8), D('mound', p_mound, 'any', (2, 4), 7), D('lantern', p_lantern, 'edge', (1, 2), 22), D('log', p_log, 'any', (0, 2), 14), D('sign', p_sign, 'edge', (0, 2), 10), D('snowman', p_snowman, 'mid', (0, 1), 12), D('ice', p_icepatch, 'any', (1, 3), 10), D('bush', p_bush, 'edge', (1, 4), 7)]),
 'lake': dict(label='얼음 호수', ground=ice_ground, face=face_rock((120, 170, 210), (24, 48, 96)), H=66, walls=[w_night], pits=[0], floor=(12, 22, 50), blocked=dark_blocked((16, 30, 66), (24, 40, 84)), vig=.2, wob=2,
   props=[D('deadtree', p_deadtree, 'edge', (2, 5), 14), D('lantern', p_lantern, 'edge', (1, 3), 22), D('hole', p_hole, 'mid', (1, 3), 12), D('drift', p_mound, 'any', (1, 3), 7), D('bucket', p_bucket, 'any', (0, 1), 14), D('shard', p_shard, 'any', (1, 3), 8), D('boat', p_boat, 'mid', (0, 1), 18), D('stones', p_stones, 'any', (0, 2), 8)]),
 'park': dict(label='폐놀이공원', ground=W.park_ground, face=face_rock((96, 80, 110), (30, 22, 44)), H=48, walls=['tent'], pits=[0], floor=(14, 12, 24), blocked=W.BLOCKED['park'], vig=.5, wob=0,
   props=[D('lamp_off', p_lamp(False), 'edge', (1, 3), 12), D('lamp_on', p_lamp(True), 'edge', (0, 1), 30), D('bench', p_bench, 'edge', (1, 2), 14), D('balloon', p_balloon, 'any', (1, 3), 8), D('kiosk', p_kiosk, 'edge', (0, 2), 20), D('cart', p_cart, 'any', (0, 1), 14), D('bumper', p_bumper, 'any', (0, 3), 12), D('bin', p_bin, 'edge', (1, 2), 8), D('fence', p_fence, 'edge', (0, 2), 16), D('horse', p_horse, 'any', (0, 1), 10)]),
 'reed': dict(label='갈대밭', ground=W.reed_ground, face=face_rock((120, 86, 50), (44, 26, 30)), H=52, walls=['reeds'], pits=[0], floor=(60, 40, 26), blocked=W.BLOCKED['reed'], vig=.24, wob=3,
   props=[D('reeds', p_reedc, 'any', (8, 16), 8), D('desk', p_desk, 'any', (0, 2), 14), D('rock', p_rock, 'any', (1, 3), 7), D('scarecrow', p_scarecrow, 'edge', (0, 1), 14), D('hay', p_hay, 'any', (0, 2), 12), D('puddle', p_puddle, 'any', (1, 2), 12), D('fence', p_fence, 'edge', (0, 2), 16)]),
 'woods': dict(label='어두운 숲', ground=W.woods_ground, face=face_rock((40, 44, 50), (8, 8, 14)), H=84, walls=['trunks'], pits=[0], floor=(10, 14, 16), blocked=W.BLOCKED['woods'], vig=.4, wob=3,
   props=[D('tree', p_dtree, 'edge', (5, 9), 13), D('stump', p_wstump, 'any', (1, 2), 8), D('shroom', p_shroom, 'any', (1, 3), 12), D('log', p_wlog, 'any', (0, 2), 14), D('rock', p_wrock, 'any', (1, 3), 7)]),
 'ridge': dict(label='낙엽 능선', ground=W.ridge_ground, face=face_rock((132, 92, 62), (36, 20, 30)), H=58, walls=['rock'], pits=[0], floor=(30, 16, 22), blocked=dark_blocked((40, 24, 30), (50, 30, 34)), vig=.36, wob=1.5,
   props=[D('tree', p_atree, 'edge', (2, 4), 14), D('fence', p_fence, 'edge', (0, 2), 16), D('cairn', p_cairn, 'any', (1, 2), 9), D('shroom', p_redshroom, 'any', (1, 3), 8), D('sign', p_sign, 'edge', (0, 1), 10), D('boulder', p_boulder, 'edge', (1, 2), 10), D('planks', p_planks, 'any', (0, 1), 12)]),
 'roofs': dict(label='밤 옥상', ground=W.roof_ground, face=W.face_building, H=54, walls=['facade'], pits=[0], floor=(12, 13, 26), blocked=dark_blocked((22, 24, 44), (30, 32, 54)), vig=.36, wob=0,
   props=[D('tank', p_tank, 'edge', (0, 1), 20), D('ac', p_ac, 'edge', (1, 3), 12), D('hut', p_hut, 'edge', (0, 1), 26), D('line', p_line, 'edge', (0, 1), 34), D('antenna', p_antenna, 'edge', (0, 2), 10), D('skylight', p_skylight, 'mid', (0, 2), 14), D('vent', p_vent, 'edge', (1, 3), 8), D('planter', p_planter, 'edge', (0, 2), 12), D('lamp', p_roofl, 'edge', (0, 2), 18), D('chimney', p_chimney, 'edge', (0, 1), 10), D('spool', p_spool, 'any', (0, 1), 10)]),
 'hall': dict(label='학교 복도', ground=W.hall_ground, face=face_rock((70, 76, 70), (10, 8, 14)), H=40, walls=['class'], pits=[0], floor=(20, 20, 24), blocked=W.BLOCKED['hall'], vig=.4, wob=0,
   props=[D('locker', p_hlocker, 'edge', (1, 3), 18), D('desk', p_desk, 'any', (0, 2), 14), D('mop', p_hmop, 'edge', (0, 1), 12), D('trophy', p_trophy, 'edge', (0, 1), 16), D('bench', p_hbench, 'edge', (0, 2), 14), D('shoes', p_shoes, 'any', (1, 2), 8), D('chair', p_chair, 'any', (0, 2), 8), D('bin', p_bin, 'edge', (0, 2), 8)]),
 'cabin': dict(label='통나무집', ground=wood_ground, face=face_rock((120, 84, 56), (40, 26, 20)), H=44, walls=[w_logs], pits=[0], floor=(30, 20, 16), blocked=dark_blocked((54, 36, 26), (64, 44, 32)), vig=.3, wob=0,
   props=[D('table', p_table, 'mid', (0, 2), 18), D('bed', p_bed, 'edge', (0, 1), 22), D('fire', p_fire, 'edge', (0, 1), 22), D('rug', p_rug, 'mid', (1, 2), 14), D('crate', p_crate, 'edge', (1, 3), 12), D('shelf', p_shelf, 'edge', (0, 2), 16), D('barrel', p_barrel, 'edge', (0, 2), 8), D('stool', p_stool, 'any', (1, 3), 8), D('stove', p_stove, 'edge', (0, 1), 12), D('lantern', p_hlantern, 'edge', (1, 2), 18)]),
 'library': dict(label='도서관', ground=parquet_ground, face=face_rock((96, 64, 44), (30, 20, 16)), H=58, walls=[w_shelves], pits=[0], floor=(24, 16, 14), blocked=dark_blocked((40, 26, 22), (50, 34, 28)), vig=.38, wob=0,
   props=[D('bookcase', p_bookcase, 'edge', (2, 4), 20), D('readtable', p_readtable, 'mid', (0, 2), 18), D('ladder', p_ladder, 'edge', (0, 1), 12), D('globe', p_globe, 'any', (0, 1), 10), D('books', p_books, 'any', (1, 3), 8), D('cart', p_cart2, 'any', (0, 1), 14), D('sofa', p_sofa, 'edge', (0, 1), 20), D('cabinet', p_cabinet, 'edge', (0, 2), 14), D('lamp', p_flamp, 'edge', (1, 2), 18)]),
 'office': dict(label='매표소', ground=lino_ground, face=face_rock((120, 124, 100), (30, 30, 26)), H=42, walls=[w_office], pits=[0], floor=(30, 30, 26), blocked=dark_blocked((70, 76, 64), (78, 84, 72)), vig=.34, wob=0,
   props=[D('counter', p_counter, 'edge', (0, 1), 30), D('desk', p_odesk, 'mid', (0, 2), 20), D('filecab', p_filecab, 'edge', (1, 3), 10), D('safe', p_safe, 'edge', (0, 1), 12), D('coat', p_coat, 'edge', (0, 2), 8), D('bench', p_hbench, 'edge', (0, 2), 14), D('machine', p_machine, 'edge', (0, 1), 10), D('bin', p_bin, 'edge', (0, 2), 8), D('chair', p_chair, 'any', (0, 2), 8)]),
 'tree': dict(label='나무집 속', ground=bark_ground, face=face_rock((140, 96, 60), (40, 26, 20)), H=56, walls=[w_bark], pits=[0], floor=(34, 22, 16), blocked=dark_blocked((70, 46, 30), (84, 56, 36)), vig=.3, wob=1,
   props=[D('root', p_root, 'edge', (2, 4), 14), D('shroom', p_tshroom, 'any', (1, 3), 10), D('jar', p_jar, 'edge', (1, 3), 14), D('hammock', p_hammock, 'mid', (0, 1), 26), D('pots', p_pots, 'edge', (0, 2), 10), D('acorns', p_acorns, 'any', (0, 2), 9), D('stump', p_tstump, 'any', (0, 2), 10), D('stool', p_stool, 'any', (0, 2), 8), D('table', p_table, 'mid', (0, 1), 18)]),
}
ORDER = ['snow', 'lake', 'park', 'reed', 'woods', 'ridge', 'roofs', 'hall', 'cabin', 'library', 'office', 'tree']

# ---------------- 연결표 · 번호 ----------------
# scene_chains.json: 테마별 장면 순서. 처음 한 번 만들어 저장하고, 이후에는 이 파일을 고쳐 장면을 빼거나 끼운다(번호는 scene_ids.json 에 고정).
CHAIN_PATH = os.path.join(HERE, 'scene_chains.json')
OPP = {'L': 'R', 'R': 'L', 'B': 'F', 'F': 'B'}                                  # 방의 면: L 왼쪽 벽, R 오른쪽(열린 쪽), B 뒷벽, F 앞쪽(열린 쪽)
INW = {'L': (1, 0), 'R': (-1, 0), 'B': (0, -1), 'F': (0, 1)}                    # 그 면의 문에서 방 안쪽으로 향하는 방향
TRAVEL = {'L': (-1, 0), 'R': (1, 0), 'B': (0, 1), 'F': (0, -1)}                 # 그 면으로 나갈 때 몸이 움직이는 방향
HONLY = ('long', 'tunnel', 'zig')                                               # 가로로만 이어지는 장면(왼쪽→오른쪽)

def gen_chains():
    out = {}
    for th in ORDER:
        r = random.Random(sum(map(ord, th)) * 977); P = sorted(r.sample(range(1, 9), 4)); shapes = ['wide'] * 10
        for i in (2, 6): shapes[i] = 'long'
        free = [i for i in range(10) if i not in (2, 6)]; r.shuffle(free)
        for q, i in enumerate(free): shapes[i] = ('square', 'square', 'deep', 'wide', 'square', 'wide', 'deep', 'wide')[q]
        pk = ['tunnel', 'bend', 'zig', 'bend']; r.shuffle(pk); seq = []
        for i in range(10):
            seq.append(dict(key='%sx%02d' % (th, i + 1), kind='room', shape=shapes[i]))
            if i in P: seq.append(dict(key='%sp%02d' % (th, P.index(i) + 1), kind='passage', shape=pk[P.index(i)]))
        entry, epos = 'L', .5
        for n, s in enumerate(seq):
            nxt = seq[n + 1] if n + 1 < len(seq) else None
            if s['shape'] in HONLY and entry not in 'LR': s['shape'] = 'bend' if s['kind'] == 'passage' else 'wide'               # 가로 전용인데 세로로 들어오면 모양을 바꾼다
            s['entry'], s['epos'] = entry, epos; sh = s['shape']; hnext = nxt is not None and (nxt['shape'] in HONLY)
            if sh in HONLY: ex = OPP[entry]
            elif sh == 'bend': ex = r.choice('BF' if entry in 'LR' else 'LR')
            else:
                ex = OPP[entry] if r.random() < .55 else r.choice([c for c in 'LRBF' if c not in (entry, OPP[entry])])
                if sh == 'deep' and r.random() < .6: ex = 'B' if entry in 'LR' else OPP[entry]
            if hnext and ex in 'BF':                                                                                                 # 다음이 가로 전용이면 L/R 로 나간다
                if sh == 'bend': s['shape'] = sh = 'tunnel'; ex = OPP[entry]
                else: ex = OPP[entry] if OPP[entry] in 'LR' else r.choice('LR')
                if ex == entry: ex = OPP[entry]
            s['exit'] = ex
            lo, hi = (.4, .6) if (nxt is not None and nxt['kind'] == 'passage') or s['kind'] == 'passage' else (.3, .7)
            s['xpos'] = round(r.uniform(lo, hi), 2)
            if sh == 'tunnel': s['xpos'] = epos
            if sh == 'zig': s['xpos'] = .22 if epos > .5 else .78
            epos = s['xpos']; entry = OPP[ex]
            s['link'] = r.choice(('pan', 'pan', 'door', 'door', 'door')) if r.random() < .5 else r.choice(('pan', 'door')); s['gate'] = r.randrange(3)
        out[th] = seq
    return out
def load_chains():
    if os.path.exists(CHAIN_PATH): return json.load(open(CHAIN_PATH))
    c = gen_chains(); json.dump(c, open(CHAIN_PATH, 'w'), ensure_ascii=False, indent=1); return c

# ---------------- 문(넘어가는 자리): 테마 소재로 만든다 ----------------
# 레시피: (이름, 기둥 종류, 기둥 높이, 기둥 색, 상인방 색, 안쪽 빛 색, 바닥 빛 깔기)
GATE_RECIPES = {
 'snow': [('전나무 아치', 'fir', 74, None, None, (255, 244, 214)), ('얼음 동굴 입구', 'ice', 60, (206, 228, 248), (214, 236, 252), (222, 244, 255)), ('눈 쌓인 석등 문', 'lantern', 44, None, (236, 242, 252), (255, 240, 200))],
 'lake': [('얼음 아치', 'ice', 64, (170, 214, 244), (196, 228, 250), (220, 242, 255)), ('잔교 끝 등불 문', 'post', 52, (120, 84, 56), (140, 98, 64), (255, 226, 170)), ('얼음 틈 문', 'rock', 46, (150, 190, 222), None, (210, 236, 255))],
 'park': [('간판 아치', 'post', 58, (110, 84, 66), (190, 60, 70), (255, 214, 150)), ('개찰구', 'post', 40, (80, 70, 92), (150, 130, 110), (255, 226, 170)), ('천막 자락 문', 'crate', 50, (190, 60, 70), (214, 200, 180), (255, 214, 150))],
 'reed': [('갈라진 갈대 틈', 'reeds', 26, None, None, (255, 230, 170)), ('짚더미 문', 'hay', 40, None, (214, 176, 84), (255, 232, 180)), ('허수아비 문', 'post', 54, (110, 84, 60), (110, 84, 60), (255, 230, 170))],
 'woods': [('속 빈 나무 문', 'trunk', 92, (46, 38, 56), (56, 46, 66), (130, 232, 212)), ('뿌리 아치', 'trunk', 64, (62, 48, 40), (70, 54, 44), (150, 220, 200)), ('버섯 빛 문', 'shroom', 20, None, None, (130, 232, 212))],
 'ridge': [('나무 도리이', 'post', 66, (150, 60, 50), (170, 70, 56), (255, 190, 120)), ('바위 틈 문', 'rock', 70, (130, 104, 96), None, (255, 190, 120)), ('밧줄 문', 'post', 50, (120, 84, 60), (190, 160, 110), (255, 200, 140))],
 'roofs': [('계단실 문', 'locker', 50, (96, 98, 124), (120, 122, 146), (255, 214, 150)), ('옥상 해치', 'crate', 30, (110, 114, 140), None, (255, 220, 160)), ('널다리 입구', 'post', 46, (120, 90, 64), (150, 108, 70), (255, 214, 150))],
 'hall': [('교실 문', 'locker', 44, (120, 92, 70), (140, 108, 80), (255, 236, 190)), ('사물함 틈', 'locker', 48, (96, 124, 140), None, (255, 236, 190)), ('계단 입구', 'post', 44, (130, 130, 120), (150, 150, 140), (255, 240, 200))],
 'cabin': [('통나무 문', 'log', 52, (126, 84, 50), (140, 96, 58), (255, 214, 150)), ('커튼 문', 'post', 46, (120, 70, 66), (170, 70, 70), (255, 214, 150)), ('지하 해치', 'crate', 30, (130, 94, 60), None, (255, 200, 130))],
 'library': [('책장 아치', 'case', 56, (78, 52, 38), (96, 66, 46), (255, 226, 170)), ('책 무더기 문', 'books', 54, None, None, (255, 226, 170)), ('사다리 책장 문', 'case', 62, (86, 58, 42), (110, 76, 52), (255, 230, 180))],
 'office': [('매표 창구 문', 'locker', 46, (110, 90, 64), (150, 126, 96), (255, 230, 180)), ('회전문', 'post', 40, (90, 96, 100), (130, 136, 140), (255, 236, 190)), ('철문', 'locker', 50, (96, 108, 112), (120, 130, 134), (255, 236, 190))],
 'tree': [('옹이구멍 문', 'trunk', 60, (96, 66, 42), (110, 76, 48), (255, 218, 150)), ('뿌리 굴', 'trunk', 46, (86, 58, 38), None, (255, 218, 150)), ('밧줄 사다리 문', 'post', 56, (130, 100, 64), (160, 130, 86), (255, 224, 160))]}

class GT:                                                                       # 방의 한 면(L/R/B/F)에 붙는 문을 그리는 도우미
    def __init__(s, k, side, lx, ld, Wl, Dl):
        s.k, s.side, s.Wl, s.Dl = k, side, Wl, Dl; s.u = ld if side in 'LR' else lx; s.o = {'L': 1.2, 'R': Wl - 2.0, 'B': Dl - 1.2, 'F': 2.0}[side]
    def plane(s, u0, u1, z0, z1, c):
        if s.side in 'LR': s.k.L(s.u + u0, s.u + u1, z0, z1, c, s.o)
        else: s.k.F(s.u + u0, s.u + u1, z0, z1, c, s.o, back=(s.side == 'B'))
    def blk(s, du, span, depth, h, c, z0=0):
        u = s.u + du - span / 2
        if s.side == 'L': s.k.B(s.o - 1, u, depth, span, h, c, z0=z0, solid=False)
        elif s.side == 'R': s.k.B(s.o - depth + 1, u, depth, span, h, c, z0=z0, solid=False)
        elif s.side == 'B': s.k.B(u, s.o - depth + 1, span, depth, h, c, z0=z0, solid=False)
        else: s.k.B(u, s.o - 1, span, depth, h, c, z0=z0, solid=False)
    def pt(s, du, inw):
        if s.side == 'L': return (s.o + inw, s.u + du)
        if s.side == 'R': return (s.o - inw, s.u + du)
        if s.side == 'B': return (s.u + du, s.o - inw)
        return (s.u + du, s.o + inw)
    def pillar(s, du, kind, h, c, r):
        k = s.k; x, d = s.pt(du, 5); nb, nr = len(k.block), len(k.rects)
        if kind == 'fir': fir2(k.sc, x, d, h)
        elif kind == 'ice': s.blk(du, 9, 8, h * .5, c or (190, 224, 246)); s.blk(du + 1, 7, 6, h * .3, tuple(min(255, v + 14) for v in (c or (190, 224, 246))), z0=h * .5); s.blk(du, 5, 5, h * .2, (236, 248, 255), z0=h * .8)
        elif kind == 'post': s.blk(du, 3.4, 3.4, h, c or (110, 84, 66))
        elif kind == 'trunk': s.blk(du, 9, 9, h, c or (46, 38, 56)); s.blk(du, 6, 6, 3, tuple(min(255, v + 22) for v in (c or (46, 38, 56))), z0=h)
        elif kind == 'reeds': p_reedc(k, x, d, random.Random(int(x * 3 + d)))
        elif kind == 'books':
            pal = ((150, 50, 50), (60, 90, 130), (200, 170, 70), (70, 110, 80), (120, 70, 120), (190, 190, 170)); z = 0; i = 0
            while z < h: s.blk(du + (i % 3 - 1) * .8, 10 - (i % 2) * 2, 7, 5, pal[(i + int(abs(du))) % 6], z0=z); z += 5; i += 1
        elif kind == 'case': s.blk(du, 10, 7, h, c or (78, 52, 38)); [s.plane(du - 4, du + 4, z, z + 6, col_) for z, col_ in ((6, (150, 50, 50)), (20, (60, 90, 130)), (34, (200, 170, 70)), (46, (70, 110, 80))) if z + 6 < h]
        elif kind == 'locker': s.blk(du, 9, 6, h, c or (96, 124, 140)); s.plane(du - 3, du + 3, h * .5, h * .5 + 3, (40, 50, 60))
        elif kind == 'rock': k.rock(x, d, 7, c or (130, 104, 96)); k.rock(x, d, 5, tuple(min(255, v + 20) for v in (c or (130, 104, 96))))
        elif kind == 'crate': s.blk(du, 9, 8, h, c or (150, 112, 70)); s.blk(du, 7, 6, 2, (230, 220, 200), z0=h)
        elif kind == 'lantern': RDL.lantern(k.sc, x, d); s.blk(du, 6, 6, 8, (236, 242, 252))
        elif kind == 'shroom': p_shroom(k, x, d, random.Random(1)); p_shroom(k, x + 3, d + 3, random.Random(2))
        elif kind == 'hay': s.blk(du, 10, 9, h, (214, 176, 84)); s.blk(du, 8, 7, 3, (230, 196, 110), z0=h)
        elif kind == 'log':
            z = 0
            while z < h: s.blk(du, 10, 7, 6, (126, 84, 50) if (z // 6) % 2 else (112, 72, 42), z0=z); z += 6
        del k.block[nb:]; del k.rects[nr:]
def gateway(k, th, side, lx, ld, Wl, Dl, gi, mode, r):                          # mode: door(문) / open(트인 입구) / closed(닫힌 문)
    nm, pk, ph, pc, lc, inn = GATE_RECIPES[th][gi % 3]; g = GT(k, side, lx, ld, Wl, Dl); half = 12.5
    ph2 = ph * (.55 if mode == 'open' else 1)
    for sgn in (-1, 1): g.pillar(sgn * (half + 4.5), pk, ph2, pc, r)
    if mode != 'open':
        top = max(40, min(ph, 52)) if pk in ('fir', 'reeds', 'shroom', 'lantern') else ph
        if lc: g.blk(0, 2 * (half + 8), 5, 4, lc, z0=top)
        g.plane(-half, half, 0, top - 1, (22, 20, 28) if mode == 'closed' else inn)
        if mode == 'closed': g.plane(-half, half, top * .45, top * .45 + 2, (70, 60, 56)); g.plane(-half, half, top * .15, top * .15 + 2, (70, 60, 56))
    if mode != 'closed':
        x, d = g.pt(0, 8); k.glow(x, d, 34 if mode == 'door' else 26, inn, .5 if mode == 'door' else .35); flat(k, x, d, 11 if side in 'LR' else 12, 4, tuple(min(255, int(v * .8 + 40)) for v in inn))
        for q in (16, 24):
            x, d = g.pt(0, q); flat(k, x, d, 3, 1, inn)
    return nm
def FC(th, gi): return ','.join(str(int(v * .55)) for v in GATE_RECIPES[th][gi % 3][5])

# ---------------- 막는 소품 · 골목 벽 ----------------
SOLID = {'fir', 'tree', 'deadtree', 'kiosk', 'hut', 'tank', 'counter', 'bed', 'fire', 'bookcase', 'shelf', 'locker', 'cabinet', 'filecab', 'safe', 'machine', 'sofa', 'table', 'readtable', 'desk', 'ladder', 'trophy', 'stove', 'antenna', 'line', 'chimney', 'lamp_on', 'lamp_off', 'lantern', 'horse', 'boat', 'scarecrow', 'boulder', 'hay', 'cart', 'bumper', 'ac', 'root', 'lamp'}
BARLOW = {                                                                     # 통로의 앞쪽(카메라 쪽) 벽: 길이 가려지지 않게 낮게
 'snow': lambda k, x, d, r: k.rock(x + 3, d + 3, 5, (238, 244, 252)), 'lake': lambda k, x, d, r: k.B(x, d, 7, 6, 9, (178, 220, 244)), 'park': lambda k, x, d, r: (k.B(x, d, 7, 2, 8, (110, 84, 66)), k.B(x, d, 7, 2, 1.4, (150, 120, 90), z0=8, solid=False)),
 'reed': lambda k, x, d, r: (k.reed(x, d, 11), k.reed(x + 3, d, 12), k.block.append((x, d, 3))), 'woods': lambda k, x, d, r: (k.B(x, d, 6, 6, 6, (54, 44, 56)), k.B(x - .5, d - .5, 7, 7, 1, (72, 60, 70), z0=6, solid=False)),
 'ridge': lambda k, x, d, r: k.rock(x + 2, d + 2, 4, (130, 104, 96)), 'roofs': lambda k, x, d, r: k.B(x, d, 7, 4, 8, (110, 114, 140)), 'hall': lambda k, x, d, r: k.B(x, d, 7, 4, 8, (150, 112, 76)),
 'cabin': lambda k, x, d, r: k.B(x, d, 8, 7, 9, (150, 112, 70)), 'library': lambda k, x, d, r: (k.B(x, d, 7, 5, 4, (150, 50, 50)), k.B(x + .5, d + .5, 6, 4, 4, (60, 90, 130), z0=4, solid=False)),
 'office': lambda k, x, d, r: k.B(x, d, 7, 5, 9, (130, 100, 72)), 'tree': lambda k, x, d, r: k.B(x, d, 6, 6, 9, (96, 66, 42))}
BAR = {                                                                        # 골목·통로 벽(막는 소품 한 칸). 통로 양옆에 줄지어 서서 벽을 이룬다
 'snow': lambda k, x, d, r: (fir2(k.sc, x + 3, d + 3, r.choice((58, 66, 74))), k.block.append((x + 3, d + 3, 4))), 'lake': lambda k, x, d, r: (k.B(x, d, 7, 6, r.choice((18, 24, 30)), (178, 220, 244)), k.B(x + 1, d + 1, 4, 4, 4, (232, 248, 255), z0=24, solid=False)),
 'park': lambda k, x, d, r: (k.B(x, d, 7, 3, 22, (190, 60, 70) if int(x / 7) % 2 else (214, 200, 180)), k.B(x, d, 7, 3, 2, (120, 96, 70), z0=22, solid=False)), 'reed': lambda k, x, d, r: (p_reedc(k, x, d, r), k.block.append((x, d, 4))),
 'woods': lambda k, x, d, r: p_dtree(k, x, d, r), 'ridge': lambda k, x, d, r: (k.rock(x + 2, d + 2, 6, (130, 104, 96)), k.rock(x + 2, d + 2, 4, (150, 122, 110))),
 'roofs': lambda k, x, d, r: k.B(x, d, 7, 5, r.choice((14, 20, 26)), (110, 114, 140)), 'hall': lambda k, x, d, r: (k.B(x, d, 6, 4, 28, (96, 124, 140)), k.F(x + 1, x + 5, 16, 18, (40, 50, 60), d)),
 'cabin': lambda k, x, d, r: k.B(x, d, 8, 7, r.choice((14, 20, 26)), (150, 112, 70)), 'library': lambda k, x, d, r: (k.B(x, d, 7, 5, 38, (78, 52, 38)), [k.F(x + 1, x + 6, z, z + r.randint(5, 8), r.choice(((150, 50, 50), (60, 90, 130), (200, 170, 70), (70, 110, 80))), d) for z in (4, 13, 22, 31)]),
 'office': lambda k, x, d, r: k.B(x, d, 7, 6, 24, (96, 108, 112)), 'tree': lambda k, x, d, r: k.B(x, d, 6, 6, 34, (96, 66, 42))}

# ---------------- 장면 사양 ----------------
def gate_pt(side, pos, Wd, Dd):
    span = Dd if side in 'LR' else Wd; c = max(15, min(span - 15, span * pos))
    return {'L': (0, c), 'R': (Wd, c), 'B': (c, Dd), 'F': (c, 0)}[side]
def route_pts(s, a, b, Wd, Dd, r):
    ent, ext = s['entry'], s['exit']; sh = s['shape']
    if sh == 'zig': x1 = Wd * .5; return [a, (x1, a[1]), (x1, b[1]), b]
    if ent in 'LR' and ext in 'LR' or ent in 'BF' and ext in 'BF':
        pts = [a, b]
        if sh in ('wide', 'square', 'deep', 'long') and r.random() < .55:                                                     # 완만한 굽이
            vert = ent in 'BF'; mid = [((a[0] * (1 - f) + b[0] * f), (a[1] * (1 - f) + b[1] * f)) for f in (.33, .66)]; off = r.choice((-1, 1)) * (Wd if vert else Dd) * .16
            mid = [(m[0] + off * (1 if i == 0 else -1), m[1]) if vert else (m[0], m[1] + off * (1 if i == 0 else -1)) for i, m in enumerate(mid)]; pts = [a, mid[0], mid[1], b]
        return pts
    c = (b[0], a[1]) if ent in 'LR' else (a[0], b[1]); return [a, c, b]                                                       # ㄱ자로 꺾이는 길
def make_spec(th, s):
    key = s['key']; r = random.Random(sum(ord(ch) * (i + 1) for i, ch in enumerate(key))); sh = s['shape']; T = THEMES[th]
    if sh == 'long': Wd, Dd = r.randint(330, 470), r.randint(46, 54)
    elif sh == 'wide': Wd, Dd = r.randint(92, 112), r.randint(60, 76)
    elif sh == 'square': Wd, Dd = r.randint(84, 100), r.randint(84, 100)
    elif sh == 'deep': Wd, Dd = r.randint(66, 78), r.randint(98, 114)
    elif sh == 'tunnel': Wd, Dd = r.randint(300, 400), 44
    elif sh == 'bend': Wd, Dd = r.randint(112, 128), r.randint(100, 110)
    else: Wd, Dd = r.randint(220, 260), r.randint(84, 92)
    a = gate_pt(s['entry'], s['epos'], Wd, Dd); b = gate_pt(s['exit'], s['xpos'], Wd, Dd)
    if sh == 'tunnel': b = (b[0], a[1])
    pts = route_pts(s, a, b, Wd, Dd, r); hw = 13 if s['kind'] == 'passage' else 14
    shapes = [('path', pts, hw)]
    if s['kind'] == 'room' and sh in ('square', 'wide') and r.random() < .6: c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); shapes.append(('circle', c[0], c[1], r.randint(20, 26)))
    spec = dict(key=key, theme=th, chain=s, kind=s['kind'], shape=sh, W=Wd, D=Dd, pts=pts, hw=hw, shapes=shapes, a=a, b=b, ent=s['entry'], ext=s['exit'], seed=r.randint(0, 9), tries=0, density=1.0, alleys=[], tips=[])
    spec['wall'] = r.choice(T['walls'])
    def zone(side, p): v = INW[side]; return (p[0] + v[0] * 4, p[1] + v[1] * 4), (p[0] + v[0] * 14, p[1] + v[1] * 14)
    spec['ea'], spec['st'] = zone(s['entry'], a); spec['eb'], spec['ab'] = zone(s['exit'], b)
    if s['kind'] == 'room':                                                                                                  # 딸린 골목(뒷벽에 붙은 칸)
        n = r.choice((2, 3)) if sh == 'long' else (1 if r.random() < .5 and sh != 'deep' else 0)
        xs = []
        for _ in range(120):
            if len(xs) >= n: break
            x = r.uniform(26, Wd - 26); ln = r.randint(26, 34)
            if any(abs(x - q) < 48 for q in xs): continue
            if (s['entry'] == 'B' and abs(x - a[0]) < 34) or (s['exit'] == 'B' and abs(x - b[0]) < 34): continue
            xx = [x - 22 + 44 * i / 5 for i in range(6)]; dd = [Dd - 4 - ln * j / 4 for j in range(5)]
            e = W.sd(shapes, np.array([[u for u in xx] for _ in dd]), np.array([[v] * 6 for v in dd]))
            if e.min() < 1: continue
            xs.append(x); spec['alleys'].append((x, ln, 17)); spec['tips'].append((x, Dd - 4 - ln / 2))
    return spec

def setup(name, spec):
    T = THEMES[spec['theme']]; H = T['H']
    if spec['shape'] in ('long', 'tunnel', 'zig'): H = min(H, 66)
    elif spec['shape'] in ('square', 'deep', 'bend'): H = min(H, 62)
    box = dict(wall=spec['wall'], vig=T['vig'] * (.6 if spec['shape'] in ('long', 'tunnel') else 1))
    W.BLOCKED[name] = lambda x, d, n, g=T['ground']: np.clip(g(x, d, np.full(n, -10.), n), 0, 255).astype(int)               # 바닥은 길 없이 한 가지 무늬
    ent = dict(H=H, shapes=spec['shapes'], zones=[], ground=T['ground'], face=T['face'], ch=30, sky=((20, 20, 30), (40, 40, 60)), start=spec['st'], box=box, wob=T['wob'], exits=[], bbox=(0, 0, spec['W'], spec['D']))
    W.AREAS[name] = ent; W.STRICT.add(name); MORE[name] = spec; return ent

def more_props(name, k, tr, inside, rng):
    spec = MORE[name]; T = THEMES[spec['theme']]; th = spec['theme']; r = random.Random(sum(map(ord, name)) * 7 + spec['tries'] * 101); sc = k.sc; Wl, Dl = sc.W, sc.D; s = spec['chain']
    gates = []
    for side, p, mode, gi in spec['gates']:
        lx, ld = tr(p); gateway(k, th, side, lx, ld, Wl, Dl, gi, mode, r); gates.append((lx, ld))
    placed = [(a, b, 16) for a, b in gates] + [(tr(spec['st'])[0], tr(spec['st'])[1], 14), (tr(spec['ab'])[0], tr(spec['ab'])[1], 14)]
    area = spec['W'] * spec['D'] / 6800.0
    if spec['kind'] == 'passage':                                                                                            # 통로 벽: 길 양옆에 소품이 줄지어 서서 벽을 이룬다
        pts = spec['pts']; hw = spec['hw'] + 5; dens_pass = 0
        for (p0, p1) in zip(pts, pts[1:]):
            L_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = int(L_ // 7) + 1; ux, ud = (p1[0] - p0[0]) / (L_ or 1), (p1[1] - p0[1]) / (L_ or 1)
            for i in range(n + 1):
                cx, cd = p0[0] + ux * min(i * 7, L_), p0[1] + ud * min(i * 7, L_)
                for sg in (-1, 1):
                    x, d = cx - ud * hw * sg, cd + ux * hw * sg
                    if not (-1 < x < spec['W'] + 1 and -1 < d < spec['D'] + 1): continue
                    if float(inside(x, d)) < hw - spec['hw'] - 1.5 + 0.0 and False: continue
                    if any(math.hypot(x - q[0], d - q[1]) < spec['hw'] + 3.5 for q in spec['pts_samples']): continue            # 다른 구간의 길 위는 비운다
                    lx, ld = tr((x, d))
                    if any(math.hypot(lx - a, ld - b) < 20 for a, b in gates): continue
                    if any(math.hypot(lx - a, ld - b) < 6.5 for a, b, g_ in placed if g_ == 7): continue
                    (BARLOW if d < cd - 3 else BAR)[th](k, lx - 3.5, ld - 3, r); placed.append((lx, ld, 7))
    for (ax, ln, w) in spec['alleys']:
        lx = ax + 3; n_ = int(ln // 7) + 1
        for q in range(n_):
            dd = Dl - 4 - q * 7
            for sx in (lx - w, lx + w): BAR[th](k, sx - 3, dd - 3, r)
        tipx, tipd = lx, Dl - 12; k.glow(tipx, tipd, 26, (255, 214, 150), .3); cand = [p for p in T['props']]; fn_ = cand[r.randrange(len(cand))][1]
        nb, nr = len(k.block), len(k.rects); fn_(k, tipx - 2, tipd, r); del k.block[nb:]; del k.rects[nr:]; placed.append((lx, Dl - ln / 2, ln))
    dens = spec['density'] * max(.6, area) * (.45 if spec['kind'] == 'passage' else 1)
    kinds = [p for p in T['props'] if p[3][0] > 0 or r.random() < .55]
    for (nm, fn, mode, (lo, hi), gap) in kinds:
        n = max(0, int(round(r.randint(lo, hi) * dens))); solid = nm in SOLID
        if dens > 0 and lo > 0 and n == 0 and not solid: n = 1
        tries = 0
        while n > 0 and tries < 900:
            tries += 1; x = r.uniform(0, spec['W']); d = r.uniform(0, spec['D']); e = float(inside(x, d)); lx, ld = tr((x, d))
            if not (6 < lx < Wl - 5 and 5 < ld < Dl - 4): continue
            if solid:
                if e < 3: continue                                                                                          # 길(입구↔출구 띠)에는 막는 소품을 두지 않는다
                if min(lx, Wl - lx, ld, Dl - ld) > 24: continue                                                             # 막는 소품은 벽·가장자리 쪽에만
            if any(math.hypot(lx - a, (ld - b) * 1.5) < gap * .5 + g_ * .5 + 2 for a, b, g_ in placed): continue
            nb, nr = len(k.block), len(k.rects); fn(k, lx, ld, r)
            if not solid: del k.block[nb:]; del k.rects[nr:]                                                                   # 막지 않는 장식은 걸을 수 있다
            placed.append((lx, ld, gap)); n -= 1

def reach(mask, meta, spec):
    g = np.array(mask) > 127; gh, gw = g.shape; tot = int(g.sum()); o = meta['origin']
    cell = lambda x, d: (max(0, min(gh - 1, int(d / CELL))), max(0, min(gw - 1, int(x / CELL))))
    def flood(m, s):
        seen = np.zeros_like(m); st = [s]; seen[s] = True
        while st:
            y, x = st.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < gh and 0 <= nx < gw and m[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((ny, nx))
        return seen
    def near(m, c, rad=4):
        ys, xs = np.nonzero(m[max(0, c[0] - rad):c[0] + rad + 1, max(0, c[1] - rad):c[1] + rad + 1])
        if not len(ys): return None
        return (ys[0] + max(0, c[0] - rad), xs[0] + max(0, c[1] - rad))
    s = near(g, cell(*meta['start']), 6)
    if s is None: return False
    seen = flood(g, s)
    if spec['kind'] == 'room' and seen.sum() < .9 * tot: return False                                                                                  # 걸을 수 있는 칸의 90% 이상이 한 덩어리
    for e in meta['exits']:
        z = e['zone']; c = cell((z[0] + z[1]) / 2, (z[2] + z[3]) / 2)
        if not seen[c]: return False
    for (tx, td) in spec['tips']:
        c = cell(tx - o[0], td - o[1])
        if not seen[max(0, c[0] - 4):c[0] + 5, max(0, c[1] - 4):c[1] + 5].any(): return False
    er = g.copy()
    for _ in range(4):                                                                                                      # 길 폭 검사: 8px(약 17px 폭) 깎고도 입구↔출구가 이어져야 한다
        e2 = er.copy(); e2[1:] &= er[:-1]; e2[:-1] &= er[1:]; e2[:, 1:] &= er[:, :-1]; e2[:, :-1] &= er[:, 1:]; er = e2
    s2 = near(er, cell(*meta['start']), 8)
    if s2 is None: return False
    seen2 = flood(er, s2)
    for e in meta['exits']:
        z = e['zone']; c = cell((z[0] + z[1]) / 2, (z[2] + z[3]) / 2)
        if not seen2[max(0, c[0] - 5):c[0] + 6, max(0, c[1] - 5):c[1] + 6].any(): return False
    return True

def main():
    want = sys.argv[1:] or ORDER; W.props_orig = W.props
    def props(name, k, tr, inside, rng):
        if name in MORE: return more_props(name, k, tr, inside, rng)
        return W.props_orig(name, k, tr, inside, rng)
    W.props = props
    chains = load_chains(); allspec = {}
    for th in ORDER:
        for s in chains[th]:
            spec = make_spec(th, s); spec['pts_samples'] = []
            for (p0, p1) in zip(spec['pts'], spec['pts'][1:]):
                L_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); spec['pts_samples'] += [(p0[0] + (p1[0] - p0[0]) * i / max(1, int(L_ / 4)), p0[1] + (p1[1] - p0[1]) * i / max(1, int(L_ / 4))) for i in range(int(L_ / 4) + 1)]
            allspec[s['key']] = spec
    for th in want:
        seq = chains[th]
        for n, s in enumerate(seq):
            spec = allspec[s['key']]; prv = seq[n - 1] if n > 0 else None; nxt = seq[n + 1] if n + 1 < len(seq) else None
            def lk(a, b):
                return (a['link'], a['gate'])
            gates = []; ex = []
            if prv is None: gates.append((s['entry'], spec['a'], 'closed', s['gate']))
            else:
                lt, gi = lk(prv, s); gates.append((s['entry'], spec['a'], 'open' if lt == 'pan' else 'door', gi if lt == 'door' else prv['gate']))
                ex.append(dict(at=spec['ea'], hw=(10 if s['entry'] in 'LR' else 5), hwx=(5 if s['entry'] in 'LR' else 10), fc=FC(th, prv['gate']), to=prv['key'], spawn=allspec[prv['key']]['ab'], dir=s['entry'], type=lt))
            if nxt is None: gates.append((s['exit'], spec['b'], 'closed', s['gate'])); ex.append(dict(at=spec['eb'], hw=(10 if s['exit'] in 'LR' else 5), hwx=(5 if s['exit'] in 'LR' else 10), fc=FC(th, s['gate']), to=None, endMsg='길이 끊겨 있다. 여기서는 더 갈 수 없다', side={'L': 'left', 'R': 'right', 'B': 'back', 'F': 'front'}[s['exit']]))
            else:
                lt, gi = s['link'], s['gate']; gates.append((s['exit'], spec['b'], 'open' if lt == 'pan' else 'door', gi))
                ex.append(dict(at=spec['eb'], hw=(10 if s['exit'] in 'LR' else 5), hwx=(5 if s['exit'] in 'LR' else 10), fc=FC(th, gi), to=nxt['key'], spawn=allspec[nxt['key']]['st'], dir=s['exit'], type=lt))
            spec['gates'] = gates; setup(s['key'], spec); W.AREAS[s['key']]['exits'] = ex
    nav = {}
    for th in want:
        for s in chains[th]:
            nm = s['key']; spec = MORE[nm]; bad = True
            for t in range(10):
                if t == 9: spec['alleys'] = []; spec['tips'] = []                                                         # 끝까지 막히면 골목을 포기한다
                spec['tries'] = t; W.SEEDOFF[nm] = t * 17; spec['density'] = .85 if t < 5 else (.5 if t < 7 else (.25 if t < 9 else .0))
                im, dep, mask, meta = W.build(nm)
                if reach(mask, meta, spec): bad = False; break
            if bad: print('!! 길이 막힘', nm)
            meta['theme'] = th; meta['kind'] = s['kind']; meta['shape'] = s['shape']; meta['label'] = '%s %s' % (THEMES[th]['label'], ('통로' if s['kind'] == 'passage' else '') + s['key'][-2:].lstrip('0')); nav[nm] = meta
            im.save(os.path.join(OUT, 'world_%s.png' % nm)); dep.save(os.path.join(OUT, 'world_%s_depth.png' % nm)); mask.save(os.path.join(OUT, 'world_%s_walk.png' % nm))
        print(th, [(s['key'][-3:], s['shape'], nav[s['key']]['CW'], nav[s['key']]['CH']) for s in chains[th]])
    for nm, meta in nav.items():
        for e in meta['exits']:
            w = e.pop('spawn_w', None)
            if w and e['to'] in nav: o = nav[e['to']]['origin']; e['spawn'] = (round(w[0] - o[0], 1), round(w[1] - o[1], 1))
    old = {}
    p = os.path.join(OUT, 'more_nav.json')
    if os.path.exists(p) and sys.argv[1:]: old = json.load(open(p))
    old.update(nav); json.dump(old, open(p, 'w'), ensure_ascii=False); print('more_nav.json', len(old), 'rooms')
if __name__ == '__main__': main()
