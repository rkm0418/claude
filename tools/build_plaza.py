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
    F = [[bool(free((i + .5) * CELL, (j + .5) * CELL)) for i in range(gw)] for j in range(gh)]
    inx = lambda x, d: any(e['zone'][0] <= x <= e['zone'][1] and e['zone'][2] <= d <= e['zone'][3] for e in exits)
    for j in range(gh):                                                                           # 아이 발 크기(좌우 4, 앞뒤 2.2)만큼 물체에서 띄운다: 몸이 물체를 뚫고 지나가지 않게
        for i in range(gw):
            if not F[j][i]: continue
            if inx((i + .5) * CELL, (j + .5) * CELL) or all(F[jj][ii] for jj in range(max(0, j - 1), min(gh, j + 2)) for ii in range(max(0, i - 2), min(gw, i + 3))): px[i, j] = 255
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
    sb, rb = room(b, 'corridor', '긴 복도', 520, 170, free_b, [14, 56], [dict(zone=[0, 5, 37, 78], to='plaza', spawn=[134, 40], type='trans', dir='L'), dict(zone=[514, 520, 37, 78], to='fountain', spawn=[12, 87], type='trans', dir='R')])
    rb['img'] = uri(b.img.convert('RGB')); rb['depth'] = uri(dep2)
    # --- 복도가 정사각형 광장으로 커지는 곳(인공 분수와 풀)
    f = C.fountain_scene(410, 'city3d_fountain', False, 'lr'); fx, fd = C.FC; fr = C.FR
    dep3 = Image.new('RGB', (f.CW, f.CH), (255, 255, 255)); d3 = ImageDraw.Draw(dep3); v = ((fd - fr + 4) + 2) * 3          # 분수가 뒤로 지나가는 아이를 가린다
    for z in (0, 7): d3.polygon([f.P1(fx - fr, fd - fr, z), f.P1(fx + fr, fd - fr, z), f.P1(fx + fr, fd + fr, z), f.P1(fx - fr, fd + fr, z)], fill=(v,) * 3)
    d3.polygon([f.P1(fx - fr, fd - fr, 0), f.P1(fx + fr, fd - fr, 0), f.P1(fx + fr, fd - fr, 7), f.P1(fx - fr, fd - fr, 7)], fill=(v,) * 3)
    d3.rectangle([f.P1(fx - 9, fd, 0)[0], f.P1(fx, fd, 28)[1], f.P1(fx + 9, fd, 0)[0], f.P1(fx, fd, 7)[1]], fill=(v,) * 3)
    def free_f(x, d):
        if x < 3 or x > 409.5: return False
        if abs(x - fx) < fr + 3 and abs(d - fd) < fr + 3: return False
        if any(abs(x - lx) < 4 and abs(d - ld_) < 4 for lx, ld_ in C.LAMPS): return False
        if any(bx - 3 < x < bx + 31 and bd - 3 < d < bd + 9 for bx, bd in C.BEN) or (C.BIN[0] - 3 < x < C.BIN[0] + 9 and C.BIN[1] - 3 < d < C.BIN[1] + 9): return False
        if C.P0 + 3 < x < C.P1 - 3 and (2 < d <= C.SQF + 6 or C.SQD - 6 <= d < C.SQD + C.PL): return True                                  # 아래쪽 가운데 통로
        if C.SQ0 + 4 < x < C.SQ1 - 4: return C.SQF + 4 < d < C.SQD - 2
        return C.C0 + 3 < d < C.C1 - 2
    sf, rf = room(f, 'fountain', '분수 광장', 410, 262, free_f, [14, 87], [dict(zone=[0, 5, 78, 96], to='corridor', spawn=[506, 56], type='trans', dir='L'), dict(zone=[404, 410, 78, 96], to='street', spawn=[22, 30], type='trans', dir='R'), dict(zone=[196, 214, 0, 6], to='lot', spawn=[295, 190], type='trans', dir='F'), dict(zone=[196, 214, C.SQD + C.PL - 6, C.SQD + C.PL], to='recycle', spawn=[205, 14], type='trans', dir='B')])
    rf['img'] = uri(f.img.convert('RGB')); rf['depth'] = uri(dep3)
    # --- 분리수거장(분수 광장 위쪽) · 주차장(아래쪽) · 거리(오른쪽, 터널 입구가 있는 장면)
    r1 = C.sq_scene('recycle', 300, 'city3d_recycle', False); r2 = C.lot_scene(C.LOT_W, 'city3d_lot', False); r3 = C.street(True)
    def blk(x, d, x0, d0, w, dp): return x0 - 3 < x < x0 + w + 3 and d0 - 3 < d < d0 + dp + 3
    def free_r(x, d):
        if x < 3 or x > 297: return False
        if any(blk(x, d, C.SQ0 + 34 + i * 18, C.SQD - 13, 12, 8) for i in range(5)) or blk(x, d, C.SQ1 - 52, C.SQD - 20, 26, 9): return False
        if abs(x - (C.SQ1 - 14)) < 4 and abs(d - (C.SQD - 4)) < 4: return False
        if C.P0 + 3 < x < C.P1 - 3 and 2 < d <= C.SQF + 6: return True
        return C.SQ0 + 4 < x < C.SQ1 - 4 and C.SQF + 4 < d < C.SQD - 2
    sr, rr_ = room(r1, 'recycle', '분리수거장', 300, 255, free_r, [205, 14], [dict(zone=[196, 214, 0, 6], to='fountain', spawn=[205, C.SQD + C.PL - 12], type='trans', dir='F')])
    rr_['img'] = uri(r1.img.convert('RGB')); rr_['depth'] = uri(Image.new('RGB', (r1.CW, r1.CH), (255, 255, 255)))
    lampsl = (C.LX0 + 14, C.LX1 - 14); SD = C.LSQD; MID = (C.LP0 + C.LP1) / 2
    def free_s(x, d):
        if x < 3 or x > C.LOT_W - 3: return False
        if any(abs(x - cx_ - 9.5) < 13 and abs(d - cd_ - 20) < 24 for cx_, cd_ in r2.cars): return False        # 세워 둔 차(크기 1.35배)
        if any(abs(x - lx) < 4 and abs(d - (SD - 4)) < 4 for lx in lampsl): return False
        if C.LP0 + 3 < x < C.LP1 - 3 and SD - 4 <= d < SD + C.PL: return True
        return C.LX0 + 4 < x < C.LX1 - 4 and C.SQF + 4 < d < SD + 3
    ex, ed = r2.egg; nx, nd = C.NOTE_AT
    poem = ['비 갠 저녁,', '가장 먼저 켜지는 것은', '신호등의 가운데 불.', '병아리가 지나간 자리에', '은행잎 한 장이 남았다.', '아무도 가져가지 않은', '마지막 햇빛의 색.']
    objs = [dict(id='lot_poem', type='poem', baked=True, x=nx, d=nd, h=8, reach=22, lines=poem), dict(id='lot_tool', type='tool', need='poem_read', x=ex + 9, d=ed + 18, h=14, rad=24, reach=44)]
    ss, rs_ = room(r2, 'lot', '주차장', C.LOT_W, 300, free_s, [MID, SD + 20], [dict(zone=[C.LP0 + 3, C.LP1 - 3, SD + C.PL - 6, SD + C.PL], to='fountain', spawn=[205, 14], type='trans', dir='B')])
    rs_['objects'] = objs; rs_['img'] = uri(r2.img.convert('RGB')); rs_['depth'] = uri(Image.new('RGB', (r2.CW, r2.CH), (255, 255, 255)))
    def free_t(x, d):
        if x > 171 or d < 2: return False
        if x < 4 and not (16 < d < 42): return False
        if d > 517 and not (40 < x < 136): return False
        if x > 170 and 230 < d < 330: return False
        for (bx, bd, bw, bdp) in ((12, 200, 5, 18), (158, 270, 8, 8), (14, 420, 5, 5)):
            if blk(x, d, bx, bd, bw, bdp): return False
        if any(abs(x - lx) < 4 and abs(d - ld_) < 4 for lx, ld_ in ((30, 170), (146, 240), (30, 330), (146, 400), (30, 452))): return False
        return True
    st_, rt_ = room(r3, 'street', '거리', 176, 520, free_t, [22, 30], [dict(zone=[0, 6, 16, 42], to='fountain', spawn=[400, 87], type='trans', dir='L'), dict(zone=[40, 136, 512, 520], to=None, type='trans', dir='B')])
    rt_['img'] = uri(r3.img.convert('RGB')); rt_['depth'] = uri(Image.new('RGB', (r3.CW, r3.CH), (255, 255, 255)))
    data = open(os.path.join(WEB, 'data.js'), encoding='utf-8').read(); full = json.loads(data[data.index('{'):data.rindex('}') + 1])
    full['rooms'] = {'plaza': ra, 'corridor': rb, 'fountain': rf, 'recycle': rr_, 'lot': rs_, 'street': rt_}; full['starts'] = {'plaza': {'room': 'plaza', 'x': 60, 'd': 24}}
    open(os.path.join(WEB, 'plaza_data.js'), 'w', encoding='utf-8').write('window.GAME_DATA = ' + json.dumps(full) + ';\n')
    h = open(os.path.join(WEB, 'index.html'), encoding='utf-8').read()
    h = h.replace('<script src="data.js"></script><script src="game.js"></script>', '<script>' + open(os.path.join(WEB, 'plaza_data.js'), encoding='utf-8').read() + '</script><script>' + open(os.path.join(WEB, 'game.js'), encoding='utf-8').read() + '</script>')
    open(os.path.join(WEB, 'plaza.html'), 'w', encoding='utf-8').write(h); print('web/plaza.html', len(h) // 1024, 'KB')
if __name__ == '__main__': main()
