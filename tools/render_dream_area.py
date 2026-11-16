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

def fir2(sc, x, d, h):
    """눈 덮인 전나무(다시 그림): 5단 층, 층마다 톱니 모양 아랫단, 왼쪽(빛)은 밝은 초록·오른쪽은 어두운 초록 두 톤, 층 윗면의 눈은 불규칙한 덩어리, 줄기는 짧고 굵게."""
    rr = random.Random(int(x * 13 + d * 7))
    def draw():
        bx, by = sc.P(x, d, 0); n = 5; trunk = max(7, h // 5)
        sc.d.rectangle([bx - 2, by - trunk, bx + 1, by], fill=(104, 74, 56)); sc.d.line([(bx + 1, by - trunk), (bx + 1, by)], fill=(70, 50, 40)); sc.d.line([(bx - 2, by - trunk), (bx - 2, by)], fill=(128, 94, 72)); sc.d.rectangle([bx - 3, by - 1, bx + 2, by], fill=(104, 74, 56))
        y = by - trunk + 1; tier_h = (h - trunk) / n
        for k in range(n):
            w = int(3 + (n - k) * (h / 22.0) * .55 + 2); top = y - tier_h - 1; base_y = y
            sc.d.polygon([(bx, top - 2), (bx - w, base_y), (bx, base_y - 1)], fill=(52, 98, 84)); sc.d.polygon([(bx, top - 2), (bx + w, base_y), (bx, base_y - 1)], fill=(30, 62, 58))
            for j in range(-w, w + 1, 3):
                jx = bx + j; c = (52, 98, 84) if j < 0 else (30, 62, 58); sc.d.polygon([(jx - 2, base_y - 1), (jx + 2, base_y - 1), (jx, base_y + 2)], fill=c)
            sc.d.line([(bx - w + 1, base_y - 1), (bx - 1, top)], fill=(78, 130, 108))
            for j in range(-w + 2, w - 1, 2):
                frac = abs(j) / float(w); yy = top + 2 + (base_y - top - 4) * frac - rr.randint(0, 1)
                if rr.random() < .8: sc.d.rectangle([bx + j - 1, yy - 1, bx + j + 1, yy + (1 if frac > .5 else 0)], fill=(250, 252, 255)); sc.d.point((bx + j + 1, yy + 1), fill=(206, 218, 240))
            for j in range(-w + 3, w - 2, 4):
                if rr.random() < .6: sc.d.point((bx + j, base_y + 1), fill=(226, 236, 250))
            y = base_y - int(tier_h * .72)
        sc.d.polygon([(bx - 1, y - 2), (bx + 1, y - 2), (bx, y - 6)], fill=(250, 252, 255))
    sc.jobs.append((d, draw))
RD.fir = fir2
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

def make_section(name, lines, clears, exits, hollow_end=None, seed=1, stream=None, puzzle=None):
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
    if hollow_end:                                                              # 속 빈 큰 나무(샛길 끝의 쉼터): 굵은 줄기 + 뿌리 + 눈 덮인 가지, 속에서 따뜻한 빛
        ex_, ed_ = tr(hollow_end); hx, hd = ex_ - 12, ed_ + 8; hbox = (hx, hd)
        def f():                                                                # 직사각형 줄기(처음 모양)를 크게: 눈 덮인 윗면, 아치 모양 구멍, 안쪽의 따뜻한 빛
            sc.box(hx, hd, 22, 14, 40, (124, 96, 78), (100, 76, 60), (78, 58, 46)); sc.box(hx - 1.5, hd - 1.5, 25, 17, 4, (246, 250, 255), (226, 234, 248), (190, 202, 226), z0=40)
            sc.poly([(hx + 6, hd - .1, 0), (hx + 16, hd - .1, 0), (hx + 16, hd - .1, 22), (hx + 11, hd - .1, 30), (hx + 6, hd - .1, 22)], (30, 22, 22))
            sc.poly([(hx + 8, hd - .2, 0), (hx + 14, hd - .2, 0), (hx + 14, hd - .2, 12), (hx + 8, hd - .2, 12)], (236, 200, 124))
        sc.jobs.append((hd, f)); sc.glow(hx + 11, hd - 2, 34, col=(255, 214, 140), power=.5)
    for (sx, sd) in STONES:                                                     # 징검다리: 나무 그루터기(둥근 단면, 나이테)
        def stump(sx=sx, sd=sd):
            sc.box(sx - 2.2, sd - 2.2, 4.4, 4.4, 2.6, (186, 140, 96), (122, 88, 60), (96, 68, 46))
            X, Y = sc.P(sx, sd, 2.6); sc.d.ellipse([X - 3, Y - 2, X + 3, Y + 2], fill=(198, 154, 106)); sc.d.ellipse([X - 1, Y - 1, X + 1, Y + 1], outline=(150, 108, 72)); sc.d.point((X, Y), fill=(150, 108, 72))
        sc.jobs.append((sd, stump))
    objects = []; extra_exits = []
    if puzzle:                                                                  # 순서 퍼즐: 발자국이 이어 주는 순서대로 등불 3개를 켜면 눈 속의 맨홀 뚜껑이 드러난다
        pl = [tr(p_) for p_ in puzzle['lanterns']]; mhx, mhd = tr(puzzle['manhole'])
        walk = [pl[0]]
        for a_, b_ in zip(pl, pl[1:]): walk += [(a_[0] + (b_[0] - a_[0]) * u, a_[1] + (b_[1] - a_[1]) * u) for u in (.25, .5, .75, 1)]
        for k_, (fx, fd) in enumerate(walk):                                     # 발자국: 등불에서 등불로(번갈아 좌우)
            X, Y = sc.P(fx + (1.8 if k_ % 2 else -1.8), fd + (1.2 if k_ % 2 else -1.2), 0); sc.d.ellipse([X - 2, Y - 1, X + 2, Y + 1], fill=(156, 174, 206))
        sx0, sd0 = pl[0]
        for k_ in range(6):                                                       # 첫 등불로 이끄는 발자국(샛길 쪽에서)
            X, Y = sc.P(sx0 - 22 + k_ * 3.5 + (1.6 if k_ % 2 else -1.6), sd0 + 8 - k_ * 1.4, 0); sc.d.ellipse([X - 2, Y - 1, X + 2, Y + 1], fill=(156, 174, 206))
        for k_, (lx, ld) in enumerate(pl):
            def lamp(lx=lx, ld=ld):                                                   # 석등(돌 등불): 낮은 받침, 기둥, 불집, 눈 덮인 지붕 - 눈 숲에 어울리는 낮은 돌 등불
                b = sc.P(lx, ld, 0)
                sc.d.rectangle([b[0] - 5, b[1] - 3, b[0] + 5, b[1]], fill=(158, 164, 178)); sc.d.rectangle([b[0] - 5, b[1] - 3, b[0] + 5, b[1] - 3], fill=(196, 202, 216))
                sc.d.rectangle([b[0] - 2, b[1] - 9, b[0] + 2, b[1] - 3], fill=(138, 144, 160)); sc.d.rectangle([b[0] - 2, b[1] - 9, b[0] - 2, b[1] - 3], fill=(176, 182, 198))
                sc.d.rectangle([b[0] - 4, b[1] - 16, b[0] + 4, b[1] - 9], fill=(150, 156, 172)); sc.d.rectangle([b[0] - 2, b[1] - 14, b[0] + 2, b[1] - 11], fill=(44, 40, 56))
                sc.d.polygon([(b[0] - 7, b[1] - 16), (b[0] + 7, b[1] - 16), (b[0] + 3, b[1] - 21), (b[0] - 3, b[1] - 21)], fill=(122, 128, 146)); sc.d.polygon([(b[0] - 6, b[1] - 17), (b[0] + 6, b[1] - 17), (b[0] + 3, b[1] - 21), (b[0] - 3, b[1] - 21)], fill=(250, 252, 255))
            sc.jobs.append((ld, lamp)); objects.append({'id': '%s_L%d' % (name, k_), 'type': 'lantern', 'h': 14, 'x': round(lx, 1), 'd': round(ld, 1), 'order': k_})
        extra_exits.append({'zone': (mhx - 5, mhx + 5, mhd - 5, mhd + 5), 'to': puzzle['to'], 'spawn': None, 'world_to': None, 'manhole': True, 'lock': 'order', 'mx': round(mhx, 1), 'md': round(mhd, 1)})
    exit_pts = [tr(e[0]) for e in exits]
    for (ex_, ed_), e in zip(exit_pts, exits):
        if len(e) > 3 and e[3] == 'manhole':                                    # 다른 맵으로 가는 곳 = 눈 속에 뚫린 맨홀
            X, Y = sc.P(ex_, ed_, 0); sc.d.ellipse([X - 9, Y - 5, X + 9, Y + 5], fill=(236, 242, 252)); sc.d.ellipse([X - 8, Y - 4, X + 8, Y + 4], fill=(86, 94, 112)); sc.d.ellipse([X - 7, Y - 3, X + 7, Y + 3], fill=(124, 134, 154)); sc.d.ellipse([X - 5, Y - 3, X + 5, Y + 2], fill=(12, 14, 26)); sc.d.rectangle([X - 1, Y, X + 1, Y + 1], fill=(236, 190, 120))
            sc.d.ellipse([X + 9, Y + 1, X + 17, Y + 5], fill=(96, 104, 122)); sc.d.ellipse([X + 10, Y, X + 16, Y + 3], fill=(134, 144, 164))
            for k, (dx, dy) in enumerate(((0, -6), (1, -9), (-1, -12))): sc.d.rectangle([X + dx - 1, Y + dy, X + dx + 1, Y + dy + 1], fill=(236, 244, 255))
            sc.glow(ex_, ed_, 16, col=(255, 214, 140), power=.3)
        else: sc.glow(ex_, ed_, 20, col=(255, 255, 255), power=.35)                     # 구간 끝: 안개빛이 번진다(이어지는 곳 표시)
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
            if (dist(x, d) < -4.5 or in_water(x, d)) and not any(abs(x - tx) < 4 and abs(d - td) < 3.5 for tx, td, _ in trees) and not (hbox and hbox[0] - 5 < x < hbox[0] + 27 and hbox[1] - 3 < d < hbox[1] + 20): mp[i, j] = 255
    nav_exits = [{'zone': (ex_ - 4, ex_ + 4, ed_ - 4, ed_ + 4), 'to': e[1], 'spawn': None, 'world_to': e[2], **({'manhole': True, 'zone': (ex_ - 5, ex_ + 5, ed_ - 5, ed_ + 5)} if len(e) > 3 else {})} for (ex_, ed_), e in zip(exit_pts, exits)]
    nav_exits += extra_exits
    return sc.img, dep, mask, {'W': Wd, 'D': Dd, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': sc.CW, 'CH': sc.CH, 'rects': [], 'objects': objects, 'exits': nav_exits, 'start': tr(lines[0][min(3, len(lines[0]) - 1)]), 'origin': (x0, d0)}

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
    out[NAMES_H] = make_section(NAMES_H, [BRANCH[bs:]], [((166, 38), 28)], [(BRANCH[bs], NAMES[1], BRANCH[7])], hollow_end=(166, 38), seed=30, puzzle={'lanterns': [(150, 30), (170, 22), (188, 34)], 'manhole': (168, 40), 'to': 'lake_1'})
    return out

def main():
    secs = build_all(); nav = {}
    for name, (im, dep, mask, meta) in secs.items():
        im.save(os.path.join(OUT, 'area_%s.png' % name)); dep.save(os.path.join(OUT, 'area_%s_depth.png' % name)); mask.save(os.path.join(OUT, 'area_%s_walk.png' % name)); nav[name] = meta
    for name, meta in nav.items():                                                 # 도착 세계좌표 -> 도착 구간의 지역 좌표(spawn)
        for e in meta['exits']:
            if e.get('world_to') and e['to'] in nav: wx, wd = e.pop('world_to'); ox, od = nav[e['to']]['origin']; e['spawn'] = (round(wx - ox, 1), round(wd - od, 1))
    json.dump(nav, open(os.path.join(OUT, 'dream_nav.json'), 'w'), ensure_ascii=False)
    names = list(secs); ims = [secs[k][0] for k in names]; S = 2; wsum = sum(i.width for i in ims) * S + 10 * (len(ims) + 1); hmax = max(i.height for i in ims) * S + 20
    sheet = Image.new('RGB', (wsum, hmax), (40, 40, 48)); x = 10
    for im in ims: sheet.paste(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, 10)); x += im.width * S + 10
    sheet.save(os.path.join(OUT, 'area_snow_sheet.png')); print('area ok', {k: v[0].size for k, v in secs.items()})
if __name__ == '__main__': main()
