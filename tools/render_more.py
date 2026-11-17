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

# ---------------- 레이아웃 ----------------
# 모든 레이아웃은 들어오는 곳이 왼쪽 가운데, 나가는 곳이 오른쪽 가운데라 방끼리 길이 이어진다. 길은 넓게(폭 26~36), 곁가지 골목(pocket)은 따로 붙인다.
def unit(a, b): dx, dd = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dd) or 1; return (dx / n, dd / n)
def LAY(shapes, Wd, Dd, zones=()): m = Dd / 2; return dict(shapes=shapes, zones=list(zones), a=(0, m), da=(1, 0), b=(Wd, m), db=(-1, 0), m=m)
def L_broad(r, Wd, Dd): h = r.randint(15, 19); m = Dd / 2; return LAY([('rect', 0, m - h, Wd, m + h)], Wd, Dd)
def L_plaza(r, Wd, Dd): R = min(Dd * .46, Wd * .3); m = Dd / 2; return LAY([('circle', Wd / 2, m, R), ('rect', 0, m - 13, Wd * .3, m + 13), ('rect', Wd * .7, m - 13, Wd, m + 13)], Wd, Dd)
def L_plazar(r, Wd, Dd): m = Dd / 2; return LAY([('rect', Wd * .24, 5, Wd * .76, Dd - 5), ('rect', 0, m - 13, Wd * .3, m + 13), ('rect', Wd * .7, m - 13, Wd, m + 13)], Wd, Dd)
def L_wave(r, Wd, Dd): m = Dd / 2; return LAY([('path', bez((0, m), (Wd * .3, m - Dd * r.uniform(.2, .4)), (Wd * .65, m + Dd * r.uniform(.2, .4)), (Wd, m)), r.randint(13, 16))], Wd, Dd)
def L_dumb(r, Wd, Dd): m = Dd / 2; R1 = min(Dd * .42, Wd * .2); R2 = min(Dd * .46, Wd * .2); return LAY([('circle', Wd * .2, m, R1), ('circle', Wd * .8, m, R2), ('rect', 0, m - 13, Wd * .2, m + 13), ('rect', Wd * .8, m - 13, Wd, m + 13), ('rect', Wd * .2, m - 11, Wd * .8, m + 11)], Wd, Dd)
def L_twin(r, Wd, Dd): m = Dd / 2; return LAY([('rect', Wd * .2, 4, Wd * .8, 22), ('rect', Wd * .2, Dd - 22, Wd * .8, Dd - 4), ('rect', Wd * .2, 4, Wd * .2 + 18, Dd - 4), ('rect', Wd * .8 - 18, 4, Wd * .8, Dd - 4), ('rect', 0, m - 13, Wd * .25, m + 13), ('rect', Wd * .75, m - 13, Wd, m + 13)], Wd, Dd)
def L_cross(r, Wd, Dd): m = Dd / 2; return LAY([('rect', 0, m - 13, Wd, m + 13), ('rect', Wd / 2 - 13, 3, Wd / 2 + 13, Dd - 3), ('circle', Wd / 2, m, 20)], Wd, Dd)
def L_fork(r, Wd, Dd): m = Dd / 2; x = Wd * r.uniform(.35, .65); return LAY([('rect', 0, m - 13, Wd, m + 13), ('path', [(x, m), (x + Wd * .12, Dd - 8)], 12), ('circle', x + Wd * .12, Dd - 14, 15), ('path', [(x, m), (x - Wd * .12, 8)], 12), ('circle', x - Wd * .12, 14, 15)], Wd, Dd)
def L_islands(r, Wd, Dd):
    m = Dd / 2; c = [(Wd * .13, m, 16), (Wd * .42, m - Dd * .22, 17), (Wd * .6, m + Dd * .2, 17), (Wd * .88, m, 16)]; br = [[(c[i][0], c[i][1]), (c[i + 1][0], c[i + 1][1])] for i in range(3)]
    return LAY([('circle', *q) for q in c] + [('path', b_, 10) for b_ in br] + [('rect', 0, m - 10, Wd * .13, m + 10), ('rect', Wd * .88, m - 10, Wd, m + 10)], Wd, Dd, [(('path', b_, 10), plank_ground) for b_ in br])
def L_zig(r, Wd, Dd): m = Dd / 2; s = r.choice((-1, 1)) * Dd * .26; return LAY([('path', [(0, m), (Wd * .3, m), (Wd * .3, m + s), (Wd * .7, m + s), (Wd * .7, m), (Wd, m)], r.randint(12, 14))], Wd, Dd)
def L_comb(r, Wd, Dd):
    m = Dd / 2; sh = [('rect', 0, m - 13, Wd, m + 13)]
    for i in range(3): x = Wd * (.22 + .28 * i); sh.append(('rect', x - 11, m, x + 11, Dd - 3) if i % 2 == 0 else ('rect', x - 11, 3, x + 11, m))
    return LAY(sh, Wd, Dd)
def L_vee(r, Wd, Dd): m = Dd / 2; s = r.choice((-1, 1)) * Dd * .26; return LAY([('path', [(0, m), (Wd * .5, m + s), (Wd, m)], 14)], Wd, Dd)
def L_bridge(r, Wd, Dd): m = Dd / 2; return LAY([('rect', 0, m - 18, Wd * .32, m + 18), ('rect', Wd * .68, m - 18, Wd, m + 18), ('rect', Wd * .32 - 10, m - 10, Wd * .68 + 10, m + 10)], Wd, Dd, [(('rect', Wd * .32, m - 10, Wd * .68, m + 10), plank_ground)])
def L_lobes(r, Wd, Dd): m = Dd / 2; return LAY([('circle', Wd * .17, m + r.randint(-6, 6), r.randint(17, 21)), ('circle', Wd * .5, m + r.randint(-8, 8), r.randint(19, 24)), ('circle', Wd * .83, m + r.randint(-6, 6), r.randint(17, 21)), ('rect', 0, m - 12, Wd, m + 12)], Wd, Dd)
def L_plus2(r, Wd, Dd): m = Dd / 2; return LAY([('rect', 0, m - 13, Wd, m + 13), ('rect', Wd * .28 - 13, 3, Wd * .28 + 13, Dd - 3), ('rect', Wd * .72 - 13, 3, Wd * .72 + 13, Dd - 3)], Wd, Dd)
LAYOUTS = [('broad', L_broad, 56), ('plaza', L_plaza, 64), ('plazar', L_plazar, 62), ('wave', L_wave, 64), ('dumbbell', L_dumb, 62), ('twin', L_twin, 70), ('cross', L_cross, 66), ('fork', L_fork, 70), ('islands', L_islands, 68), ('zig', L_zig, 68), ('comb', L_comb, 70), ('vee', L_vee, 66), ('bridge', L_bridge, 62), ('lobes', L_lobes, 62)]

def flip(res, Wd, Dd, fx, fd):                                                  # 좌우·앞뒤를 뒤집어 같은 레이아웃도 다르게 보이게(들어오는 곳은 늘 왼쪽 가운데)
    X = (lambda x: Wd - x) if fx else (lambda x: x); Y = (lambda d: Dd - d) if fd else (lambda d: d)
    def sh(s):
        if s[0] == 'rect': x0, x1 = sorted((X(s[1]), X(s[3]))); d0, d1 = sorted((Y(s[2]), Y(s[4]))); return ('rect', x0, d0, x1, d1)
        if s[0] == 'circle': return ('circle', X(s[1]), Y(s[2]), s[3])
        return ('path', [(X(p[0]), Y(p[1])) for p in s[1]], s[2])
    o = dict(res); o['shapes'] = [sh(s) for s in res['shapes']]; o['zones'] = [(sh(z), g) for z, g in res.get('zones', [])]
    return o

# ---------------- 문(넘어가는 자리) · 골목 · 롱레인지 ----------------
GATES = {                                                                      # 테마별 문: (틀 색, 안쪽 색/빛 색)
 'snow': ((196, 220, 244), (255, 244, 214)), 'lake': ((110, 150, 200), (216, 240, 255)), 'park': ((150, 60, 70), (255, 214, 150)), 'reed': ((150, 110, 60), (255, 230, 170)),
 'woods': ((62, 52, 70), (130, 232, 212)), 'ridge': ((120, 84, 60), (255, 190, 120)), 'roofs': ((96, 98, 124), (255, 214, 150)), 'hall': ((120, 92, 70), (255, 236, 190)),
 'cabin': ((96, 64, 40), (255, 214, 150)), 'library': ((80, 54, 40), (255, 226, 170)), 'office': ((110, 90, 64), (255, 230, 180)), 'tree': ((80, 56, 36), (255, 218, 150))}
def gateway(k, theme, lx, ld, closed=False):                                   # 한눈에 문으로 보이는 자리: 틀, 밝은 속, 문턱 빛. 속은 불이 켜져 있어 "저기로 나간다"가 보인다
    fr, gl = GATES[theme]; d0, d1 = ld - 10, ld + 10; xw = 1.2 if lx < 20 else lx + 4
    inner = (22, 20, 28) if closed else gl
    k.L(d0 - 2.2, d1 + 2.2, 0, 42, fr, xw); k.L(d0, d1, 0, 38, inner, xw + .2); k.L(d0 - 2.2, d1 + 2.2, 38, 42, tuple(int(v * .8) for v in fr), xw + .1)
    if lx >= 20:                                                                # 벽이 없는 쪽: 틀 기둥 두 개로 세운다
        for dd in (d0 - 3.5, d1 + 1.5): k.B(xw - 1, dd, 3, 2.2, 42, fr, solid=False)
    if not closed:
        k.glow(xw + 6, ld, 34, gl, .55); flat(k, xw + 7, ld, 11, 4, tuple(min(255, int(v * .8 + 40)) for v in gl))
        for sx in (xw + 16, xw + 24): flat(k, sx, ld, 3, 1, tuple(min(255, v) for v in gl))      # 문 앞 바닥에 이어지는 빛 점(들어가라는 표시)
BAR = {                                                                        # 골목 벽(막는 소품 한 칸)
 'snow': lambda k, x, d, r: (k.B(x, d, 7, 6, 11, (206, 226, 246)), snowtop(k, x, d, 7, 6, 11)), 'lake': lambda k, x, d, r: (k.B(x, d, 7, 6, 12, (178, 220, 244)), k.B(x + 1, d + 1, 3, 3, 4, (230, 246, 255), z0=12, solid=False)),
 'park': lambda k, x, d, r: (k.B(x, d, 7, 2, 12, (110, 84, 66)), k.B(x, d, 7, 2, 1.6, (150, 120, 90), z0=12, solid=False)), 'reed': lambda k, x, d, r: (p_reedc(k, x, d, r), k.block.append((x, d, 4))),
 'woods': lambda k, x, d, r: p_dtree(k, x, d, r), 'ridge': lambda k, x, d, r: k.rock(x, d, 5, (130, 104, 96)),
 'roofs': lambda k, x, d, r: k.B(x, d, 7, 4, 12, (110, 114, 140)), 'hall': lambda k, x, d, r: (k.B(x, d, 6, 4, 26, (96, 124, 140)), k.F(x + 1, x + 5, 16, 18, (40, 50, 60), d)),
 'cabin': lambda k, x, d, r: k.B(x, d, 7, 6, 12, (150, 112, 70)), 'library': lambda k, x, d, r: (k.B(x, d, 7, 5, 36, (78, 52, 38)), [k.F(x + 1, x + 6, z, z + r.randint(5, 8), r.choice(((150, 50, 50), (60, 90, 130), (200, 170, 70), (70, 110, 80))), d) for z in (4, 13, 22, 31)]),
 'office': lambda k, x, d, r: k.B(x, d, 7, 6, 22, (96, 108, 112)), 'tree': lambda k, x, d, r: k.B(x, d, 6, 6, 30, (96, 66, 42))}
def add_alleys(r, o, Wd, Dd, n):                                               # 딸린 골목: 뒷벽에 붙은 좁은 칸. 앞쪽이 열려 있고, 양옆은 막는 소품 줄, 안쪽 끝엔 보상 소품
    al = []; tips = []; xs = []
    for _ in range(80):
        if len(xs) >= n: break
        x = r.uniform(24, Wd - 24)
        if all(abs(x - q) > 44 for q in xs): xs.append(x)
    for x in xs: ln = r.randint(24, 32); al.append((x, ln, 14)); tips.append((x, Dd + 6 - 4 - ln / 2 - 3))
    o['alleys'] = al; o['tips'] = tips

LONG_LAYOUTS = ('broad', 'wave', 'zig', 'lobes')
def make_spec(theme, i):
    r = random.Random(sum(map(ord, theme)) * 31 + i * 7919); T = THEMES[theme]; long = i in (2, 6)
    seq = list(range(len(LAYOUTS))); random.Random(sum(map(ord, theme)) * 13).shuffle(seq)
    if long: pool = [q for q in seq if LAYOUTS[q][0] in LONG_LAYOUTS]; li = pool[(i // 4) % len(pool)]
    else: li = seq[i % len(seq)]
    nm, fn, dmin = LAYOUTS[li]
    if long: Wd = r.randint(330, 470); Dd = r.randint(46, 54)
    else: Wd = r.randint(92, 112); Dd = r.randint(dmin, dmin + 14)
    res = fn(r, Wd, Dd); res = flip(res, Wd, Dd, r.random() < .5, r.random() < .5)
    res['a'], res['b'] = (0, Dd / 2), (Wd, Dd / 2); res['da'], res['db'] = (1, 0), (-1, 0); res['zones'] = []
    add_alleys(r, res, Wd, Dd, r.choice((3, 4)) if long else r.choice((1, 1, 2)))
    return dict(theme=theme, i=i, layout=nm, long=long, W=Wd, D=Dd, res=res, pit=0, wall=r.choice(T['walls']), seed=r.randint(0, 9), tries=0, density=1.0)

def setup(name, spec):
    T = THEMES[spec['theme']]; res = spec['res']; a, da, b, db = res['a'], res['da'], res['b'], res['db']
    ea = (a[0] + da[0] * 4, a[1] + da[1] * 4); st = (a[0] + da[0] * 14, a[1] + da[1] * 14); eb = (b[0] + db[0] * 4, b[1] + db[1] * 4); ab = (b[0] + db[0] * 14, b[1] + db[1] * 14)
    spec.update(ea=ea, st=st, eb=eb, ab=ab)
    box = dict(wall=spec['wall'], vig=T['vig'] * (.6 if spec['long'] else 1))
    W.BLOCKED[name] = lambda x, d, n, g=T['ground']: np.clip(g(x, d, np.full(n, -10.), n), 0, 255).astype(int)       # 바닥은 길 없이 한 가지 무늬(길을 강요하지 않는다)
    ent = dict(H=min(T['H'], 70) if spec['long'] else T['H'], shapes=res['shapes'], zones=[], ground=T['ground'], face=T['face'], ch=30, sky=((20, 20, 30), (40, 40, 60)), start=st, box=box, wob=T['wob'], exits=[],
               bbox=(0, 0, spec['W'], spec['D']))
    W.AREAS[name] = ent; W.STRICT.add(name); MORE[name] = spec; return ent

def more_props(name, k, tr, inside, rng):
    spec = MORE[name]; T = THEMES[spec['theme']]; th = spec['theme']; r = random.Random(sum(map(ord, name)) * 7 + spec['tries'] * 101); avoid = [tr(spec[q]) for q in ('st', 'ab', 'ea', 'eb')]
    placed = [(a, b, 14) for a, b in avoid]; kinds = [p for p in T['props'] if p[3][0] > 0 or r.random() < .55]
    dens = spec['density'] * (spec['W'] / 100 if spec['long'] else 1); sc = k.sc; Wl, Dl = sc.W, sc.D
    gateway(k, th, *tr(spec['ea']), closed=False) if spec['i'] > 0 else gateway(k, th, *tr(spec['ea']), closed=True)
    gateway(k, th, *tr(spec['eb']), closed=(spec['i'] == N_PER - 1))
    for (ax, ln, w) in spec['res'].get('alleys', []):
        lx = ax + 3; n_ = int(ln // 7) + 1
        for q in range(n_):
            dd = Dl - 4 - q * 7
            for sx in (lx - w, lx + w): BAR[th](k, sx - 3, dd - 3, r)
        tipx, tipd = lx, Dl - 12; k.glow(tipx, tipd, 26, (255, 214, 150), .3); cand = [p for p in T['props'] if p[2] in ('any', 'mid')] or T['props']; cand[r.randrange(len(cand))][1](k, tipx - 2, tipd, r); placed.append((lx, Dl - ln / 2, ln))
    for (nm, fn, mode, (lo, hi), gap) in kinds:
        n = max(0, int(round(r.randint(lo, hi) * dens)))
        if dens > 0 and lo > 0 and n == 0: n = 1
        tries = 0
        while n > 0 and tries < 700:
            tries += 1; x = r.uniform(0, spec['W']); d = r.uniform(0, spec['D']); e = inside(x, d)
            if mode == 'edge' and not (-9 < e < 12): continue
            if mode == 'mid' and not e < -7: continue
            if mode == 'any' and e < -6: continue
            lx, ld = tr((x, d))
            if not (6 < lx < Wl - 4 and 5 < ld < Dl - 4): continue
            if any(math.hypot(lx - a, (ld - b) * 1.5) < gap * .5 + g_ * .5 + 2 for a, b, g_ in placed): continue
            fn(k, lx, ld, r); placed.append((lx, ld, gap)); n -= 1

def reach(mask, meta, tips=()):
    g = np.array(mask) > 127; gh, gw = g.shape; sx, sd_ = meta['start']; s = (min(gh - 1, int(sd_ / CELL)), min(gw - 1, int(sx / CELL)))
    if not g[s]:
        ys, xs = np.nonzero(g)
        if not len(ys): return False
        i = np.argmin((ys - s[0]) ** 2 + (xs - s[1]) ** 2); s = (ys[i], xs[i])
    seen = np.zeros_like(g); st = [s]; seen[s] = True
    while st:
        y, x = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < gh and 0 <= nx < gw and g[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((ny, nx))
    o = meta['origin']
    for (tx, td) in tips:
        c = (min(gh - 1, int((td - o[1]) / CELL)), min(gw - 1, int((tx - o[0]) / CELL)))
        if not seen[max(0, c[0] - 4):c[0] + 5, max(0, c[1] - 4):c[1] + 5].any(): return False
    for e in meta['exits']:
        z = e['zone']; cx, cd = (z[0] + z[1]) / 2, (z[2] + z[3]) / 2; c = (min(gh - 1, int(cd / CELL)), min(gw - 1, int(cx / CELL)))
        if not seen[c]: return False
    return True

def FC(th): return ','.join(str(int(v * .55)) for v in GATES[th][1])
def main():
    want = sys.argv[1:] or ORDER; W.props_orig = W.props
    def props(name, k, tr, inside, rng):
        if name in MORE: return more_props(name, k, tr, inside, rng)
        return W.props_orig(name, k, tr, inside, rng)
    W.props = props
    names = {}
    for th in want:
        for i in range(N_PER): spec = make_spec(th, i); names[(th, i)] = '%sx%02d' % (th, i + 1); setup(names[(th, i)], spec)
    for th in want:
        for i in range(N_PER):
            nm = names[(th, i)]; spec = MORE[nm]
            ex = []
            if i > 0: ex.append(dict(at=spec['ea'], hw=10, fc=FC(th), to=names[(th, i - 1)], spawn=MORE[names[(th, i - 1)]]['ab']))
            ex.append(dict(at=spec['eb'], hw=10, fc=FC(th), to=names[(th, i + 1)], spawn=MORE[names[(th, i + 1)]]['st']) if i < N_PER - 1 else dict(at=spec['eb'], hw=10, fc=FC(th), to=None, endMsg='길이 끊겨 있다. 여기서는 더 갈 수 없다', side='right'))
            W.AREAS[nm]['exits'] = ex
    nav = {}
    for th in want:
        for i in range(N_PER):
            nm = names[(th, i)]; spec = MORE[nm]
            for t in range(10):
                if t == 9: spec['res']['alleys'] = []; spec['res']['tips'] = []                # 끝까지 막히면 골목을 포기한다
                spec['tries'] = t; W.SEEDOFF[nm] = t * 17; spec['density'] = .85 if t < 5 else (.5 if t < 7 else (.25 if t < 9 else .0))
                im, dep, mask, meta = W.build(nm)
                if reach(mask, meta, spec['res'].get('tips', [])): break
            else: print('!! 길이 막힘', nm)
            meta['label'] = '%s %d' % (THEMES[th]['label'], i + 1); meta['theme'] = th; nav[nm] = meta
            im.save(os.path.join(OUT, 'world_%s.png' % nm)); dep.save(os.path.join(OUT, 'world_%s_depth.png' % nm)); mask.save(os.path.join(OUT, 'world_%s_walk.png' % nm))
        print(th, [(MORE[names[(th, i)]]['layout'], nav[names[(th, i)]]['CW'], nav[names[(th, i)]]['CH']) for i in range(N_PER)])
    for nm, meta in nav.items():
        for e in meta['exits']:
            w = e.pop('spawn_w', None)
            if w and e['to'] in nav: o = nav[e['to']]['origin']; e['spawn'] = (round(w[0] - o[0], 1), round(w[1] - o[1], 1))
    old = {}
    p = os.path.join(OUT, 'more_nav.json')
    if os.path.exists(p) and sys.argv[1:]: old = json.load(open(p))
    old.update(nav); json.dump(old, open(p, 'w'), ensure_ascii=False); print('more_nav.json', len(old), 'rooms')
if __name__ == '__main__': main()
