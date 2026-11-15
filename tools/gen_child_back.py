#!/usr/bin/env python3
"""주인공 뒷모습 동작 스프라이트(컷신용, 24x42: 위로 뻗은 팔을 위해 위쪽 4칸 여유).
걷기 4장(앞모습 걷기에서 얼굴·옷깃을 뒷모습으로), 서기, 매달리기(두 팔 위, 다리 버둥 2장), 올라가기(한 팔·한 다리 위, 좌우 2장).
사용: python3 tools/gen_child_back.py -> art/out/sprites/child_b_*.png"""
import os
from PIL import Image
SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'out', 'sprites')
A, HAIR, HL = (26, 22, 32, 255), (90, 70, 54, 255), (138, 106, 78, 255)
SKIN, SKIN2, SH, SH2 = (242, 220, 180, 255), (211, 165, 116, 255), (47, 74, 58, 255), (31, 51, 41, 255)
PAD = 4
CLEAR = (0, 0, 0, 0)

def base(name):
    src = Image.open(os.path.join(SPR, name + '.png')).convert('RGBA')
    im = Image.new('RGBA', (24, 38 + PAD), CLEAR); im.alpha_composite(src, (0, PAD)); px = im.load()
    for y in range(PAD, PAD + 20):                         # 얼굴 -> 뒷머리
        for x in range(24):
            if px[x, y] in (SKIN, SKIN2): px[x, y] = HAIR
    for y in range(PAD + 19, PAD + 24):                    # 앞 옷깃 -> 등판
        for x in range(24):
            if px[x, y] in (SKIN, SKIN2): px[x, y] = SH
    return im

def drop_hand(im, side):
    """옆으로 내린 손(29~32줄 바깥쪽)을 지운다. side: 'l' | 'r'"""
    px = im.load()
    for y in range(PAD + 29, PAD + 33):
        for x in (range(0, 7) if side == 'l' else range(17, 24)): px[x, y] = CLEAR

def arm_up(im, side, top=PAD + 13):
    """어깨(23줄)에서 짧게 들어 올린 팔(2등신 비율: 내린 팔 길이와 같은 약 8칸). top: 손 윗끝 높이"""
    px = im.load(); xs = (2, 3, 4, 5) if side == 'l' else (18, 19, 20, 21)
    for y in range(top + 2, PAD + 24):                     # 소매(머리 옆을 살짝 덮는다)
        px[xs[0], y] = A; px[xs[1], y] = SH; px[xs[2], y] = SH2; px[xs[3], y] = A
    for y in (top, top + 1):                               # 손
        px[xs[0], y] = A; px[xs[1], y] = SKIN; px[xs[2], y] = SKIN2; px[xs[3], y] = A
    px[xs[1], top - 1] = A; px[xs[2], top - 1] = A

def lift_leg(im, side, dy):
    """다리(29~37줄)를 dy칸 들어 올린다(무릎 굽힘)."""
    px = im.load(); xs = range(6, 12) if side == 'l' else range(12, 18)
    block = {(x, y): px[x, y] for x in xs for y in range(PAD + 29, PAD + 38)}
    for (x, y) in block: px[x, y] = CLEAR
    for (x, y), c in block.items():
        if y - dy >= PAD + 29 and c[3]: px[x, y - dy] = c
    for x in xs:                                            # 들린 발바닥 선
        if px[x, PAD + 37 - dy][3]: px[x, PAD + 37 - dy] = A

def make():
    out = {}
    out['walk'] = [base(f'child_w{i}') for i in (1, 2, 3, 4)]
    out['idle'] = base('child')
    hang = []
    for k in range(2):
        im = base('child'); drop_hand(im, 'l'); drop_hand(im, 'r'); arm_up(im, 'l', PAD + 11); arm_up(im, 'r', PAD + 11)
        lift_leg(im, 'l' if k == 0 else 'r', 3); hang.append(im)
    out['hang'] = hang
    climb = []
    for side in ('l', 'r'):
        im = base('child'); drop_hand(im, side); arm_up(im, side, PAD + 12); lift_leg(im, side, 4); climb.append(im)
    out['climb'] = climb
    reach = base('child'); drop_hand(reach, 'l'); drop_hand(reach, 'r'); arm_up(reach, 'l', PAD + 13); arm_up(reach, 'r', PAD + 13)
    out['reach'] = reach
    return out

if __name__ == '__main__':
    s = make()
    flat = [('walk%d' % i, im) for i, im in enumerate(s['walk'], 1)] + [('idle', s['idle']), ('reach', s['reach'])] + \
           [('hang%d' % i, im) for i, im in enumerate(s['hang'], 1)] + [('climb%d' % i, im) for i, im in enumerate(s['climb'], 1)]
    for n, im in flat: im.save(os.path.join(SPR, 'child_b_' + n + '.png'))
    sheet = Image.new('RGBA', (len(flat) * 30 * 4, 46 * 4), (40, 44, 60, 255))
    for i, (n, im) in enumerate(flat): sheet.alpha_composite(im.resize((96, 168), Image.NEAREST), (i * 120 + 12, 8))
    sheet.save(os.path.join(SPR, '..', '..', '..', 'maps', 'out', 'child_back_poses.png')); print(len(flat), 'poses')
