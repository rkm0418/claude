#!/usr/bin/env python3
"""테마마다 한 장의 긴 띠(strip): 방과 통로를 가로로 이어 한 공간으로 만든다. 컷이 없고, 아이가 걸으면 앞 구간에 불이 켜지고 지나온 구간은 어두워진다(엔진 조명).
구간 목록은 tools/scene_chains.json(키·번호 고정). 구간 내용은 키 시드로 정해져, 다른 구간을 빼도 안 바뀐다.
사용: python3 tools/render_strips.py [테마 ...]  -> maps/out/world_<테마>strip.png/_depth/_walk, more_nav.json (export_web 이 읽는다)"""
import json, math, os, random, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import render_more as M
import render_world as W
from render_world import OUT
from render_dream_area import CELL

THEMES, ORDER, INTERIOR = M.THEMES, M.ORDER, M.INTERIOR
STRIPS = {}
rnd = lambda key: random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(key)))
cl = lambda v, a, b: max(a, min(b, v))

def layout(th, chain):                                                          # 구간을 왼→오로 배치하고 구간마다 길(lane)과 영역을 정한다
    inter = th in INTERIOR; D = 64 if inter else 84; x = 0.0; d_in = D * .5; secs = []
    for s in chain:
        r = rnd(s['key']); sh = 'square' if s['shape'] == 'deep' else s['shape']; hw = 13 if s['kind'] == 'passage' else 14
        if s['kind'] == 'passage':
            w = {'tunnel': r.randint(170, 240), 'hall': r.randint(80, 110), 'bend': r.randint(90, 120) if inter else r.randint(130, 170), 'zig': r.randint(160, 200)}[sh]
            sg = 1 if d_in < D * .5 else -1
            if sh in ('tunnel', 'hall'): d_out = d_in; pts = [(x, d_in), (x + w, d_in)]
            elif sh == 'bend': d_out = cl(d_in + sg * r.uniform(20, 26), 22, D - 22); xm = x + w * .5; pts = [(xm - w * .5, d_in), (xm, d_in), (xm, d_out), (x + w, d_out)]
            else: d_mid = cl(d_in + sg * 24, 22, D - 22); d_out = d_in; pts = [(x, d_in), (x + w * .3, d_in), (x + w * .3, d_mid), (x + w * .7, d_mid), (x + w * .7, d_in), (x + w, d_in)]
            ys = [p[1] for p in pts]; ext = (cl(min(ys) - hw - 7, 2, D), cl(max(ys) + hw + 7, 0, D - 2))
        else:
            if sh == 'long': w = r.randint(280, 420); h = r.randint(44, 54)
            elif sh == 'square': w = r.randint(56, 60) if inter else r.randint(78, 84); h = min(D - 6, w)
            else: w = r.randint(80, 96) if inter else r.randint(92, 112); h = r.randint(46, 52) if inter else r.randint(56, 66)
            d_out = r.uniform(D * .34, D * .66); d0 = max(3, min(d_in, d_out) - 16); d1 = min(D - 3, d0 + h)
            if d1 < max(d_in, d_out) + 16: d1 = min(D - 3, max(d_in, d_out) + 16); d0 = max(3, d1 - h)
            ext = (d0, d1); dm = (d_in + d_out) / 2 + r.uniform(-8, 8)
            pts = [(x, d_in), (x + w * .35, d_in), (x + w * .65, d_out), (x + w, d_out)] if sh == 'long' else [(x, d_in), (x + w * .5, cl(dm, d0 + 14, d1 - 14)), (x + w, d_out)]
        secs.append(dict(s=s, key=s['key'], kind=s['kind'], shape=sh, x0=x, x1=x + w, pts=pts, hw=hw, d_in=d_in, d_out=d_out, ext=ext, mid=M.polymid(pts)))
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
    spec['start'] = (14, secs[0]['d_in']); spec['end'] = (Wt - 14, secs[-1]['d_out'])
    for sec in secs:                                                                                                       # 딸린 골목(뒷벽에 붙은 칸): 뒷벽까지 열린 방에만
        if sec['kind'] != 'room' or sec['ext'][1] < D - 8: continue
        rr = rnd(sec['key'] + 'a'); n = rr.choice((2, 3)) if sec['shape'] == 'long' else (1 if rr.random() < .4 else 0); xs = []
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
    box = dict(wall=spec['wall'], vig=T['vig'] * .5)
    W.BLOCKED[name] = lambda x, d, n, g=T['ground']: np.clip(g(x, d, np.full(n, -10.), n), 0, 255).astype(int)
    last = spec['secs'][-1]
    ex = [dict(at=(spec['W'] - 8, last['d_out']), hw=14, hwx=5, to=None, endMsg='길이 끊겨 있다. 여기서는 더 갈 수 없다', side='right')]
    ent = dict(H=spec['H'], shapes=spec['shapes'], zones=[], ground=T['ground'], face=T['face'], ch=30, sky=((20, 20, 30), (40, 40, 60)), start=spec['start'], box=box, wob=T['wob'], exits=ex, bbox=(0, 0, spec['W'], spec['D']))
    W.AREAS[name] = ent; W.STRICT.add(name); STRIPS[name] = spec; return ent

def unit(k, th, lx, ld, low, r):                                               # 벽 줄 한 칸
    (M.BARLOW if low else M.BAR)[th](k, lx - 3.5, ld - 3, r)

def strip_props(name, k, tr, inside, rng):
    spec = STRIPS[name]; th = spec['theme']; T = THEMES[th]; sc = k.sc; Wl, Dl = sc.W, sc.D; D = spec['D']; secs = spec['secs']; r = random.Random(sum(map(ord, name)) * 7 + spec['tries'] * 101); placed = []
    def put(lx, ld, g_, low_ok=True):
        if any(math.hypot(lx - a, ld - b) < 5.5 for a, b, gg in placed if gg == 7): return False
        placed.append((lx, ld, 7)); return True
    for i, sec in enumerate(secs):                                              # 1) 구간 벽: 통로는 길 양옆, 방은 앞·뒤 줄
        rr = rnd(sec['key'] + 'w' + str(spec['tries']))
        if sec['kind'] == 'passage':
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
                    if put(lx, ld, 7): unit(k, th, lx, ld, False, rr)
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
                if put(sx, dd, 7): M.BAR[th](k, sx - 3, dd - 3, rr)
        k.glow(lx, Dl - 12, 26, (255, 214, 150), .3); cand = list(T['props']); fn_ = cand[rr.randrange(len(cand))][1]
        nb, nr = len(k.block), len(k.rects); fn_(k, lx - 2, Dl - 12, rr); del k.block[nb:]; del k.rects[nr:]
    lamp = M.p_lamp(True)                                                       # 4) 가로등과 빛 웅덩이
    for sec in secs:
        rr = rnd(sec['key'] + 'l')
        xs = list(np.arange(sec['x0'] + 30, sec['x1'] - 14, 58.0)) if sec['kind'] == 'passage' else [rr.uniform(sec['x0'] + 14, sec['x1'] - 14) for _ in range(rr.choice((1, 1, 2)))]
        for x in xs:
            d = (lane_d(sec, x) + sec['hw'] + 3) if sec['kind'] == 'passage' else sec['ext'][1] - 6
            lx, ld = tr((x, min(d, D - 6))); nb, nr = len(k.block), len(k.rects); lamp(k, lx, ld, rr); del k.block[nb:]; del k.rects[nr:]; M.flat(k, lx + 2, ld, 12, 4, (60, 52, 40))
    for sec in secs:                                                            # 5) 소품(막는 것은 가장자리·길 밖에만)
        rr = rnd(sec['key'] + 'p' + str(spec['tries'])); d0, d1 = sec['ext']; w = sec['x1'] - sec['x0']
        area = w * (d1 - d0) / 6800.0; dens = spec['density'] * max(.6, area) * (.28 if sec['kind'] == 'passage' else .55)
        kinds = [p for p in T['props'] if p[3][0] > 0 or rr.random() < .55]
        for (nm, fn, mode, (lo, hi), gap) in kinds:
            n = max(0, int(round(rr.randint(lo, hi) * dens))); solid = nm in M.SOLID
            if dens > 0 and lo > 0 and n == 0 and not solid: n = 1
            tries = 0
            while n > 0 and tries < 500:
                tries += 1; x = rr.uniform(sec['x0'] + 6, sec['x1'] - 6); d = rr.uniform(d0 + 4, d1 - 4); e = float(inside(x, d)); lx, ld = tr((x, d))
                if solid:
                    if e < 3: continue
                    if min(x - sec['x0'], sec['x1'] - x, d - d0, d1 - d) > 22: continue
                if any(math.hypot(lx - a, (ld - b) * 1.5) < gap * .5 + g_ * .5 + 2 for a, b, g_ in placed): continue
                nb, nr = len(k.block), len(k.rects); fn(k, lx, ld, rr)
                if not solid: del k.block[nb:]; del k.rects[nr:]
                placed.append((lx, ld, gap)); n -= 1

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
    if st is None: return False
    seen = flood(g, st)
    for (tx, td) in spec['tips']:
        c = cell(tx - o[0], td - o[1])
        if not seen[max(0, c[0] - 4):c[0] + 5, max(0, c[1] - 4):c[1] + 5].any(): return False
    er = g.copy()
    for _ in range(4): e2 = er.copy(); e2[1:] &= er[:-1]; e2[:-1] &= er[1:]; e2[:, 1:] &= er[:, :-1]; e2[:, :-1] &= er[:, 1:]; er = e2          # 길 폭 약 17px 이상
    s2 = near(er, cell(*meta['start']), 8)
    if s2 is None: return False
    seen2 = flood(er, s2)
    for sec in spec['secs']:
        c = cell(sec['mid'][0] - o[0], sec['mid'][1] - o[1])
        if not seen2[max(0, c[0] - 5):c[0] + 6, max(0, c[1] - 5):c[1] + 6].any(): return False
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
        if bad: print('!! 길이 막힘', name)
        o = meta['origin']; meta['theme'] = th; meta['kind'] = 'strip'; meta['label'] = THEMES[th]['label']
        meta['sections'] = [dict(key=s['key'], kind=s['kind'], shape=s['shape'], x0=round(s['x0'] - o[0], 1), x1=round(s['x1'] - o[0], 1), mid=[round(s['mid'][0] - o[0], 1), round(s['mid'][1] - o[1], 1)],
                                  label='%s %s%s' % (THEMES[th]['label'], '통로' if s['kind'] == 'passage' else '', s['key'][-2:].lstrip('0') or '0')) for s in spec['secs']]
        nav[name] = meta; im.save(os.path.join(OUT, 'world_%s.png' % name)); dep.save(os.path.join(OUT, 'world_%s_depth.png' % name)); mask.save(os.path.join(OUT, 'world_%s_walk.png' % name))
        print(name, im.size, 'sections', len(spec['secs']), 'W', round(spec['W']), 'try', spec['tries'])
    p = os.path.join(OUT, 'more_nav.json'); old = {}
    if sys.argv[1:] and os.path.exists(p): old = {k: v for k, v in json.load(open(p)).items() if v.get('kind') == 'strip'}
    old.update(nav); json.dump(old, open(p, 'w'), ensure_ascii=False); print('more_nav.json', len(old), 'strips')
if __name__ == '__main__': main()
