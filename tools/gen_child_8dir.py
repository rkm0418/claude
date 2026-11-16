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
    """leg_*: 발이 앞(+)/뒤(-)로 나간 칸 수. arm: 가까운 팔 손의 앞뒤 위치. lift: 'near'|'far' 이면 그 발을 2칸 든다(지나가는 자세)."""
    im = Image.new('RGBA', (24, 38 + PAD), CLEAR); px = im.load(); f = FRONT['idle'].load()
    # 옆머리(사용자 참고 사진): 헬멧처럼 덮지 않는다. 윗머리는 볼륨, 앞머리는 이마로 흘러내린 가닥, 귀가 보이고 귀 앞에 뾰족한 구레나룻,
    # 뒷머리는 목덜미로 짧게 좁아진다. 눈은 그리지 않는다.
    HAIRR = {0: [(8, 17)], 1: [(6, 19)], 2: [(5, 20)], 3: [(4, 21)], 4: [(4, 21)], 5: [(3, 21)], 6: [(3, 22)], 7: [(3, 22)], 8: [(3, 21)],
             9: [(4, 15), (17, 18), (20, 20)], 10: [(4, 9), (12, 13), (15, 15), (18, 18)], 11: [(5, 9), (12, 13)], 12: [(6, 9), (12, 12)], 13: [(7, 9)], 14: [(8, 9)]}
    SKINR = {9: (16, 20), 10: (10, 20), 11: (10, 20), 12: (10, 21), 13: (10, 20), 14: (10, 20), 15: (9, 19), 16: (10, 18), 17: (10, 16), 18: (10, 14), 19: (10, 14)}
    for yy, (x0, x1) in SKINR.items():
        for x in range(x0, x1 + 1): px[x, PAD + yy] = SKIN
    for yy, runs in HAIRR.items():
        for x0, x1 in runs:
            for x in range(x0, x1 + 1): px[x, PAD + yy] = HAIR
    for x, yy in ((8, 2), (9, 2), (7, 3), (12, 3), (13, 4), (14, 5), (16, 6), (17, 7), (10, 5), (11, 6), (6, 6), (6, 9), (7, 11)): px[x, PAD + yy] = HL      # 머릿결(뒤에서 앞으로 흐름)
    for x, yy in ((10, 10), (10, 11), (11, 12), (14, 10), (16, 10), (17, 10), (10, 16), (10, 18), (10, 19), (11, 17), (9, 15)): px[x, PAD + yy] = SKIN2     # 귀 안쪽, 앞머리 그늘, 턱선, 목 그늘
    px[19, PAD + 15] = SKIN2                                                                                                                  # 입
    for yy in range(-1, 20):                                    # 윤곽선: 채운 화소에 맞닿은 빈 화소
        for x in range(1, 23):
            if px[x, PAD + yy][3] == 0 and any(0 <= PAD + yy + dy < im.height and px[x + dx, PAD + yy + dy][3] and px[x + dx, PAD + yy + dy] != A for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if PAD + yy + dy >= 0):
                px[x, PAD + yy] = A
    def leg(off, far, up=0):
        for yy in range(29, 37 - up):
            x0 = 9 + round(off * (yy - 29) / 7)
            cols = (A, PANT2, PANT2, PANT2, A) if far else (A, PANT, PANT, PANT2, A)
            for k, c in enumerate(cols): px[x0 + k, PAD + yy] = c
        x0 = 9 + off
        for k in range(7): px[x0 + k, PAD + 37 - up] = A        # 신발(앞코가 두 칸 나옴)
        for k in range(1, 5): px[x0 + k, PAD + 36 - up] = PANT2
        px[x0 + 5, PAD + 36 - up] = A
    leg(leg_far, True, 2 if lift == 'far' else 0); leg(leg_near, False, 2 if lift == 'near' else 0)
    for yy in range(20, 29):                                    # 몸통(옆에서 본 좁은 폭)
        for x in range(7, 17):
            edge = x in (7, 16) or yy in (20, 28)
            px[x, PAD + yy] = A if edge else (SH2 if x < 10 or yy == 27 else SH)
    for x in range(12, 16): px[x, PAD + 20] = SKIN2 if x < 13 else SKIN     # 목
    CB.limb(im, [(11, PAD + 22), (11 + arm // 2, PAD + 25), (11 + arm, PAD + 28)])       # 가까운 팔(어깨 → 팔꿈치 → 손)
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
