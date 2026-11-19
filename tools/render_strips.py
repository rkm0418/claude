#!/usr/bin/env python3
"""테마마다 한 장의 긴 띠(strip): 방과 통로를 가로로 이어 한 공간으로 만든다. 컷이 없고, 아이가 걸으면 앞 구간에 불이 켜지고 지나온 구간은 어두워진다(엔진 조명).
구간 목록은 tools/scene_chains.json(키·번호 고정). 구간 내용은 키 시드로 정해져, 다른 구간을 빼도 안 바뀐다.
사용: python3 tools/render_strips.py [테마 ...]  -> maps/out/world_<테마>strip.png/_depth/_walk, more_nav.json (export_web 이 읽는다)"""
import json, math, os, random, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_more as M
import render_world as W
import theme_design as TD
from render_world import OUT
from render_dream_area import CELL

THEMES, ORDER, INTERIOR = M.THEMES, M.ORDER, M.INTERIOR
STRIPS = {}
rnd = lambda key: random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(key)))
cl = lambda v, a, b: max(a, min(b, v))

def layout(th, chain):                                                          # 구간을 왼→오로 배치하고 구간마다 길(lane)과 영역을 정한다
    inter = th in INTERIOR; D = 64 if inter else 84; x = 0.0; d_in = D * .5; secs = []
    for si, s in enumerate(chain):
        z3 = None; r = rnd(s['key']); sh = 'square' if s['shape'] == 'deep' else s['shape']; hw = (9 if sh == 'switch' else 13) if s['kind'] == 'passage' else 14; nxt = chain[si + 1] if si + 1 < len(chain) else None
        if s['kind'] == 'passage':
            w = {'tunnel': r.randint(170, 240), 'hall': r.randint(80, 110), 'bend': r.randint(90, 120) if inter else r.randint(130, 170), 'zig': r.randint(160, 200), 'switch': r.randint(150, 190)}[sh]
            sg = 1 if d_in < D * .5 else -1
            if s.get('bend') == 'down': sg = -1
            if s.get('bend') == 'up': sg = 1
            if s.get('len'): w = s['len']
            if sh == 'switch':                                                      # ㄱ 밑에 ㄴ이 붙은 S자(ㄹ) 공간: 위 칸 오른쪽으로 → 내려와 가운데 칸 왼쪽으로 → 내려와 아래 칸 오른쪽으로
                d_in = D * .2; dB = d_in + 30; dC = dB + 30; d_out = dC                                        # 3차원: 앞 칸(바닥) → 계단으로 뒤로 올라 가운데 칸(높음) → 계단으로 더 올라 뒤 칸(가장 높음) → 오른쪽 끝에서 계단으로 내려온다
                pts = [(x, d_in), (x + w * .82, d_in), (x + w * .82, dB), (x + w * .18, dB), (x + w * .18, dC), (x + w, dC)]
                z3 = dict(dA=d_in, dB=dB, dC=dC, zB=12, zC=24, xr=x + w * .82, xl=x + w * .18, xd=x + w - 48, hw=hw)
            elif sh in ('tunnel', 'hall'): d_out = d_in; pts = [(x, d_in), (x + w, d_in)]
            elif sh == 'bend': d_out = cl(d_in + sg * r.uniform(20, 26), 22, D - 22); xm = x + w * .5; pts = [(xm - w * .5, d_in), (xm, d_in), (xm, d_out), (x + w, d_out)]
            else: d_mid = cl(d_in + sg * 24, 22, D - 22); d_out = d_in; pts = [(x, d_in), (x + w * .3, d_in), (x + w * .3, d_mid), (x + w * .7, d_mid), (x + w * .7, d_in), (x + w, d_in)]
            ys = [p[1] for p in pts]; ext = (cl(min(ys) - hw - 7, 2, D), cl(max(ys) + hw + 7, 0, D - 2))
        else:
            if sh == 'long': w = r.randint(280, 420); h = r.randint(44, 54)
            elif sh == 'square': w = r.randint(56, 60) if inter else r.randint(78, 84); h = min(D - 6, w)
            else: w = r.randint(80, 96) if inter else r.randint(92, 112); h = r.randint(46, 52) if inter else r.randint(56, 66)
            d_out = r.uniform(D * .34, D * .66)
            if s.get('dout') is not None: d_out = D * s['dout']
            if nxt is not None and nxt['shape'] == 'switch': d_out = D * .2       # S자 통로로 들어가기 좋은 높이에서 나간다
            d0 = max(3, min(d_in, d_out) - 16); d1 = min(D - 3, d0 + h)
            if d1 < max(d_in, d_out) + 16: d1 = min(D - 3, max(d_in, d_out) + 16); d0 = max(3, d1 - h)
            d0 = max(3, min(d0, min(d_in, d_out) - 14)); d1 = min(D - 3, max(d1, max(d_in, d_out) + 14))                  # 들어오는 길·나가는 길이 항상 방 영역 안에 들어오게
            ext = (d0, d1); dm = (d_in + d_out) / 2 + r.uniform(-8, 8)
            pts = [(x, d_in), (x + w * .35, d_in), (x + w * .65, d_out), (x + w, d_out)] if sh == 'long' else [(x, d_in), (x + w * .5, cl(dm, d0 + 14, d1 - 14)), (x + w, d_out)]
        secs.append(dict(s=s, key=s['key'], kind=s['kind'], shape=sh, x0=x, x1=x + w, pts=pts, hw=hw, d_in=d_in, d_out=d_out, ext=ext, mid=M.polymid(pts), z3=(z3 if sh == 'switch' and s['kind'] == 'passage' else None)))
        x += w; d_in = d_out
    return secs, x, D

def lane_d(sec, x):                                                             # 구간 안 x 에서의 길 중심 d
    for p, q in zip(sec['pts'], sec['pts'][1:]):
        if p[0] <= x <= q[0] or q[0] <= x <= p[0]:
            if abs(q[0] - p[0]) < 1e-6: return q[1]
            return p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0])
    return sec['d_out']

def strip_spec(th, chain):
    secs, Wt, D = layout(th, chain); T = THEMES[th]; r = rnd(th + 'strip'); inter = th in INTERIOR
    shapes = []
    for sec in secs:
        shapes.append(('path', sec['pts'], sec['hw']))
        if sec['kind'] == 'room' and sec['shape'] in ('square', 'wide') and rnd(sec['key'] + 'c').random() < .6: shapes.append(('circle', M.polymid(sec['pts'])[0], M.polymid(sec['pts'])[1], rnd(sec['key'] + 'r').randint(20, 26)))
    spec = dict(theme=th, W=Wt, D=D, secs=secs, shapes=shapes, wall=r.choice(T['walls']), tries=0, density=1.0, alleys=[], tips=[], H=min(T['H'], 44 if inter else 64))
    spec['erode'] = 3 if any(s['shape'] == 'switch' for s in secs) else 4
    spec['start'] = (14, secs[0]['d_in']) if th != 'city' else ((secs[0]['x0'] + secs[0]['x1']) / 2 - 6, secs[0]['d_in'] - 2); spec['end'] = (Wt - 14, secs[-1]['d_out'])
    for sec in secs:                                                                                                       # 딸린 골목(뒷벽에 붙은 칸): 뒷벽까지 열린 방에만
        if sec['kind'] != 'room' or sec['ext'][1] < D - 8: continue
        rr = rnd(sec['key'] + 'a'); n = rr.choice((1, 2)) if sec['shape'] == 'long' else 0; xs = []
        for _ in range(120):
            if len(xs) >= n: break
            x = rr.uniform(sec['x0'] + 26, sec['x1'] - 26); ln = rr.randint(26, 34)
            if any(abs(x - q) < 48 for q in xs): continue
            xx = [x - 22 + 44 * i / 5 for i in range(6)]; dd = [D - 4 - ln * j / 4 for j in range(5)]
            e = W.sd(shapes, np.array([[u for u in xx] for _ in dd]), np.array([[v] * 6 for v in dd]))
            if e.min() < 1: continue
            xs.append(x); spec['alleys'].append((x, ln, 17)); spec['tips'].append((x, D - 4 - ln / 2))
    return spec

def setup(name, spec):
    T = THEMES[spec['theme']]; W.GRADE[name] = M.GRADES[spec['theme']]
    box = dict(wall=spec['wall'], vig=T['vig'] * .5, pranges=[(s['x0'] + 3, s['x1'] + 3, TD.PWALL[spec['theme']]) for s in spec['secs'] if s['kind'] == 'passage'])
    W.BLOCKED[name] = lambda x, d, n, g=T['ground']: np.clip(g(x, d, np.full(n, -10.), n), 0, 255).astype(int)
    last = spec['secs'][-1]
    ex = [dict(at=(spec['W'] - 8, last['d_out']), hw=14, hwx=5, to=None, endMsg='길이 끊겨 있다. 여기서는 더 갈 수 없다', side='right')]
    ent = dict(H=spec['H'], shapes=spec['shapes'], zones=[], lane_zones=[(('path', s['pts'], s['hw']), TD.LANE[spec['theme']]) for s in spec['secs'] if s['kind'] == 'passage'], ground=T['ground'], face=T['face'], ch=30, sky=((20, 20, 30), (40, 40, 60)), start=spec['start'], box=box, wob=T['wob'], exits=ex, bbox=(0, 0, spec['W'], spec['D']))
    W.AREAS[name] = ent; W.STRICT.add(name); STRIPS[name] = spec; return ent

UNIT_I = [0]
def unit(k, th, lx, ld, low, r, run=True):                                    # 벽 줄 한 칸: 통로·칸막이는 연속 벽(run_unit), 방 가장자리는 낮고 가벼운 소품
    UNIT_I[0] += 1
    if run: TD.run_unit(k, th, lx, ld, low, UNIT_I[0], r)
    else: M.BARLOW[th](k, lx - 3.5, ld - 3, r)

def strip_props(name, k, tr, inside, rng):
    spec = STRIPS[name]; th = spec['theme']; T = THEMES[th]; sc = k.sc; Wl, Dl = sc.W, sc.D; D = spec['D']; secs = spec['secs']; r = random.Random(sum(map(ord, name)) * 7 + spec['tries'] * 101); placed = []
    def put(lx, ld, g_, low_ok=True):
        if any(math.hypot(lx - a, ld - b) < 5.5 for a, b, gg in placed if gg == 7): return False
        placed.append((lx, ld, 7)); return True
    for i, sec in enumerate(secs):                                              # 1) 구간 벽: 통로는 길 양옆, 방은 앞·뒤 줄
        rr = rnd(sec['key'] + 'w' + str(spec['tries']))
        if sec['kind'] == 'passage' and sec['shape'] == 'switch':                # S자(ㄹ) 통로: 칸 사이마다 낮은 칸막이 줄 하나, 바깥쪽은 앞은 낮게·뒤는 높게
            pa, pb, pc, pd_, pe, pf = sec['pts']; dA, dB, dC = pa[1], pc[1], pe[1]; xr, xl, hw = pb[0], pe[0], sec['hw']; sg2 = 1 if dB > dA else -1
            def row(xa, xb, dd, low):
                for x in np.arange(min(xa, xb), max(xa, xb), 7.0):
                    if sec['x0'] + 1 < x < sec['x1'] - 1 and 1 < dd < D - 1:
                        lx, ld = tr((x, dd))
                        if put(lx, ld, 7): unit(k, th, lx, ld, low, rr)
            row(sec['x0'] + 2, xr + hw + 6, dA - sg2 * (hw + 5), sg2 > 0)                          # A 바깥쪽
            row(sec['x0'] + 2, xr - hw - 9, (dA + dB) / 2, True)                                  # A·B 사이
            row(xl + hw + 9, sec['x1'] - 2, (dB + dC) / 2, True)                                  # B·C 사이
            row(xl - hw - 6, sec['x1'] - 2, dC + sg2 * (hw + 5), sg2 < 0)                         # C 바깥쪽
            for dd in np.arange(min(dB, dC) - hw, max(dB, dC) + hw, 7.0):                          # 왼쪽·오른쪽 꺾이는 곳의 바깥 벽
                lx, ld = tr((xl - hw - 6, dd))
                if put(lx, ld, 7): unit(k, th, lx, ld, False, rr)
            for dd in np.arange(min(dA, dB) - hw, max(dA, dB) + hw, 7.0):
                lx, ld = tr((xr + hw + 6, dd))
                if put(lx, ld, 7): unit(k, th, lx, ld, False, rr)
            z3 = sec['z3']; hwz = z3['hw']; tc = TD.RUN[th][3]; top = tuple(min(255, int(v * 1.12) + 8) for v in tc); fr = tuple(int(v * .78) for v in tc); rt = tuple(int(v * .62) for v in tc)
            def plat(x, d, w_, dp_, h_, z0=0, alt=False):                                           # 입체 바닥판/계단 한 칸: 바닥처럼 가장 먼저 그리고 깊이 지도에는 남기지 않는다(아이를 가리지 않는다)
                lx, ld = tr((x, d)); tp = tuple(min(255, v + 14) for v in top) if alt else top
                k.sc.jobs.append((390 + d / 100.0, lambda lx=lx, ld=ld, w_=w_, dp_=dp_, h_=h_, z0=z0, tp=tp: k.sc.box(lx, ld, w_, dp_, h_, tp, fr, rt, z0=z0)))
            plat(z3['xl'] - hwz, z3['dC'] - hwz, z3['xd'] - (z3['xl'] - hwz), 2 * hwz, z3['zC'])                       # 뒤 칸(가장 높음)
            plat(z3['xl'] - hwz, z3['dB'] - hwz, z3['xr'] + hwz - (z3['xl'] - hwz), 2 * hwz, z3['zB'])                 # 가운데 칸
            for i in range(6):                                                                         # 앞 칸 → 가운데 칸 계단(오른쪽 끝)
                plat(z3['xr'] - hwz, z3['dA'] + hwz + 2 * i, 2 * hwz, 2, z3['zB'] * (i + 1) / 6.5, alt=i % 2 == 1)
            for i in range(6):                                                                         # 가운데 칸 → 뒤 칸 계단(왼쪽 끝)
                plat(z3['xl'] - hwz, z3['dB'] + hwz + 2 * i, 2 * hwz, 2, z3['zB'] + (z3['zC'] - z3['zB']) * (i + 1) / 6.5, alt=i % 2 == 1)
            for i in range(6):                                                                         # 뒤 칸 → 바닥 내림 계단(오른쪽 끝)
                plat(z3['xd'] + 8 * i, z3['dC'] - hwz, 8, 2 * hwz, z3['zC'] * (1 - (i + 1) / 7.0), alt=i % 2 == 1)
        elif sec['kind'] == 'passage':
            hw = sec['hw'] + 7
            for p0, p1 in zip(sec['pts'], sec['pts'][1:]):
                L_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = int(L_ // 7) + 1; ux, ud = (p1[0] - p0[0]) / (L_ or 1), (p1[1] - p0[1]) / (L_ or 1)
                for q in range(n + 1):
                    cx, cd = p0[0] + ux * min(q * 7, L_), p0[1] + ud * min(q * 7, L_)
                    for sg in (-1, 1):
                        x, d = cx - ud * hw * sg, cd + ux * hw * sg
                        if not (sec['x0'] + 1 < x < sec['x1'] - 1 and 1 < d < D - 1): continue
                        if any(math.hypot(x - a, d - b) < sec['hw'] + 3.5 for a, b in [(sx, sd_) for (sx, sd_) in sec['samples']]): continue
                        lx, ld = tr((x, d))
                        if put(lx, ld, 7): unit(k, th, lx, ld, d < cd - 3, rr)
        else:
            d0, d1 = sec['ext']
            for x in np.arange(sec['x0'] + 4, sec['x1'] - 2, 7.0):
                if d0 > 10:
                    lx, ld = tr((x, d0 - 4))
                    if put(lx, ld, 7): unit(k, th, lx, ld, True, rr)
                if d1 < D - 10:
                    lx, ld = tr((x, d1 + 4))
                    if put(lx, ld, 7): unit(k, th, lx, ld, True, rr)
    for i in range(len(secs) + 1):                                              # 2) 구간 경계: 칸막이 기둥줄 + 길 자리에 컨셉 아치
        xb = secs[i]['x0'] if i < len(secs) else spec['W']
        if i == 0: continue
        prv = secs[i - 1]; lane = prv['d_out'] if i < len(secs) else secs[-1]['d_out']; rr = rnd('b%d%s' % (i, name))
        closed = (i == len(secs))
        for d in np.arange(3.0, D - 2, 7.0):
            if not closed and abs(d - lane) < 16: continue
            lx, ld = tr((xb, d))
            if put(lx, ld, 7): unit(k, th, lx, ld, d < lane - 3, rr)
        gi = (secs[i]['s']['gate'] if i < len(secs) else secs[-1]['s']['gate']); lx, ld = tr((xb, lane)); M.gateway(k, th, 'L', 0, ld, Wl, Dl, gi, 'closed' if closed else 'arch', rr, ox=lx)
    for (ax, ln, w) in spec['alleys']:                                          # 3) 딸린 골목
        lx = ax + 3; rr = rnd('al%d%s' % (int(ax), name))
        for q in range(int(ln // 7) + 1):
            dd = Dl - 4 - q * 7
            for sx in (lx - w, lx + w):
                if put(sx, dd, 7): unit(k, th, sx, dd, False, rr)
        cand = list(T['props']); fn_ = cand[rr.randrange(len(cand))][1]
        nb, nr = len(k.block), len(k.rects); fn_(k, lx - 2, Dl - 12, rr); del k.block[nb:]; del k.rects[nr:]
    LC = TD.LIGHT[th]; lamp = M.p_streetlamp(True, LC, 26, .35) if th == 'city' else M.p_lamp(True, LC, 26, .35)                        # 4) 조명은 절제: 통로는 120px마다 뒷벽 쪽 가로등 하나, 방은 대표 연출에 불이 없을 때만 하나
    chosen = {}
    for sec in secs:                                                            # 4.5) 방 대표 연출(set piece): 방 뒤쪽 중앙에 줄 맞춰 하나
        if sec['kind'] != 'room': continue
        rr = rnd(sec['key'] + 'set'); sets = TD.SETS[th]; fn_set = TD.SETS_KEY.get(sec['key']) or sets[rr.randrange(len(sets))]; d0, d1 = sec['ext']; cx = (sec['x0'] + sec['x1']) / 2; ok_ = None
        for dx in (0, 14, -14, 28, -28, 42, -42):
            x = round((cx + dx) / 14.0) * 14.0; lane = lane_d(sec, x)
            for d in (lane + 24, lane + 20, lane - 24, lane - 20):
                d = round(d / 7.0) * 7.0
                if d0 + 8 < d < d1 - 8 and float(inside(x, d)) >= (0 if sec['key'] in TD.SETS_KEY else 12) and sec['x0'] + 30 < x < sec['x1'] - 30: ok_ = (x, d); break
            if ok_: break
        if ok_:
            lx, ld = tr(ok_); fn_set(k, lx, ld, rr); placed.append((lx, ld, 34)); chosen[sec['key']] = (ok_, fn_set.lit)
    for sec in secs:
        rr = rnd(sec['key'] + 'l')
        if sec['kind'] == 'passage' and sec['shape'] == 'switch': xs = []
        elif sec['kind'] == 'passage': xs = [(x, lane_d(sec, x) + sec['hw'] + 3) for x in np.arange(sec['x0'] + 50, sec['x1'] - 20, float(sec['s'].get('lamp', 120)))]
        else:
            c = chosen.get(sec['key']); xs = [(c[0][0] + (26 if c[0][0] < (sec['x0'] + sec['x1']) / 2 else -26), min(sec['ext'][1] - 6, D - 6))] if (c and not c[1]) else []
        for x, d in xs:
            lx, ld = tr((x, min(d, D - 6))); nb, nr = len(k.block), len(k.rects); lamp(k, lx, ld, rr); del k.block[nb:]; del k.rects[nr:]
    for sec in secs:                                                            # 4.7) 정사각 방: 사용자가 만든 집 방처럼 가운데 깔개 + 뒷벽 창(불 켜진 창 하나)
        if sec['kind'] != 'room' or sec['shape'] != 'square': continue
        d0, d1 = sec['ext']; cx = (sec['x0'] + sec['x1']) / 2; cd = (d0 + d1) / 2; lx, ld = tr((cx, cd)); rx = min(30, (sec['x1'] - sec['x0']) / 2 - 12)
        M.flat(k, lx, ld, rx, rx * .5, tuple(int(v * .28) for v in LC)); M.flat(k, lx, ld, rx - 4, rx * .5 - 2, tuple(int(v * .4) for v in LC)); M.flat(k, lx, ld, rx - 9, rx * .5 - 4, tuple(int(v * .3) for v in LC))
        if d1 >= D - 10:
            wx, wd = tr((cx - 22 if (int(sec['x0']) % 2) else cx + 22, D)); win = tuple(int(min(255, v * .85)) for v in LC); fr = tuple(int(v * .35) for v in LC)
            k.F(wx - 9, wx + 9, 18, 40, win, Dl - 1.2, back=True); k.F(wx - 10.5, wx - 9, 17, 41.5, fr, Dl - 1.3, back=True); k.F(wx + 9, wx + 10.5, 17, 41.5, fr, Dl - 1.3, back=True); k.F(wx - 10.5, wx + 10.5, 40, 41.5, fr, Dl - 1.3, back=True); k.F(wx - .6, wx + .6, 18, 40, fr, Dl - 1.3, back=True); k.F(wx - 9, wx + 9, 28.2, 29.4, fr, Dl - 1.3, back=True)
    for sec in secs:                                                            # 5) 일반 소품: 방에만, 작은 것(걸을 수 있는 것) 최대 3종 1개씩, 길 밖
        if sec['kind'] != 'room' or sec['key'] in TD.SETS_KEY: continue
        rr = rnd(sec['key'] + 'p' + str(spec['tries'])); d0, d1 = sec['ext']
        kinds = [p for p in T['props'] if p[0] not in M.SOLID and p[1].__name__ not in ('f',) and p[0] not in ('lamp', 'lamp_on', 'lamp_off', 'lantern')]; rr.shuffle(kinds)
        for (nm, fn, mode, (lo, hi), gap) in kinds[:int(round(3 * spec['density'] + .4))]:
            for _ in range(200):
                x = rr.uniform(sec['x0'] + 8, sec['x1'] - 8); d = rr.uniform(d0 + 4, d1 - 4); e = float(inside(x, d)); lx, ld = tr((x, d))
                if e < 6 or min(x - sec['x0'], sec['x1'] - x, d - d0, d1 - d) > 26: continue
                if any(math.hypot(lx - a, (ld - b) * 1.5) < gap * .5 + g_ * .5 + 2 for a, b, g_ in placed): continue
                nb, nr = len(k.block), len(k.rects); fn(k, lx, ld, rr); del k.block[nb:]; del k.rects[nr:]; placed.append((lx, ld, gap)); break

WHYLAST = [0]
def WHY(n, k=None): WHYLAST[0] = (n, k); return False
def reach(mask, meta, spec):
    g = np.array(mask) > 127; gh, gw = g.shape; cell = lambda x, d: (cl(int(d / CELL), 0, gh - 1), cl(int(x / CELL), 0, gw - 1))
    def flood(m, s):
        seen = np.zeros_like(m); st = [s]; seen[s] = True
        while st:
            y, x = st.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < gh and 0 <= nx < gw and m[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; st.append((ny, nx))
        return seen
    def near(m, c, rad):
        y0, x0 = max(0, c[0] - rad), max(0, c[1] - rad); ys, xs = np.nonzero(m[y0:c[0] + rad + 1, x0:c[1] + rad + 1])
        return None if not len(ys) else (ys[0] + y0, xs[0] + x0)
    o = meta['origin']; st = near(g, cell(*meta['start']), 6)
    if st is None: return WHY(1)
    seen = flood(g, st)
    for (tx, td) in spec['tips']:
        c = cell(tx - o[0], td - o[1])
        if not seen[max(0, c[0] - 4):c[0] + 5, max(0, c[1] - 4):c[1] + 5].any(): return WHY(2)
    er = g.copy()
    for _ in range(spec.get('erode', 4)): e2 = er.copy(); e2[1:] &= er[:-1]; e2[:-1] &= er[1:]; e2[:, 1:] &= er[:, :-1]; e2[:, :-1] &= er[:, 1:]; er = e2          # 길 폭 약 17px 이상
    s2 = near(er, cell(*meta['start']), 8)
    if s2 is None: return WHY(3)
    seen2 = flood(er, s2)
    for sec in spec['secs']:
        c = cell(sec['mid'][0] - o[0], sec['mid'][1] - o[1])
        if not seen2[max(0, c[0] - 5):c[0] + 6, max(0, c[1] - 5):c[1] + 6].any(): return WHY(4, sec['key'])
    e = meta['exits'][0]['zone']; c = cell((e[0] + e[1]) / 2, (e[2] + e[3]) / 2)
    return bool(seen2[max(0, c[0] - 5):c[0] + 6, max(0, c[1] - 5):c[1] + 6].any())

def main():
    want = sys.argv[1:] or ORDER; W.props_orig = W.props
    def props(name, k, tr, inside, rng):
        if name in STRIPS: return strip_props(name, k, tr, inside, rng)
        return W.props_orig(name, k, tr, inside, rng)
    W.props = props; chains = M.load_chains(); nav = {}
    for th in want:
        name = th + 'strip'; spec = strip_spec(th, chains[th])
        for sec in spec['secs']:
            sec['samples'] = []
            for p0, p1 in zip(sec['pts'], sec['pts'][1:]):
                L_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = max(1, int(L_ / 4)); sec['samples'] += [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]
        setup(name, spec); bad = True
        for t in range(10):
            if t == 9: spec['alleys'] = []; spec['tips'] = []
            spec['tries'] = t; W.SEEDOFF[name] = t * 17; spec['density'] = .85 if t < 5 else (.5 if t < 7 else (.25 if t < 9 else .0))
            im, dep, mask, meta = W.build(name)
            if reach(mask, meta, spec): bad = False; break
        if bad: print('!! 길이 막힘', name, 'reason', WHYLAST[0])
        o = meta['origin']; meta['theme'] = th; meta['kind'] = 'strip'; meta['label'] = THEMES[th]['label']
        meta['sections'] = [dict(key=s['key'], kind=s['kind'], shape=s['shape'], x0=round(s['x0'] - o[0], 1), x1=round(s['x1'] - o[0], 1), mid=[round(s['mid'][0] - o[0], 1), round(s['mid'][1] - o[1], 1)],
                                  label='%s %s%d' % (THEMES[th]['label'], '통로' if s['kind'] == 'passage' else '', 1 + sum(1 for t in spec['secs'][:i_] if t['kind'] == s['kind'])), **({'z3': {kk: round((vv - (o[0] if kk in ('xr', 'xl', 'xd') else o[1] if kk in ('dA', 'dB', 'dC') else 0)), 1) for kk, vv in s['z3'].items()}} if s.get('z3') else {})) for i_, s in enumerate(spec['secs'])]
        nav[name] = meta; im.save(os.path.join(OUT, 'world_%s.png' % name)); dep.save(os.path.join(OUT, 'world_%s_depth.png' % name)); mask.save(os.path.join(OUT, 'world_%s_walk.png' % name))
        print(name, im.size, 'sections', len(spec['secs']), 'W', round(spec['W']), 'try', spec['tries'])
    p = os.path.join(OUT, 'more_nav.json'); old = {}
    if sys.argv[1:] and os.path.exists(p): old = {k: v for k, v in json.load(open(p)).items() if v.get('kind') == 'strip'}
    old.update(nav); json.dump(old, open(p, 'w'), ensure_ascii=False); print('more_nav.json', len(old), 'strips')
if __name__ == '__main__': main()
