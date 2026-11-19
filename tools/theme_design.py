#!/usr/bin/env python3
"""테마 디자인(띠 장면): 통로는 밤거리·터널처럼 끊김 없는 연속 벽 + 길 전용 바닥, 방은 테마 고유의 대표 연출(set piece)과 큰 바닥 장식.
render_strips.py 가 불러 쓴다. 장면 번호·구간 키·연결 구조는 건드리지 않는다."""
import math, random
import numpy as np
import render_more as M
from render_world import nz, col

# ---------------- 통로 뒷벽 무늬(연속) ----------------
def brick(base, mortar, bw=10, bh=5, tint=.12, cap=None, capz=5):
    def f(u, z, n_, H_, us, seed, pit):
        row = np.floor(z / bh); off = (row % 2) * bw / 2; cl = np.floor((us + off) / bw); mort = ((z % bh) < 1) | (((us + off) % bw) < 1)
        v = 1 + (nz(cl, row, 3) - .5) * tint * 2; c = np.where(mort[..., None], np.array(mortar, float), np.array(base, float)[None, None, :] * v[..., None])
        if cap is not None: c = np.where((z > H_ - capz)[..., None], np.array(cap, float), c)
        return c
    return f
def planks_h(base, dark, rope=None, row=6):
    def f(u, z, n_, H_, us, seed, pit):
        r = np.floor(z / row); c = np.where((r % 2 == 0)[..., None], np.array(base, float), np.array(base, float) * .88); c = np.where(((z % row) < .9)[..., None], np.array(dark, float), c)
        c = np.where((nz(np.floor(us / 9), r, 4) > .93)[..., None], np.array(dark, float) * 1.2, c)
        if rope is not None: c = np.where(((z > H_ * .45) & (z < H_ * .45 + 1.6))[..., None], np.array(rope, float), c)
        return c
    return f
def stripes_v(bg, bar, neon=None, bw=4, nz_=8):
    def f(u, z, n_, H_, us, seed, pit):
        c = np.where(((us % bw) < 1.2)[..., None], np.array(bar, float), np.array(bg, float) * (.8 + .2 * np.clip(z / H_, 0, 1))[..., None])
        if neon is not None: c = np.where(((z > H_ - nz_ - 1.4) & (z < H_ - nz_))[..., None], np.array(neon, float), c)
        return c
    return f
def trunks(bg, edge, w=14):
    def f(u, z, n_, H_, us, seed, pit):
        k = (us % w); c = np.where((k < 2)[..., None], np.array(edge, float), np.array(bg, float)); c = np.where(((k > w - 3) & (n_ > .5))[..., None], np.array(bg, float) * .7, c)
        return np.where((z > H_ - 8 + 3 * np.sin(us / 4.0))[..., None], np.array((18, 34, 36), float), c)
    return f
def strata(base, hi, row=6):
    def f(u, z, n_, H_, us, seed, pit):
        r = np.floor((z + 3 * np.sin(us / 17.0)) / row); c = np.where((r % 2 == 0)[..., None], np.array(base, float), np.array(base, float) * .85); return np.where((n_ > .92)[..., None], np.array(hi, float), c)
    return f
def concrete(base, pipe, neon=None):
    def f(u, z, n_, H_, us, seed, pit):
        c = np.array(base, float)[None, None, :] * (.85 + .15 * np.clip(z / H_, 0, 1))[..., None] * np.ones(np.shape(u) + (3,)); c = np.where(((us % 24) < 1)[..., None], np.array(base, float) * .7, c)
        c = np.where((((z % 16) > 11) & ((z % 16) < 14) & (z > 6))[..., None], np.array(pipe, float), c)
        if neon is not None: c = np.where(((z > H_ - 6) & (z < H_ - 4.6))[..., None], np.array(neon, float), c)
        return c
    return f
def lockers_w(base, door=(80, 100, 110)):
    def f(u, z, n_, H_, us, seed, pit):
        k = (us % 9); c = np.where((k < 1.2)[..., None], np.array(door, float) * .6, np.array(base, float) * (.85 + .15 * np.clip(z / H_, 0, 1))[..., None])
        c = np.where((((z % 28) > 20) & ((z % 28) < 23) & (k > 2) & (k < 7))[..., None], np.array(door, float) * .5, c); return c
    return f
def glass_w(frame, pane, pw=18):
    def f(u, z, n_, H_, us, seed, pit):
        k = (us % pw); c = np.where((k < 1.4)[..., None] | ((z < 14) & (z > 12.4))[..., None], np.array(frame, float), np.where((z < 12.4)[..., None], np.array(pane, float) * .55, np.array(pane, float) * (.8 + .2 * np.clip(z / H_, 0, 1))[..., None]))
        return c
    return f
def roots_w(bg, root):
    def f(u, z, n_, H_, us, seed, pit):
        k = (us % 11); c = np.where((k < 2.4)[..., None], np.array(bg, float) * .75, np.array(bg, float)); c = np.where((np.abs(np.sin(us / 6.0 + z / 9.0)) > .93)[..., None], np.array(root, float), c)
        return np.where((z > H_ - 6)[..., None], np.array((40, 60, 40), float), c)
    return f

def facade_w(base, mortar, lit=(255, 214, 140), dark=(20, 22, 40)):            # 밤 건물 벽: 벽돌 + 드문드문 켜진 창
    def f(u, z, n_, H_, us, seed, pit):
        row = np.floor(z / 5); off = (row % 2) * 5; cl = np.floor((us + off) / 10); mort = ((z % 5) < 1) | (((us + off) % 10) < 1)
        c = np.where(mort[..., None], np.array(mortar, float), np.array(base, float)[None, None, :] * (1 + (nz(cl, row, 3) - .5) * .2)[..., None])
        wx = (us % 22); wz = (z % 18); win = (wx > 6) & (wx < 15) & (wz > 6) & (wz < 14) & (z > 8) & (z < H_ - 4); on = nz(np.floor(us / 22), np.floor(z / 18), 9) > .86
        return np.where(win[..., None], np.where(on[..., None], np.array(lit, float), np.array(dark, float)), c)
    return f
def facade_user(u, z, n_, H_, us, seed, pit):                                   # 사용자가 만든 광장 건물 벽: 어두운 벽 + 가로 줄 + 규칙적인 꺼진 창
    c = np.where((z % 12 < .9)[..., None], np.array((20, 23, 44), float), np.array((28, 32, 60), float))
    win = ((us % 16) > 6) & ((us % 16) < 15) & ((z % 12) > 3) & ((z % 12) < 9) & (z > 10) & (z < H_ - 5)
    return np.where(win[..., None], np.array((22, 26, 50), float), c)
PWALL = {
 'city': facade_user,
 'snow': brick((98, 106, 122), (58, 66, 82), cap=(236, 242, 252)), 'lake': planks_h((96, 70, 54), (40, 30, 28), rope=(190, 170, 130)),
 'park': stripes_v((38, 36, 56), (70, 70, 96), neon=(255, 90, 150)), 'reed': stripes_v((120, 92, 46), (170, 130, 60), bw=3), 'woods': trunks((38, 32, 46), (62, 52, 70)),
 'ridge': strata((112, 88, 80), (150, 120, 104)), 'roofs': concrete((72, 76, 98), (112, 118, 138), neon=(90, 220, 255)), 'hall': lockers_w((96, 124, 140)),
 'cabin': planks_h((126, 84, 50), (70, 44, 30), row=7), 'library': M.w_shelves, 'office': glass_w((100, 104, 100), (150, 190, 205)), 'tree': roots_w((92, 62, 40), (140, 100, 62))}

# ---------------- 통로 길 바닥 ----------------
def L_snow(x, d, e, n): q = nz(x / 2, d / 2, 3); return col([(q >= 0, (206, 218, 236)), (q > .7, (194, 208, 230)), ((np.abs((d * 3 + x * .0) % 11) < .8), (178, 192, 220)), (e > -2.5, (170, 184, 212))], n)
def L_lake(x, d, e, n): q = nz(x / 3, d / 3, 5); return col([(np.floor(x / 6) % 2 == 0, (140, 100, 68)), (np.floor(x / 6) % 2 == 1, (124, 88, 60)), (np.abs(x % 6) < .8, (70, 50, 38)), (q > .93, (160, 120, 84)), (e > -2.5, (96, 70, 50))], n)
def L_park(x, d, e, n): return col([(np.floor(d / 5) % 2 == 0, (122, 44, 56)), (np.floor(d / 5) % 2 == 1, (200, 186, 168)), (e > -2.5, (60, 56, 70))], n)
def L_reed(x, d, e, n): q = nz(x / 2, d / 2, 6); return col([(q >= 0, (146, 116, 74)), (q > .8, (166, 134, 88)), (nz(x, d, 9) > .95, (110, 90, 60)), (e > -2.5, (118, 94, 58))], n)
def L_woods(x, d, e, n): q = nz(x / 2, d / 2, 8); return col([(q >= 0, (52, 70, 56)), (q > .7, (64, 84, 66)), (nz(x, d, 4) > .94, (110, 96, 60)), (e > -2.5, (38, 52, 42))], n)
def L_ridge(x, d, e, n): q = nz(x, d, 3); return col([(q >= 0, (150, 124, 102)), (q > .6, (166, 140, 116)), (q > .9, (120, 98, 82)), (e > -2.5, (112, 92, 78))], n)
def L_roofs(x, d, e, n): return col([(nz(x / 3, d / 3, 4) >= 0, (82, 88, 112)), (nz(x / 3, d / 3, 4) > .6, (90, 96, 120)), (((np.abs(d % 200 - 0) > 0) & (np.abs(x % 16) < 5) & (np.abs(e + 13) < .9)), (212, 190, 90)), (e > -2.5, (60, 64, 86))], n)
def L_hall(x, d, e, n): return col([(nz(x / 2, d / 2, 6) >= 0, (88, 110, 100)), (np.abs(e + 13) < 1.1, (206, 194, 120)), (e > -2.5, (60, 76, 70))], n)
def L_cabin(x, d, e, n): return col([(nz(x, d, 1) >= 0, (126, 56, 54)), (e > -4, (196, 170, 120)), (np.floor(x / 4) % 2 == 0, (118, 52, 50)), (e > -2.5, (86, 56, 44))], n)
def L_library(x, d, e, n): return col([(nz(x, d, 1) >= 0, (104, 34, 40)), (e > -5, (200, 164, 84)), (e > -3.6, (92, 30, 36)), (np.floor(x / 8) % 2 == 0, (96, 30, 36)), (e > -2.5, (60, 40, 30))], n)
def L_office(x, d, e, n): return col([(nz(x / 2, d / 2, 6) >= 0, (156, 160, 140)), (np.abs(e + 13) < .9, (230, 218, 150)), (e > -2.5, (120, 124, 110))], n)
def L_tree(x, d, e, n): q = nz(x / 2, d / 2, 8); return col([(q >= 0, (126, 90, 56)), (q > .8, (146, 106, 66)), (nz(x, d, 4) > .95, (96, 150, 80)), (e > -2.5, (96, 68, 44))], n)
def L_city(x, d, e, n):                                                        # 차도: 아스팔트 + 노란 중앙 점선 + 흰 가장자리선
    q = nz(x / 2, d / 2, 3); return col([(q >= 0, (46, 48, 62)), (q > .8, (52, 54, 70)), ((np.abs(e + 13) < .8) & (np.floor(x / 7) % 2 == 0), (206, 176, 76)), ((e > -3.4) & (e < -2.3), (150, 152, 170)), (e > -1.8, (84, 86, 106))], n)
LANE = {'city': (lambda x, d, e, n: M.city_ground(x, d, e, n)), 'snow': L_snow, 'lake': L_lake, 'park': L_park, 'reed': L_reed, 'woods': L_woods, 'ridge': L_ridge, 'roofs': L_roofs, 'hall': L_hall, 'cabin': L_cabin, 'library': L_library, 'office': L_office, 'tree': L_tree}

# ---------------- 통로 연속 벽 (상자를 이음새 없이 이어 붙인다) ----------------
# (뒤쪽 높이, 앞쪽 높이, 뒤 색, 앞 색, 윗면 색)
RUN = {'city': (36, 9, (56, 60, 90), (90, 94, 110), (110, 114, 140)), 'snow': (26, 9, (96, 104, 120), (96, 104, 120), (240, 246, 255)), 'lake': (22, 8, (70, 52, 46), (84, 62, 50), (120, 92, 68)), 'park': (24, 8, (44, 42, 62), (70, 74, 90), (255, 90, 150)),
       'reed': (28, 12, (130, 100, 50), (150, 116, 58), (210, 176, 90)), 'woods': (40, 8, (40, 34, 48), (54, 44, 56), (30, 52, 44)), 'ridge': (30, 9, (118, 92, 84), (130, 104, 96), (160, 130, 114)),
       'roofs': (24, 8, (92, 96, 122), (104, 108, 132), (150, 156, 176)), 'hall': (30, 9, (96, 124, 140), (150, 112, 76), (130, 156, 170)), 'cabin': (26, 9, (126, 84, 50), (112, 72, 42), (160, 112, 70)),
       'library': (40, 5, (78, 52, 38), (150, 50, 50), (110, 76, 52)), 'office': (26, 9, (130, 160, 176), (130, 100, 72), (110, 112, 108)), 'tree': (34, 8, (96, 66, 42), (86, 58, 38), (60, 90, 52))}
def run_unit(k, th, lx, ld, low, i, r):
    hb, hf, cb, cf, ct = RUN[th]; h = hf if low else hb; c = cf if low else cb
    if (i // 4) % 2: c = tuple(int(v * .9) for v in c)
    if th == 'reed':
        for q in (-2, 0, 2): k.reed(lx + q, ld, h + (q + 2)); k.block.append((lx, ld, 3.5)); return
    k.B(lx - 4.2, ld - 3.5, 8.6, 7, h, c); k.B(lx - 4.2, ld - 3.5, 8.6, 7, 1.4, ct, z0=h, solid=False)
    if th == 'library' and not low: [k.F(lx - 3.6, lx + 3.6, z, z + r.randint(5, 8), r.choice(((150, 50, 50), (60, 90, 130), (200, 170, 70), (70, 110, 80))), ld - 3.5) for z in (4, 13, 22, 31)]
    if th == 'hall' and not low: k.F(lx - 3, lx + 3, 16, 18, (40, 50, 60), ld - 3.5)
    if th == 'woods' and not low and i % 3 == 0: k.B(lx - 1, ld - 4.5, 3, 2, 5, (30, 24, 36), solid=False)

# ---------------- 방 대표 연출(set piece) ----------------
SOLIDFN = {'p_car', 'p_vending', 'p_busstop', 'p_trafficlight', 'p_fir', 'p_dtree', 'p_deadtree', 'p_kiosk', 'p_hut', 'p_tank', 'p_counter', 'p_bed', 'p_fire', 'p_bookcase', 'p_shelf', 'p_hlocker', 'p_cabinet', 'p_filecab', 'p_safe', 'p_machine', 'p_sofa', 'p_table', 'p_readtable', 'p_desk', 'p_ladder', 'p_trophy', 'p_stove', 'p_antenna', 'p_line', 'p_chimney', 'p_horse', 'p_boat', 'p_scarecrow', 'p_boulder', 'p_hay', 'p_cart', 'p_bumper', 'p_ac', 'p_root', 'p_atree', 'p_lantern', 'p_roofl'}
def hut(k, x, d, w, dp, h, wall, roof, door=(18, 16, 24), lit=None):
    k.B(x - w / 2, d - dp / 2, w, dp, h, wall); k.B(x - w / 2 - 1, d - dp / 2 - 1, w + 2, dp + 2, 3, roof, z0=h, solid=False); k.F(x - 3, x + 3, 0, h * .6, door, d - dp / 2)
    if lit: k.F(x + w / 2 - 7, x + w / 2 - 2, h * .45, h * .8, lit, d - dp / 2); k.glow(x + w / 2 - 4, d - dp / 2 - 4, 22, lit, .4)
def ring(k, x, d, rx, ry, c0, c1): M.flat(k, x, d, rx, ry, c0); M.flat(k, x, d, rx - 2, ry - 1, c1)
def at(k, fn, x, d, r):
    nb, nr = len(k.block), len(k.rects); fn(k, x, d, r)
    if fn.__name__ not in SOLIDFN: del k.block[nb:]; del k.rects[nr:]
LITFN = {'p_fire', 'p_flamp', 'p_hlantern', 'p_readtable', 'p_lantern', 'p_jar', 'p_stove', 'p_hut', 'p_lamp'}
LIGHT = {'city': (255, 214, 150), 'snow': (214, 232, 255), 'lake': (200, 226, 255), 'park': (255, 150, 170), 'reed': (255, 206, 130), 'woods': (130, 232, 212), 'ridge': (255, 190, 120), 'roofs': (190, 226, 255), 'hall': (226, 246, 214),
         'cabin': (255, 200, 130), 'library': (255, 210, 140), 'office': (230, 240, 255), 'tree': (255, 214, 140)}                      # 테마별 광색 하나로 통일
def S(*items):                                                                  # 대표 연출: 소품은 최대 3개로 줄여 가운데 정렬, 글로우는 절제
    ps = [it for it in items if it[0] == 'p']; rest = [it for it in items if it[0] != 'p']
    if len(ps) > 3: ps = ps[:3]
    if ps: mx = sum(it[2] for it in ps) / len(ps); ps = [(it[0], it[1], round(it[2] - mx), it[3]) for it in ps]
    items = tuple(ps + [(it[0], it[1], it[2], it[3] * .5, it[4], it[5]) if it[0] == 'glow' else it for it in [((it[0], int(it[1] * .7), it[2], it[3], it[4], it[5]) if it[0] == 'glow' else it) for it in rest]])
    def f(k, cx, cd, r):
        for it in items:
            if it[0] == 'p': at(k, it[1], cx + it[2], cd + it[3], r)
            elif it[0] == 'ring': ring(k, cx + it[5], cd + it[6], it[1], it[2], it[3], it[4])
            elif it[0] == 'flat': M.flat(k, cx + it[4], cd + it[5], it[1], it[2], it[3])
            elif it[0] == 'glow': k.glow(cx + it[4], cd + it[5], it[1], it[2], it[3])
            elif it[0] == 'hut': hut(k, cx + it[1], cd + it[2], *it[3:])
    f.lit = any(it[0] == 'glow' or (it[0] == 'p' and getattr(it[1], '__name__', '') in LITFN) or (it[0] == 'hut' and len(it) > 9 and it[9]) for it in items)
    return f
P = M
SETS_KEY = {                                                                   # 특정 방(key)에 정해 놓는 대표 연출. 여기에 적은 방은 무작위 대신 이것을 쓴다(수정·추가 자유)
 'cityx01': S(('p', P.p_hedgebed, 0, 0), ('p', P.p_streetlamp(), 40, 4), ('p', P.p_bench, 22, 12)),
}
SETS_KEY['cityx01'].lit = True                                                    # 이 연출이 자기 가로등을 가지므로 방에 가로등을 더 세우지 않는다
SETS = {
 'city': [S(('p', P.p_crosswalk, -20, -6), ('p', P.p_trafficlight, 26, 4), ('p', P.p_car, -10, 12), ('p', P.p_manhole, 6, 2)),
          S(('hut', 0, 0, 32, 16, 26, (70, 76, 104), (60, 64, 90), (14, 12, 20), (255, 232, 176)), ('p', P.p_vending, -24, 6), ('p', P.p_vending, 24, 6), ('p', P.p_bench, 0, 14)),
          S(('p', P.p_busstop, -8, 0), ('p', P.p_bin, 22, 4), ('p', P.p_hydrant, -26, 8)),
          S(('p', P.p_bin, -16, 0), ('p', P.p_bike, 0, 4), ('p', P.p_mailbox, 16, 0), ('p', P.p_hydrant, 26, 8))],
 'snow': [S(('ring', 16, 6, (92, 70, 58), (30, 24, 24), 0, 0), ('glow', 34, (255, 170, 90), .55, 0, 0), ('p', P.p_log, -16, 5), ('p', P.p_log, 8, 6), ('p', P.p_stump, -4, -8), ('p', P.p_stump, 10, -6)),
          S(('ring', 22, 8, (206, 228, 248), (178, 208, 236), 0, 0), ('p', P.p_hole, -6, 0), ('p', P.p_hole, 8, 2), ('p', P.p_stump, -20, 6), ('p', P.p_shard, 14, -3)),
          S(('p', P.p_snowman, -14, 0), ('p', P.p_snowman, 0, 3), ('p', P.p_snowman, 14, -1), ('p', P.p_log, -4, 9)),
          S(('hut', 0, 0, 26, 16, 24, (110, 84, 64), (240, 246, 255), (14, 12, 20), (255, 200, 120)), ('p', P.p_lantern, -20, 6), ('p', P.p_bush, 20, 3))],
 'lake': [S(('hut', 0, 0, 24, 14, 22, (84, 62, 50), (200, 216, 232), (14, 12, 20), (255, 200, 120)), ('p', P.p_hole, -12, 14), ('p', P.p_hole, 4, 15), ('p', P.p_bucket, 16, 12)),
          S(('flat', 22, 3, (232, 246, 255), 0, 0), ('p', P.p_shard, -14, 0), ('p', P.p_shard, 0, 4), ('p', P.p_shard, 14, -1), ('p', P.p_stones, -22, 8)),
          S(('flat', 24, 7, (16, 30, 66), 0, 2), ('p', P.p_boat, -8, 0), ('p', P.p_stones, 20, 6)),
          S(('p', P.p_lantern, 0, 0), ('glow', 50, (255, 226, 160), .5, 0, -4), ('p', P.p_deadtree, -18, 4), ('p', P.p_hole, 14, 6))],
 'park': [S(('ring', 22, 8, (90, 80, 100), (60, 54, 72), 0, 0), ('p', P.p_horse, -14, 0), ('p', P.p_horse, -4, 4), ('p', P.p_horse, 6, 0), ('p', P.p_horse, 16, 4), ('p', P.p_lamp(True), 0, -7)),
          S(('p', P.p_kiosk, -22, 0), ('p', P.p_kiosk, 0, 0), ('p', P.p_kiosk, 22, 0), ('p', P.p_balloon, -10, 8), ('p', P.p_balloon, 12, 9)),
          S(('ring', 14, 6, (76, 70, 86), (30, 28, 40), 0, 0), ('p', P.p_bench, -26, 4), ('p', P.p_bench, 14, 6), ('p', P.p_bin, 28, 2)),
          S(('p', P.p_bumper, -18, 0), ('p', P.p_bumper, -4, 3), ('p', P.p_bumper, 10, 0), ('p', P.p_bumper, 24, 4), ('p', P.p_fence, -28, 12))],
 'reed': [S(('p', P.p_scarecrow, -16, 0), ('p', P.p_scarecrow, 0, 4), ('p', P.p_scarecrow, 16, 0), ('p', P.p_reedc, -8, 10), ('p', P.p_reedc, 10, 10)),
          S(('p', P.p_hay, -20, 0), ('p', P.p_hay, -6, 3), ('p', P.p_hay, 8, 0), ('p', P.p_hay, 22, 4)),
          S(('ring', 22, 7, (86, 66, 46), (104, 118, 110), 0, 0), ('p', P.p_rock, -26, 4), ('p', P.p_rock, 26, 3), ('p', P.p_reedc, 0, 12)),
          S(('p', P.p_desk, -22, 0), ('p', P.p_desk, -6, 4), ('p', P.p_desk, 12, 0), ('p', P.p_chair, 26, 4))],
 'woods': [S(('ring', 16, 7, (30, 26, 32), (54, 48, 52), 0, 0), ('p', P.p_wstump, -2, 0), ('p', P.p_wlog, -22, 8), ('p', P.p_dtree, 22, 6)),
           S(('p', P.p_shroom, -14, 0), ('p', P.p_shroom, 0, 6), ('p', P.p_shroom, 14, 0), ('p', P.p_shroom, 0, -8), ('glow', 40, (110, 230, 210), .3, 0, 0)),
           S(('flat', 24, 7, (20, 30, 28), 0, 0), ('p', P.p_wlog, -14, 2), ('p', P.p_wlog, 4, 6), ('p', P.p_wrock, 22, 4)),
           S(('ring', 18, 7, (170, 186, 190), (120, 140, 150), 0, 0), ('glow', 44, (180, 210, 230), .35, 0, 0), ('p', P.p_wrock, -22, 5), ('p', P.p_dtree, 24, 8))],
 'ridge': [S(('p', P.p_fence, -22, 4), ('p', P.p_fence, -6, 4), ('p', P.p_fence, 10, 4), ('p', P.p_sign, 28, 4), ('p', P.p_boulder, -30, 0)),
           S(('p', P.p_atree, -14, 3), ('p', P.p_atree, 4, 6), ('p', P.p_atree, 20, 2), ('p', P.p_redshroom, -4, -4), ('p', P.p_redshroom, 12, -5)),
           S(('p', P.p_cairn, -18, 0), ('p', P.p_cairn, -4, 4), ('p', P.p_cairn, 10, 0), ('p', P.p_cairn, 24, 4)),
           S(('p', P.p_sign, -10, 0), ('p', P.p_sign, 4, 4), ('p', P.p_sign, 18, 0), ('p', P.p_planks, -26, 6))],
 'roofs': [S(('p', P.p_line, -24, 6), ('p', P.p_planter, -20, -4), ('p', P.p_planter, 14, -4)),
           S(('p', P.p_tank, -14, 0), ('p', P.p_hut, 12, 2), ('p', P.p_vent, 30, 6)),
           S(('p', P.p_vent, -24, 0), ('p', P.p_vent, -12, 6), ('p', P.p_vent, 0, 0), ('p', P.p_ac, 12, 3), ('p', P.p_ac, 26, 0), ('p', P.p_vent, 34, 6)),
           S(('p', P.p_planter, -22, 0), ('p', P.p_planter, -8, 4), ('p', P.p_planter, 8, 0), ('p', P.p_planter, 22, 4), ('p', P.p_bench, -4, -8))],
 'hall': [S(('p', P.p_hlocker, -26, 0), ('p', P.p_hlocker, 0, 0), ('p', P.p_hlocker, 26, 0), ('p', P.p_shoes, -12, 8), ('p', P.p_shoes, 14, 8)),
          S(('p', P.p_trophy, -12, 0), ('p', P.p_hbench, 8, 4), ('p', P.p_bin, 26, 2)),
          S(('p', P.p_desk, -22, 0), ('p', P.p_desk, -6, 4), ('p', P.p_desk, 12, 0), ('p', P.p_chair, 28, 3)),
          S(('p', P.p_hmop, -14, 0), ('p', P.p_bin, 0, 2), ('p', P.p_hbench, 16, 4), ('p', P.p_shoes, -2, 10))],
 'cabin': [S(('p', P.p_fire, 0, 0), ('p', P.p_rug, 0, 12), ('p', P.p_stool, -16, 8), ('p', P.p_stool, 16, 8)),
           S(('p', P.p_table, 0, 0), ('p', P.p_stool, -12, 12), ('p', P.p_stool, 14, 12), ('p', P.p_hlantern, -22, 4)),
           S(('p', P.p_bed, -10, 0), ('p', P.p_shelf, 22, 0), ('p', P.p_rug, -8, 14)),
           S(('p', P.p_shelf, -20, 0), ('p', P.p_shelf, 0, 0), ('p', P.p_crate, 20, 2), ('p', P.p_barrel, -4, 12))],
 'library': [S(('p', P.p_readtable, -16, 0), ('p', P.p_readtable, 14, 3), ('p', P.p_flamp, 0, 10), ('p', P.p_books, -2, 12)),
             S(('p', P.p_bookcase, -18, 0), ('p', P.p_bookcase, 6, 0), ('p', P.p_ladder, 24, 2), ('p', P.p_globe, -2, 14)),
             S(('p', P.p_sofa, 0, 0), ('p', P.p_rug, 0, 12), ('p', P.p_flamp, 22, 4), ('p', P.p_books, -18, 10)),
             S(('p', P.p_cabinet, -22, 0), ('p', P.p_cabinet, -8, 0), ('p', P.p_cabinet, 6, 0), ('p', P.p_cart2, 24, 6))],
 'office': [S(('p', P.p_counter, 0, 0), ('p', P.p_chair, -14, 12), ('p', P.p_chair, 12, 12), ('p', P.p_machine, 30, 2)),
            S(('p', P.p_hbench, -20, 4), ('p', P.p_hbench, -2, 4), ('p', P.p_hbench, 16, 4), ('p', P.p_bin, 32, 2)),
            S(('p', P.p_safe, -10, 0), ('p', P.p_filecab, 8, 0), ('p', P.p_filecab, 20, 0), ('p', P.p_coat, -24, 4)),
            S(('p', P.p_filecab, -24, 0), ('p', P.p_filecab, -12, 0), ('p', P.p_filecab, 0, 0), ('p', P.p_filecab, 12, 0), ('p', P.p_cart2, 28, 6))],
 'tree': [S(('p', P.p_acorns, -16, 2), ('p', P.p_acorns, 0, 4), ('p', P.p_pots, 14, 0), ('p', P.p_pots, 24, 6)),
          S(('p', P.p_hammock, 0, 4), ('p', P.p_jar, -22, 0), ('p', P.p_jar, 22, 0), ('p', P.p_root, -30, 6)),
          S(('p', P.p_tshroom, -18, 0), ('p', P.p_tshroom, -6, 5), ('p', P.p_tshroom, 8, 0), ('p', P.p_tshroom, 20, 5), ('p', P.p_tshroom, 0, -6), ('glow', 36, (255, 232, 150), .25, 0, 0)),
          S(('p', P.p_table, 0, 0), ('p', P.p_jar, -16, 4), ('p', P.p_jar, 18, 4), ('p', P.p_books, -4, 12), ('p', P.p_stool, 14, 12))]}
