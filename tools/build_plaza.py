#!/usr/bin/env python3
"""사용자가 만든 첫 장면(광장 화단)과 긴 복도 두 곳만 같은 엔진으로 걸어 다니게 하는 별도 파일(web/plaza.html).
사용: python3 tools/build_plaza.py  (먼저 python3 tools/export_web.py 로 web/data.js 가 있어야 한다: 아이·적 그림을 가져온다)"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
import render_city3d as C
from export_web import uri
WEB = os.path.join(HERE, '..', 'web'); CELL = 2

def room(s, key, label, W, D, free, start, exits, rects=()):
    CW, CH = s.CW, s.CH; gw, gh = math.ceil(W / CELL), math.ceil(D / CELL)
    walk = Image.new('L', (gw, gh), 0); px = walk.load()
    for j in range(gh):
        for i in range(gw):
            if free((i + .5) * CELL, (j + .5) * CELL): px[i, j] = 255
    return s, dict(W=W, D=D, X0=s.X0, Y0=s.Y0, CW=CW, CH=CH, rects=[list(r) for r in rects], exits=exits, start=start, S=2, label=label, walk=uri(walk.convert('RGB')))

def main():
    # --- 광장(첫 장면)
    a = C.landing(150, False, 'city3d_landing', True, False, False, 'r', False, 26)
    dep = Image.new('RGB', (a.CW, a.CH), (255, 255, 255)); dd = ImageDraw.Draw(dep)
    for (x, d, z, r) in a.front: cx, cy = a.P(x, d, z); dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=((d + 2) * 3,) * 3); dd.rectangle([cx - r, cy - r - 1, cx + r, cy + r // 5], fill=(255, 255, 255))    # 앞줄 수풀이 아이 아랫도리를 가린다
    dd.polygon([a.P(12, 38, 0), a.P(82, 38, 0), a.P(82, 38, 9), a.P(12, 38, 9)], fill=((38 + 2) * 3,) * 3)
    def free_a(x, d):
        if d < 4 or d > 77 or x < 4 or x > 146: return False
        if 8 < x < 86 and 34 < d < 72: return False                                        # 화단
        if math.hypot(x - 140, d - 74) < 4: return False
        return True
    sa, ra = room(a, 'plaza', '광장', 150, 80, free_a, [60, 24], [dict(zone=[144, 150, 4, 77], to='corridor', spawn=[12, 56], type='trans', dir='R')])
    ra['img'] = uri(a.img.convert('RGB')); ra['depth'] = uri(dep)
    # --- 긴 복도(화단 없이)
    b = C.landing(520, True, 'city3d_corridor', False, False, False, 'lr'); EX = 520 - 56
    dep2 = Image.new('RGB', (b.CW, b.CH), (255, 255, 255))
    def free_b(x, d):
        if x < 3 or x > 519.5: return False
        if any(abs(x - lx) < 4 and abs(d - 74) < 4 for lx in b.lampx): return False
        return 37 < d < 78
    sb, rb = room(b, 'corridor', '긴 복도', 520, 170, free_b, [14, 56], [dict(zone=[0, 5, 37, 78], to='plaza', spawn=[134, 40], type='trans', dir='L'), dict(zone=[514, 520, 37, 78], to='fountain', spawn=[12, 46], type='trans', dir='R')])
    rb['img'] = uri(b.img.convert('RGB')); rb['depth'] = uri(dep2)
    # --- 복도가 정사각형 광장으로 커지는 곳(인공 분수와 풀)
    f = C.fountain_scene(410, 'city3d_fountain', False, 'lr'); fx, fd = C.FC; fr = C.FR
    dep3 = Image.new('RGB', (f.CW, f.CH), (255, 255, 255)); d3 = ImageDraw.Draw(dep3); v = ((fd - fr + 4) + 2) * 3          # 분수가 뒤로 지나가는 아이를 가린다
    for z in (0, 9): d3.polygon([f.P(fx - fr, fd - fr, z), f.P(fx + fr, fd - fr, z), f.P(fx + fr, fd + fr, z), f.P(fx - fr, fd + fr, z)], fill=(v,) * 3)
    d3.polygon([f.P(fx - fr, fd - fr, 0), f.P(fx + fr, fd - fr, 0), f.P(fx + fr, fd - fr, 9), f.P(fx - fr, fd - fr, 9)], fill=(v,) * 3)
    d3.rectangle([f.P(fx - 11, fd, 0)[0], f.P(fx, fd, 34)[1], f.P(fx + 11, fd, 0)[0], f.P(fx, fd, 9)[1]], fill=(v,) * 3)
    def free_f(x, d):
        if x < 3 or x > 409.5: return False
        if abs(x - fx) < fr + 3 and abs(d - fd) < fr + 3: return False
        if any(abs(x - lx) < 4 and abs(d - ld_) < 4 for lx, ld_ in C.LAMPS): return False
        if any(bx - 3 < x < bx + 39 and bd - 3 < d < bd + 9 for bx, bd in C.BEN) or (C.BIN[0] - 3 < x < C.BIN[0] + 10 and C.BIN[1] - 3 < d < C.BIN[1] + 10): return False
        if C.SQ0 + 4 < x < C.SQ1 - 4: return 8 < d < C.SQD - 2
        return 37 < d < 56
    sf, rf = room(f, 'fountain', '분수 광장', 410, 190, free_f, [14, 46], [dict(zone=[0, 5, 37, 56], to='corridor', spawn=[506, 56], type='trans', dir='L'), dict(zone=[404, 410, 37, 56], to=None, type='trans', dir='R')])
    rf['img'] = uri(f.img.convert('RGB')); rf['depth'] = uri(dep3)
    data = open(os.path.join(WEB, 'data.js'), encoding='utf-8').read(); full = json.loads(data[data.index('{'):data.rindex('}') + 1])
    full['rooms'] = {'plaza': ra, 'corridor': rb, 'fountain': rf}; full['starts'] = {'plaza': {'room': 'plaza', 'x': 60, 'd': 24}}
    open(os.path.join(WEB, 'plaza_data.js'), 'w', encoding='utf-8').write('window.GAME_DATA = ' + json.dumps(full) + ';\n')
    h = open(os.path.join(WEB, 'index.html'), encoding='utf-8').read()
    h = h.replace('<script src="data.js"></script><script src="game.js"></script>', '<script>' + open(os.path.join(WEB, 'plaza_data.js'), encoding='utf-8').read() + '</script><script>' + open(os.path.join(WEB, 'game.js'), encoding='utf-8').read() + '</script>')
    open(os.path.join(WEB, 'plaza.html'), 'w', encoding='utf-8').write(h); print('web/plaza.html', len(h) // 1024, 'KB')
if __name__ == '__main__': main()
