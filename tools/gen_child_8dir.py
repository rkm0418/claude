#!/usr/bin/env python3
"""주인공 8방향 스프라이트(서기 + 걷기 4장).  사용: python3 tools/gen_child_8dir.py
출력: art/out/sprites/child8/child_<방향>_<idle|w1|w2|w3|w4>.png (24x42, 발 기준점 = 아래 가운데, 위 4칸은 여유)
      art/out/sprites/child8/manifest.json, maps/out/child_8dir_sheet.png, maps/out/child_8dir_walk.gif
방향: d(아래=정면) u(위=뒷모습) l r(옆) dl dr(정면 대각) ul ur(뒷모습 대각).  왼쪽 계열은 오른쪽 계열의 좌우 반전.
만드는 법: 정면은 art/objects.txt 의 child, child_w1~4. 뒷모습은 gen_child_back. 옆모습은 이 파일에서 절차적으로 그림.
대각은 정면/뒷모습의 얼굴·팔을 바라보는 쪽으로 치우치게 고친다."""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_child_back as CB
SPR = CB.SPR; OUT = os.path.join(SPR, 'child8'); os.makedirs(OUT, exist_ok=True)
A, HAIR, HL, SKIN, SKIN2, SH, SH2 = CB.A, CB.HAIR, (138, 106, 78, 255), CB.SKIN, CB.SKIN2, CB.SH, CB.SH2
PANT, PANT2 = (59, 51, 64, 255), (43, 36, 48, 255)
PAD = CB.PAD; CLEAR = (0, 0, 0, 0)

def padded(name):
    src = Image.open(os.path.join(SPR, name + '.png')).convert('RGBA')
    im = Image.new('RGBA', (24, 38 + PAD), CLEAR); im.alpha_composite(src, (0, PAD)); return im
FRONT = {'idle': padded('child'), **{f'w{i}': padded(f'child_w{i}') for i in (1, 2, 3, 4)}}
_b = CB.make(); BACK = {'idle': _b['idle'], **{f'w{i + 1}': _b['walk'][i] for i in range(4)}}
flip = lambda im: im.transpose(Image.FLIP_LEFT_RIGHT)

# ---------- 옆모습(오른쪽을 봄) ----------
def side(leg_near=0, leg_far=0, arm=0, lift=None):
    """정면 그림과 같은 덩어리 비율로 그린 옆모습: 큰 머리가 목 없이 어깨 위에 얹히고(정면과 같음), 몸통은 두툼하다(14칸).
    leg_*: 발이 앞(+)/뒤(-)로 나간 칸 수. arm: 가까운 팔 손의 앞뒤 위치. lift: 'near'|'far' 이면 그 발을 1칸 든다."""
    im = Image.new('RGBA', (24, 38 + PAD), CLEAR); px = im.load()
    # --- 다리(정면과 같은 길이): 두 다리가 조금 어긋나 겹쳐 폭이 넓어 보인다 ---
    def leg(base, off, far, up=0):
        for yy in range(29, 37 - up):
            x0 = base + round(off * (yy - 29) / 7)
            cols = (A, PANT2, PANT2, PANT2, PANT2, PANT2, A) if far else (A, PANT, PANT, PANT, PANT, PANT2, A)
            for k, c in enumerate(cols): px[x0 + k, PAD + yy] = c
        x0 = base + off
        for k in range(9): px[x0 + k, PAD + 37 - up] = A        # 신발(앞코가 두 칸 나옴)
        for k in range(1, 7): px[x0 + k, PAD + 36 - up] = PANT2
        px[x0 + 7, PAD + 36 - up] = A
    leg(10, leg_far, True, 2 if lift == 'far' else 0); leg(7, leg_near, False, 2 if lift == 'near' else 0)
    # --- 몸통(정면과 같은 높이: 어깨 둥글게, 두툼하게 14칸) ---
    TOR = {18: (8, 15), 19: (6, 17), **{yy: (5, 18) for yy in range(20, 28)}, 28: (6, 17)}
    inside = lambda x, yy: yy in TOR and TOR[yy][0] <= x <= TOR[yy][1]
    for yy, (x0, x1) in TOR.items():
        for x in range(x0, x1 + 1):
            edge = not all(inside(x + dx, yy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            px[x, PAD + yy] = A if edge else (SH2 if x < 8 or yy >= 27 else SH)
    CB.limb(im, [(12, PAD + 21), (12 + arm // 2, PAD + 25), (12 + arm, PAD + 28)])       # 가까운 팔(어깨 → 팔꿈치 → 손)
    # --- 머리(사용자 참고 사진의 머리 모양): 따로 그린 뒤 가로로 2칸 늘려 정면 머리 크기에 맞추고, 목 없이 어깨 위에 얹는다 ---
    hd = Image.new('RGBA', (24, 24), CLEAR); h = hd.load()
    HAIRR = {0: [(10, 17)], 1: [(8, 19)], 2: [(7, 20)], 3: [(6, 21)], 4: [(5, 21)], 5: [(5, 21)], 6: [(5, 22)], 7: [(5, 22)], 8: [(5, 21)],
             9: [(5, 15), (17, 18), (20, 20)], 10: [(6, 9), (12, 13), (15, 15), (18, 18)], 11: [(6, 9), (12, 13)], 12: [(7, 9), (12, 12)], 13: [(8, 9)], 14: [(9, 9)]}
    SKINR = {9: (16, 20), 10: (10, 20), 11: (10, 20), 12: (10, 21), 13: (10, 20), 14: (10, 20), 15: (9, 19), 16: (10, 18), 17: (11, 16)}
    for yy, (x0, x1) in SKINR.items():
        for x in range(x0, x1 + 1): h[x, yy] = SKIN
    for yy, runs in HAIRR.items():
        for x0, x1 in runs:
            for x in range(x0, x1 + 1): h[x, yy] = HAIR
    for x, yy in ((8, 2), (9, 2), (7, 3), (12, 3), (13, 4), (14, 5), (16, 6), (17, 7), (10, 5), (11, 6), (7, 6), (7, 9), (8, 11)): h[x, yy] = HL
    for x, yy in ((10, 10), (10, 11), (11, 12), (14, 10), (16, 10), (17, 10), (10, 16), (11, 17), (9, 15)): h[x, yy] = SKIN2
    h[19, 15] = SKIN2                                           # 입
    wide = Image.new('RGBA', (26, 24), CLEAR); w = wide.load()   # 가로 2칸 늘리기: 뒷머리 쪽 한 칸(x=7), 얼굴 쪽 한 칸(x=15)을 겹쳐 그린다
    for yy in range(24):
        ox = 0
        for x in range(24):
            w[ox, yy] = h[x, yy]; ox += 1
            if x in (7, 15): w[ox, yy] = h[x, yy]; ox += 1
    HX0, HY0 = -3, PAD + 2                                      # 머리 놓는 자리: 가운데가 몸통 가운데에 오고, 턱이 어깨선에 닿는다
    for yy in range(24):
        for x in range(26):
            X, Y = x + HX0, yy + HY0
            if w[x, yy][3] and 0 <= X < 24 and 0 <= Y < im.height: px[X, Y] = w[x, yy]
    for Y in range(0, PAD + 21):                                # 머리 윤곽선: 머리 화소에 맞닿은 빈 화소와 몸통 화소
        for X in range(0, 24):
            c = px[X, Y]
            if c in (HAIR, HL, SKIN, SKIN2) : continue
            near = any(0 <= X + dx < 24 and 0 <= Y + dy < im.height and px[X + dx, Y + dy] in (HAIR, HL, SKIN, SKIN2) and (Y + dy) <= PAD + 19 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if near and (c[3] == 0 or c in (SH, SH2)): px[X, Y] = A
    return im
SIDE = {'idle': side(), 'w1': side(3, -3, -3), 'w2': side(0, 0, 0, 'far'), 'w3': side(-3, 3, 3), 'w4': side(0, 0, 0, 'near')}

# ---------- 대각 ----------
def diag_front(im):
    """정면 → 오른쪽 아래를 봄: 얼굴(살색)을 오른쪽으로 2칸 치우치게 하고 왼쪽은 머리카락, 먼 쪽(왼쪽) 손은 몸 뒤로 숨긴다."""
    im = im.copy(); px = im.load()
    for y in range(PAD + 9, PAD + 20):
        row = [px[x, y] for x in range(24)]
        skin_x = [x for x in range(24) if row[x] in (SKIN, SKIN2)]
        if not skin_x: continue
        lo = min(skin_x)
        for x in range(lo, lo + 3):
            if px[x, y] in (SKIN, SKIN2): px[x, y] = HAIR
        px[lo + 3, y] = SKIN2 if px[lo + 3, y] in (SKIN, SKIN2) else px[lo + 3, y]
    for y in range(PAD + 28, PAD + 33):                         # 먼 쪽 손(화면 왼쪽)을 숨김
        for x in range(0, 7):
            if px[x, y] in (SKIN, SKIN2) or (px[x, y] == A and x < 6): px[x, y] = CLEAR
    for y in range(PAD + 28, PAD + 31): px[5, y] = A if px[6, y][3] else px[5, y]
    return im
def diag_back(im):
    """뒷모습 → 오른쪽 위를 봄: 머리 오른쪽 가장자리에 뺨이 살짝 보이고, 먼 쪽(왼쪽) 손은 몸 앞으로 숨는다."""
    im = im.copy(); px = im.load()
    for y in range(PAD + 13, PAD + 18):
        xs = [x for x in range(24) if px[x, y][3]]
        if not xs: continue
        hi = max(xs)                                            # 오른쪽 끝(윤곽선)
        px[hi - 1, y] = SKIN; px[hi - 2, y] = SKIN2 if y > PAD + 13 else HAIR
    for y in range(PAD + 28, PAD + 33):
        for x in range(0, 7):
            if px[x, y] in (SKIN, SKIN2) or (px[x, y] == A and x < 6): px[x, y] = CLEAR
    for y in range(PAD + 28, PAD + 31): px[5, y] = A if px[6, y][3] else px[5, y]
    return im

FR = ['idle', 'w1', 'w2', 'w3', 'w4']
SETS = {'d': FRONT, 'u': BACK, 'r': SIDE, 'l': {k: flip(v) for k, v in SIDE.items()},
        'dr': {k: diag_front(v) for k, v in FRONT.items()}, 'ur': {k: diag_back(v) for k, v in BACK.items()}}
SETS['dl'] = {k: flip(v) for k, v in SETS['dr'].items()}; SETS['ul'] = {k: flip(v) for k, v in SETS['ur'].items()}
ORDER = ['d', 'dr', 'r', 'ur', 'u', 'ul', 'l', 'dl']           # 시계 반대 방향(아래부터)

if __name__ == '__main__':
    for d in ORDER:
        for k in FR: SETS[d][k].save(os.path.join(OUT, f'child_{d}_{k}.png'))
    json.dump({'size': [24, 42], 'anchor': 'bottom-center', 'top_padding': PAD, 'directions': ORDER, 'frames': FR, 'walk_cycle': ['w1', 'w2', 'w3', 'w4'],
               'fps': 6, 'file': 'child_<dir>_<frame>.png', 'vector': {'d': [0, 1], 'dr': [1, 1], 'r': [1, 0], 'ur': [1, -1], 'u': [0, -1], 'ul': [-1, -1], 'l': [-1, 0], 'dl': [-1, 1]}},
              open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
    S = 4; sheet = Image.new('RGBA', (len(FR) * 26 * S + 8, len(ORDER) * 44 * S + 8), (44, 48, 64, 255))
    for r, d in enumerate(ORDER):
        for c, k in enumerate(FR): sheet.alpha_composite(SETS[d][k].resize((24 * S, 42 * S), Image.NEAREST), (4 + c * 26 * S, 4 + r * 44 * S))
    mo = os.path.join(SPR, '..', '..', '..', 'maps', 'out'); sheet.save(os.path.join(mo, 'child_8dir_sheet.png'))
    gif = []
    for t in range(8):                                          # 8방향이 제자리에서 걷는 미리보기(3x3, 가운데는 정면 서기)
        fr = Image.new('RGBA', (3 * 30 * 3, 3 * 46 * 3), (44, 48, 64, 255))
        pos = {'ul': (0, 0), 'u': (1, 0), 'ur': (2, 0), 'l': (0, 1), 'r': (2, 1), 'dl': (0, 2), 'd': (1, 2), 'dr': (2, 2)}
        for d, (cx, cy) in pos.items(): fr.alpha_composite(SETS[d][f'w{t // 2 % 4 + 1}'].resize((72, 126), Image.NEAREST), (cx * 90 + 9, cy * 138 + 6))
        fr.alpha_composite(SETS['d']['idle'].resize((72, 126), Image.NEAREST), (99, 144)); gif.append(fr.convert('RGB'))
    gif[0].save(os.path.join(mo, 'child_8dir_walk.gif'), save_all=True, append_images=gif[1:], duration=160, loop=0)
    print('child8:', len(ORDER) * len(FR), 'sprites')
