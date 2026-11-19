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
    inx = lambda x, d: any(e['zone'][0] <= x <= e['zone'][1] and e['zone'][2] <= d <= e['zone'][3] for e in exits)
    F = [[bool(free((i + .5) * CELL, (j + .5) * CELL)) or inx((i + .5) * CELL, (j + .5) * CELL) for i in range(gw)] for j in range(gh)]   # 출구 칸도 '빈 칸'으로 쳐서 출구 앞 칸이 고립되지 않게
    for j in range(gh):                                                                           # 아이 발 크기(좌우 4, 앞뒤 2.2)만큼 물체에서 띄운다: 몸이 물체를 뚫고 지나가지 않게
        for i in range(gw):
            if not F[j][i]: continue
            if inx((i + .5) * CELL, (j + .5) * CELL) or all(F[jj][ii] for jj in range(max(0, j - 1), min(gh, j + 2)) for ii in range(max(0, i - 2), min(gw, i + 3))): px[i, j] = 255
    return s, dict(W=W, D=D, X0=s.X0, Y0=s.Y0, CW=CW, CH=CH, rects=[list(r) for r in rects], exits=exits, start=start, S=2, label=label, walk=uri(walk.convert('RGB')))

def occl(s, base=None, min_top=5, skip=lambda b: False):
    """그린 상자 기록으로 깊이 지도(몸 가림)를 만든다. 앞면은 d 고정, 윗면은 화소마다 실제 깊이, 오른쪽 면은 가리지 않는다(옆을 지나는 아이를 가리지 않게)."""
    import numpy as np
    dep = np.full((s.CH, s.CW), 1e9)
    if base is not None: dep = np.minimum(dep, np.where(np.array(base.convert('L')) >= 255, 1e9, np.array(base.convert('L')) / 3.0 - 2))
    for b in s.log:
        x, d, w, dp, h, z0 = b; top = z0 + h
        if top < min_top or w > 70 or dp > 70 or d > s.D or h > 60 or skip(b): continue
        ya, yb = round(s.Y0 - .5 * d - top), round(s.Y0 - .5 * d - z0); xa, xb = round(s.X0 + x + .5 * d), round(s.X0 + x + w + .5 * d)
        ya, xa = max(0, ya), max(0, xa); sub = dep[ya:yb + 1, xa:xb + 1]; np.minimum(sub, d, out=sub)
        for Y in range(max(0, round(s.Y0 - .5 * (d + dp) - top)), round(s.Y0 - .5 * d - top) + 1):
            dd = min(d + dp, max(d, (s.Y0 - top - Y) / .5)); xa2, xb2 = max(0, round(s.X0 + x + .5 * dd)), round(s.X0 + x + w + .5 * dd)
            if Y < s.CH: sub = dep[Y, xa2:xb2 + 1]; np.minimum(sub, dd, out=sub)
    v = np.where(dep >= 1e8, 255, np.clip((dep + 2) * 3, 0, 254)).astype('uint8')
    return Image.fromarray(np.stack([v, v, v], -1), 'RGB')

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
    ra['img'] = uri(a.img.convert('RGB')); ra['depth'] = uri(occl(a, dep))
    # --- 긴 복도(화단 없이)
    b = C.landing(520, True, 'city3d_corridor', False, False, False, 'lr'); EX = 520 - 56
    dep2 = Image.new('RGB', (b.CW, b.CH), (255, 255, 255))
    def free_b(x, d):
        if x < 3 or x > 519.5: return False
        if any(abs(x - lx) < 4 and abs(d - 74) < 4 for lx in b.lampx): return False
        return 37 < d < 78
    sb, rb = room(b, 'corridor', '긴 복도', 520, 170, free_b, [14, 56], [dict(zone=[0, 5, 37, 78], to='plaza', spawn=[134, 40], type='trans', dir='L'), dict(zone=[514, 520, 37, 78], to='fountain', spawn=[12, 87], type='trans', dir='R')])
    rb['img'] = uri(b.img.convert('RGB')); rb['depth'] = uri(occl(b))
    # --- 복도가 정사각형 광장으로 커지는 곳(인공 분수와 풀)
    f = C.fountain_scene(410, 'city3d_fountain', False, 'lr'); fx, fd = C.FC; fr = C.FR
    def free_f(x, d):
        if x < 3 or x > 409.5: return False
        if abs(x - fx) < fr + 3 and abs(d - fd) < fr + 3: return False
        if any(abs(x - lx) < 4 and abs(d - ld_) < 4 for lx, ld_ in C.LAMPS): return False
        if any(bx - 3 < x < bx + 31 and bd - 3 < d < bd + 9 for bx, bd in C.BEN) or (C.BIN[0] - 3 < x < C.BIN[0] + 9 and C.BIN[1] - 3 < d < C.BIN[1] + 9): return False
        if C.P0 + 3 < x < C.P1 - 3 and (2 < d <= C.SQF + 6 or C.SQD - 6 <= d < C.SQD + C.PL): return True                                  # 아래쪽 가운데 통로
        if C.SQ0 + 4 < x < C.SQ1 - 4: return C.SQF + 4 < d < C.SQD - 2
        return C.C0 + 3 < d < C.C1 - 2
    sf, rf = room(f, 'fountain', '분수 광장', 410, 262, free_f, [14, 87], [dict(zone=[0, 5, 78, 96], to='corridor', spawn=[506, 56], type='trans', dir='L'), dict(zone=[404, 410, 78, 96], to='street', spawn=[22, 30], type='trans', dir='R'), dict(zone=[196, 214, 0, 6], to='lot', spawn=[295, 190], type='trans', dir='F'), dict(zone=[196, 214, C.SQD + C.PL - 6, C.SQD + C.PL], to='recycle', spawn=[205, 14], type='trans', dir='B')])
    rf['img'] = uri(f.img.convert('RGB')); rf['depth'] = uri(occl(f))
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
    rr_['img'] = uri(r1.img.convert('RGB')); rr_['depth'] = uri(occl(r1))
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
    rs_['objects'] = objs; rs_['img'] = uri(r2.img.convert('RGB')); rs_['depth'] = uri(occl(r2))
    def free_t(x, d):
        if x > 171 or d < 2: return False
        if x < 4 and not (16 < d < 42): return False
        if d > 517 and not (40 < x < 136): return False
        for (bx, bd, bw, bdp) in ((12, 200, 5, 18), (14, 420, 5, 5)):
            if blk(x, d, bx, bd, bw, bdp): return False
        if any(abs(x - lx) < 4 and abs(d - ld_) < 4 for lx, ld_ in ((30, 170), (146, 240), (30, 330), (146, 400), (30, 452))): return False
        return True
    st_, rt_ = room(r3, 'street', '거리', 176, 520, free_t, [22, 30], [dict(zone=[0, 6, 16, 42], to='fountain', spawn=[400, 87], type='trans', dir='L'), dict(zone=[40, 136, 512, 520], to='rtunnel', spawn=[76, 8], type='trans', dir='B')])
    rt_['img'] = uri(r3.img.convert('RGB')); rt_['depth'] = uri(occl(r3))
    # --- 아치 안 일자 도로 터널 → 옆으로 파인 비상구 → ㄴ자 정비 통로 → 사용자가 만든 터널
    r4 = C.road_tunnel('city3d_roadtunnel', False); n0, n1 = C.NICHE
    def free_u(x, d):
        if C.RV0 - 8 < x < C.RV1 - 3 and 3 < d < C.RTD - 4: return True
        return 5 < x <= C.RV0 - 6 and n0 + 2 < d < n1 - 2
    su, ru = room(r4, 'rtunnel', '도로 터널', C.RTW, C.RTD, free_u, [76, 8], [dict(zone=[C.RV0, C.RV1 - 3, 0, 6], to='street', spawn=[88, 498], type='trans', dir='F'), dict(zone=[5, 9, n0 + 2, n1 - 2], to='annex', spawn=[(C.ADOOR[0] + C.ADOOR[1]) / 2, 26], type='trans', dir='L'), dict(zone=[C.RV0, C.RV1 - 3, C.RTD - 6, C.RTD], to=None, type='trans', dir='B', endMsg='터널은 아직 이어지지 않았어요')])
    ru['img'] = uri(r4.img.convert('RGB')); ru['depth'] = uri(occl(r4))
    r6 = C.annex('city3d_annex', False)
    def free_a2(x, d):
        if 3 < x < C.AV - 3 and 3 < d < C.AD - 2: return True
        return 3 < x < C.AW - 4 and 3 < d < C.AV - 4
    sa2, ra2 = room(r6, 'annex', '정비 통로', C.AW, C.AD, free_a2, [(C.ADOOR[0] + C.ADOOR[1]) / 2, 26], [dict(zone=[C.ADOOR[0] + 2, C.ADOOR[1] - 2, C.AV - 8, C.AV - 2], to='rtunnel', spawn=[19, (n0 + n1) / 2], type='trans', dir='F'), dict(zone=[C.APASS[0], C.APASS[1], C.AD - 6, C.AD], to='tunnel', spawn=[32, 8], type='trans', dir='B')])
    ra2['img'] = uri(r6.img.convert('RGB')); ra2['depth'] = uri(occl(r6))
    import render_tunnel as T
    r5 = T.build()
    def free_v(x, d): return 3 < x < 61 and 2 < d < 297
    sv, rv = room(r5, 'tunnel', '터널', T.W, T.D, free_v, [32, 8], [dict(zone=[3, 61, 0, 4], to='annex', spawn=[(C.APASS[0] + C.APASS[1]) / 2, C.AD - 18], type='trans', dir='F'), dict(zone=[3, 61, 296, 300], to=None, type='trans', dir='B', endMsg='터널 끝 — 여기서부터는 아직 만들지 않았어요')])
    rv['img'] = uri(r5.img.convert('RGB')); rv['depth'] = uri(Image.new('RGB', (r5.CW, r5.CH), (255, 255, 255)))
    data = open(os.path.join(WEB, 'data.js'), encoding='utf-8').read(); full = json.loads(data[data.index('{'):data.rindex('}') + 1])
    full['rooms'] = {'plaza': ra, 'corridor': rb, 'fountain': rf, 'recycle': rr_, 'lot': rs_, 'street': rt_, 'rtunnel': ru, 'annex': ra2, 'tunnel': rv}; full['starts'] = {'plaza': {'room': 'plaza', 'x': 60, 'd': 24}}
    open(os.path.join(WEB, 'plaza_data.js'), 'w', encoding='utf-8').write('window.GAME_DATA = ' + json.dumps(full) + ';\n')
    h = open(os.path.join(WEB, 'index.html'), encoding='utf-8').read()
    h = h.replace('<script src="data.js"></script><script src="game.js"></script>', '<script>' + open(os.path.join(WEB, 'plaza_data.js'), encoding='utf-8').read() + '</script><script>' + open(os.path.join(WEB, 'game.js'), encoding='utf-8').read() + '</script>')
    open(os.path.join(WEB, 'plaza.html'), 'w', encoding='utf-8').write(h); print('web/plaza.html', len(h) // 1024, 'KB')
if __name__ == '__main__': main()
