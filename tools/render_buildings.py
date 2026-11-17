#!/usr/bin/env python3
"""건물 안 4채(사선 3차원 방, 집 안·나무 속 방과 같은 방식). 퍼즐 기믹은 전부 건물 안에 둔다.
 cabin_main 호숫가 통나무집 안(난로·탁자·침대) / cabin_back 곳간(양동이 속 열쇠)  — 쪽지 → 열쇠 → 잠긴 뒷문
 library    도서관(책장·독서대 책 3권)                                              — 쪽지 → 알맞은 책 고르기 → 책장 문이 열림
 office     폐 놀이공원 매표소(창구·개찰구·레버 3개)                                — 쪽지 → 레버 켜고 끄기 → 개찰구가 열림
사용: python3 tools/render_buildings.py -> maps/out/bld_<방>.png, _depth.png, _x3.png, bld_nav.json"""
import json, os, random, sys
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT
H = 54
ROOM = {'cabin_main': (100, 58, 'log'), 'cabin_back': (64, 44, 'log'), 'library': (108, 62, 'lib'), 'office': (92, 56, 'booth')}
WOOD, WOOD_D = (176, 130, 90), (140, 100, 68)
EXITS = {
    'cabin_main': [{'zone': (44, 62, 0, 3), 'to': 'lake_3', 'spawn': None, 'door': True, 'indoor': True},
                   {'zone': (0, 5, 22, 38), 'to': 'cabin_back', 'spawn': (52, 22)},
                   {'zone': (40, 58, 55, 58), 'to': 'library', 'spawn': (54, 8), 'need': 'cabin_key', 'side': 'back'}],
    'cabin_back': [{'zone': (59, 64, 14, 30), 'to': 'cabin_main', 'spawn': (10, 30)}],
    'library': [{'zone': (46, 64, 0, 3), 'to': 'cabin_main', 'spawn': (49, 48)},
                {'zone': (86, 102, 59, 62), 'to': 'office', 'spawn': (45, 8), 'need': 'lib_open', 'side': 'back', 'open': {'x0': 86, 'x1': 102, 'z1': 40}}],
    'office': [{'zone': (36, 54, 0, 3), 'to': 'library', 'spawn': (94, 52)},
               {'zone': (62, 80, 53, 56), 'to': 'park', 'spawn': None, 'need': 'office_open', 'side': 'back', 'open': {'x0': 62, 'x1': 80, 'z1': 30}, 'endMsg': '개찰구 너머 — 여기서부터는 아직 만들지 않았어요'}],
}
OBJECTS = {}; PUZZLE = {}                                                    # 퍼즐은 tools/puzzles_data.py(두 시선, §31)로 옮겼다

def make(key):
    W, D, style = ROOM[key]; sc = Scene(W, D, H + 2); sc.img.paste((24, 20, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    def floor(x, d):
        if style == 'booth': return (236, 214, 200) if (int(x // 8) + int(d // 8)) % 2 == 0 else (206, 120, 130)
        if style == 'lib': return (96, 70, 56) if d % 10 > .9 else (84, 60, 48) if int(d // 10) % 2 else (92, 66, 52)
        return WOOD_D if d % 8 < .8 else WOOD if int(d // 8) % 2 == 0 else (166, 120, 82)
    sc.floor(floor)
    base_w = {'log': (108, 78, 54), 'lib': (46, 66, 62), 'booth': (232, 196, 120)}[style]
    sc.poly([(0, 0, -5), (W, 0, -5), (W, 0, 0), (0, 0, 0)], dk(base_w, .8)); sc.poly([(W, 0, -5), (W, D, -5), (W, D, 0), (W, 0, 0)], dk(base_w, .6))
    def front(x0, x1, z0, z1, col, d=D): sc.poly([(x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)], col)
    def left(d0, d1, z0, z1, col, x=0): sc.poly([(x, d0, z0), (x, d1, z0), (x, d1, z1), (x, d0, z1)], col)
    if style == 'log':                                                           # 통나무 벽: 가로로 쌓은 통나무와 어두운 이음
        for z in range(0, H, 6):
            c = (122, 88, 60) if (z // 6) % 2 == 0 else (108, 76, 52); front(0, W, z, z + 5, c); front(0, W, z + 5, z + 6, (70, 48, 34)); left(0, D, z, z + 5, dk(c, .92)); left(0, D, z + 5, z + 6, (62, 42, 30))
    elif style == 'lib':                                                         # 짙은 초록 벽지 + 아랫부분 나무 판벽
        for xx in range(0, W): front(xx, xx + 1, 14, H, (46, 66, 62) if (xx // 5) % 2 == 0 else (52, 74, 68)); front(xx, xx + 1, 0, 14, (96, 66, 46) if xx % 6 else (74, 50, 36))
        for dd in range(0, D): left(dd, dd + 1, 14, H, (38, 56, 52) if (dd // 5) % 2 == 0 else (44, 62, 58)); left(dd, dd + 1, 0, 14, (82, 56, 40) if dd % 6 else (62, 42, 30))
        front(0, W, 14, 16, (150, 112, 70)); left(0, D, 14, 16, (130, 96, 60))
    else:                                                                        # 매표소: 분홍·크림 줄무늬 벽 + 노란 띠
        for xx in range(0, W): front(xx, xx + 1, 8, H, (240, 206, 196) if (xx // 6) % 2 == 0 else (222, 130, 144)); front(xx, xx + 1, 0, 8, (150, 110, 90))
        for dd in range(0, D): left(dd, dd + 1, 8, H, (226, 188, 180) if (dd // 6) % 2 == 0 else (200, 114, 130)); left(dd, dd + 1, 0, 8, (120, 88, 72))
        front(0, W, H - 5, H, (250, 214, 120)); left(0, D, H - 5, H, (226, 192, 104))
    front(0, W, 0, 3, dk(base_w, .7)); left(0, D, 0, 3, dk(base_w, .7))
    def frame_front(x0, x1):
        sc.poly([(x0, 0, 0), (x1, 0, 0), (x1, 5, 0), (x0, 5, 0)], (228, 214, 174))
        sc.jobs.append((-1, lambda: [sc.box(x0 - 1.5, 0, 1.5, 2, 6, (220, 200, 160), (226, 206, 166), (180, 160, 124)), sc.box(x1, 0, 1.5, 2, 6, (220, 200, 160), (226, 206, 166), (180, 160, 124))]))
    def opening_left(d0, d1):
        left(d0, d1, 0, 40, (40, 30, 28)); left(d0, d1, 0, 8, (90, 66, 48))
        for (a, b, z0, z1) in ((d0 - 1.5, d0, 0, 41.5), (d1, d1 + 1.5, 0, 41.5), (d0 - 1.5, d1 + 1.5, 40, 41.5)): left(a, b, z0, z1, (214, 196, 156))
    def opening_right_door(d0, d1): sc.poly([(W - 5, d0, 0), (W, d0, 0), (W, d1, 0), (W - 5, d1, 0)], (228, 214, 174))
    rects = []
    def B(x, d, w, dp, h, c, z0=0, sh=(.86, .72)):
        if z0 < 28: rects.append((round(x, 1), round(d, 1), round(w, 1), round(dp, 1)))
        sc.jobs.append((d, lambda: sc.box(x, d, w, dp, h, c, dk(c, sh[0]), dk(c, sh[1]), z0=z0)))
    def FR(x0, x1, z0, z1, col, d=D): sc.jobs.append(((d + .3) if d == D else (d - .3), lambda: front(x0, x1, z0, z1, col, d=d)))
    def legs(x, d, w, dp, h, c=(110, 80, 56), t=1.4):
        for (lx, ld) in ((x + .6, d + .6), (x + w - t - .6, d + .6), (x + .6, d + dp - t - .6), (x + w - t - .6, d + dp - t - .6)): B(lx, ld, t, t, h, c, sh=(.9, .8))
    def stool(x, d, c=(176, 132, 90)): B(x, d, 6, 6, 5, c); sc.jobs.append((d, lambda: sc.d.ellipse([sc.P(x + 3, d + 3, 5)[0] - 4, sc.P(x + 3, d + 3, 5)[1] - 2, sc.P(x + 3, d + 3, 5)[0] + 4, sc.P(x + 3, d + 3, 5)[1] + 2], fill=dk(c, 1.12), outline=dk(c, .8))))
    def glows(*g):
        for (gx, gd, r, col, pw) in g: sc.glow(gx, gd, r, col=col, power=pw)
    def rug(cx, cd, rx, ry, col, col2=None):
        def f():
            X, Y = sc.P(cx, cd, 0); sc.d.ellipse([X - rx, Y - ry, X + rx, Y + ry], fill=col)
            if col2: sc.d.ellipse([X - rx + 4, Y - ry + 2, X + rx - 4, Y + ry - 2], outline=col2)
        sc.jobs.append((90, f))
    def window(x0, x1, z0, z1, light, d=D, frame=(210, 190, 150)):
        FR(x0 - 1.5, x1 + 1.5, z0 - 1.5, z1 + 1.5, frame); FR(x0, x1, z0, z1, light); FR((x0 + x1) / 2 - .5, (x0 + x1) / 2 + .5, z0, z1, frame); FR(x0, x1, (z0 + z1) / 2 - .5, (z0 + z1) / 2 + .5, frame)
    def shelf(x, d, w, dp, h, rows, seed, depth_face=None):
        B(x, d, w, dp, h, (112, 78, 52)); rr = random.Random(seed); fd = d
        for r in range(rows):
            z0 = 3 + r * (h - 4) / rows; z1 = z0 + (h - 4) / rows - 1.6; FR(x + 1, x + w - 1, z0, z1, (44, 30, 22), d=fd)
            xx = x + 1.5
            while xx < x + w - 3:
                bw = rr.choice((1.4, 1.8, 2.2, 2.8)); bh = rr.uniform(.55, .95) * (z1 - z0); c = rr.choice(((176, 90, 80), (90, 120, 150), (210, 180, 90), (110, 150, 110), (150, 110, 150), (200, 120, 90), (80, 100, 80)))
                FR(xx, xx + bw, z0, z0 + bh, c, d=fd); xx += bw + .3

    if key == 'cabin_main':
        frame_front(44, 62); opening_left(22, 38)
        front(40, 58, 0, 34, (92, 64, 44)); front(40, 58, 33, 35, (60, 40, 30)); front(39, 40, 0, 35, (214, 196, 156)); front(58, 59, 0, 35, (214, 196, 156)); front(39, 59, 35, 36.5, (214, 196, 156)); front(54, 56, 16, 18, (230, 190, 90)); front(41, 57, 16, 17, (60, 40, 30))
        front(46, 52, 24, 28, (214, 150, 60)); front(48, 50, 25, 27, (50, 40, 30))                                    # 잠긴 뒷문: 자물쇠
        window(64, 74, 16, 34, (170, 198, 232), frame=(210, 186, 140))
        left(44, 52, 14, 40, (84, 68, 70)); left(44, 52, 36, 40, (140, 120, 90)); left(5, 9, 18, 40, (190, 170, 130)); left(12, 15, 22, 34, (176, 150, 110))   # 외투와 낚싯대
        B(8, 44, 18, 14, 30, (150, 146, 150)); FR(12, 22, 2, 14, (28, 24, 26), d=44); FR(14, 20, 3, 9, (246, 170, 80), d=44); FR(8.5, 25.5, 14, 16, (120, 116, 122), d=44)
        legs(62, 24, 20, 14, 10, t=1.6); B(62, 24, 20, 14, 2, (186, 140, 96), z0=10); B(66, 29, 3, 3, 4, (240, 232, 190), z0=12, sh=(.9, .8))
        stool(54, 26); stool(86, 28); stool(68, 40)
        B(76, 42, 22, 14, 6, (140, 100, 70)); B(77, 43, 20, 12, 4, (200, 90, 80), z0=6, sh=(.9, .8)); B(77, 43, 8, 6, 2, (240, 236, 228), z0=9.5, sh=(.92, .84))
        rug(34, 32, 15, 7, (126, 86, 70), (176, 130, 100))
        glows((17, 44, 34, (255, 178, 100), .42), (67, 31, 30, (255, 226, 160), .3), (69, 50, 24, (190, 210, 240), .12))
    elif key == 'cabin_back':
        opening_right_door(14, 30)
        shelf(6, 36, 24, 6, 34, 3, 3); B(34, 36, 9, 9, 12, (130, 96, 66)); B(45, 34, 9, 9, 14, (124, 90, 62)); FR(35, 42, 6, 7, (80, 56, 40), d=36); B(5, 6, 14, 10, 9, (150, 112, 78)); B(5, 20, 14, 10, 7, (160, 120, 84))
        B(18, 12, 8, 8, 8, (122, 134, 156)); B(19, 13, 6, 6, 1, (30, 40, 56), z0=8, sh=(1, 1))
        FR(24, 44, 18, 40, (160, 150, 120)); front(24, 44, 18, 20, (96, 70, 50))                                  # 벽에 건 그물
        for k in range(0, 21, 4): front(24 + k, 24 + k + .7, 18, 40, (110, 100, 78))
        for k in range(0, 22, 4): front(24, 44, 18 + k, 18.7 + k, (110, 100, 78))
        window(50, 58, 24, 36, (170, 198, 232), frame=(210, 186, 140))
        glows((20, 18, 36, (255, 210, 150), .28), (54, 30, 26, (190, 210, 240), .14))
    elif key == 'library':
        frame_front(46, 64)
        shelf(4, 54, 76, 8, 46, 4, 11)
        front(86, 102, 0, 44, (84, 56, 40)); front(86, 102, 40, 44, (70, 46, 34)); front(93.4, 94.6, 0, 40, (60, 40, 30)); front(90, 92, 18, 21, (230, 190, 90))   # 책장 문
        left(26, 40, 18, 44, (24, 30, 64)); left(26, 40, 44, 46, (170, 130, 80)); left(26, 40, 16, 18, (170, 130, 80)); left(25, 26, 16, 46, (170, 130, 80)); left(40, 41, 16, 46, (170, 130, 80)); left(33, 33.8, 18, 44, (170, 130, 80)); left(28, 31, 34, 38, (250, 246, 220))
        legs(44, 28, 26, 12, 11, t=1.8); B(44, 28, 26, 12, 2, (120, 84, 56), z0=11); B(56, 32, 2, 2, 3, (240, 220, 140), z0=13, sh=(.9, .8)); B(48, 31, 6, 5, 1, (214, 200, 160), z0=13, sh=(.95, .9))
        stool(52, 42, (120, 84, 56))
        for (px, pd) in ((12, 14), (12, 44), (94, 24)): B(px, pd, 6, 6, 10, (130, 94, 64)); B(px - 1, pd - 1, 8, 8, 1.4, (110, 76, 50), z0=10)
        rug(54, 38, 28, 12, (92, 52, 56), (170, 130, 96))
        glows((57, 32, 30, (255, 220, 150), .32), (33, 6, 40, (160, 180, 240), .12))
    else:
        frame_front(36, 54)
        B(8, 46, 50, 8, 16, (230, 120, 130)); B(8, 46, 50, 8, 2, (250, 214, 120), z0=16)
        window(14, 52, 20, 36, (40, 50, 90), frame=(250, 214, 120))
        for k in range(5): FR(18 + k * 7, 20.4 + k * 7, 22, 25 + (k % 3) * 2, (250, 220, 130), d=D)               # 창구 안쪽의 표 더미
        front(0, 0, 0, 0, (0, 0, 0))
        for gx in (58, 85): B(gx, 49, 3, 4, 16, (250, 214, 120)); B(gx + .5, 49.5, 2, 3, 3, (230, 120, 130), z0=16)
        front(62, 80, 0, 26, (60, 54, 70)); front(61, 62, 0, 28, (250, 214, 120)); front(80, 81, 0, 28, (250, 214, 120)); front(61, 81, 28, 30, (250, 214, 120)); front(62, 80, 20, 22, (200, 60, 70)); front(66, 76, 22, 26, (250, 240, 200))   # 개찰구 막대(닫힘)
        left(10, 24, 18, 42, (250, 214, 120)); left(11, 23, 19, 41, (90, 150, 190)); left(14, 20, 24, 36, (240, 210, 100)); left(16, 18, 26, 34, (210, 70, 90)); left(28, 40, 20, 40, (250, 214, 120)); left(29, 39, 21, 39, (216, 120, 140)); left(31, 37, 25, 35, (250, 240, 200))
        stool(24, 38, (226, 150, 100)); stool(66, 38, (226, 150, 100))
        glows((33, 40, 40, (255, 214, 150), .3), (71, 50, 30, (255, 230, 170), .22), (72, 28, 30, (250, 230, 160), .12))
    dep = Image.new('L', sc.img.size, 255)
    for depth, f in sorted(sc.jobs, key=lambda j: -j[0]):
        before = sc.img.copy(); f()
        if depth < D - .5:
            diff = ImageChops.difference(sc.img, before).convert('L').point(lambda v: 255 if v else 0)
            dep.paste(int(max(0, min(254, round((depth + 2) * 3)))), (0, 0), diff)
    sc.jobs = []
    return sc.img, dep, {'W': W, 'D': D, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': sc.CW, 'CH': sc.CH, 'rects': rects, 'exits': EXITS[key], 'start': [W / 2, 8], 'objects': OBJECTS.get(key, []), 'puzzle': PUZZLE.get(key)}

def main():
    nav = {}
    for k in ROOM:
        im, dep, meta = make(k); nav[k] = meta
        im.save(os.path.join(OUT, 'bld_%s.png' % k)); dep.save(os.path.join(OUT, 'bld_%s_depth.png' % k)); im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(OUT, 'bld_%s_x3.png' % k))
    json.dump(nav, open(os.path.join(OUT, 'bld_nav.json'), 'w'), ensure_ascii=False); print('bld ok', {k: v['CW'] for k, v in nav.items()})
if __name__ == '__main__': main()
