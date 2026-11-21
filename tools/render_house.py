#!/usr/bin/env python3
"""집 안: 거실을 가운데 두고 방들이 퍼져 나간다. 사선 3차원 장면(layer-rules 규칙을 따른다: 단단한 것은 box, 평면은 poly, 먼 것부터).
  거실(living) — 왼쪽 벽 문 → 안방(bedroom) / 오른쪽 낮은 벽 틈 → 부엌(kitchen) / 뒤 벽 왼쪽 문 → 서재(study) / 뒤 벽 오른쪽 문 → 욕실(bath) / 앞 틈 → 앞마당
  안방은 오른쪽 낮은 벽 틈이, 부엌은 왼쪽 벽 문이, 서재·욕실은 앞쪽 낮은 벽 틈이 들어온 문이다(지나온 문이 뒤쪽에 보인다).
사용: build_plaza.py 가 가져다 쓴다."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render_city3d import Scene, outline_px, dk

H = 64
WALL1, WALL2 = (206, 192, 162), (166, 142, 110)
WT, WF, WR = (150, 134, 112), (112, 98, 84), (86, 74, 62)          # 앞·오른쪽 낮은 벽
DOOR, DOORF, DOORK = (150, 104, 70), (80, 56, 40), (232, 202, 124)
MAT1, MAT2 = (62, 54, 48), (54, 47, 42)
OL = (56, 44, 38)                                                    # 가구 모서리선

# ---- 방 크기와 문 자리(build_plaza.py 가 같이 쓴다) ----
LVW, LVD = 320, 120                                                  # 거실
LV_FRONT = (150, 168)                                                # 앞마당으로 나가는 앞쪽 틈 x
LV_SIDE = (36, 54)                                                   # 안방(왼쪽 벽)·부엌(오른쪽 벽) 문의 d 범위
LV_STUDY, LV_BATH = (34, 50), (250, 266)                             # 뒤 벽 문 x 범위
BRW, BRD = 170, 100                                                  # 안방
KIW, KID = 170, 100                                                  # 부엌
STW, STD = 140, 92                                                   # 서재
STDOOR = LV_STUDY                                                    # 서재 앞 틈 x(거실 뒤 문과 같은 x)
BAW, BAD = 116, 90                                                   # 욕실
BADOOR = (20, 36)                                                    # 욕실 앞 틈 x


def new(W, D):
    s = Scene(W, D, H, k=2); s.d.rectangle([0, 0, s.img.size[0], s.img.size[1]], fill=(10, 7, 6)); return s


def planks(c1, c2, seam, rugs=(), pw=8):
    """나무 바닥(가로 널). rugs: (x0, x1, d0, d1, 색, 테두리색)."""
    def fl(x, d):
        for (a, b, c, e, col, bd) in rugs:
            if a <= x < b and c <= d < e:
                if x < a + 2.4 or x >= b - 2.4 or d < c + 2.4 or d >= e - 2.4: return bd
                return col if (int(x // 4) + int(d // 4)) % 2 == 0 else dk(col, .94)
        col = c1 if int(d // pw) % 2 == 0 else c2
        if d % pw < .4 or ((int(d // pw) % 2) and x % 30 < .5) or ((int(d // pw) % 2 == 0) and (x + 15) % 30 < .5): col = seam
        return col
    return fl


def tiles(c1, c2, seam, n=8, rugs=()):
    def fl(x, d):
        for (a, b, c, e, col, bd) in rugs:
            if a <= x < b and c <= d < e:
                if x < a + 2 or x >= b - 2 or d < c + 2 or d >= e - 2: return bd
                return col
        if x % n < .5 or d % n < .5: return seam
        return c1 if (int(x // n) + int(d // n)) % 2 == 0 else c2
    return fl


def mat(s, x0, x1, d0, d1):
    s.floor(lambda x, d: MAT1 if (int(x // 3) + int(d // 3)) % 2 == 0 else MAT2, x0=x0, x1=x1, d0=d0, d1=d1)


def wall_d(s, dp, x0, x1, h=60, up=WALL1, low=WALL2, rail=(112, 94, 74)):
    for x in range(int(x0), int(x1), 6):
        for z in range(0, h, 6): s.poly([(x, dp, z), (x + 6.2, dp, z), (x + 6.2, dp, min(h, z + 6)), (x, dp, min(h, z + 6))], up if z >= 14 else low)
    s.poly([(x0, dp, 13.4), (x1, dp, 13.4), (x1, dp, 14.6), (x0, dp, 14.6)], rail)


def wall_x(s, x, d0, d1, h=60, up=WALL1, low=WALL2, rail=(112, 94, 74)):
    for d in range(int(d0), int(d1), 6):
        for z in range(0, h, 6): s.poly([(x, d, z), (x, d + 6.2, z), (x, d + 6.2, min(h, z + 6)), (x, d, min(h, z + 6))], up if z >= 14 else low)
    s.poly([(x, d0, 13.4), (x, d1, 13.4), (x, d1, 14.6), (x, d0, 14.6)], rail)


def door_d(s, x0, x1, dp, h=32):
    """뒤 벽(d 고정)에 달린 나무 문."""
    s.poly([(x0 - 1.6, dp, 0), (x1 + 1.6, dp, 0), (x1 + 1.6, dp, h + 1.8), (x0 - 1.6, dp, h + 1.8)], DOORF)
    s.poly([(x0, dp, 0), (x1, dp, 0), (x1, dp, h), (x0, dp, h)], DOOR)
    w = x1 - x0; m = w * .2
    for z0, z1 in ((3, h * .46), (h * .54, h - 3)): s.poly([(x0 + m, dp, z0), (x1 - m, dp, z0), (x1 - m, dp, z1), (x0 + m, dp, z1)], (132, 90, 60))
    s.poly([(x1 - 3, dp, h * .48), (x1 - 1.6, dp, h * .48), (x1 - 1.6, dp, h * .48 + 1.6), (x1 - 3, dp, h * .48 + 1.6)], DOORK)


def door_x(s, x, d0, d1, h=32):
    """왼쪽 벽(x 고정)에 달린 나무 문."""
    s.holes.append(('x', x, d0 - 1.7, d1 + 1.7))                                                  # 문 자리의 벽 면은 걸음을 막지 않는다(걸어서 문에 닿는다)
    s.poly([(x, d0 - 1.6, 0), (x, d1 + 1.6, 0), (x, d1 + 1.6, h + 1.8), (x, d0 - 1.6, h + 1.8)], DOORF)
    s.poly([(x, d0, 0), (x, d1, 0), (x, d1, h), (x, d0, h)], DOOR)
    w = d1 - d0; m = w * .2
    for z0, z1 in ((3, h * .46), (h * .54, h - 3)): s.poly([(x, d0 + m, z0), (x, d1 - m, z0), (x, d1 - m, z1), (x, d0 + m, z1)], (132, 90, 60))
    s.poly([(x, d1 - 3, h * .48), (x, d1 - 1.6, h * .48), (x, d1 - 1.6, h * .48 + 1.6), (x, d1 - 3, h * .48 + 1.6)], DOORK)


def frame_d(s, x, dp, w, h, z0, inner=(124, 152, 150)):
    """뒤 벽에 거는 그림 액자(평면)."""
    s.poly([(x, dp, z0), (x + w, dp, z0), (x + w, dp, z0 + h), (x, dp, z0 + h)], (96, 68, 46)); s.poly([(x + 1.4, dp, z0 + 1.4), (x + w - 1.4, dp, z0 + 1.4), (x + w - 1.4, dp, z0 + h - 1.4), (x + 1.4, dp, z0 + h - 1.4)], inner)
    s.poly([(x + 1.4, dp, z0 + h * .45), (x + w - 1.4, dp, z0 + h * .45), (x + w - 1.4, dp, z0 + h - 1.4), (x + 1.4, dp, z0 + h - 1.4)], dk(inner, 1.18))


def part(s, x, d, w, dp, h, top, front, right, z0=0, ol=OL, skip=()):
    s.box(x, d, w, dp, h, top, front, right, z0); outline_px(s, x, d, w, dp, h, z0, ol, 1, skip=skip)


def low_front(s, W, gaps):
    x = 0
    for a, b in sorted(gaps):
        if a - 2 > x: s.box(x, 0, a - 2 - x, 6, 10, WT, WF, WR)
        x = b + 2
    if x < W: s.box(x, 0, W - x, 6, 10, WT, WF, WR)


def low_right(s, W, D, gaps):
    d = 0; segs = []
    for a, b in sorted(gaps): segs.append((d, a - 2)); d = b + 2
    segs.append((d, D))
    for d0, d1 in reversed(segs):
        if d1 > d0: s.box(W, d0, 6, d1 - d0, 10, WT, WF, WR)


def plant(s, x, d, big=True):
    s.box(x, d, 11, 11, 11, (122, 82, 60), (100, 66, 48), (80, 52, 38))
    s.box(x + 1.5, d + 4, 8, 3, 20 if big else 12, (66, 124, 78), (50, 100, 62), (40, 80, 52), z0=11)
    s.box(x - .5, d + 2, 12, 8, 6, (76, 138, 88), (56, 110, 68), (46, 92, 56), z0=(24 if big else 16))


def floor_lamp(s, x, d):
    s.box(x, d, 6, 6, 2, (70, 60, 52), (56, 48, 42), (44, 38, 34))
    s.box(x + 2.2, d + 2.2, 1.6, 1.6, 36, (96, 84, 72), (82, 72, 62), (66, 58, 50), z0=2)
    s.box(x - .5, d - .5, 7, 7, 7, (255, 232, 170), (236, 204, 130), (206, 172, 104), z0=38)
    s.glow(x + 3, d + 3, 34, col=(255, 214, 140), power=.28, z=36)


# ---------------- 거실 ----------------
def living(save=False):
    W, D = LVW, LVD; s = new(W, D)
    rug = (92, 228, 22, 96, (140, 84, 74), (190, 150, 106))
    s.floor(planks((158, 120, 86), (150, 112, 80), (116, 84, 58), rugs=[rug]), x0=0, x1=W, d0=6, d1=D)
    mat(s, LV_FRONT[0], LV_FRONT[1], 0, 12)                                        # 앞마당으로 나가는 문 앞 매트
    mat(s, 0, 12, LV_SIDE[0], LV_SIDE[1])                                          # 안방 문 앞 매트
    mat(s, W - 12, W, LV_SIDE[0], LV_SIDE[1])                                      # 부엌 쪽 문 앞 매트
    wall_d(s, D, 0, W); wall_x(s, 0, 6, D)
    door_d(s, *LV_STUDY, D); door_d(s, *LV_BATH, D); door_x(s, 0, *LV_SIDE)
    frame_d(s, 200, D, 22, 16, 30)
    # --- 먼 것부터(d 큰 것부터)
    part(s, 128, D - 12, 64, 12, 14, (140, 102, 70), (118, 84, 58), (96, 68, 46))   # 텔레비전 장
    part(s, 142, D - 8, 36, 3, 22, (44, 48, 56), (28, 32, 40), (20, 24, 30), z0=14)
    s.poly([(144, D - 8, 17), (176, D - 8, 17), (176, D - 8, 33), (144, D - 8, 33)], (38, 54, 64), z=False); s.poly([(146, D - 8, 28), (158, D - 8, 28), (158, D - 8, 32), (146, D - 8, 32)], (74, 100, 112), z=False)
    floor_lamp(s, 234, D - 14); plant(s, 286, D - 22)
    part(s, 2, 80, 9, 16, 14, (150, 108, 72), (126, 90, 60), (102, 72, 48))        # 왼쪽 벽 옆 작은 탁자
    # --- 소파(등받이가 보는 쪽): 앉는 면 → 왼쪽 팔걸이 → 등받이 → 오른쪽 팔걸이
    SF, ST_, SR, SE = (162, 96, 76), (190, 124, 100), (124, 70, 56), (88, 46, 38)
    part(s, 118, 46, 84, 20, 10, ST_, SF, SR, ol=SE)
    part(s, 112, 40, 6, 26, 16, ST_, SF, SR, ol=SE)
    part(s, 118, 40, 84, 6, 24, ST_, SF, (140, 80, 64), ol=SE, skip=(0,))
    part(s, 202, 40, 6, 26, 16, ST_, SF, SR, ol=SE)
    s.run(); low_front(s, W, [LV_FRONT]); low_right(s, W, D, [LV_SIDE])
    s.lamps = []
    return s.save('house_living') if save else s


# ---------------- 안방 ----------------
def bedroom(save=False):
    W, D = BRW, BRD; s = new(W, D)
    rug = (24, 112, 20, 58, (86, 112, 132), (150, 156, 140))
    s.floor(planks((148, 118, 90), (140, 110, 84), (110, 84, 62), rugs=[rug]), x0=0, x1=W, d0=6, d1=D)
    mat(s, W - 12, W, LV_SIDE[0], LV_SIDE[1])
    wall_d(s, D, 0, W, up=(196, 182, 168), low=(150, 128, 112)); wall_x(s, 0, 6, D, up=(196, 182, 168), low=(150, 128, 112))
    frame_d(s, 90, D, 20, 14, 30, (160, 140, 120)); frame_d(s, 116, D, 14, 18, 28)
    # 옷장(뒤 벽 오른쪽)
    part(s, 118, D - 14, 44, 14, 52, (132, 96, 68), (150, 110, 78), (112, 80, 54))
    s.poly([(139.4, D - 14, 3), (140.6, D - 14, 3), (140.6, D - 14, 49), (139.4, D - 14, 49)], (96, 68, 46), z=False)
    for xx in (134, 143): s.poly([(xx, D - 14, 24), (xx + 2, D - 14, 24), (xx + 2, D - 14, 29), (xx, D - 14, 29)], DOORK, z=False)
    part(s, 72, D - 14, 14, 14, 14, (140, 102, 70), (118, 84, 58), (96, 68, 46))     # 침대 옆 협탁과 작은 등
    part(s, 76, D - 11, 6, 6, 5, (255, 232, 170), (236, 204, 130), (206, 172, 104), z0=14, ol=(150, 110, 70)); s.glow(79, D - 8, 30, col=(255, 214, 140), power=.26, z=16)
    # 침대: 머리판 → 매트리스 → 베개 → 이불 (머리가 뒤 벽)
    part(s, 18, D - 4, 50, 4, 24, (128, 92, 64), (146, 106, 72), (108, 76, 50))
    part(s, 20, D - 38, 46, 34, 8, (150, 112, 80), (130, 96, 68), (104, 76, 54))
    part(s, 21, D - 37, 44, 32, 6, (232, 228, 214), (196, 190, 178), (160, 154, 144), z0=8, ol=(120, 112, 100))
    part(s, 25, D - 12, 16, 8, 3, (248, 244, 234), (214, 208, 196), (176, 170, 160), z0=14, ol=(140, 132, 120)); part(s, 45, D - 12, 16, 8, 3, (248, 244, 234), (214, 208, 196), (176, 170, 160), z0=14, ol=(140, 132, 120))
    part(s, 21, D - 37, 44, 24, 3, (104, 128, 162), (84, 106, 138), (66, 86, 114), z0=14, ol=(52, 70, 96))
    part(s, 2, 36, 10, 26, 18, (140, 102, 70), (118, 84, 58), (96, 68, 46))          # 왼쪽 벽 서랍장
    s.run(); low_front(s, W, []); low_right(s, W, D, [LV_SIDE])
    s.lamps = []
    return s.save('house_bedroom') if save else s


# ---------------- 부엌 ----------------
def kitchen(save=False):
    W, D = KIW, KID; s = new(W, D)
    s.floor(tiles((214, 204, 176), (190, 178, 148), (150, 138, 112), 8), x0=0, x1=W, d0=6, d1=D)
    mat(s, 0, 12, LV_SIDE[0], LV_SIDE[1])
    wall_d(s, D, 0, W, up=(214, 204, 176), low=(136, 160, 150), rail=(96, 116, 108)); wall_x(s, 0, 6, D, up=(214, 204, 176), low=(136, 160, 150), rail=(96, 116, 108))
    door_x(s, 0, *LV_SIDE)
    CT, CF, CR = (226, 214, 188), (168, 130, 94), (136, 102, 72)
    # 위 찬장(뒤 벽, 머리 위) → 아래 찬장 → 냉장고
    part(s, 18, D - 8, 76, 8, 16, (178, 140, 100), (160, 124, 90), (130, 98, 68), z0=36)
    part(s, 18, D - 14, 100, 14, 22, CT, CF, CR)
    for xx in range(18, 118, 25): s.poly([(xx + .8, D - 14, 3), (xx + 1.6, D - 14, 3), (xx + 1.6, D - 14, 19), (xx + .8, D - 14, 19)], (116, 86, 60), z=False)
    s.poly([(54, D - 14, 22.2), (76, D - 14, 22.2), (76, D - 14, 22.2 + .1), (54, D - 14, 22.3)], (150, 156, 156), z=False)
    s.poly([(52, D - 12, 22.1), (78, D - 12, 22.1), (78, D - 6, 22.1), (52, D - 6, 22.1)], (150, 160, 162), z=False); s.poly([(54, D - 11, 22.2), (76, D - 11, 22.2), (76, D - 7, 22.2), (54, D - 7, 22.2)], (96, 118, 130), z=False)
    s.poly([(26, D - 12, 22.1), (44, D - 12, 22.1), (44, D - 6, 22.1), (26, D - 6, 22.1)], (46, 46, 52), z=False)
    for cx in (30, 40): s.poly([(cx - 3, D - 9, 22.2), (cx + 3, D - 9, 22.2), (cx + 3, D - 8, 22.2), (cx - 3, D - 8, 22.2)], (96, 96, 104), z=False)
    part(s, 128, D - 16, 24, 16, 50, (232, 234, 232), (214, 218, 216), (170, 176, 176), ol=(120, 126, 126))                # 냉장고
    s.poly([(129, D - 16, 30), (151, D - 16, 30), (151, D - 16, 31), (129, D - 16, 31)], (150, 156, 156), z=False); s.poly([(145, D - 16, 33), (146.6, D - 16, 33), (146.6, D - 16, 42), (145, D - 16, 42)], (150, 156, 156), z=False); s.poly([(145, D - 16, 8), (146.6, D - 16, 8), (146.6, D - 16, 22), (145, D - 16, 22)], (150, 156, 156), z=False)
    # 식탁과 의자
    part(s, 62, 44, 48, 22, 13, (190, 146, 100), (160, 120, 80), (128, 94, 62), ol=(92, 66, 44))
    part(s, 70, 40, 8, 8, 9, (168, 126, 86), (140, 104, 72), (112, 82, 56)); part(s, 94, 40, 8, 8, 9, (168, 126, 86), (140, 104, 72), (112, 82, 56))
    part(s, 82, 50, 8, 8, 4, (240, 232, 214), (214, 204, 184), (176, 166, 148), z0=13, ol=(150, 140, 120))                  # 식탁 위 그릇
    s.run(); low_front(s, W, []); low_right(s, W, D, [])
    s.lamps = []
    return s.save('house_kitchen') if save else s


# ---------------- 서재 ----------------
def study(save=False):
    W, D = STW, STD; s = new(W, D)
    s.floor(planks((120, 96, 72), (112, 90, 68), (88, 70, 52), rugs=[(50, 112, 22, 58, (78, 100, 92), (140, 130, 100))]), x0=0, x1=W, d0=6, d1=D)
    mat(s, STDOOR[0], STDOOR[1], 0, 12)
    wall_d(s, D, 0, W, up=(176, 164, 138), low=(122, 104, 82)); wall_x(s, 0, 6, D, up=(176, 164, 138), low=(122, 104, 82))
    frame_d(s, 100, D, 22, 16, 34, (140, 130, 110))
    def shelf(x, d, w, dp, h, front_axis='d'):
        part(s, x, d, w, dp, h, (116, 82, 56), (136, 98, 66), (98, 68, 46))
        if front_axis == 'd':
            for z in range(10, h, 12): s.poly([(x + 1.2, d, z), (x + w - 1.2, d, z), (x + w - 1.2, d, z + 1), (x + 1.2, d, z + 1)], (84, 58, 40), z=False)
            for r_, z in enumerate(range(1, h - 8, 12)):
                xx = x + 2
                for k in range(int((w - 4) / 3.2)):
                    ww = 2.6 + (k * 7 + r_ * 3) % 3 * .4; hh = 6 + (k * 5 + r_) % 4
                    s.poly([(xx, d, z), (xx + ww, d, z), (xx + ww, d, z + hh), (xx, d, z + hh)], [(170, 78, 66), (80, 118, 146), (202, 164, 80), (92, 136, 96), (146, 106, 156)][(k + r_) % 5], z=False); xx += ww + .5
                    if xx > x + w - 4: break
    shelf(6, D - 12, 48, 12, 54)
    part(s, 62, D - 18, 52, 18, 16, (150, 112, 76), (126, 92, 62), (102, 74, 50), ol=(80, 56, 40))                      # 책상
    part(s, 70, D - 14, 14, 9, 8, (60, 64, 72), (36, 40, 48), (28, 32, 38), z0=16, ol=(20, 22, 28)); part(s, 70, D - 7, 14, 1.6, 12, (60, 64, 72), (34, 44, 56), (26, 34, 44), z0=24, ol=(20, 22, 28))
    part(s, 98, D - 12, 6, 6, 4, (255, 232, 170), (236, 204, 130), (206, 172, 104), z0=16, ol=(150, 110, 70)); s.glow(101, D - 9, 30, col=(255, 214, 140), power=.28, z=19)
    shelf(2, 24, 10, 30, 26, 'x')                                                                                       # 왼쪽 벽 낮은 책장
    part(s, 78, 56, 16, 12, 8, (96, 72, 60), (76, 58, 48), (60, 46, 38)); part(s, 78, 54, 16, 2, 16, (96, 72, 60), (76, 58, 48), (60, 46, 38), z0=8)   # 의자(등받이가 보는 쪽)
    s.run(); low_front(s, W, [STDOOR]); low_right(s, W, D, [])
    s.lamps = []
    return s.save('house_study') if save else s


# ---------------- 욕실 ----------------
def bath(save=False):
    W, D = BAW, BAD; s = new(W, D)
    s.floor(tiles((222, 232, 232), (204, 218, 220), (160, 180, 184), 8, rugs=[(14, 46, 22, 46, (238, 218, 150), (200, 176, 110))]), x0=0, x1=W, d0=6, d1=D)
    mat(s, BADOOR[0], BADOOR[1], 0, 12)
    TU, TL = (214, 228, 228), (150, 184, 190)
    wall_d(s, D, 0, W, up=TU, low=TL, rail=(110, 140, 146)); wall_x(s, 0, 6, D, up=TU, low=TL, rail=(110, 140, 146))
    # 거울(뒤 벽, 세면대 위)
    s.poly([(7, D, 30), (27, D, 30), (27, D, 52), (7, D, 52)], (110, 100, 90)); s.poly([(8.4, D, 31.4), (25.6, D, 31.4), (25.6, D, 50.6), (8.4, D, 50.6)], (176, 206, 220)); s.poly([(10, D, 40), (14, D, 40), (14, D, 48), (10, D, 48)], (206, 226, 234))
    part(s, 58, D - 24, 54, 24, 16, (240, 242, 240), (222, 226, 226), (180, 188, 190), ol=(130, 142, 146))               # 욕조
    part(s, 61, D - 21, 48, 18, 1, (160, 200, 218), (140, 180, 198), (120, 160, 178), z0=16, ol=(110, 150, 168))
    part(s, 36, D - 12, 14, 12, 22, (240, 242, 240), (222, 226, 226), (180, 188, 190), ol=(130, 142, 146))               # 변기 탱크
    part(s, 36, D - 24, 14, 12, 10, (246, 248, 246), (228, 232, 232), (186, 194, 196), ol=(130, 142, 146))              # 변기
    part(s, 6, D - 14, 20, 14, 22, (236, 238, 236), (216, 222, 222), (176, 184, 186), ol=(130, 142, 146))               # 세면대
    s.poly([(10, D - 12, 22.1), (22, D - 12, 22.1), (22, D - 4, 22.1), (10, D - 4, 22.1)], (160, 200, 218), z=False)
    s.run(); low_front(s, W, [BADOOR]); low_right(s, W, D, [])
    s.lamps = []
    return s.save('house_bath') if save else s


if __name__ == '__main__':
    for f in (living, bedroom, kitchen, study, bath): f(True)
    print('ok')
