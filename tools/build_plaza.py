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
    a = C.landing(150, False, 'city3d_landing', True, False, False)
    dep = Image.new('RGB', (a.CW, a.CH), (255, 255, 255)); dd = ImageDraw.Draw(dep)
    for (x, d, z, r) in a.front: cx, cy = a.P(x, d, z); dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=((d + 2) * 3,) * 3); dd.rectangle([cx - r, cy - r - 1, cx + r, cy + r // 5], fill=(255, 255, 255))    # 앞줄 수풀이 아이 아랫도리를 가린다
    dd.polygon([a.P(12, 38, 0), a.P(82, 38, 0), a.P(82, 38, 9), a.P(12, 38, 9)], fill=((38 + 2) * 3,) * 3)
    def free_a(x, d):
        if d < 4 or d > 77 or x < 4 or x > 146: return False
        if 8 < x < 86 and 34 < d < 72 and not (36 < x < 68 and d < 60): return False        # 화단(가운데 움푹한 곳으로만 드나든다)
        if math.hypot(x - 140, d - 74) < 4: return False
        return True
    sa, ra = room(a, 'plaza', '광장', 150, 80, free_a, [50, 57], [dict(zone=[144, 150, 4, 77], to='corridor', spawn=[12, 56])])
    ra['img'] = uri(a.img.convert('RGB')); ra['depth'] = uri(dep)
    # --- 긴 복도(화단 없이)
    b = C.landing(520, True, 'city3d_corridor', False, False); EX = 520 - 56
    dep2 = Image.new('RGB', (b.CW, b.CH), (255, 255, 255))
    def free_b(x, d):
        if x < 3 or x > 517: return False
        if x >= EX: return 3 < d < 78
        if any(abs(x - lx) < 4 and abs(d - 74) < 4 for lx in b.lampx): return False
        return 37 < d < 78
    sb, rb = room(b, 'corridor', '긴 복도', 520, 120, free_b, [14, 56], [dict(zone=[0, 5, 37, 78], to='plaza', spawn=[134, 40])])
    rb['img'] = uri(b.img.convert('RGB')); rb['depth'] = uri(dep2)
    data = open(os.path.join(WEB, 'data.js'), encoding='utf-8').read(); full = json.loads(data[data.index('{'):data.rindex('}') + 1])
    full['rooms'] = {'plaza': ra, 'corridor': rb}; full['starts'] = {'plaza': {'room': 'plaza', 'x': 50, 'd': 57}}
    open(os.path.join(WEB, 'plaza_data.js'), 'w', encoding='utf-8').write('window.GAME_DATA = ' + json.dumps(full) + ';\n')
    h = open(os.path.join(WEB, 'index.html'), encoding='utf-8').read()
    h = h.replace('<script src="data.js"></script><script src="game.js"></script>', '<script>' + open(os.path.join(WEB, 'plaza_data.js'), encoding='utf-8').read() + '</script><script>' + open(os.path.join(WEB, 'game.js'), encoding='utf-8').read() + '</script>')
    open(os.path.join(WEB, 'plaza.html'), 'w', encoding='utf-8').write(h); print('web/plaza.html', len(h) // 1024, 'KB')
if __name__ == '__main__': main()
