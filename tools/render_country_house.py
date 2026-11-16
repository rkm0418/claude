#!/usr/bin/env python3
"""가을 세계의 집 안 — 사용자 절개도(가운데 거실 + 위 부엌 + 왼쪽 침실 + 오른쪽 서재). 방 하나씩 따로 보이고, 문으로 넘어가면 다음 방 장면으로 바뀐다.
사선 3차원 시점(아이 방과 같은 투영), 뒤·왼쪽 벽은 높고 오른쪽·앞은 잘라낸 단면. 가구는 작고 얇은 다리·매트한 단색 면으로 깔끔하게.
문: 거실(왼쪽 벽 -> 침실, 뒷벽 -> 부엌, 오른쪽 -> 서재, 앞 중앙 = 현관) / 부엌(앞) / 침실(오른쪽) / 서재(왼쪽 벽).
사용: python3 tools/render_country_house.py -> maps/out/house_<방>.png, house_sheet.png (+_x3)"""
import math, os, random, sys
import json
from PIL import Image, ImageChops, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, dk, OUT

H = 52
OAK, OAK_D, OAK_L = (200, 164, 120), (170, 134, 96), (216, 184, 142)
WHITE, GRAY = (236, 234, 228), (150, 152, 158)
ROOM = {  # 크기 (W, D), 벽지색, 바닥 종류
    'living':  ((112, 64), (236, 226, 204), 'wood'), 'kitchen': ((80, 44), (214, 228, 214), 'tile'),
    'bedroom': ((60, 44), (212, 218, 226), 'wood'), 'study': ((52, 40), (230, 216, 212), 'wood'),
}

# 문(나가는 곳): zone = 바닥 좌표 (x0, x1, d0, d1) 안에 들어서면 to 방의 spawn (x, d) 로 넘어간다
EXITS = {
    'living':  [{'zone': (0, 5, 30, 46), 'to': 'bedroom', 'spawn': (52, 20)}, {'zone': (74, 90, 60, 64), 'to': 'kitchen', 'spawn': (59, 7)},
                {'zone': (107, 112, 12, 26), 'to': 'study', 'spawn': (8, 15)}, {'zone': (70, 86, 0, 3), 'to': None, 'spawn': None}],
    'kitchen': [{'zone': (51, 67, 0, 3), 'to': 'living', 'spawn': (82, 56)}],
    'bedroom': [{'zone': (56, 60, 13, 28), 'to': 'living', 'spawn': (9, 38)}],
    'study':   [{'zone': (0, 4, 8, 22), 'to': 'living', 'spawn': (103, 19)}],
}

def make(key):
    (W, D), wc, fl = ROOM[key]; sc = Scene(W, D, H + 2); sc.img.paste((30, 22, 24), (0, 0, sc.CW, sc.CH)); sc.d = ImageDraw.Draw(sc.img)
    # 바닥: 연한 오크 판(가로 줄, 이음 불규칙) / 타일(베이지 격자). 질감 노이즈 없이 매트하게
    def floor(x, d):
        if fl == 'tile': return (206, 200, 184) if (x % 10 < 1 or d % 10 < 1) else (228, 222, 206)
        if d % 9 < .8: return OAK_D
        if x % 34 < .8 and int(d // 9) % 2: return OAK_D
        return OAK if int(d // 9) % 2 == 0 else OAK_L
    sc.floor(floor)
    sc.poly([(0, 0, -5), (W, 0, -5), (W, 0, 0), (0, 0, 0)], (96, 70, 50)); sc.poly([(W, 0, -5), (W, D, -5), (W, D, 0), (W, 0, 0)], (72, 52, 38))
    # 벽(뒤·왼쪽): 단색 벽지 + 연한 걸레받이 + 윗띠
    def front(x0, x1, z0, z1, col, d=D): sc.poly([(x0, d, z0), (x1, d, z0), (x1, d, z1), (x0, d, z1)], col)
    def left(d0, d1, z0, z1, col, x=0): sc.poly([(x, d0, z0), (x, d1, z0), (x, d1, z1), (x, d0, z1)], col)
    front(0, W, 0, H, wc); front(0, W, 0, 4, WHITE); front(0, W, H - 3, H, dk(wc, .86))
    left(0, D, 0, H, dk(wc, .94)); left(0, D, 0, 4, WHITE); left(0, D, H - 3, H, dk(wc, .8))
    # 문 틈: 뒷벽/왼쪽 벽은 어두운 열린 문(문틀 + 다음 방의 따뜻한 빛), 잘린 오른쪽·앞은 문틀 기둥과 문턱
    def opening_back(x0, x1):
        front(x0, x1, 0, 42, (42, 34, 30)); front(x0 + 1, x1 - 1, 0, 8, (92, 70, 52))
        for (a, b, z0, z1) in ((x0 - 1.5, x0, 0, 43.5), (x1, x1 + 1.5, 0, 43.5), (x0 - 1.5, x1 + 1.5, 42, 43.5)): front(a, b, z0, z1, (246, 242, 234))
    def opening_left(d0, d1):
        left(d0, d1, 0, 42, (42, 34, 30)); left(d0, d1, 0, 8, (92, 70, 52))
        for (a, b, z0, z1) in ((d0 - 1.5, d0, 0, 43.5), (d1, d1 + 1.5, 0, 43.5), (d0 - 1.5, d1 + 1.5, 42, 43.5)): left(a, b, z0, z1, (246, 242, 234))
    def frame_right(d0, d1):                                   # 오른쪽 가장자리(잘린 쪽)의 문: 밝은 문턱 띠 + 문기둥 밑동만
        sc.poly([(W - 5, d0, 0), (W, d0, 0), (W, d1, 0), (W - 5, d1, 0)], (232, 208, 166))
        sc.jobs.append((d0, lambda: [sc.box(W - 2, d0 - 1.5, 2, 1.5, 6, (246, 242, 234), (246, 242, 234), (206, 202, 194)), sc.box(W - 2, d1, 2, 1.5, 6, (246, 242, 234), (246, 242, 234), (206, 202, 194))]))
    def frame_front(x0, x1):                                   # 앞 가장자리의 문
        sc.poly([(x0, 0, 0), (x1, 0, 0), (x1, 5, 0), (x0, 5, 0)], (232, 208, 166))
        sc.jobs.append((-1, lambda: [sc.box(x0 - 1.5, 0, 1.5, 2, 6, (246, 242, 234), (246, 242, 234), (206, 202, 194)), sc.box(x1, 0, 1.5, 2, 6, (246, 242, 234), (246, 242, 234), (206, 202, 194))]))
    # ---- 가구 도우미(뒤 d 큰 것부터 그려지게 jobs 로) ----
    rects = []                                                 # 이동을 막는 가구 바닥 자리 (x, d, w, dp)
    def B(x, d, w, dp, h, c, z0=0, sh=(.86, .72)):
        if z0 < 28: rects.append((round(x, 1), round(d, 1), round(w, 1), round(dp, 1)))
        sc.jobs.append((d, lambda: sc.box(x, d, w, dp, h, c, dk(c, sh[0]), dk(c, sh[1]), z0=z0)))
    def legs(x, d, w, dp, h, c=(120, 96, 72), t=1.4):
        for (lx, ld) in ((x + .6, d + .6), (x + w - t - .6, d + .6), (x + .6, d + dp - t - .6), (x + w - t - .6, d + dp - t - .6)): B(lx, ld, t, t, h, c, sh=(.9, .8))
    def FR(x0, x1, z0, z1, col, d=D): sc.jobs.append(((d + .3) if d == D else (d - .3), lambda: front(x0, x1, z0, z1, col, d=d)))
    def LF(d0, d1, z0, z1, col): left(d0, d1, z0, z1, col)
    def table(x, d, w, dp, h, top=OAK_L):
        legs(x, d, w, dp, h - 2); B(x, d, w, dp, 2, top, z0=h - 2)
    def chair(x, d, far):
        legs(x, d, 7, 7, 7, t=1.2); B(x, d, 7, 7, 1.6, OAK_L, z0=7); B(x, d + (5.6 if far else 0), 7, 1.4, 9, OAK, z0=8.6)
    def sofa(x, d, w, back_near=True):
        c = (104, 134, 140); cl = (122, 152, 158)
        legs(x, d, w, 11, 2, c=(90, 78, 66))
        B(x, d, w, 11, 5, c, z0=2); B(x + 3, d + (3 if back_near else 0), w - 6, 8, 2.4, cl, z0=7)
        B(x, d + (0 if back_near else 8.2), w, 2.8, 11, c, z0=2); B(x, d + 2.8 if False else d, 3, 11, 9, dk(c, .94), z0=2) if False else None
        B(x, d, 2.6, 11, 9, c, z0=2); B(x + w - 2.6, d, 2.6, 11, 9, c, z0=2)
    def rug(x, d, w, dp, c):
        sc.jobs.append((d + 100, lambda: sc.poly([(x, d, 0), (x + w, d, 0), (x + w, d + dp, 0), (x, d + dp, 0)], c)))
        sc.jobs.append((d + 99, lambda: sc.poly([(x + 1.5, d + 1.5, 0), (x + w - 1.5, d + 1.5, 0), (x + w - 1.5, d + dp - 1.5, 0), (x + 1.5, d + dp - 1.5, 0)], dk(c, .9))))
    def plant(x, d):
        B(x, d, 5, 5, 5, (176, 130, 100), sh=(.88, .74)); sc.jobs.append((d + 1, lambda: [sc.d.ellipse([sc.P(x + 2.5, d + 2.5, 11)[0] - 5, sc.P(x + 2.5, d + 2.5, 11)[1] - 5, sc.P(x + 2.5, d + 2.5, 11)[0] + 5, sc.P(x + 2.5, d + 2.5, 11)[1] + 4], fill=(96, 140, 98)), sc.d.ellipse([sc.P(x + 2.5, d + 2.5, 14)[0] - 3, sc.P(x + 2.5, d + 2.5, 14)[1] - 3, sc.P(x + 2.5, d + 2.5, 14)[0] + 3, sc.P(x + 2.5, d + 2.5, 14)[1] + 2], fill=(116, 162, 116))]))
    def window_back(x0, x1, z0=20, z1=42, light=(246, 210, 150)):
        FR(x0 - 1.5, x1 + 1.5, z0 - 1.5, z1 + 1.5, WHITE); FR(x0, x1, z0, z1, light); FR((x0 + x1) / 2 - .5, (x0 + x1) / 2 + .5, z0, z1, WHITE); FR(x0, x1, (z0 + z1) / 2 - .5, (z0 + z1) / 2 + .5, WHITE)
        FR(x0 - 4, x0 - 1, z0 - 3, z1 + 5, (196, 150, 138)); FR(x1 + 1, x1 + 4, z0 - 3, z1 + 5, (196, 150, 138))
    def window_left(d0, d1, z0=20, z1=42, light=(246, 210, 150)):
        left(d0 - 1.5, d1 + 1.5, z0 - 1.5, z1 + 1.5, WHITE); left(d0, d1, z0, z1, light); left((d0 + d1) / 2 - .5, (d0 + d1) / 2 + .5, z0, z1, WHITE); left(d0, d1, (z0 + z1) / 2 - .5, (z0 + z1) / 2 + .5, WHITE)
        left(d0 - 4, d0 - 1, z0 - 3, z1 + 5, (196, 150, 138)); left(d1 + 1, d1 + 4, z0 - 3, z1 + 5, (196, 150, 138))
    def pic(x0, x1, z0, z1, col): FR(x0 - 1, x1 + 1, z0 - 1, z1 + 1, WHITE); FR(x0, x1, z0, z1, col)
    def glows(*g):
        for (gx, gd, r, col, pw) in g: sc.glow(gx, gd, r, col=col, power=pw)

    if key == 'living':
        opening_left(30, 46); opening_back(74, 90); frame_right(12, 26); frame_front(70, 86)
        window_back(10, 34, light=(246, 214, 160)); pic(44, 56, 26, 38, (150, 170, 150)); pic(58, 68, 28, 38, (196, 160, 140))
        B(6, 54, 30, 9, 8, (138, 110, 84), z0=3); legs(6, 54, 30, 9, 3, c=(110, 88, 66)); B(10, 56, 22, 1.4, 12, (46, 48, 52), z0=11, sh=(.9, .8)); B(18, 56.4, 6, 1.4, 3, (60, 62, 66), z0=8, sh=(.9, .8))    # TV장 + 얇은 TV
        rug(6, 18, 44, 30, (176, 98, 84))
        sofa(8, 8, 34, True)
        table(20, 28, 16, 9, 6, top=OAK_L)
        table(54, 30, 22, 13, 14); chair(57, 22, False); chair(70, 22, False); chair(57, 43, True); chair(70, 43, True)
        plant(100, 52); B(98, 6, 4, 4, 14, (90, 80, 70), sh=(.9, .8)); B(96, 4, 8, 8, 2, (240, 224, 170), z0=14, sh=(.92, .82))
        glows((28, 30, 50, (255, 226, 160), .32), (82, 40, 34, (255, 226, 170), .18))
    elif key == 'kitchen':
        frame_front(51, 67)
        window_back(14, 38, light=(246, 218, 170))
        B(6, 34, 46, 10, 12, (232, 226, 212)); B(6, 34, 46, 10, 1.6, (176, 178, 184), z0=12, sh=(.9, .8)); B(22, 37, 12, 5, .8, (110, 116, 126), z0=13.5, sh=(.9, .8)); B(27, 41, 1.2, 1.2, 5, (170, 174, 182), z0=13, sh=(.9, .8))   # 하부장+상판+싱크+수도
        B(6, 38, 46, 6, 8, (210, 204, 190), z0=34, sh=(.88, .74)) if False else None
        B(58, 32, 12, 11, 36, (236, 238, 240)); FR(59, 69, 22, 23, (170, 172, 180), d=32); FR(66, 67.2, 26, 34, (150, 152, 160), d=32); FR(66, 67.2, 6, 16, (150, 152, 160), d=32)
        table(14, 12, 22, 12, 14); chair(16, 5, False); chair(28, 5, False); chair(16, 24, True); chair(28, 24, True)
        B(20, 16, 4, 4, 1.4, (240, 236, 226), z0=14, sh=(.92, .82)); B(27, 17, 3, 3, 3, (206, 118, 96), z0=14, sh=(.9, .78))
        glows((38, 22, 44, (255, 228, 170), .34))
    elif key == 'bedroom':
        frame_right(13, 28); window_left(14, 30, light=(236, 206, 160))
        B(6, 14, 25, 30, 5, (170, 134, 100)); B(7, 14, 23, 29, 3.4, (226, 232, 238), z0=5, sh=(.9, .8)); B(7, 14, 23, 17, 1.2, (170, 190, 208), z0=8.2, sh=(.9, .8)); B(8, 38, 9, 5, 2.4, (248, 248, 246), z0=8.4, sh=(.92, .84)); B(19, 38, 9, 5, 2.4, (248, 248, 246), z0=8.4, sh=(.92, .84))
        B(6, 42, 25, 2, 14, (150, 116, 86), z0=0)                                       # 머리판
        B(34, 38, 8, 6, 8, (180, 144, 108)); legs(34, 38, 8, 6, 3, c=(130, 100, 76), t=1.2); B(37, 40, 2, 2, 5, (226, 214, 174), z0=8, sh=(.9, .8)); B(35.5, 39.5, 5, 5, 3, (248, 238, 196), z0=12, sh=(.92, .82))
        B(43, 33, 15, 10, 21, (168, 170, 176)); B(43, 33, 15, 10, 1.2, (186, 188, 194), z0=21, sh=(.92, .84))                                  # 회색 서랍장
        for k in range(4): FR(44, 57, 1.5 + k * 5, 5.5 + k * 5, (156, 158, 164), d=33); FR(48.5, 52.5, 3 + k * 5, 3.8 + k * 5, (96, 98, 104), d=33)
        rug(34, 8, 20, 14, (182, 160, 150))
        glows((24, 24, 44, (255, 226, 170), .3))
    elif key == 'study':
        opening_left(8, 22); window_back(36, 48, light=(240, 214, 160))
        B(8, 31, 26, 9, 38, (140, 100, 70)); B(8, 31, 26, 9, 1.2, (156, 114, 80), z0=38, sh=(.92, .84))                                         # 갈색 옷장
        FR(9, 20.5, 3, 35, (124, 88, 60), d=31); FR(21.5, 33, 3, 35, (124, 88, 60), d=31); FR(19, 20, 17, 23, (214, 190, 120), d=31); FR(22, 23, 17, 23, (214, 190, 120), d=31)
        table(28, 14, 20, 11, 12); B(32, 18, 8, 1, 8, (60, 62, 66), z0=12, sh=(.9, .8)); B(35, 18.4, 2, 2, 1, (80, 82, 86), z0=12, sh=(.9, .8)); B(41, 17, 3, 3, 4, (226, 214, 174), z0=12, sh=(.9, .8))
        chair(34, 5, False); plant(44, 30); rug(14, 6, 18, 14, (150, 168, 182))
        glows((30, 18, 40, (255, 226, 170), .32))
    # 그리면서 깊이 지도도 만든다: 화소마다 '그 화소를 덮은 가구의 앞쪽 깊이'(바닥·벽·러그는 255 = 가리지 않음). 엔진이 아이를 가구 뒤로 가릴 때 쓴다
    dep = Image.new('L', sc.img.size, 255)
    for depth, f in sorted(sc.jobs, key=lambda j: -j[0]):
        before = sc.img.copy(); f()
        if depth < D - .5:
            diff = ImageChops.difference(sc.img, before).convert('L').point(lambda v: 255 if v else 0)
            dep.paste(int(max(0, min(254, round((depth + 2) * 3)))), (0, 0), diff)
    sc.jobs = []
    ov = Image.new('RGB', sc.img.size, (255, 200, 130)); sc.img = Image.blend(sc.img, ov, .03)
    return sc.img, dep, {'W': W, 'D': D, 'X0': sc.X0, 'Y0': sc.Y0, 'CW': sc.CW, 'CH': sc.CH, 'rects': rects, 'exits': EXITS[key]}

def main():
    imgs = {}; nav = {}
    for k in ROOM:
        im, dep, meta = make(k); imgs[k] = im; nav[k] = meta; dep.save(os.path.join(OUT, 'house_%s_depth.png' % k)); im.save(os.path.join(OUT, 'house_%s.png' % k)); im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(OUT, 'house_%s_x4.png' % k))
    order = ['living', 'kitchen', 'bedroom', 'study']; S = 3; pad = 12
    w = sum(imgs[k].width * S for k in order[:2]) + pad * 3; h = max(imgs['living'].height, imgs['kitchen'].height) * S + max(imgs['bedroom'].height, imgs['study'].height) * S + pad * 3
    sheet = Image.new('RGB', (max(imgs['living'].width * S + imgs['kitchen'].width * S, imgs['bedroom'].width * S + imgs['study'].width * S) + pad * 3, h), (40, 40, 48))
    y = pad; x = pad
    for k in order[:2]: sheet.paste(imgs[k].resize((imgs[k].width * S, imgs[k].height * S), Image.NEAREST), (x, y)); x += imgs[k].width * S + pad
    y += max(imgs['living'].height, imgs['kitchen'].height) * S + pad; x = pad
    for k in order[2:]: sheet.paste(imgs[k].resize((imgs[k].width * S, imgs[k].height * S), Image.NEAREST), (x, y)); x += imgs[k].width * S + pad
    json.dump(nav, open(os.path.join(OUT, 'house_nav.json'), 'w'), ensure_ascii=False)
    sheet.save(os.path.join(OUT, 'house_sheet.png')); print('house ok', {k: v.size for k, v in imgs.items()})
if __name__ == '__main__': main()
