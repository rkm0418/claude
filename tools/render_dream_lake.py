#!/usr/bin/env python3
"""꿈 구역 2: 얼어붙은 호수 — 눈 숲길과 같은 방식(바닥은 평평한 한 장, 길이 휘어지는 구간 여러 장).
두꺼운 얼음 길(걸을 수 있음) 밖은 검푸른 열린 물(못 걷음)과 금 간 얇은 얼음(위험 표시), 얼음 아래로 아파트 창 불빛이 비친다. 길가에 마른 나무와 등불 기둥.
구간 3장: lake_1 호숫가 시작 → lake_2 갈라진 얼음 들판(추격 자리) → lake_3 등불 나무가 선 섬.
사용: python3 tools/render_dream_lake.py -> maps/out/area_lake_<1..3>.png, _depth.png, _walk.png, dream_nav_lake.json"""
import json, math, os, random, sys
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_dream as RD
from render_dream_area import seg_dist, bez, CELL
from render_city3d import Scene, dk, OUT

H = 58; HW = 17; MARGIN_W = 20
RD.H = H
TRAIL = bez((12, 10), (50, 6), (70, 34), (96, 44)) + bez((96, 44), (126, 54), (122, 86), (156, 92))[1:] + bez((156, 92), (190, 98), (206, 70), (240, 66))[1:] + bez((240, 66), (268, 62), (276, 100), (300, 104))[1:]
N = len(TRAIL); CUTS = [(0, 20), (14, 40), (34, N - 1)]; NAMES = ['lake_1', 'lake_2', 'lake_3']
CLEARS = {0: [((12, 10), 24)], 1: [((156, 92), 34)], 2: [((300, 104), 34)]}

def dead_tree(sc, x, d, h):
    def draw():
        b = sc.P(x, d, 0); top = (b[0], b[1] - h)
        sc.d.line([b, top], fill=(70, 62, 78), width=2); sc.d.line([(b[0] - 1, b[1]), (b[0] - 1, top[1])], fill=(106, 96, 112))
        for k, (dx, dy, ln) in enumerate(((-9, -6, 0.62), (8, -9, 0.74), (-6, -14, 0.84), (6, -4, 0.5), (0, -18, 0.95))):
            y0 = b[1] - int(h * ln); sc.d.line([(b[0], y0), (b[0] + dx, y0 + dy)], fill=(70, 62, 78)); sc.d.line([(b[0] + dx, y0 + dy), (b[0] + dx + (3 if dx > 0 else -3), y0 + dy - 4)], fill=(70, 62, 78))
            sc.d.point((b[0] + dx, y0 + dy - 1), fill=(240, 246, 255)); sc.d.point((b[0], y0 - 1), fill=(240, 246, 255))
        sc.d.ellipse([b[0] - 5, b[1] - 1, b[0] + 5, b[1] + 2], fill=(236, 242, 252))
    sc.jobs.append((d, draw))

def lantern(sc, x, d):
    def draw():
        b = sc.P(x, d, 0); t = sc.P(x, d, 26); sc.d.line([b, t], fill=(70, 62, 86), width=2); sc.d.rectangle([t[0] - 3, t[1] - 5, t[0] + 3, t[1]], fill=(255, 226, 150)); sc.d.rectangle([t[0] - 4, t[1] - 6, t[0] + 4, t[1] - 5], fill=(110, 98, 130))
    sc.jobs.append((d, draw)); sc.glow(x, d, 24, col=(255, 214, 140), power=.35)

def section(name, lines, clears, exits, seed, last=False):
    pts = [p for ln in lines for p in ln] + [c for c, r in clears]
    x0 = min(p[0] for p in pts) - MARGIN_W; x1 = max(p[0] for p in pts) + MARGIN_W; d0 = min(p[1] for p in pts) - MARGIN_W; d1 = max(p[1] for p in pts) + MARGIN_W
    tr = lambda p: (p[0] - x0, p[1] - d0)
    L = [[tr(p) for p in ln] for ln in lines]; C = [(tr(c), r) for c, r in clears]; Wd, Dd = int(x1 - x0), int(d1 - d0)
    RD.W, RD.D = Wd, Dd; rng = random.Random(seed)
    def dist(x, d):
        r = min(seg_dist(x, d, a, b) for ln in L for a, b in zip(ln, ln[1:])); w = 1.4 * math.sin(d / 5.0 + x / 7.0); inside = r - HW - w
        for (cx, cd), cr in C: inside = min(inside, math.hypot(x - cx, (d - cd) * 1.15) - cr - w)
        return inside
    cracks = []                                                                  # 얼음 위의 금(길 쪽에서 물 쪽으로 번지는 지그재그)
    for _ in range(9):
        a = rng.choice([p for ln in L for p in ln]); x, d = a[0] + rng.uniform(-8, 8), a[1] + rng.uniform(-8, 8); ang = rng.uniform(0, math.tau); seg = [(x, d)]
        for _ in range(6): ang += rng.uniform(-.7, .7); x += math.cos(ang) * 7; d += math.sin(ang) * 6; seg.append((x, d))
        cracks.append(seg)
    def ground(x, d):
        e = dist(x, d); n = RD.noise(x + x0, d + d0)
        if e < 0:
            if e > -1.4: return (226, 240, 252)                                  # 두꺼운 얼음 가장자리
            return (176 + int(n * 10), 214 + int(n * 8), 238) if RD.noise(int(x // 5), int(d // 5), 2) > .3 else (164, 204, 232)
        if e < 7: return (150 + int(n * 12), 188 + int(n * 8), 224) if int((x + d) // 4) % 2 else (136, 176, 214)    # 금 간 얇은 얼음(위험)
        return (46 + int(n * 12), 78 + int(n * 12), 122 + int(n * 12)) if int((x * .5 + d * 1.2) // 3) % 2 else (56, 92, 136)   # 열린 물
    sc = RD.base((52, 60, 108), (150, 160, 210), ground)
    for gx in range(6, Wd - 4, 11):                                              # 얼음 아래로 비치는 아파트 창 불빛
        for gd in range(6, Dd - 4, 11):
            if RD.noise(gx + x0, gd + d0, 7) > .55: X, Y = sc.P(gx, gd, 0); sc.d.rectangle([X - 2, Y - 1, X + 2, Y + 1], fill=(206, 188, 140) if dist(gx, gd) < 0 else (150, 140, 120))
    for seg in cracks:
        for a, b in zip(seg, seg[1:]): sc.d.line([sc.P(*a, 0), sc.P(*b, 0)], fill=(246, 252, 255))
    X, Y = sc.P(Wd * .3, Dd, 48); sc.d.ellipse([X - 9, Y - 9, X + 9, Y + 9], fill=(250, 246, 226)); sc.d.ellipse([X - 4, Y - 9, X + 12, Y + 7], fill=(150, 160, 210))
    allp = [p for ln in L for p in ln]; trees = []
    for _ in range(300):                                                          # 마른 나무: 길 바깥 뒤쪽(화면 위)의 호숫가 쪽에만, 서로 30 이상 떨어지게
        x = rng.uniform(4, Wd - 4); d = rng.uniform(4, Dd - 4); e = dist(x, d)
        if e < 1 or e > 14: continue
        nx, nd = min(allp, key=lambda p: math.hypot(x - p[0], d - p[1]))
        if d < nd - 2 or any(math.hypot(x - tx, d - td) < 30 for tx, td in trees): continue
        trees.append((x, d)); dead_tree(sc, x, d, rng.choice((30, 36, 42)))
    for (cx, cd), cr in C[-1:]:
        if last: lantern(sc, cx + 14, cd - 6)
    for _ in range(40): X, Y = rng.randrange(6, sc.CW - 6), rng.randrange(6, sc.CH - 6); (sc.px[X, Y] != RD.MARGIN) and sc.d.point((X, Y), fill=(255, 255, 255))
    exit_pts = [tr(e[0]) for e in exits]
    for (ex_, ed_) in exit_pts: sc.glow(ex_, ed_, 20, col=(255, 255, 255), power=.35)
    dep = Image.new('L', sc.img.size, 255)
    for depth, f in sorted(sc.jobs, key=lambda j: -j[0]):
        before = sc.img.copy(); f(); diff = ImageChops.difference(sc.img, before).convert('L').point(lambda v: 255 if v else 0)
        dep.paste(int(max(0, min(254, round((depth + 2) * 3)))), (0, 0), diff)
    gw, gh = math.ceil(Wd / CELL), math.ceil(Dd / CELL); mask = Image.new('L', (gw, gh), 0); mp = mask.load()
    for j in range(gh):
        for i in range(gw):
            x, d = (i + .5) * CELL, (j + .5) * CELL
            if dist(x, d) < -4.5 and not any(abs(x - tx) < 4 and abs(d - td) < 3.5 for tx, td in trees): mp[i, j] = 255
    nav_exits = [{'zone': (ex_ - 4, ex_ + 4, ed_ - 4, ed_ + 4), 'to': e[1], 'spawn': None, 'world_to': e[2]} for (ex_, ed_), e in zip(exit_pts, exits)]
    return sc.img, dep, mask, {'W': Wd, 'D': Dd, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': sc.CW, 'CH': sc.CH, 'rects': [], 'exits': nav_exits, 'start': tr(lines[0][min(3, len(lines[0]) - 1)]), 'origin': (x0, d0)}

def main():
    nav = {}; secs = {}
    for k, (s, e) in enumerate(CUTS):
        exits = []
        if k > 0: exits.append((TRAIL[s], NAMES[k - 1], TRAIL[s + 3]))
        if k < len(CUTS) - 1: exits.append((TRAIL[e], NAMES[k + 1], TRAIL[e - 3]))
        secs[NAMES[k]] = section(NAMES[k], [TRAIL[s:e + 1]], CLEARS.get(k, []), exits, 40 + k, last=(k == len(CUTS) - 1))
    for name, (im, dep, mask, meta) in secs.items():
        im.save(os.path.join(OUT, 'area_%s.png' % name)); dep.save(os.path.join(OUT, 'area_%s_depth.png' % name)); mask.save(os.path.join(OUT, 'area_%s_walk.png' % name)); nav[name] = meta
    for name, meta in nav.items():
        for e in meta['exits']:
            wx, wd = e.pop('world_to'); ox, od = nav[e['to']]['origin']; e['spawn'] = (round(wx - ox, 1), round(wd - od, 1))
    json.dump(nav, open(os.path.join(OUT, 'dream_nav_lake.json'), 'w'), ensure_ascii=False)
    ims = [secs[k][0] for k in NAMES]; S = 3; wsum = sum(i.width for i in ims) * S + 10 * (len(ims) + 1); hmax = max(i.height for i in ims) * S + 20
    sheet = Image.new('RGB', (wsum, hmax), (40, 40, 48)); x = 10
    for im in ims: sheet.paste(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, 10)); x += im.width * S + 10
    sheet.save(os.path.join(OUT, 'area_lake_sheet.png')); print('lake ok', {k: v[0].size for k, v in secs.items()})
if __name__ == '__main__': main()
