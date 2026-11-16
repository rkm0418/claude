#!/usr/bin/env python3
"""건물 안: 속 빈 큰 나무의 내부(눈 숲 쉼터의 나무 구멍으로 들어간다). 집 안과 같은 사선 3차원 방 한 칸씩.
tree_main(주 방: 난로·둥근 탁자·책장·잠자리·창, 앞 = 밖으로 나가는 문, 왼쪽 벽 = 곳간) / tree_back(곳간: 통·상자·선반·밧줄 사다리).
퍼즐 기믹은 앞으로 이런 건물 안에 둔다(바깥 맵에는 두지 않는다).
사용: python3 tools/render_treehouse.py -> maps/out/tree_<방>.png, _depth.png, tree_nav.json"""
import json, math, os, random, sys
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT
H = 54
BARK, BARK_D, PLANK, PLANK_D = (118, 86, 62), (92, 66, 48), (170, 126, 86), (140, 100, 66)
ROOM = {'tree_main': (104, 60), 'tree_back': (68, 48)}
EXITS = {
    'tree_main': [{'zone': (44, 62, 0, 3), 'to': 'snow_h', 'spawn': None, 'door': True, 'indoor': True}, {'zone': (0, 5, 22, 38), 'to': 'tree_back', 'spawn': (56, 30)}],
    'tree_back': [{'zone': (62, 68, 14, 30), 'to': 'tree_main', 'spawn': (10, 30)},
                  {'zone': (22, 34, 12, 24), 'to': 'lake_1', 'spawn': None, 'manhole': True, 'hidden': True, 'need': 'tree_open', 'mx': 28, 'md': 18}],
}
OBJECTS = {'tree_main': [
    {'id': 'tm_note', 'type': 'note', 'x': 50, 'd': 33, 'z': 12, 'h': 6, 'reach': 26, 'text': '쪽지: "책장의 책이 꽂힌 순서대로 촛불을 밝혀라."'},
    {'id': 'tm_c0', 'type': 'candle', 'order': 0, 'x': 32, 'd': 48, 'h': 18, 'reach': 16, 'color': [176, 90, 80]},
    {'id': 'tm_c1', 'type': 'candle', 'order': 1, 'x': 66, 'd': 46, 'h': 18, 'reach': 16, 'color': [90, 120, 150]},
    {'id': 'tm_c2', 'type': 'candle', 'order': 2, 'x': 88, 'd': 30, 'h': 18, 'reach': 16, 'color': [210, 180, 90]}]}
PUZZLE = {'tree_main': {'flag': 'tree_open', 'hud': True, 'solvedMsg': '곳간 쪽에서 쇳소리가 났다. 바닥에 무언가 드러났을 것이다'}}

def make(key):
    W, D = ROOM[key]; sc = Scene(W, D, H + 2); sc.img.paste((30, 22, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    def floor(x, d):                                                            # 나무 마루: 가로 널, 어긋난 이음, 가운데 둥근 나이테 무늬 러그 느낌의 짙은 결
        if d % 8 < .8: return PLANK_D
        if x % 30 < .8 and int(d // 8) % 2: return PLANK_D
        return PLANK if int(d // 8) % 2 == 0 else (160, 118, 80)
    sc.floor(floor)
    sc.poly([(0, 0, -5), (W, 0, -5), (W, 0, 0), (0, 0, 0)], (84, 60, 44)); sc.poly([(W, 0, -5), (W, D, -5), (W, D, 0), (W, 0, 0)], (62, 44, 34))
    def front(x0, x1, z0, z1, col, d=D): sc.poly([(x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)], col)
    def left(d0, d1, z0, z1, col, x=0): sc.poly([(x, d0, z0), (x, d1, z0), (x, d1, z1), (x, d0, z1)], col)
    # 벽: 나무 속이라 세로 결의 나무껍질. 짙고 옅은 줄이 번갈아, 군데군데 옹이
    rng = random.Random(7)
    for xx in range(0, W):
        c = BARK if (xx // 3) % 2 == 0 else BARK_D; front(xx, xx + 1, 0, H, c)
    for dd in range(0, D):
        c = dk(BARK, .94) if (dd // 3) % 2 == 0 else dk(BARK_D, .94); left(dd, dd + 1, 0, H, c)
    for _ in range(6):
        kx = rng.uniform(8, W - 8); kz = rng.uniform(14, 40); front(kx - 2, kx + 2, kz - 3, kz + 3, (74, 52, 38)); front(kx - 1, kx + 1, kz - 1.5, kz + 1.5, (50, 34, 26))
    front(0, W, 0, 4, (82, 60, 44)); left(0, D, 0, 4, (82, 60, 44)); front(0, W, H - 4, H, (70, 50, 38)); left(0, D, H - 4, H, (62, 44, 34))
    # 문 틈
    def frame_front(x0, x1):
        sc.poly([(x0, 0, 0), (x1, 0, 0), (x1, 5, 0), (x0, 5, 0)], (228, 214, 174))
        sc.jobs.append((-1, lambda: [sc.box(x0 - 1.5, 0, 1.5, 2, 6, (220, 200, 160), (226, 206, 166), (180, 160, 124)), sc.box(x1, 0, 1.5, 2, 6, (220, 200, 160), (226, 206, 166), (180, 160, 124))]))
    def opening_left(d0, d1):
        left(d0, d1, 0, 40, (40, 30, 28)); left(d0, d1, 0, 8, (90, 66, 48))
        for (a, b, z0, z1) in ((d0 - 1.5, d0, 0, 41.5), (d1, d1 + 1.5, 0, 41.5), (d0 - 1.5, d1 + 1.5, 40, 41.5)): left(a, b, z0, z1, (214, 196, 156))
    def opening_right_door(d0, d1):
        sc.poly([(W - 5, d0, 0), (W, d0, 0), (W, d1, 0), (W - 5, d1, 0)], (228, 214, 174))
    rects = []
    def B(x, d, w, dp, h, c, z0=0, sh=(.86, .72)):
        if z0 < 28: rects.append((round(x, 1), round(d, 1), round(w, 1), round(dp, 1)))
        sc.jobs.append((d, lambda: sc.box(x, d, w, dp, h, c, dk(c, sh[0]), dk(c, sh[1]), z0=z0)))
    def FR(x0, x1, z0, z1, col, d=D): sc.jobs.append(((d + .3) if d == D else (d - .3), lambda: front(x0, x1, z0, z1, col, d=d)))
    def legs(x, d, w, dp, h, c=(110, 80, 56), t=1.4):
        for (lx, ld) in ((x + .6, d + .6), (x + w - t - .6, d + .6), (x + .6, d + dp - t - .6), (x + w - t - .6, d + dp - t - .6)): B(lx, ld, t, t, h, c, sh=(.9, .8))
    def stool(x, d): B(x, d, 6, 6, 5, (176, 132, 90)); sc.jobs.append((d, lambda: sc.d.ellipse([sc.P(x + 3, d + 3, 5)[0] - 4, sc.P(x + 3, d + 3, 5)[1] - 2, sc.P(x + 3, d + 3, 5)[0] + 4, sc.P(x + 3, d + 3, 5)[1] + 2], fill=(196, 152, 106), outline=(140, 100, 68))))
    def glows(*g):
        for (gx, gd, r, col, pw) in g: sc.glow(gx, gd, r, col=col, power=pw)
    def round_window(cx, cz, r, light):
        FR(cx - r - 1.5, cx + r + 1.5, cz - r - 1, cz + r + 1, (82, 60, 44)); FR(cx - r, cx + r, cz - r + .5, cz + r - .5, light)
        FR(cx - .5, cx + .5, cz - r + .5, cz + r - .5, (82, 60, 44)); FR(cx - r, cx + r, cz - .5, cz + .5, (82, 60, 44))
    if key == 'tree_main':
        frame_front(44, 62); opening_left(22, 38)
        round_window(60, 32, 7, (214, 230, 250))                               # 줄기에 뚫린 둥근 창(눈빛)
        # 난로(철)와 연통: 뒤쪽 왼쪽
        B(10, 44, 14, 12, 14, (66, 62, 70)); FR(12, 22, 3, 11, (28, 26, 32), d=44); FR(14, 20, 4, 8, (236, 170, 90), d=44)
        B(15, 49, 3, 3, 36, (80, 76, 84), z0=14, sh=(.9, .8))
        # 책장(줄기 벽에 짜 넣음), 둥근 탁자와 그루터기 의자, 잠자리
        B(74, 54, 26, 6, 34, (150, 112, 78)); FR(75, 99, 9, 10, (120, 88, 60), d=54); FR(75, 99, 21, 22, (120, 88, 60), d=54)
        for k, c in enumerate(((176, 90, 80), (90, 120, 150), (210, 180, 90), (110, 150, 110), (150, 110, 150), (200, 120, 90))): FR(76 + k * 4, 79 + k * 4, 10.5, 19.5, c, d=54); FR(76 + k * 3.5, 78.6 + k * 3.5, 22.5, 31.5, c, d=54)
        legs(40, 26, 20, 14, 10, t=1.6); B(40, 26, 20, 14, 2, (186, 140, 96), z0=10); B(48, 31, 3, 3, 4, (240, 232, 190), z0=12, sh=(.9, .8))
        stool(34, 18); stool(60, 22); stool(46, 42)
        B(8, 8, 26, 26, 5, (140, 100, 70)); B(9, 9, 24, 24, 3.4, (214, 196, 160), z0=5, sh=(.9, .8)); B(9, 9, 24, 14, 1.2, (176, 100, 90), z0=8.4, sh=(.9, .8)); B(10, 24, 11, 6, 2.4, (240, 236, 228), z0=8.6, sh=(.92, .84))
        sc.jobs.append((90, lambda: sc.d.ellipse([sc.P(70, 24, 0)[0] - 16, sc.P(70, 24, 0)[1] - 8, sc.P(70, 24, 0)[0] + 16, sc.P(70, 24, 0)[1] + 8], fill=(110, 70, 60))))
        glows((16, 44, 32, (255, 188, 110), .4), (50, 32, 46, (255, 226, 160), .3), (60, 38, 40, (214, 230, 250), .14))
    else:
        opening_right_door(14, 30)
        B(6, 36, 10, 10, 14, (150, 112, 78)); B(18, 38, 9, 9, 10, (160, 120, 84)); B(30, 36, 12, 8, 8, (170, 130, 90)); B(31, 37, 10, 6, 6, (180, 140, 96), z0=8)
        B(46, 38, 20, 8, 36, (150, 112, 78))
        for z in (10, 20, 30): FR(47, 65, z, z + 1, (110, 80, 56), d=38)
        for k in range(5): FR(48 + k * 3.4, 50.4 + k * 3.4, 11, 17, ((210, 90, 90), (90, 140, 180), (220, 190, 110), (120, 160, 120), (170, 120, 170))[k], d=38); FR(48 + k * 3.4, 50.4 + k * 3.4, 21, 27, ((120, 160, 120), (210, 90, 90), (170, 120, 170), (220, 190, 110), (90, 140, 180))[k], d=38)
        FR(24, 28, 24, 52, (200, 176, 130), d=D); FR(34, 38, 24, 52, (200, 176, 130), d=D)
        for z in range(26, 52, 5): FR(24, 38, z, z + 1, (176, 150, 104), d=D)                                    # 밧줄 사다리
        round_window(52, 40, 5, (214, 230, 250))
        glows((22, 22, 40, (255, 214, 150), .3))
    dep = Image.new('L', sc.img.size, 255)                                       # 깊이 지도: 그리는 일마다 바뀐 화소에 그 깊이를 적는다(가구 뒤로 아이가 가려진다)
    for depth, f in sorted(sc.jobs, key=lambda j: -j[0]):
        before = sc.img.copy(); f()
        if depth < D - .5:
            diff = ImageChops.difference(sc.img, before).convert('L').point(lambda v: 255 if v else 0)
            dep.paste(int(max(0, min(254, round((depth + 2) * 3)))), (0, 0), diff)
    sc.jobs = []; img = sc.img
    return img, dep, {'W': W, 'D': D, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': sc.CW, 'CH': sc.CH, 'rects': rects, 'exits': EXITS[key], 'start': [W / 2, 8], 'objects': OBJECTS.get(key, []), 'puzzle': PUZZLE.get(key)}

def main():
    nav = {}
    for k in ROOM:
        im, dep, meta = make(k); nav[k] = meta
        im.save(os.path.join(OUT, 'tree_%s.png' % k)); dep.save(os.path.join(OUT, 'tree_%s_depth.png' % k)); im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(OUT, 'tree_%s_x3.png' % k))
    json.dump(nav, open(os.path.join(OUT, 'tree_nav.json'), 'w'), ensure_ascii=False); print('tree ok', {k: v['CW'] for k, v in nav.items()})
if __name__ == '__main__': main()
