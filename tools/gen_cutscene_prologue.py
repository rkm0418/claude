#!/usr/bin/env python3
"""프롤로그 추락 컷신(1인칭: 베란다 정면, 올려다보는 구도) 초안.  사용: python3 tools/gen_cutscene_prologue.py
출력: maps/out/prologue_cutscene.gif (10fps, 320x240), maps/out/prologue_cutscene_sheet.png (주요 컷)
흐름: 무음 → 철창 앞으로 걸어감 → 맨몸으로 매달려 보며 낑낑 → 옆의 의자를 발견 → 의자를 끌고 와 밟고 올라섬 →
철창 위에서 결심한 듯 잠깐 멈춤 → 옆으로 기울어지며 떨어짐 → 암전 → 타이틀. 착지는 그리지 않는다.
카메라는 고정(확대 없음)."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_balcony2d as B, gen_child_back as CB
LIB = B.R.load_library(); CHAIR = LIB['iron_chair']
FWALK = [LIB[f'child_w{i}'] for i in (1, 2, 3, 4)]            # 앞모습 걷기(보는 쪽·옆으로 걸을 때)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out')
P = CB.make(); WALK, IDLE, HANG, REACH, FOOT = P['walk'], P['idle'], P['hang'], P['reach'], P['foot']
PUSH = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in P['push']]      # 의자 왼쪽에 서서 오른손으로 잡는다
SLIP = Image.new('RGBA', (8, 4), (150, 60, 60, 255)); LIGHT = Image.new('RGBA', (3, 8), (230, 210, 120, 255))
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 30)
BASE_Y, RAIL_TOP = 79, 50
SS = 8                                                     # 카메라 계산용 내부 확대(소수 배율 확대를 부드럽게)
frames, labels, cams = [], [], []

def lerp(a, b, t): return a + (b - a) * t
def ease(t): return t * t * (3 - 2 * t)

def render(st, cam):
    """st: chair, child=(cx, feet_y, sprite, layer, angle), slip, light, bang, fade, title.  cam: (중심x, 중심y, 화면배율)"""
    def actors(im, stage):
        ch = st.get('child')
        if ch and ch[3] == stage:
            cx, fy, spr, _, ang = ch
            if ang:                                         # 발을 축으로 옆으로 기울인다(각도, 도)
                big = Image.new('RGBA', (spr.width * 3, spr.height * 2), (0, 0, 0, 0)); big.alpha_composite(spr, (spr.width, 0))
                spr = big.rotate(ang, resample=Image.NEAREST, center=(spr.width * 1.5, spr.height))
                ox, oy = cx - spr.width / 2, fy - spr.height / 2
            else:
                ox, oy = cx - spr.width / 2, fy - spr.height
            tmp = Image.new('RGBA', im.size, (0, 0, 0, 0)); tmp.alpha_composite(spr, (int(ox), int(oy)))
            if stage == 'behind':                           # 철창 바깥: 바닥선 아래로는 보이지 않는다
                tmp.paste((0, 0, 0, 0), (0, BASE_Y, im.width, im.height))
            im.alpha_composite(tmp)
            if stage == 'front' and st.get('chair_over'):       # 의자 위에 올라선 동안은 등받이(보는 쪽)가 아이 다리 앞에 온다
                im.alpha_composite(CHAIR, (int(st['chair'][0]), int(st['chair'][1]) - CHAIR.height))
            if stage == 'front' and st.get('bang'):
                for dx in (0, 1):
                    for dy in list(range(5)) + [6]: im.putpixel((int(cx + 9 + dx), int(fy - 44 + dy)), (240, 240, 220, 255))
        if stage == 'behind':
            for key, spr in (('slip', SLIP), ('light', LIGHT)):
                p = st.get(key)
                if p and p[1] < BASE_Y: im.alpha_composite(spr, (int(p[0]), int(p[1])))
    sc = B.scene(chair_pos=(int(st['chair'][0]), int(st['chair'][1])), actors=actors).convert('RGB')
    cx, cy, s = cam; vw, vh = 320 / s, 240 / s
    big = sc.resize((sc.width * SS, sc.height * SS), Image.NEAREST)
    box = [int((cx - vw / 2) * SS), int((cy - vh / 2) * SS), int((cx + vw / 2) * SS), int((cy + vh / 2) * SS)]
    view = Image.new('RGB', (box[2] - box[0], box[3] - box[1]), (8, 8, 14)); view.paste(big, (-box[0], -box[1]))
    c = view.resize((320, 240), Image.LANCZOS)              # 도트를 다시 찍지 않는 화면 확대 효과
    if st.get('fade'): c = Image.blend(c, Image.new('RGB', c.size, (0, 0, 0)), st['fade'])
    if st.get('title'):
        d = ImageDraw.Draw(c); txt = '멈춘 시계'; w = d.textlength(txt, font=FONT)
        d.text(((320 - w) / 2, 104), txt, font=FONT, fill=tuple(int(v * st['title']) for v in (230, 225, 205)))
    return c

def add(st, n=1, label=''):
    for i in range(n): frames.append(st); labels.append(label if i == 0 else '')

CH0 = (48, 105); GOAL = (30, 88)                             # 의자: 처음 자리 → 철창 앞(왼쪽) 목표 자리
S = dict(chair=CH0)
def kid(x, y, spr, layer='front', ang=0): return (x, y, spr, layer, ang)
# 1. 무음: 빈 베란다
add(S, 8, '1 어두운 베란다 (무음)')
# 2. 철창 앞으로 걸어감(뒷모습 걷기)
SPOT = (32, 84); start = (26, 150)                           # 의자를 지나치지 않도록 왼쪽으로 곧장 올라간다
for i in range(28):
    t = i / 27; add(dict(S, child=kid(lerp(start[0], SPOT[0], t), lerp(start[1], SPOT[1], t), WALK[(i // 3) % 4])), 1, '2 철창 앞으로 감' if i == 0 else '')
add(dict(S, child=kid(*SPOT, IDLE)), 4)
# 3. 맨몸으로 매달려 보며 낑낑(세 번): 팔을 뻗고 → 폴짝 매달려 다리를 버둥 → 미끄러져 내려옴
for k in range(3):
    add(dict(S, child=kid(*SPOT, REACH)), 3, '3 매달려 보며 낑낑' if k == 0 else '')
    for i in range(8): add(dict(S, child=kid(SPOT[0] + (1 if i % 2 else -1) * (i % 4 < 2), SPOT[1] - 5, HANG[(i // 2) % 2])))
    for i in range(3): add(dict(S, child=kid(SPOT[0], SPOT[1] - 5 + (i + 1) * 5 / 3, REACH)))
    add(dict(S, child=kid(*SPOT, REACH)), 3)                 # 사이에 팔을 내리지 않고 잡은 채로 숨을 고른다
add(dict(S, child=kid(*SPOT, IDLE)), 6)
# 4. 옆의 의자를 발견
add(dict(S, child=kid(*SPOT, IDLE), bang=True), 8, '4 옆의 의자를 발견')
# 5. 의자의 가까운 쪽(왼쪽 옆)으로 최단 경로로 가서 등받이를 잡고 철창 앞으로 끌고 온다
def behind(cp): return (cp[0] - 5, cp[1] - 2)                # 의자 왼쪽 옆(아이에게 가까운 쪽): 오른손이 등받이 옆에 실제로 닿는 자리
def walk_to(a, bpt, n, st, label=''):
    for i in range(n):
        t = (i + 1) / n; fr = (WALK if bpt[1] < a[1] - 2 else FWALK)[(i // 3) % 4]     # 화면 위쪽(안쪽)으로 갈 때만 뒷모습, 아래·옆으로 갈 때는 앞모습
        add(dict(st, child=kid(lerp(a[0], bpt[0], t), lerp(a[1], bpt[1], t), fr)), 1, label if i == 0 else '')
cur = CH0; bh = behind(CH0)                                     # 가장 가까운 쪽(의자 왼쪽 옆)으로 곧장 간다
walk_to(SPOT, bh, 12, S, '5 의자로 곧장 가서 잡고 끌고 옴')
add(dict(S, child=kid(*bh, PUSH[0])), 5)                        # 등받이를 잡음
for k in range(3):                                              # 세 번에 나눠 민다: 힘을 줘 밀고(팔이 펴짐) → 멈춰 숨 고름
    nxt = (lerp(CH0[0], GOAL[0], (k + 1) / 3), lerp(CH0[1], GOAL[1], (k + 1) / 3))
    for i in range(8):
        t = ease((i + 1) / 8); cp = (lerp(cur[0], nxt[0], t), lerp(cur[1], nxt[1], t)); add(dict(chair=cp, child=kid(*behind(cp), PUSH[(i // 2) % 2])))
    cur = nxt; add(dict(chair=cur, child=kid(*behind(cur), PUSH[0])), 5)
CH = cur; cx = CH[0] + 14; seat_y = CH[1] - 12
# 6. 올라가기: 의자 옆(오른쪽)으로 돌아가 → 잡고 → 한 발을 올리고 → 몸을 끌어올려 선다. 그다음 철창도 같은 순서
side = (behind(CH)[0] + 7, behind(CH)[1]); TOPY = RAIL_TOP     # 오를 때는 한 걸음 오른쪽으로 다가서서 등받이를 더 안쪽(오른쪽)에서 잡는다
add(dict(chair=CH, child=kid(behind(CH)[0] + 4, behind(CH)[1], WALK[0])), 3)
#                             # 끌고 온 자리(의자 오른쪽 옆)에서 바로 오른다. TOPY: 철창 윗줄 위에 완전히 올라선 발 높이
add(dict(chair=CH, child=kid(*side, PUSH[0])), 4, '6 잡고 발을 올려 올라감')      # 팔걸이를 잡음
add(dict(chair=CH, child=kid(*side, FOOT[0])), 6)               # 한 발을 앉는 판에 올림
add(dict(chair=CH, child=kid((side[0] + cx) / 2, seat_y + 5, HANG[0])), 3)       # 힘줘서 몸을 끌어올림(끊어서)
add(dict(chair=CH, child=kid(cx, seat_y + 1, HANG[1]), chair_over=True), 3)
add(dict(chair=CH, child=kid(cx, seat_y, IDLE), chair_over=True), 7)             # 의자 위에 섬
def rail(feet_y, leg=None, lean=0):                              # 손이 철창 윗줄(y=RAIL_TOP+1)을 놓지 않는 자세
    return CB.hold(round(RAIL_TOP + 1 - (feet_y - 42)) - CB.PAD, leg, lean)
add(dict(chair=CH, child=kid(cx, seat_y, rail(seat_y)), chair_over=True), 5)                     # 철창 윗줄을 잡음
add(dict(chair=CH, child=kid(cx, seat_y, rail(seat_y, ('r', 6))), chair_over=True), 6)           # 한 발을 철창에 걸침
for fy, leg, n, over in ((seat_y - 6, ('r', 5), 4, True), (seat_y - 12, ('l', 4), 4, False), (TOPY + 8, ('r', 4), 4, False)):
    add(dict(chair=CH, child=kid(cx, fy, rail(fy, leg)), chair_over=over), n)                    # 끊어서 끌어올림: 손은 그대로, 몸만 올라옴
add(dict(chair=CH, child=kid(cx, TOPY, CB.hold(31, None, 3))), 4)                                # 철창 위에 웅크려 올라앉음(손은 발 옆 철창)
add(dict(chair=CH, child=kid(cx, TOPY, IDLE)), 3)                                                # 일어섬
# 7. 철창 위에서 결심한 듯 잠깐 멈춤
add(dict(chair=CH, child=kid(cx, TOPY, IDLE)), 16, '7 결심한 듯 멈춤')
# 8. 옆으로 기울어지며 떨어짐
for i in range(8):
    add(dict(chair=CH, child=kid(cx + i * .4, TOPY, IDLE, 'front', -(i + 1) * 3)), 1, '8 기울어지며 떨어짐' if i == 0 else '')
yy, v, ang = TOPY, .6, -24
for i in range(14):
    yy += v; v += .8; ang -= 4
    add(dict(chair=CH, child=kid(cx + 4 + i * .3, yy, IDLE, 'behind', ang)))
add(dict(chair=CH), 12)
# 9. 암전 → 타이틀(착지는 그리지 않는다)
for i in range(10): add(dict(chair=CH, fade=(i + 1) / 10), 1, '9 암전' if i == 0 else '')
for i in range(12): add(dict(chair=CH, fade=1.0, title=(i + 1) / 12), 1, '10 타이틀' if i == 0 else '')
add(dict(chair=CH, fade=1.0, title=1.0), 14)

# 카메라: 확대 없이 고정(전체, 2배)
cams = [(48, 66, 2.0)] * len(frames)
imgs = [render(st, cam) for st, cam in zip(frames, cams)]
os.makedirs(OUT, exist_ok=True)
imgs[0].save(os.path.join(OUT, 'prologue_cutscene.gif'), save_all=True, append_images=imgs[1:], duration=100, loop=0)
idx = [i for i, l in enumerate(labels) if l]
cols = 4; rows = math.ceil(len(idx) / cols)
sheet = Image.new('RGB', (cols * 330 + 10, rows * 262 + 10), (50, 50, 56)); d = ImageDraw.Draw(sheet)
F = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 11)
for n, i in enumerate(idx):
    x, y = 10 + (n % cols) * 330, 10 + (n // cols) * 262
    sheet.paste(imgs[i + (4 if labels[i].startswith(('3', '8')) else 0)], (x, y + 16)); d.text((x, y), labels[i], fill=(230, 230, 210), font=F)
sheet.save(os.path.join(OUT, 'prologue_cutscene_sheet.png')); print(len(imgs), 'frames')
