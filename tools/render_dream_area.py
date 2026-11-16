#!/usr/bin/env python3
"""꿈 구역 = 네모 상자가 아니라 '지형': 길쭉하게 휘어지는 길(복도처럼), 곳곳에 넓어지는 빈터, 샛길. 길 밖은 안개 낀 허공이고 가장자리는 낭떠러지 단면, 가장자리를 따라 나무가 벽처럼 선다.
화면보다 큰 한 장의 긴 지도이고, 엔진이 카메라로 아이를 따라간다(언더테일의 긴 복도처럼). 이동 가능한 곳은 지형에서 계산한 '걸을 수 있는 칸 마스크'로 내보낸다.
구역 1: 눈 덮인 숲길(snow_trail) — 입구 → 구불구불 긴 길 → 갈림 빈터 → (샛길) 속 빈 나무 쉼터 / 큰 눈밭(추격 자리) → 출구.
사용: python3 tools/render_dream_area.py -> maps/out/area_snow_trail.png, _depth.png, _walk.png, maps/out/dream_nav.json"""
import json, math, os, random, sys
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_dream as RD
from render_city3d import Scene, dk, OUT

CELL = 2
def seg_dist(x, d, a, b):
    ax, ad = a; bx, bd = b; dx, dd = bx - ax, bd - ad; L2 = dx * dx + dd * dd or 1
    t = max(0, min(1, ((x - ax) * dx + (d - ad) * dd) / L2)); return math.hypot(x - (ax + dx * t), d - (ad + dd * t))
def bez(p0, p1, p2, p3, n=16): return [tuple((1 - u) ** 3 * p0[i] + 3 * (1 - u) ** 2 * u * p1[i] + 3 * (1 - u) * u * u * p2[i] + u ** 3 * p3[i] for i in (0, 1)) for u in [k / n for k in range(n + 1)]]

# --- 눈 덮인 숲길의 지형 ---
MAIN = bez((14, 8), (60, 4), (84, 26), (96, 42)) + bez((96, 42), (104, 56), (70, 66), (90, 82))[1:] + bez((90, 82), (112, 96), (150, 90), (176, 96))[1:] + bez((176, 96), (204, 102), (214, 84), (236, 82))[1:] + bez((236, 82), (262, 80), (268, 108), (296, 124))[1:]
BRANCH = bez((96, 42), (120, 34), (140, 46), (166, 38))                      # 갈림 샛길 -> 속 빈 나무
CLEAR = [((96, 42), 17), ((166, 38), 17), ((236, 82), 25), ((14, 8), 12)]    # 빈터(중심, 반지름)
HW = 19                                                                       # 길 반폭
H = 58
RD.H = H
N = len(MAIN)
CUTS = [(0, 18), (12, 31), (25, 51), (45, 67), (61, N - 1)]                    # 구간(MAIN 점 번호 범위): 서로 6점씩 겹쳐서 길이 끊기지 않는다
NAMES = ['snow_1', 'snow_2', 'snow_3', 'snow_4', 'snow_5']; NAMES_H = 'snow_h'
MARGIN_W = 20

def make_section(name, lines, clears, exits, hollow_end=None, seed=1, stream=None):
    """lines: 이 구간의 중심선들(세계 좌표), clears: 빈터 [(중심, 반지름)], exits: [(세계좌표 점, 이동할 구간, 도착 세계좌표)]. 구간마다 자기 바탕(안개 허공 위의 지형 조각)을 가진다."""
    pts = [p for ln in lines for p in ln] + [c for c, r in clears]
    x0 = min(p[0] for p in pts) - MARGIN_W; x1 = max(p[0] for p in pts) + MARGIN_W; d0 = min(p[1] for p in pts) - MARGIN_W; d1 = max(p[1] for p in pts) + MARGIN_W
    tr = lambda p: (p[0] - x0, p[1] - d0)
    L = [[tr(p) for p in ln] for ln in lines]; C = [(tr(c), r) for c, r in clears]; Wd, Dd = int(x1 - x0), int(d1 - d0)
    SA, SB, STONES = (tr(stream[0]), tr(stream[1]), [tr(s) for s in stream[2]]) if stream else (None, None, [])
    in_water = lambda x, d: bool(stream) and seg_dist(x, d, SA, SB) < 12
    RD.W, RD.D = Wd, Dd; rng = random.Random(seed)
    main = L[0]
    def dist(x, d):
        r = min(seg_dist(x, d, a, b) for ln in L for a, b in zip(ln, ln[1:])); inside = r - HW - 1.6 * math.sin(d / 6.0 + x / 8.0)
        for (cx, cd), cr in C: inside = min(inside, math.hypot(x - cx, (d - cd) * 1.15) - cr - 1.6 * math.sin(d / 6.0 + x / 8.0))
        return inside
    def ground(x, d):                                                          # 바닥은 구간 전체가 평평한 눈 평면, 다져진 길만 색이 다르다
        n = RD.noise(x + x0, d + d0)
        if in_water(x, d): return (92 + int(n * 14), 150 + int(n * 14), 196) if int((x * .6 + d * 1.3) // 3) % 2 else (112, 170, 210)      # 시냇물(평평한 바닥 위, 물결 줄무늬)
        if stream and seg_dist(x, d, SA, SB) < 14: return (250, 252, 255)                                                                   # 물가 눈둑
        on = min(seg_dist(x, d, a, b) for ln in L for a, b in zip(ln, ln[1:])) < 6 or any(math.hypot(x - cx, (d - cd) * 1.15) < cr * .55 for (cx, cd), cr in C)
        if on: return (206 + int(n * 8), 216 + int(n * 8), 236)
        c = (238, 242, 250) if n > .3 else (224, 232, 245)
        return (202, 214, 234) if RD.noise(x + x0, d + d0, 5) > .93 else c
    sc = RD.base((236, 240, 250), (206, 216, 236), ground)
    for k in range(1, len(main) - 1):                                          # 발자국
        (ax, ad), (bx, bd) = main[k - 1], main[min(k + 1, len(main) - 1)]; dx, dd = bx - ax, bd - ad; Ln = math.hypot(dx, dd) or 1
        for j in range(3):
            t_ = j / 3; px_ = main[k][0] + (main[min(k + 1, len(main) - 1)][0] - main[k][0]) * t_; pd_ = main[k][1] + (main[min(k + 1, len(main) - 1)][1] - main[k][1]) * t_; side = 2.2 if (k * 3 + j) % 2 else -2.2
            X, Y = sc.P(px_ - dd / Ln * side, pd_ + dx / Ln * side, 0); sc.d.ellipse([X - 2, Y - 1, X + 2, Y + 1], fill=(156, 174, 206))
    # 땅의 모양은 바닥이 아니라 '나무 벽'이 만든다: 길 밖은 전나무를 빽빽이 심어 막고, 길 앞쪽(화면 아래)은 낮은 어린 나무로 길이 가려지지 않게 한다
    trees = []; drifts = []; allp = [p for ln in L for p in ln]
    for _ in range(400):                                                       # 푸아송 원반식: 서로 28 이상 떨어진 곳에만 심어 고르게 띄엄띄엄
        x = rng.uniform(3, Wd - 3); d = rng.uniform(3, Dd - 3)
        if dist(x, d) < 1.5 or in_water(x, d) or stream and seg_dist(x, d, SA, SB) < 20: continue
        nx, nd = min(allp, key=lambda p: math.hypot(x - p[0], d - p[1]))
        if d < nd - 2:                                                          # 길 앞쪽(화면 아래)은 나무가 길을 가리므로 낮은 눈더미만
            if rng.random() < .15 and dist(x, d) > 5 and not any(math.hypot(x - a, d - b) < 20 for a, b, _ in drifts): drifts.append((x - 3, d - 2, rng.choice((6, 8, 10))))
            continue
        if any(math.hypot(x - tx, d - td) < 28 for tx, td, _ in trees): continue
        trees.append((x, d, rng.choice((38, 42, 46))))
    for (x, d, h) in trees: RD.fir(sc, x, d, h)
    for (x, d, w) in drifts: sc.jobs.append((d, lambda x=x, d=d, w=w: [sc.box(x, d, w, w * .6, w * .45, (246, 250, 255), (206, 216, 236), (178, 190, 216))]))
    for _ in range(5):                                                          # 길가의 눈 덮인 바위와 쓰러진 통나무(입체 소품)
        xc, dc = rng.choice([p for ln in L for p in ln]); x = xc + rng.uniform(-14, 14); d = dc + rng.uniform(-12, 12); e = dist(x, d)
        if not (-9 < e < -5.5) or any(math.hypot(x - tx, d - td) < 6 for tx, td, _ in trees): continue
        if rng.random() < .5: sc.jobs.append((d, lambda x=x, d=d: sc.box(x, d, 7, 5, 4, (246, 250, 255), (176, 188, 210), (150, 162, 188))))
        else: sc.jobs.append((d, lambda x=x, d=d: [sc.box(x, d, 12, 3.5, 3, (136, 106, 88), (104, 80, 66), (82, 62, 52)), sc.box(x - .5, d - .3, 13, 4.2, 1, (246, 250, 255), (226, 234, 248), (190, 202, 226), z0=3)]))
    hbox = None
    if hollow_end:                                                              # 속 빈 나무(샛길 끝의 쉼터)
        ex_, ed_ = tr(hollow_end); hx, hd = ex_ - 7, ed_ + 7; hbox = (hx, hd)
        def f():
            sc.box(hx, hd, 14, 10, 36, (124, 96, 78), (100, 76, 60), (78, 58, 46)); sc.box(hx - 1, hd - 1, 16, 12, 3, (246, 250, 255), (226, 234, 248), (190, 202, 226), z0=36)
            sc.poly([(hx + 4, hd - .1, 0), (hx + 10, hd - .1, 0), (hx + 10, hd - .1, 17), (hx + 7, hd - .1, 22), (hx + 4, hd - .1, 17)], (30, 22, 22)); sc.poly([(hx + 5, hd - .2, 0), (hx + 9, hd - .2, 0), (hx + 9, hd - .2, 9), (hx + 5, hd - .2, 9)], (236, 200, 124))
        sc.jobs.append((hd, f)); sc.glow(hx + 7, hd - 2, 26, col=(255, 214, 140), power=.45)
    for (sx, sd) in STONES:                                                     # 징검다리: 나무 그루터기(둥근 단면, 나이테)
        def stump(sx=sx, sd=sd):
            sc.box(sx - 2.2, sd - 2.2, 4.4, 4.4, 2.6, (186, 140, 96), (122, 88, 60), (96, 68, 46))
            X, Y = sc.P(sx, sd, 2.6); sc.d.ellipse([X - 3, Y - 2, X + 3, Y + 2], fill=(198, 154, 106)); sc.d.ellipse([X - 1, Y - 1, X + 1, Y + 1], outline=(150, 108, 72)); sc.d.point((X, Y), fill=(150, 108, 72))
        sc.jobs.append((sd, stump))
    exit_pts = [tr(e[0]) for e in exits]
    for (ex_, ed_) in exit_pts: sc.glow(ex_, ed_, 20, col=(255, 255, 255), power=.35)                     # 구간 끝: 안개빛이 번진다(이어지는 곳 표시)
    for _ in range(120): X, Y = rng.randrange(6, sc.CW - 6), rng.randrange(6, sc.CH - 6); sc.d.point((X, Y), fill=(255, 255, 255))
    dep = Image.new('L', sc.img.size, 255)
    for depth, f in sorted(sc.jobs, key=lambda j: -j[0]):
        before = sc.img.copy(); f(); diff = ImageChops.difference(sc.img, before).convert('L').point(lambda v: 255 if v else 0)
        dep.paste(int(max(0, min(254, round((depth + 2) * 3)))), (0, 0), diff)
    gw, gh = math.ceil(Wd / CELL), math.ceil(Dd / CELL); mask = Image.new('L', (gw, gh), 0); mp = mask.load()
    for j in range(gh):
        for i in range(gw):
            x, d = (i + .5) * CELL, (j + .5) * CELL
            if in_water(x, d) and not any(math.hypot(x - sx, d - sd) < 3.6 for sx, sd in STONES): continue
            if (dist(x, d) < -4.5 or in_water(x, d)) and not any(abs(x - tx) < 4 and abs(d - td) < 3.5 for tx, td, _ in trees) and not (hbox and hbox[0] - 2 < x < hbox[0] + 16 and hbox[1] - 2 < d < hbox[1] + 12): mp[i, j] = 255
    nav_exits = [{'zone': (ex_ - 4, ex_ + 4, ed_ - 4, ed_ + 4), 'to': e[1], 'spawn': None, 'world_to': e[2]} for (ex_, ed_), e in zip(exit_pts, exits)]
    return sc.img, dep, mask, {'W': Wd, 'D': Dd, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': sc.CW, 'CH': sc.CH, 'rects': [], 'exits': nav_exits, 'start': tr(lines[0][min(3, len(lines[0]) - 1)]), 'origin': (x0, d0)}

def build_all():
    out = {}; bs, be = 4, len(BRANCH) - 1
    # 각 구간: (이름, 중심선들, 빈터, 나가는 곳들 [(점, 이동할 구간, 도착점)], 속 빈 나무 끝)
    for k, (s, e) in enumerate(CUTS):
        lines = [MAIN[s:e + 1]]; clears = []; exits = []
        if k > 0: exits.append((MAIN[s], NAMES[k - 1], MAIN[s + 3]))
        if k < len(CUTS) - 1: exits.append((MAIN[e], NAMES[k + 1], MAIN[e - 3]))
        if k == 0: clears.append(((14, 8), 26))
        if k == 1: lines.append(BRANCH[:10]); clears.append(((96, 42), 30)); exits.append((BRANCH[9], NAMES_H, BRANCH[bs + 1]))
        if k == 4: clears.append(((236, 82), 40))
        stream = None
        if k == 2:                                                              # 징검다리: 길을 가로지르는 시냇물 + 나무 그루터기 5개
            m = MAIN[38]; ta, tb = MAIN[37], MAIN[39]; tx, td = tb[0] - ta[0], tb[1] - ta[1]; ln_ = math.hypot(tx, td) or 1; tx, td = tx / ln_, td / ln_
            stream = ((m[0] - td * 60, m[1] + tx * 60), (m[0] + td * 60, m[1] - tx * 60), [(m[0] + tx * s, m[1] + td * s) for s in (-12, -6, 0, 6, 12)])
        out[NAMES[k]] = make_section(NAMES[k], lines, clears, exits, seed=10 + k, stream=stream)
    out[NAMES_H] = make_section(NAMES_H, [BRANCH[bs:]], [((166, 38), 28)], [(BRANCH[bs], NAMES[1], BRANCH[7])], hollow_end=(166, 38), seed=30)
    return out

def main():
    secs = build_all(); nav = {}
    for name, (im, dep, mask, meta) in secs.items():
        im.save(os.path.join(OUT, 'area_%s.png' % name)); dep.save(os.path.join(OUT, 'area_%s_depth.png' % name)); mask.save(os.path.join(OUT, 'area_%s_walk.png' % name)); nav[name] = meta
    for name, meta in nav.items():                                                 # 도착 세계좌표 -> 도착 구간의 지역 좌표(spawn)
        for e in meta['exits']:
            wx, wd = e.pop('world_to'); ox, od = nav[e['to']]['origin']; e['spawn'] = (round(wx - ox, 1), round(wd - od, 1))
    json.dump(nav, open(os.path.join(OUT, 'dream_nav.json'), 'w'), ensure_ascii=False)
    names = list(secs); ims = [secs[k][0] for k in names]; S = 2; wsum = sum(i.width for i in ims) * S + 10 * (len(ims) + 1); hmax = max(i.height for i in ims) * S + 20
    sheet = Image.new('RGB', (wsum, hmax), (40, 40, 48)); x = 10
    for im in ims: sheet.paste(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, 10)); x += im.width * S + 10
    sheet.save(os.path.join(OUT, 'area_snow_sheet.png')); print('area ok', {k: v[0].size for k, v in secs.items()})
if __name__ == '__main__': main()
