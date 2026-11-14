#!/usr/bin/env python3
"""나무 머리 11번(가시 가지) 수정판: 끝 가지가 더 불규칙, 반짝이 없음, 왼팔은 드문드문하되 이어진 구슬 팔, 오른팔은 정상 팔, 팔 끝 회색 없음.
사용: python3 tools/gen_t11.py && python3 tools/variants.py t11   (시드만 바꾼 4종)"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import gen_gross  # 48x84
from gen_shadow import C
from gen_creep import tube, chaikin
from gen_treehead import trunk

def branch(c, x, y, ang, L, depth, rng, spread=1.0):
    if depth <= 0 or L < 1.5: return
    k1, k2 = rng.uniform(-.4, .4), rng.uniform(-.4, .4)
    mx, my = x + math.cos(ang + k1) * L * .5, y + math.sin(ang + k1) * L * .5
    ex, ey = mx + math.cos(ang + k2) * L * .5, my + math.sin(ang + k2) * L * .5
    c.line(x, y, mx, my, 2 if depth >= 5 else 1, 1, ch='l'); c.line(mx, my, ex, ey, 1, 1, ch='l')
    if depth == 1:                                   # 끝 가시
        for _ in range(rng.randint(1, 3)):
            a = ang + rng.uniform(-1.2, 1.2); l = rng.uniform(1.5, 4)
            c.line(ex, ey, ex + math.cos(a) * l, ey + math.sin(a) * l, 1, ch='l')
        return
    if depth <= 3 and rng.random() < .3: return    # 중간에 끊긴 가지
    n = rng.choice((1, 2, 2)) if depth > 3 else rng.choice((1, 1, 2))
    for _ in range(n):
        branch(c, ex, ey, ang + rng.uniform(-1, 1) * spread * (1.2 if depth <= 3 else 1.0), L * rng.uniform(.6, 1.0), depth - 1, rng, spread)
    if rng.random() < .15:                           # 몸통에서 곁가지
        branch(c, mx, my, ang + rng.choice((-1, 1)) * rng.uniform(.6, 1.3), L * rng.uniform(.3, .6), depth - 2, rng, spread)

def dome(c, x, y, ang, L, depth, rng):
    if depth <= 0 or L < 1.4: return
    k = rng.uniform(-.15, .15)
    ex, ey = x + math.cos(ang + k) * L, y + math.sin(ang + k) * L
    col = 'l' if depth >= 4 else 'm'                              # 바깥 가지일수록 어두운 회색: 색의 조화
    c.line(x, y, ex, ey, 2 if depth >= 6 else 1, 1, ch=col)
    if depth == 1:
        for _ in range(rng.randint(1, 3)):                       # 끝 가시: 길이와 방향이 제각각
            a = ang + rng.uniform(-1.3, 1.3); l = rng.uniform(1.5, 4.5)
            c.line(ex, ey, ex + math.cos(a) * l, ey + math.sin(a) * l, 1, ch='d' if rng.random() < .4 else 'm')
        return
    if depth <= 2 and rng.random() < .12: return
    n = rng.choice((1, 2, 2, 2))
    for i in range(n):
        off = math.radians(rng.uniform(-1, 1) * 30 + (i - (n - 1) / 2) * 34)
        a2 = ang + off
        a2 += (1 if math.cos(a2) >= 0 else -1) * (0.22 + (0.18 if depth <= 4 else 0)) * (1 if abs(math.cos(a2)) > .15 else 0)   # 축 처짐: 아래로 휜다
        dome(c, ex, ey, a2, L * rng.uniform(.58, .85), depth - 1, rng)

def trunk2(c, n=5, y0=49, y1=34):
    # 줄기 가닥: 아래(어깨)에서 넓게 벌어져 박히고, 몸으로 들어갈수록 색이 어두워진다
    for k in range(n):
        off = k - (n - 1) / 2
        for t in range(0, 31):
            f = t / 30; y = y0 + (y1 - y0) * f
            x = 24 + off * (1.0 + 1.4 * max(0, (1 - f) - .55) * 2.2)
            ch = 'l' if y < y0 - 7 else 'm' if y < y0 - 4 else 'd' if y < y0 - 2 else 's'
            c.put(x, y, ch)
            if t % 2 == 0: c.put(x, y + .5, ch)

def beaded(c, pts, wmin=0.4, wmax=4.2, period=7):
    P = chaikin(pts, 3)
    for i, (x, y) in enumerate(P):
        w = wmin + (wmax - wmin) * (.5 + .5 * math.sin(i * 6.28 / period))
        c.disc(x, y, w / 2, 's')

def root(c, x, y, ang, L, depth, rng):
    if depth <= 0 or L < 1.5: return
    ang += (math.pi / 2 - ang) * .22 + rng.uniform(-.5, .5)          # 아래로 흘러내리며 구불거림
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
    ch = 'l' if depth >= 4 else 'm' if depth >= 2 else 'd'            # 끝으로 갈수록 어두워짐
    c.line(x, y, ex, ey, 1, 1, ch=ch)
    for _ in range(rng.choice((1, 1, 2))):
        root(c, ex, ey, ang + rng.uniform(-.8, .8), L * rng.uniform(.65, .95), depth - 1, rng)

def root2(c, x, y, ang, L, depth, rng):
    # 몸 윤곽에 맞춘 뿌리: 척추 쪽으로 모이며 세로로 흐르고, 끝으로 갈수록 몸색에 묻힌다
    if depth <= 0 or L < 1.5: return
    ang += (math.pi / 2 - ang) * .45 + rng.uniform(-.28, .28)
    ex, ey = x + math.cos(ang) * L, y + math.sin(ang) * L
    c.line(x, y, ex, ey, 2 if depth >= 6 else 1, 1, ch='l' if depth >= 3 else 'm')
    for _ in range(rng.choice((1, 1, 2))):
        root2(c, ex, ey, ang + rng.uniform(-.55, .55), L * rng.uniform(.75, 1.0), depth - 1, rng)

def chain(c, pts, gap=4.2, ry=3.4, rx=2.5):
    """사슬 팔: 고리가 번갈아 세로/가로로 꿰어진 모양. 고리 안쪽은 비워 둔다."""
    P = chaikin(pts, 3); acc = 0.0; i = 0; last = P[0]
    links = [P[0]]
    for p in P[1:]:
        acc += math.hypot(p[0] - last[0], p[1] - last[1]); last = p
        if acc >= gap: links.append(p); acc = 0.0
    for i, (x, y) in enumerate(links):
        a, b = (rx, ry) if i % 2 == 0 else (ry * .78, rx * .8)
        c.ell(x, y, a, b, 's')
    for i, (x, y) in enumerate(links):
        a, b = (rx, ry) if i % 2 == 0 else (ry * .78, rx * .8)
        for yy in range(int(y - b), int(y + b) + 1):
            for xx in range(int(x - a), int(x + a) + 1):
                if ((xx - x) / max(.1, a - 1.3)) ** 2 + ((yy - y) / max(.1, b - 1.3)) ** 2 <= 1: c.g[yy][xx] = '.'
    return links

def fill_eye_holes(c, ymax=44):
    # 줄기 쪽에 좌우로 나란한 큰 구멍은 눈처럼 보이므로 메운다 (가장자리 쪽 작은 틈은 뇌 질감으로 남긴다)
    W, H = 48, 104; seen = set(); st = [(0, 0)]
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (0 <= x < W and 0 <= y < ymax) or c.g[y][x] != '.': continue
        seen.add((x, y)); st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for x0 in range(W):
        for y0 in range(ymax):
            if c.g[y0][x0] == '.' and (x0, y0) not in seen and (x0, y0) not in seen:
                comp, st = [], [(x0, y0)]; seen2 = {(x0, y0)}
                while st:
                    x, y = st.pop(); comp.append((x, y))
                    for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if n not in seen2 and 0 <= n[0] < W and 0 <= n[1] < ymax and c.g[n[1]][n[0]] == '.' and n not in seen:
                            seen2.add(n); st.append(n)
                cx = sum(p[0] for p in comp) / len(comp); cy = sum(p[1] for p in comp) / len(comp)
                bw = max(p[0] for p in comp) - min(p[0] for p in comp) + 1; bh = max(p[1] for p in comp) - min(p[1] for p in comp) + 1
                if len(comp) >= 8 and bw >= 2 and bh >= 3 and abs(cx - 24) <= 11 and 12 <= cy <= 30:
                    for x, y in comp: c.g[y][x] = 'l'
                for p in comp: seen.add(p)

def carve_holes(c, rng, n=16):
    # 가지 사이 구멍: 크기와 기울기를 제각각으로, 좌우 대칭 쌍과 줄기 중앙부(눈처럼 보임)는 피한다
    holes = []
    for _ in range(3000):
        if len(holes) >= n: break
        x, y = rng.uniform(8, 40), rng.uniform(5, 30)
        if abs(x - 24) < 6 and y > 12: continue
        rx = rng.choice((1.0, 1.4, 1.8, 2.2)); ry = rx * rng.uniform(2.0, 3.6); th = rng.uniform(0, 3.14)
        R = max(rx, ry) + 1
        ok = all(c.g[yy][xx] != '.' for yy in range(int(y - R), int(y + R) + 1) for xx in range(int(x - R), int(x + R) + 1) if 0 <= yy < 104 and 0 <= xx < 48 and (xx - x) ** 2 + (yy - y) ** 2 <= R * R)
        if not ok: continue
        if any(abs((48 - x) - hx) < 4 and abs(y - hy) < 3 for hx, hy, *_ in holes): continue      # 좌우 대칭 쌍 금지
        if any(math.hypot(x - hx, y - hy) < 7 for hx, hy, *_ in holes): continue
        holes.append((x, y, rx, ry, th))
    for x, y, rx, ry, th in holes:
        ct, st = math.cos(th), math.sin(th)
        for yy in range(int(y - 5), int(y + 6)):
            for xx in range(int(x - 5), int(x + 6)):
                u, v = (xx - x) * ct + (yy - y) * st, -(xx - x) * st + (yy - y) * ct
                if (u / rx) ** 2 + (v / ry) ** 2 <= 1 and 0 <= yy < 104 and 0 <= xx < 48: c.g[yy][xx] = '.'

def joint_fade(c):
    # 몸 연결부위(어깨-팔, 골반-다리)의 회색을 검은색으로 서서히 어둡게 한다 (디더링으로 계단 없이)
    for y in range(104):
        for x in range(48):
            ch = c.g[y][x]
            if ch not in 'lmd': continue
            w = 0.0
            if (x <= 16 or x >= 32) and 50 <= y <= 78: w = max(w, 1 - (y - 50) / 28)       # 어깨에서 팔로
            if 14 <= x <= 34 and 58 <= y <= 88: w = max(w, 1 - abs(y - 73) / 15)           # 골반에서 다리로
            if 42 <= y <= 62 and 14 <= x <= 34: w = max(w, 1 - abs(y - 50) / 12)            # 목에서 어깨로
            v = w + .14 * (((x + y) % 2) - .5)
            c.g[y][x] = 's' if v > .8 else 'd' if v > .55 else 'm' if v > .3 else ch

def figure(seed, phase=None):
    sw = math.sin(phase) if phase is not None else 0.0                # 걷기 동작 위상 (None 이면 정지 자세)
    import gen_shadow as G
    G.W, G.H = 48, 104
    c = C(); rng = random.Random(seed)
    tube(c, [(24, 50), (24, 74)], 15, 8, .03); c.ell(24, 52, 9, 3.2, 's'); tube(c, [(24, 47), (13, 54)], 6, 5); tube(c, [(24, 47), (35, 54)], 6, 5); tube(c, [(24, 44), (24, 53)], 7, 10)
    lift_l, lift_r = 3 * max(0, sw), 3 * max(0, -sw)                       # 발을 드는 쪽만 살짝 든다 (나머지는 바닥을 끈다)
    tube(c, [(22, 66), (20 + 1.5 * sw, 88 - lift_l / 2), (21 + 2.5 * sw, 103 - lift_l)], 6, 2.4); tube(c, [(26, 66), (28 + 1.5 * sw, 88 - lift_r / 2), (27 + 2.5 * sw, 103 - lift_r)], 6, 2.4)
    r2 = random.Random(seed + 100); tmp = C()
    for sx, a0 in [(20, 105), (28, 75), (16, 115), (32, 65), (24, 90), (22, 98), (30, 80)]:
        root2(tmp, sx, 54, math.radians(a0), 9, 5, r2)
    for sx, a0 in [(21, 95), (28, 80)]:
        root2(tmp, sx, 74, math.radians(a0), 7, 3, r2)
    for y in range(104):
        for x in range(48):
            if tmp.g[y][x] != '.' and c.g[y][x] != '.' and 14 <= x <= 34 and y >= 49 and y <= 98: c.g[y][x] = tmp.g[y][x]
    hx, hy = 25.5, 64                                                  # 심장 쪽(보는 사람 기준 오른쪽 가슴)이 뚫림
    for y in range(104):
        for x in range(48):
            th = math.atan2(y - hy, x - hx); d = (((x - hx) / 3.0) ** 2 + ((y - hy) / 5.8) ** 2) / (1 + .28 * math.sin(3 * th + seed) + .15 * math.sin(5 * th)) ** 2
            if d <= 1: c.g[y][x] = '.'
            elif d <= 1.7 and c.g[y][x] != '.': c.g[y][x] = 'l' if d <= 1.35 else 'm'   # 구멍 가장자리 테두리
    for a0 in (200, 340, 270):                              # 구멍 가장자리에서 안쪽으로 뻗은 뿌리 잔가지
        a = math.radians(a0); sx, sy = hx + math.cos(a) * 3.6, hy + math.sin(a) * 4.6
        c.line(sx, sy, sx - math.cos(a) * r2.uniform(1.5, 3), sy - math.sin(a) * r2.uniform(1.5, 3.5), 1, ch='m')
    L = chain(c, [(12, 53), (9 - sw, 78), (8 - 3 * sw, 102)])
    for k in range(1, 14):                                             # 끌린 자국: 길게, 위줄은 듬성듬성
        xx = 8 - 3 * sw + (k if sw <= 0 else -k)
        c.put(xx, 103, 'd' if k < 9 else 'm'); c.put(xx, 102, 'd' if k % 3 == 1 and k < 8 else '.')
    tube(c, [(36, 53), (38 - sw, 78), (38 - 3 * sw, 99)], 4.2, 3.4); c.ell(38 - 3 * sw, 101, 2.8, 3, "s")
    for k in range(1, 10):
        xx = 38 - 3 * sw + (k if sw <= 0 else -k)
        c.put(xx, 103, 'd' if k < 7 else 'm'); c.put(xx, 102, 'd' if k % 3 == 1 and k < 7 else '.')
    tmp3 = C()                                                         # 어깨선을 따라 바깥으로 뻗는 회색 뿌리
    for sx, a0 in [(21, 160), (27, 20), (22, 140), (26, 40), (20, 175), (28, 5)]:
        root2(tmp3, sx, 49, math.radians(a0), 7, 4, r2)
    for y in range(44, 60):
        for x in range(48):
            if tmp3.g[y][x] != '.' and c.g[y][x] != '.': c.g[y][x] = tmp3.g[y][x]
    tmp2 = C()                                                         # 팔에도 회색 뿌리 (팔 끝 y>84 는 제외)
    for sx, a0 in [(12, 95), (10, 85), (14, 100), (36, 85), (37, 95), (35, 80)]:
        root2(tmp2, sx, 54, math.radians(a0), 10, 5, r2)
    for y in range(54, 90):
        for x in range(48):
            if tmp2.g[y][x] != '.' and c.g[y][x] != '.' and (x <= 16 or x >= 33): c.g[y][x] = tmp2.g[y][x]
    trunk2(c, 7, 51, 31)
    for i in range(7):
        dome(c, 24 + (i - 3) * 1.2, 31, math.radians(-90 + (i - 3) * rng.uniform(21, 27)), 8, 6, rng)
    fill_eye_holes(c)
    joint_fade(c)
    if sw:                                                             # 수관과 목이 걸음에 따라 흔들림(위쪽일수록 크게)
        for y in range(46):
            sh = int(round(2.6 * sw * (46 - y) / 46)); row = c.g[y]
            if sh > 0: c.g[y] = ['.'] * sh + row[:-sh]
            elif sh < 0: c.g[y] = row[-sh:] + ['.'] * (-sh)
    if phase is not None and abs(sw) < .5:                                # 발을 끌며 옮기는 사이 몸이 살짝 떠올랐다 내려앉음
        c.g = c.g[1:] + [['.'] * 48]
    return c

def downscale(rows, f=2):
    """문자 격자를 1/f 로 줄인다. 밝은 가지(l)는 한 점만 있어도 살리고, 마지막에 윤곽선(k)을 다시 두른다."""
    H, W = len(rows), len(rows[0]); h, w = H // f, W // f; out = []
    for by in range(h):
        line = []
        for bx in range(w):
            cells = [rows[by * f + j][bx * f + i] for j in range(f) for i in range(f)]
            solid = [ch for ch in cells if ch not in '.k']
            if 'l' in solid: line.append('l')
            elif len(solid) >= 2 or (solid and cells.count('k') == 0): line.append(max(set(solid), key=solid.count))
            elif cells.count('k') >= 2: line.append('k')
            else: line.append('.')
        out.append(line)
    res = [r[:] for r in out]
    for y in range(h):
        for x in range(w):
            if out[y][x] == '.' and any(0 <= y + dy < h and 0 <= x + dx < w and out[y + dy][x + dx] not in '.k' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))): res[y][x] = 'k'
    return [''.join(r) for r in res]

def resample(rows, w, h, outline=False):
    """임의 크기로 줄인다(맵용). 윤곽선(k)은 몸색(s)으로 바꿔 지우고, 밝은 부분(l) 주위에만 얇은 어두운 선(d)을 두른다."""
    rows = [r.replace('k', 's') for r in rows]; H, W = len(rows), len(rows[0]); out = []
    for y in range(h):
        y0 = int(y * H / h); y1 = max(y0 + 1, int((y + 1) * H / h)); line = []
        for x in range(w):
            x0 = int(x * W / w); x1 = max(x0 + 1, int((x + 1) * W / w))
            cells = [rows[j][i] for j in range(y0, y1) for i in range(x0, x1)]
            solid = [c for c in cells if c != '.']
            if 'l' in solid: line.append('l')
            elif len(solid) * 2 >= len(cells): line.append(max(set(solid), key=solid.count))
            else: line.append('.')
        out.append(line)
    res = [r[:] for r in out]
    for y in range(h if outline else 0):
        for x in range(w):
            if out[y][x] == '.' and any(0 <= y + dy < h and 0 <= x + dx < w and out[y + dy][x + dx] == 'l' for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))): res[y][x] = 'd'
    return [''.join(r) for r in res]

MAP_W, MAP_H = 30, 64   # (윤곽선은 resample(..., outline=True) 로 켠다)
#         # 맵용 크기(약 4m): 문(32px)의 2배. 바꾸려면 여기만 고친다

def export_final(seed=12):
    """확정안(2번, 시드 12): 정지 1장 + 걷기 4장을 art/objects.txt 에 넣는다."""
    import re
    root = os.path.join(os.path.dirname(__file__), '..', 'art')
    frames = [('shadow_tree', None, '검은 사람(나무 머리) 정지 | dream')] + [(f'shadow_tree_w{i + 1}', p, f'검은 사람(나무 머리) 걷기 {i + 1}/4 | dream') for i, p in enumerate((0.0, 1.57, 3.14, 4.71))]
    blocks = []
    for name, ph, desc in frames:
        blocks.append(f'[{name}] {desc}\n' + '\n'.join(''.join(r) for r in figure(seed, ph).finish()) + '\n')
    for name, ph, desc in frames:                                      # 게임 크기(1/2, 24x52): 맵에 놓는 용
        small = resample(figure(seed, ph).finish(), MAP_W, MAP_H)
        blocks.append(f'[{name.replace("shadow_tree", "chaser")}] {desc.split(" | ")[0]} (맵 크기 30x64) | dream\n' + '\n'.join(small) + '\n')
    smear = ['.' * 40, '.' * 40]
    r = random.Random(7); row1 = ''.join('d' if (i % 7 < 5 and i > 3) else ('m' if i % 7 < 6 and i > 1 else '.') for i in range(40)); row2 = ''.join('k' if (i % 5 < 3 and r.random() < .8) else '.' for i in range(40))
    row0 = ''.join('m' if (i % 9 == 0 and 4 < i < 36) else '.' for i in range(40))
    blocks.append('[drag_smear] 바닥에 끌린 자국(추격자 뒤에 깐다) | dream\n' + '\n'.join([row0, row1, row2]) + '\n')
    path = os.path.join(root, 'objects.txt'); txt = open(path, encoding='utf-8').read()
    keep, skip = [], False
    for line in txt.split('\n'):                                      # 기존 shadow_tree* 블록을 헤더부터 다음 헤더 전까지 지운다
        if line.startswith('['): skip = line.startswith('[shadow_tree') or line.startswith('[drag_smear') or line.startswith('[chaser')
        if not skip: keep.append(line)
    txt = '\n'.join(keep).rstrip('\n') + '\n\n' + '\n'.join(blocks)
    open(path, 'w', encoding='utf-8').write(txt)

def main():
    root = os.path.join(os.path.dirname(__file__), '..', 'art', 'variants')
    lines = ['# 나무 머리 11번 수정판 (tools/gen_t11.py 가 생성함)', '']
    for i, seed in enumerate((11, 12, 13, 14)):
        lines.append(f'[a_{i + 1:02d}] 가시 가지 수정판 시드 {seed} | {i + 1}'); lines += figure(seed).finish(); lines.append('')
    open(os.path.join(root, 't11_pixels.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'final': export_final()
    else: main()
