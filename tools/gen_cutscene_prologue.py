#!/usr/bin/env python3
"""프롤로그 추락 컷신(1인칭: 베란다 정면, 올려다보는 구도) 초안.  사용: python3 tools/gen_cutscene_prologue.py
출력: maps/out/prologue_cutscene.gif (10fps, 320x240), maps/out/prologue_cutscene_sheet.png (주요 컷)
흐름(설계 문서 §3.5): 무음 → 아이가 들어옴 → 의자를 철창 앞으로 주섬주섬 밀고 감 → 올라서다 미끄러짐 → 다시 올라서 철창을 넘음 →
슬리퍼 한 짝이 떨어지고 손전등이 떠오름 → 타이틀. 착지는 그리지 않는다. 아이는 철창 쪽(뒤)을 보고 있으므로 앞모습 스프라이트의 얼굴을 머리색으로 덮어 뒷모습으로 쓴다."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_balcony2d as B

SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'out', 'sprites')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out')
HAIR, SKIN, SKIN2 = (90, 70, 54, 255), (242, 220, 180, 255), (211, 165, 116, 255)

def back(name):
    im = Image.open(os.path.join(SPR, name + '.png')).convert('RGBA'); px = im.load()
    for y in range(20):                                     # 머리 부분의 얼굴색 -> 머리색(뒷모습)
        for x in range(im.width):
            if px[x, y] in (SKIN, SKIN2): px[x, y] = HAIR
    return im
IDLE = back('child'); WALK = [back(f'child_w{i}') for i in (1, 2, 3, 4)]
SLIP = Image.new('RGBA', (8, 4), (150, 60, 60, 255)); LIGHT = Image.new('RGBA', (3, 8), (230, 210, 120, 255))
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 30)

BASE_Y = 79; RAIL_TOP = 50
frames, labels = [], []

def lerp(a, b, t): return a + (b - a) * t

def render(state):
    """state: dict(chair=(x,y), child=(cx,feet_y,sprite,layer), slip=(x,y)|None, light=(x,y)|None, fade=0..1, title=0..1)"""
    def actors(im, stage):
        ch = state.get('child')
        if ch and ch[3] == stage:
            cx, fy, spr = ch[0], ch[1], ch[2]
            tmp = Image.new('RGBA', im.size, (0, 0, 0, 0)); tmp.alpha_composite(spr, (int(cx - spr.width / 2), int(fy - spr.height)))
            if stage == 'behind':                           # 철창 바깥: 바닥(y>=BASE_Y) 아래로 떨어지면 보이지 않는다
                for y in range(BASE_Y, im.height):
                    for x in range(im.width): tmp.putpixel((x, y), (0, 0, 0, 0))
            im.alpha_composite(tmp)
        if stage == 'behind':
            for key, spr in (('slip', SLIP), ('light', LIGHT)):
                p = state.get(key)
                if p and p[1] < BASE_Y: im.alpha_composite(spr, (int(p[0]), int(p[1])))
    sc = B.scene(chair_pos=(int(state['chair'][0]), int(state['chair'][1])), actors=actors)
    big = sc.resize((192, 272), Image.NEAREST).crop((0, 32, 192, 272))
    c = Image.new('RGB', (320, 240), (8, 8, 14)); c.paste(big.convert('RGB'), (64, 0))
    f = state.get('fade', 0)
    if f: c = Image.blend(c, Image.new('RGB', c.size, (0, 0, 0)), f)
    t = state.get('title', 0)
    if t:
        d = ImageDraw.Draw(c); txt = '멈춘 시계'; w = d.textlength(txt, font=FONT)
        col = tuple(int(v * t) for v in (230, 225, 205)); d.text(((320 - w) / 2, 104), txt, font=FONT, fill=col)
    return c

def add(state, n=1, label=''):
    for i in range(n):
        frames.append(render(state))
        labels.append(label if i == 0 else '')

chair = [48, 105]
S = dict(chair=tuple(chair), child=None)
# 1. 무음: 빈 베란다
add(S, 12, '1 어두운 베란다 (무음)')
# 2. 아이가 앞쪽(보는 쪽) 왼쪽에서 들어온다: 뒷모습으로 의자 쪽으로 걸어 올라감
start, end = (22, 150), (chair[0] + 22, 120)
steps = 26
for i in range(steps):
    t = i / (steps - 1); wlk = WALK[(i // 3) % 4]
    add(dict(S, child=(lerp(start[0], end[0], t), lerp(start[1], end[1], t), wlk, 'front')), 1, '2 아이가 들어옴' if i == 0 else '')
add(dict(S, child=(end[0], end[1], IDLE, 'front')), 6)
# 3. 의자를 철창 앞으로 주섬주섬: 세 번에 나눠 밀고, 중간에 멈춘다
goal = (36, 88); cur = tuple(chair)
child_x, child_y = end
for k in range(3):
    nxt = (lerp(chair[0], goal[0], (k + 1) / 3), lerp(chair[1], goal[1], (k + 1) / 3))
    for i in range(5):
        t = (i + 1) / 5; cp = (lerp(cur[0], nxt[0], t), lerp(cur[1], nxt[1], t))
        add(dict(chair=cp, child=(cp[0] + 22, cp[1] + 15, WALK[(i + k) % 4], 'front')), 1, '3 의자를 끌고 감' if (k == 0 and i == 0) else '')
    cur = nxt
    add(dict(chair=cur, child=(cur[0] + 22, cur[1] + 15, IDLE, 'front')), 6)          # 쉬었다 다시
CH = cur
cx = CH[0] + 14
# 4. 의자 위로 올라선다(한 번 미끄러지고 다시 오름)
seat_y = CH[1] - 12
for i in range(6): add(dict(chair=CH, child=(lerp(cx, cx, 1), lerp(CH[1] + 12, seat_y, (i + 1) / 6), IDLE, 'front')), 1, '4 의자에 올라섬(미끄러짐)' if i == 0 else '')
for i in range(4): add(dict(chair=CH, child=(cx, seat_y + 7 * math.sin(math.pi * (i + 1) / 4), IDLE, 'front')))   # 미끄러짐
add(dict(chair=CH, child=(cx, seat_y, IDLE, 'front')), 5)
# 5. 철창 윗줄까지 올라 넘는다
for i in range(10):
    t = (i + 1) / 10; add(dict(chair=CH, child=(cx, lerp(seat_y, RAIL_TOP + 4, t), IDLE, 'front')), 1, '5 철창을 넘음' if i == 0 else '')
add(dict(chair=CH, child=(cx, RAIL_TOP + 4, IDLE, 'front')), 4)
# 6. 넘어가는 순간: 아이는 철창 바깥으로, 슬리퍼가 먼저 떨어지고 손전등은 떠오른다
yy, v = RAIL_TOP + 2, 1.0
for i in range(14):
    yy += v; v += 0.9
    add(dict(chair=CH, child=(cx, yy, IDLE, 'behind'), slip=(cx - 14, RAIL_TOP + 4 + (i * 2.2) ** 1.2 * .8), light=(cx + 10, RAIL_TOP - 4 - i * .8)), 1, '6 넘어감: 슬리퍼는 떨어지고 손전등은 떠오름' if i == 0 else '')
for i in range(12): add(dict(chair=CH, light=(cx + 10, RAIL_TOP - 14 - i * .8)), 1)
# 7. 타이틀(착지는 그리지 않는다): 암전 후 제목
for i in range(10): add(dict(chair=CH, fade=(i + 1) / 10), 1, '7 암전' if i == 0 else '')
for i in range(12): add(dict(chair=CH, fade=1.0, title=(i + 1) / 12), 1, '8 타이틀' if i == 0 else '')
add(dict(chair=CH, fade=1.0, title=1.0), 14)

os.makedirs(OUT, exist_ok=True)
frames[0].save(os.path.join(OUT, 'prologue_cutscene.gif'), save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=False)
idx = [i for i, l in enumerate(labels) if l]
cols = 4; rows = math.ceil(len(idx) / cols)
sheet = Image.new('RGB', (cols * 330 + 10, rows * 262 + 10), (50, 50, 56)); d = ImageDraw.Draw(sheet)
F = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 11)
for n, i in enumerate(idx):
    x, y = 10 + (n % cols) * 330, 10 + (n // cols) * 262
    sheet.paste(frames[i], (x, y + 16)); d.text((x, y), labels[i], fill=(230, 230, 210), font=F)
sheet.save(os.path.join(OUT, 'prologue_cutscene_sheet.png')); print(len(frames), 'frames ->', OUT)
