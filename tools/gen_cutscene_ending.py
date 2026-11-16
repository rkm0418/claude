#!/usr/bin/env python3
"""수미상관 컷신(본편 끝, 숲 베란다, 게임 모드 사선 시점).  사용: python3 tools/gen_cutscene_ending.py
출력: maps/out/ending_cutscene.gif (10fps, 320x240), maps/out/ending_cutscene_sheet.png
프롤로그(아파트 베란다 추락)와 같은 순서를 숲에서 되풀이한다: 달려 들어옴 → 무너진 울타리에 막혀 매달려 보며 낑낑 →
뒤에서 나무 머리가 다가옴 → 기울어진 들보를 발견해 타고 올라감 → 울타리 위에서 잠깐 멈춤 → 기울어지며 울타리 너머로 떨어짐 → 흰 화면."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_balcony_forest as F, gen_child_back as CB, render_maps as R

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out')
LIB = R.load_library()
half = lambda im: im.resize((im.width // 2, im.height // 2), Image.NEAREST)
P = CB.make()
BWALK = [half(i) for i in P['walk']]; BIDLE = half(P['idle']); BREACH = half(P['reach']); BHANG = [half(i) for i in P['hang']]; BFOOT = [half(i) for i in P['foot']]
FWALK = [LIB[f'child_s_w{i}'] for i in (1, 2, 3, 4)]; FIDLE = LIB['child_s']
CHASER = [half(LIB[f'chaser_w{i}']) for i in (1, 2, 3, 4)]; CH_IDLE = half(LIB['chaser'])
X0, Y0, SK, SS, D, RAIL = F.X0, F.Y0, F.SK, F.SS, F.D, F.RAIL
BY = Y0 - SS * D; TOP = BY - RAIL
def S(x, d): return (X0 + x + SK * d, Y0 - SS * d)             # 바닥 좌표(x, 깊이) -> 화면 좌표
def lerp(a, b, t): return a + (b - a) * t
def ease(t): return t * t * (3 - 2 * t)
frames, labels = [], []

def render(st, n):
    def actors(img, stage):
        items = [a for a in st.get('actors', []) if a[3] == stage]
        for (sx, sy, spr, _, ang) in sorted(items, key=lambda a: a[1]):       # 화면에서 위(먼 쪽)부터
            if ang:
                big = Image.new('RGBA', (spr.width * 3, spr.height * 2), (0, 0, 0, 0)); big.alpha_composite(spr, (spr.width, 0))
                spr = big.rotate(ang, resample=Image.NEAREST, center=(spr.width * 1.5, spr.height)); ox, oy = sx - spr.width / 2, sy - spr.height / 2
            else: ox, oy = sx - spr.width / 2, sy - spr.height
            tmp = Image.new('RGBA', img.size, (0, 0, 0, 0)); tmp.alpha_composite(spr, (int(ox), int(oy)))
            if stage == 'behind': tmp.paste((0, 0, 0, 0), (0, int(BY) - 2, img.width, img.height))    # 울타리 너머: 땅 아래로는 보이지 않음
            img.alpha_composite(tmp)
        if stage == 'front' and st.get('bang'):
            bx, by_ = st['bang']
            for dy in (0, 1, 2, 4): img.putpixel((int(bx), int(by_ + dy)), (240, 240, 220, 255))
    sc = F.scene(actors=actors, flick=(n // 3) % 2).convert('RGB')
    c = Image.new('RGB', (320, 240), (6, 6, 14)); c.paste(sc.resize((232, 204), Image.NEAREST), (44, 18))
    if st.get('white'): c = Image.blend(c, Image.new('RGB', c.size, (255, 255, 255)), st['white'])
    return c

def add(st, n=1, label=''):
    for i in range(n): frames.append(st); labels.append(label if i == 0 else '')
def kid(pos, spr, layer='front', ang=0): return (pos[0], pos[1], spr, layer, ang)

# 자리: 울타리 가운데 앞(매달려 보는 곳), 기울어진 들보의 아래 끝과 위 끝(화면 좌표)
SPOT = S(46, 45)
posts0 = int(X0 + SK * D) + 2
BEAM_LO, BEAM_HI = (posts0 + 3, BY + 1), (posts0 + 22, TOP + 3)      # 왼쪽 큰 대각 들보: 아래 → 위
chaser_path = [S(-4, -22), S(22, 6), S(30, 30)]
def chaser_at(t):
    t = max(0, min(1, t)); k = t * 2
    a, b = (chaser_path[0], chaser_path[1]) if k < 1 else (chaser_path[1], chaser_path[2]); f = k if k < 1 else k - 1
    return (lerp(a[0], b[0], f), lerp(a[1], b[1], f))
CT = [0.0]                                                           # 추격자 진행도(0~1), 장면이 진행될수록 다가온다
def chs(step=0.0, walking=True, n=0):
    CT[0] = min(1, CT[0] + step)
    return kid(chaser_at(CT[0]), CHASER[(n // 3) % 4] if walking else CH_IDLE)

# 1. 어두운 숲 베란다, 횃불만 흔들림
add(dict(actors=[]), 8, '1 숲 베란다 (횃불만 흔들림)')
# 2. 아이가 앞쪽에서 달려 들어와 울타리로(뒷모습, 빠르게)
start = S(14, -16)
for i in range(14):
    t = (i + 1) / 14; add(dict(actors=[kid((lerp(start[0], SPOT[0], t), lerp(start[1], SPOT[1], t)), BWALK[i % 4])]), 1, '2 달려 들어옴' if i == 0 else '')
# 3. 무너진 울타리에 막힘: 매달려 보며 낑낑(두 번)
for k in range(2):
    add(dict(actors=[kid(SPOT, BREACH)]), 3, '3 울타리에 막혀 낑낑' if k == 0 else '')
    for i in range(8): add(dict(actors=[kid((SPOT[0] + (1 if i % 2 else 0), SPOT[1] - 2), BHANG[(i // 2) % 2])]))
add(dict(actors=[kid(SPOT, BREACH)]), 4)
# 4. 뒤에서 나무 머리가 나타남: 아이가 돌아봄(앞모습)
for i in range(16):
    add(dict(actors=[kid(SPOT, FIDLE if i > 5 else BIDLE), chs(.022, True, i)]), 1, '4 나무 머리가 다가옴, 돌아봄' if i == 0 else '')
# 5. 기울어진 들보를 발견(느낌표) → 들보 아래로 달려감
add(dict(actors=[kid(SPOT, BIDLE), chs(.01, True, 3)], bang=(SPOT[0] + 5, SPOT[1] - 24)), 6, '5 기울어진 들보를 발견')
lo = (BEAM_LO[0] + 2, BEAM_LO[1] + 3)
for i in range(8):
    t = (i + 1) / 8; add(dict(actors=[kid((lerp(SPOT[0], lo[0], t), lerp(SPOT[1], lo[1], t)), FWALK[i % 4] if i < 4 else BWALK[i % 4]), chs(.02, True, i)]))
# 6. 들보를 잡고 발을 올려 타고 오름(끊어서), 추격자는 계속 다가옴
add(dict(actors=[kid(lo, BREACH), chs(.015, True, 0)]), 3, '6 들보를 타고 오름')
add(dict(actors=[kid(lo, BFOOT[0]), chs(.015, True, 2)]), 4)
steps = 5
for k in range(steps):
    t = (k + 1) / steps; pos = (lerp(lo[0], BEAM_HI[0], t), lerp(lo[1], BEAM_HI[1], t))
    add(dict(actors=[kid(pos, BHANG[k % 2]), chs(.02, True, k * 3)]), 3)
    add(dict(actors=[kid(pos, BFOOT[(k + 1) % 2]), chs(.012, True, k * 3 + 2)]), 2)
topp = (BEAM_HI[0] + 2, TOP)
add(dict(actors=[kid(topp, BIDLE), chs(.02, True, 1)]), 2)
# 7. 울타리 위에서 결심한 듯 잠깐 멈춤(프롤로그와 같은 박자). 추격자가 바로 뒤까지 온다
for i in range(14):
    add(dict(actors=[kid(topp, BIDLE), chs(.012, True, i)]), 1, '7 울타리 위에서 멈춤' if i == 0 else '')
# 8. 옆으로 기울어지며 울타리 너머로 떨어짐(프롤로그와 같은 동작). 추격자는 멈춰 선다
for i in range(8):
    add(dict(actors=[kid((topp[0] + i * .3, topp[1]), BIDLE, 'front', -(i + 1) * 3), chs(0, False)]), 1, '8 기울어지며 떨어짐' if i == 0 else '')
yy, v, ang = topp[1], .5, -24
for i in range(12):
    yy += v; v += .6; ang -= 4
    add(dict(actors=[kid((topp[0] + 3 + i * .25, yy), BIDLE, 'behind', ang), chs(0, False)]))
add(dict(actors=[chs(0, False)]), 10)
# 9. 흰 화면(프롤로그의 암전과 대비)
for i in range(12): add(dict(actors=[chs(0, False)], white=(i + 1) / 12), 1, '9 흰 화면' if i == 0 else '')
add(dict(actors=[], white=1.0), 10)

imgs = [render(st, n) for n, st in enumerate(frames)]
imgs[0].save(os.path.join(OUT, 'ending_cutscene.gif'), save_all=True, append_images=imgs[1:], duration=100, loop=0)
idx = [i for i, l in enumerate(labels) if l]
cols = 3; rows = math.ceil(len(idx) / cols)
sheet = Image.new('RGB', (cols * 330 + 10, rows * 262 + 10), (50, 50, 56)); d = ImageDraw.Draw(sheet)
Fnt = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 11)
for n, i in enumerate(idx):
    x, y = 10 + (n % cols) * 330, 10 + (n // cols) * 262
    sheet.paste(imgs[min(len(imgs) - 1, i + (5 if labels[i][0] in '3468' else 0))], (x, y + 16)); d.text((x, y), labels[i], fill=(230, 230, 210), font=Fnt)
sheet.save(os.path.join(OUT, 'ending_cutscene_sheet.png')); print(len(imgs), 'frames')
