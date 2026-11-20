#!/usr/bin/env python3
"""사용자가 만든 첫 장면(광장 화단)과 긴 복도 두 곳만 같은 엔진으로 걸어 다니게 하는 별도 파일(web/plaza.html).
사용: python3 tools/build_plaza.py  (먼저 python3 tools/export_web.py 로 web/data.js 가 있어야 한다: 아이·적 그림을 가져온다)"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
import render_city3d as C
import layers as L
from export_web import uri
WEB = os.path.join(HERE, '..', 'web'); CELL = 2

GEOM = {}                                                                                         # 검사기(tools/layers.py)용: 방마다 (장면, 걷는 칸, 출구 칸, 출발점, 출구)

def room(s, key, label, W, D, free, start, exits, rects=(), geom=None):
    """방 하나. 걷는 칸은 레이어 규칙(tools/layers.py, docs/layer-rules.md)으로 만든다: free 는 바닥 모양만 말하고,
    물체(상자·가로등 기둥·벽 면)에서 띄우는 것은 장면이 기록한 물체로 자동 계산한다. 깊이 지도도 장면이 그리며 남긴 zb 그대로."""
    g = geom or s
    for e in exits:                                                                              # 문·통로를 누를 수 있는 화면 범위(논리 화소): 출구 구역을 위(문 높이 40)까지 세운 상자의 화면 윤곽
        if (e.get('to') or e.get('need')) and 'hit' not in e:
            z = e['zone']; pts = [(s.X0 + x + .5 * d, s.Y0 - .5 * d - h) for x in (z[0] - 4, z[1] + 4) for d in (z[2] - 3, z[3] + 3) for h in (0, 40)]
            e['hit'] = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
    walk, zone = L.walk_grid(g, W, D, free, exits); GEOM[key] = (g, walk, zone, start, exits)
    im = Image.fromarray((walk * 255).astype('uint8'), 'L')
    return s, dict(W=W, D=D, X0=s.X0, Y0=s.Y0, CW=s.CW, CH=s.CH, rects=[list(r) for r in rects], exits=exits, start=start, S=2, label=label, walk=uri(im.convert('RGB')),
                   img=uri(s.img.convert('RGB')), depth=uri(g.depth_rgb()), dep16=1)

def build(check=False):
    # --- 광장(첫 장면)
    a = C.landing(150, False, 'city3d_landing', True, False, False, 'r', False, 26)
    def free_a(x, d):
        if d < 4 or d > 77 or x < 4 or x > 146: return False
        return True
    sa, ra = room(a, 'plaza', '광장', 150, 80, free_a, [60, 24], [dict(zone=[144, 150, 4, 77], to='corridor', spawn=[12, 56], type='trans', dir='R')])
    # --- 긴 복도(화단 없이)
    b = C.landing(520, True, 'city3d_corridor', False, False, False, 'lr'); EX = 520 - 56
    def free_b(x, d):
        if x < 3 or x > 519.5: return False
        return 37 < d < 78
    sb, rb = room(b, 'corridor', '긴 복도', 520, 170, free_b, [14, 56], [dict(zone=[0, 5, 37, 78], to='plaza', spawn=[134, 40], type='trans', dir='L'), dict(zone=[514, 520, 37, 78], to='fountain', spawn=[12, 87], type='trans', dir='R')])
    # --- 복도가 정사각형 광장으로 커지는 곳(인공 분수와 풀)
    f = C.fountain_scene(410, 'city3d_fountain', False, 'lr'); fx, fd = C.FC; fr = C.FR
    def free_f(x, d):
        if x < 3 or x > 409.5: return False
        if C.P0 + 3 < x < C.P1 - 3 and (2 < d <= C.SQF + 6 or C.SQD - 6 <= d < C.SQD + C.PL): return True                                  # 아래쪽 가운데 통로
        if C.SQ0 + 4 < x < C.SQ1 - 4: return C.SQF + 4 < d < C.SQD - 2
        return C.C0 + 3 < d < C.C1 - 2
    sf, rf = room(f, 'fountain', '분수 광장', 410, 262, free_f, [14, 87], [dict(zone=[0, 5, 78, 96], to='corridor', spawn=[506, 56], type='trans', dir='L'), dict(zone=[404, 410, 78, 96], to='street', spawn=[22, 30], type='trans', dir='R'), dict(zone=[196, 214, 0, 6], to='lot', spawn=[295, 190], type='trans', dir='F'), dict(zone=[196, 214, C.SQD + C.PL - 6, C.SQD + C.PL], to='recycle', spawn=[205, 14], type='trans', dir='B')])
    # --- 분리수거장(분수 광장 위쪽) · 주차장(아래쪽) · 거리(오른쪽, 터널 입구가 있는 장면)
    r1 = C.sq_scene('recycle', 300, 'city3d_recycle', False); r2 = C.lot_scene(C.LOT_W, 'city3d_lot', False); r3 = C.street(True)
    def blk(x, d, x0, d0, w, dp): return x0 - 3 < x < x0 + w + 3 and d0 - 3 < d < d0 + dp + 3
    def free_r(x, d):
        if x < 3 or x > 297: return False
        if d > C.SQD - 12: return False                                                                # 분리수거함·상자 뒤쪽 좁은 틈은 못 들어간다
        if C.P0 + 3 < x < C.P1 - 3 and 2 < d <= C.SQF + 6: return True
        return C.SQ0 + 4 < x < C.SQ1 - 4 and C.SQF + 4 < d < C.SQD - 2
    sr, rr_ = room(r1, 'recycle', '분리수거장', 300, 255, free_r, [205, 14], [dict(zone=[196, 214, 0, 6], to='fountain', spawn=[205, C.SQD + C.PL - 12], type='trans', dir='F')])
    lampsl = (C.LX0 + 14, C.LX1 - 14); SD = C.LSQD; MID = (C.LP0 + C.LP1) / 2
    def free_s(x, d):
        if x < 3 or x > C.LOT_W - 3: return False
        if C.LP0 + 3 < x < C.LP1 - 3 and SD - 4 <= d < SD + C.PL: return True
        return C.LX0 + 4 < x < C.LX1 - 4 and C.SQF + 4 < d < SD + 3
    ex, ed = r2.egg; nx, nd = C.NOTE_AT
    poem = ['비 갠 저녁,', '가장 먼저 켜지는 것은', '신호등의 가운데 불.', '병아리가 지나간 자리에', '은행잎 한 장이 남았다.', '아무도 가져가지 않은', '마지막 햇빛의 색.']
    objs = [dict(id='lot_poem', type='poem', baked=True, x=nx, d=nd, h=8, reach=22, lines=poem), dict(id='lot_tool', type='tool', need='poem_read', x=ex + 9, d=ed + 18, h=14, rad=24, reach=44)]
    ss, rs_ = room(r2, 'lot', '주차장', C.LOT_W, 300, free_s, [MID, SD + 20], [dict(zone=[C.LP0 + 3, C.LP1 - 3, SD + C.PL - 6, SD + C.PL], to='fountain', spawn=[205, 14], type='trans', dir='B')])
    rs_['objects'] = objs
    def free_t(x, d):
        if x > 171 or d < 2: return False
        if x < 4 and not (16 < d < 42): return False
        if d > 517 and not (40 < x < 136): return False
        return True
    st_, rt_ = room(r3, 'street', '거리', 176, 520, free_t, [22, 30], [dict(zone=[0, 6, 16, 42], to='fountain', spawn=[400, 87], type='trans', dir='L'), dict(zone=[40, 136, 512, 520], to='rtunnel', spawn=[76, 8], type='trans', dir='B')])
    # --- 아치 안 일자 도로 터널 → 옆으로 파인 비상구 → ㄴ자 정비 통로 → 사용자가 만든 터널
    r4 = C.road_tunnel('city3d_roadtunnel', False, True); r4a = C.road_tunnel('city3d_roadtunnel_open', False, False); n0, n1 = C.NICHE
    from PIL import ImageChops
    bb = ImageChops.difference(r4.img.convert('RGB'), r4a.img.convert('RGB')).getbbox(); K = r4.k          # 가려진 그림과 열린 그림이 다른 부분 = 비상구 자리
    patch = r4a.img.convert('RGB').crop(bb)
    def free_u(x, d):
        if C.RV0 - 8 < x < C.RV1 - 3 and 3 < d < C.RTD - 4: return True
        return 5 < x <= C.RV0 - 6 and n0 + 2 < d < n1 - 2
    su, ru = room(r4, 'rtunnel', '도로 터널', C.RTW, C.RTD, free_u, [76, 8], geom=r4a, exits=[dict(zone=[C.RV0, C.RV1 - 3, 0, 6], to='street', spawn=[88, 498], type='trans', dir='F'), dict(zone=[5, 9, n0 + 2, n1 - 2], to='annex', spawn=[C.AL - 16, 28], type='trans', dir='L'), dict(zone=[C.RV0, C.RV1 - 3, C.RTD - 6, C.RTD], to='outroad', spawn=[88, 12], type='trans', dir='B')])
    ru['reveal'] = [dict(img=uri(patch), x=bb[0] / K, y=bb[1] / K, w=(bb[2] - bb[0]) / K, h=(bb[3] - bb[1]) / K, zone=[C.WX, C.WX + 30, n0 - 12, n1 + 12], r=46)]
    r6 = C.annex('city3d_annex', False)
    def free_a2(x, d): return 3 < x < C.AL - 3 and C.AF + 2 < d < C.AB - 8
    sa2, ra2 = room(r6, 'annex', '정비 복도', C.AW, C.AD, free_a2, [C.AL - 16, 28], [dict(zone=[C.AL - 6, C.AL, C.AF + 2, C.AB - 2], to='rtunnel', spawn=[19, (n0 + n1) / 2], type='trans', dir='R'), dict(zone=[0, 6, C.APASS[0] + 2, C.APASS[1] - 2], to='tunnel', spawn=[52, 40], type='trans', dir='L'),
        dict(zone=[233, 244, C.AB - 10, C.AB], to='lounge', spawn=[C.LDOOR[0] + 7, 20], type='trans', dir='B'), dict(zone=[85, 96, C.AB - 10, C.AB], to='annex', need='never_open', needMsg='문이 잠겨 있다', side='back')])
    r7 = C.lounge('city3d_lounge', False)
    def free_l(x, d): return 3 < x < C.LW - 3 and 8 < d < C.LD - 5 or (C.LDOOR[0] < x < C.LDOOR[1] and 0 <= d <= 8)
    sl, rl = room(r7, 'lounge', '휴게실', C.LW, C.LD, free_l, [C.LDOOR[0] + 7, 20], [dict(zone=[C.LDOOR[0] + 1, C.LDOOR[1] - 1, 0, 6], to='annex', spawn=[238, C.AB - 14], type='trans', dir='F')])
    import render_tunnel as T
    r5 = T.build()
    def free_v(x, d): return 3 < x < 61 and 2 < d < T.D - 3
    sv, rv = room(r5, 'tunnel', '터널', T.W, T.D, free_v, [52, 40], [dict(zone=[57, 61, 22, 58], to='annex', spawn=[14, (C.APASS[0] + C.APASS[1]) / 2], type='trans', dir='R'), dict(zone=[3, 61, T.D - 4, T.D], to='autumn', spawn=[44, 20], type='trans', dir='B')])
    import render_autumn as AU
    r9 = AU.build('forest')                                                                       # 가로로 쭉 이어지는 빽빽한 가을 숲(처음 만든 집 있는 시골은 build('original') 로 보관)
    AU_W, AU_D = r9.W, r9.D
    def free_au(x, d): return 4 < x < AU_W - 4 and 3 < d < AU_D - 4
    sau, rau = room(r9, 'autumn', '가을 낙엽길', AU_W, AU_D, free_au, [44, 20], [dict(zone=[27, 33, 12, 28], to='tunnel', spawn=[52, T.D - 18], type='trans', dir='L'), dict(zone=[AU_W - 14, AU_W - 6, 6, 34], to='scurve', spawn=[42, 25], type='trans', dir='R')])
    r10 = AU.build('s_curve')                                                                      # 숲길 오른쪽 끝에서 이어지는 S자 흙길 구간
    SW, SD = r10.W, r10.D
    def free_sc(x, d): return 4 < x < SW - 14 and 4 < d < SD - 4
    ssc, rsc = room(r10, 'scurve', 'S자 숲길', SW, SD, free_sc, [42, 25], [dict(zone=[3, 9, 10, 44], to='autumn', spawn=[AU_W - 80, 20], type='trans', dir='L'), dict(zone=[SW - 22, SW - 14, 150, 182], to='scurve2', spawn=[42, 165], type='trans', dir='R')])
    r11 = AU.build('s_curve2')                                                                     # S자 구간을 좌우반전 + 나무 사이 벤치: 위쪽 왼쪽에서 들어와 아래쪽 오른쪽으로 내려간다
    def free_sc2(x, d): return 4 < x < SW - 14 and 4 < d < SD - 4
    ssc2, rsc2 = room(r11, 'scurve2', '벤치 숲길', SW, SD, free_sc2, [42, 165], [dict(zone=[3, 9, 150, 182], to='scurve', spawn=[SW - 80, 165], type='trans', dir='L'), dict(zone=[SW - 22, SW - 14, 6, 44], to='bend', spawn=[42, 34], type='trans', dir='R')])
    r12 = AU.build('bend')                                                                        # 왼쪽에서 들어와 오른쪽으로 가다 위쪽(뒤)으로 꺾이는 길, 꺾이는 곳 안쪽에 그네
    BW, BD = r12.W, r12.D
    def free_bd(x, d): return 4 < x < BW - 4 and 4 < d < BD - 8
    sbd, rbd = room(r12, 'bend', '그네 꺾인 길', BW, BD, free_bd, [42, 34], [dict(zone=[3, 9, 20, 48], to='scurve2', spawn=[SW - 80, 25], type='trans', dir='L'), dict(zone=[152, 188, BD - 24, BD - 10], to='house', spawn=[170, 40], type='trans', dir='B')])
    r13 = AU.build('house')                                                                       # 위로 올라간 끝: 집 앞마당(보관해 둔 기와집)
    HW, HD = r13.W, r13.D
    def free_hs(x, d): return 4 < x < HW - 4 and 4 < d < HD - 8
    shs, rhs = room(r13, 'house', '집 앞마당', HW, HD, free_hs, [170, 40], [dict(zone=[158, 182, 0, 6], to='bend', spawn=[170, 190], type='trans', dir='F'), dict(zone=[158, 182, 138, 150], to=None, type='trans', dir='B', endMsg='집 안은 아직 만들지 않았어요')])
    r8 = C.street(True, 'out'); D8 = 480
    def free_o(x, d): return 4 < x < 171 and 2 < d < r8.erode_front - 6                          # 끝에서 뾰족하게 번져 오는 검은 이빨 앞에서 막힌다(로딩 안 된 곳)
    so, ro = room(r8, 'outroad', '터널 밖 길', 176, D8, free_o, [88, 12], [dict(zone=[24, 150, 0, 4], to='rtunnel', spawn=[(C.RV0 + C.RV1) / 2, C.RTD - 14], type='trans', dir='F')])
    if check:
        sp = {}
        for k, (g, w, z, st, ex) in GEOM.items():
            for e in ex:
                if e.get('to') and e.get('spawn'): sp.setdefault(e['to'], []).append((k, e['spawn']))
        return {k: (g, w, z, st, ex, sp.get(k, [])) for k, (g, w, z, st, ex) in GEOM.items()}
    data = open(os.path.join(WEB, 'data.js'), encoding='utf-8').read(); full = json.loads(data[data.index('{'):data.rindex('}') + 1])
    full['rooms'] = {'plaza': ra, 'corridor': rb, 'fountain': rf, 'recycle': rr_, 'lot': rs_, 'street': rt_, 'rtunnel': ru, 'annex': ra2, 'lounge': rl, 'tunnel': rv, 'outroad': ro, 'autumn': rau, 'scurve': rsc, 'scurve2': rsc2, 'bend': rbd, 'house': rhs}; full['starts'] = {'plaza': {'room': 'plaza', 'x': 60, 'd': 24}}
    open(os.path.join(WEB, 'plaza_data.js'), 'w', encoding='utf-8').write('window.GAME_DATA = ' + json.dumps(full) + ';\n')
    h = open(os.path.join(WEB, 'index.html'), encoding='utf-8').read()
    h = h.replace('<script src="data.js"></script><script src="game.js"></script>', '<script>' + open(os.path.join(WEB, 'plaza_data.js'), encoding='utf-8').read() + '</script><script>' + open(os.path.join(WEB, 'game.js'), encoding='utf-8').read() + '</script>')
    NAMES = [('plaza', '광장 · 시작'), ('corridor', '긴 복도'), ('fountain', '분수 광장'), ('recycle', '분리수거장'), ('lot', '주차장'), ('street', '거리'), ('rtunnel', '도로 터널'), ('annex', '정비 복도'), ('lounge', '휴게실'), ('tunnel', '터널'), ('outroad', '터널 밖 길'), ('autumn', '가을 낙엽길'), ('scurve', 'S자 숲길'), ('scurve2', '벤치 숲길'), ('bend', '그네 꺾인 길'), ('house', '집 앞마당')]
    assert [k for k, _ in NAMES] == list(full['rooms'].keys()), 'NAMES 가 방 목록과 다르다'
    ui = """<style>
#where{position:fixed;left:8px;top:8px;z-index:9;font:14px/1.2 system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.55);border-radius:6px;padding:6px 10px;pointer-events:none}
#jumpb{position:fixed;right:8px;top:8px;z-index:9;font:14px system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.55);border:1px solid #888;border-radius:6px;padding:6px 12px;cursor:pointer}
#jumpl{position:fixed;right:8px;top:44px;z-index:9;display:none;flex-direction:column;gap:3px;background:rgba(0,0,0,.75);border:1px solid #888;border-radius:6px;padding:6px;max-height:80vh;overflow:auto}
#jumpl button{font:14px system-ui,sans-serif;color:#fff;background:#2a2a30;border:1px solid #666;border-radius:4px;padding:5px 14px;text-align:left;cursor:pointer}
#jumpl button.on{background:#3a5a8a}
#dbg{top:8px !important;right:84px !important}
</style>
<div id="where">-</div><button id="jumpb">이동</button><div id="jumpl"></div>
<script>
(function(){var N=%s,W=document.getElementById('where'),B=document.getElementById('jumpb'),L=document.getElementById('jumpl'),cur='';
N.forEach(function(n,i){var b=document.createElement('button');b.dataset.k=n[0];b.textContent=(i+1)+'. '+n[1];b.onclick=function(){L.style.display='none';var g=window.__game;if(!g)return;var st=window.GAME_DATA.rooms[n[0]].start;g.enter(n[0],[st[0],st[1]]);};L.appendChild(b);});
B.onclick=function(e){e.stopPropagation();L.style.display=L.style.display==='flex'?'none':'flex';};
['pointerdown','touchstart','mousedown'].forEach(function(t){[B,L].forEach(function(el){el.addEventListener(t,function(e){e.stopPropagation();});});});
setInterval(function(){var g=window.__game;if(!g||!g.room)return;var k=g.room;if(k===cur)return;cur=k;var i=N.findIndex(function(n){return n[0]===k;});W.textContent=i<0?k:(i+1)+'. '+N[i][1];Array.prototype.forEach.call(L.children,function(b){b.className=b.dataset.k===k?'on':'';});},150);})();
</script>""" % json.dumps(NAMES, ensure_ascii=False)
    h = h.replace('</body>', ui + '</body>')
    open(os.path.join(WEB, 'plaza.html'), 'w', encoding='utf-8').write(h); print('web/plaza.html', len(h) // 1024, 'KB')
if __name__ == '__main__': build()
