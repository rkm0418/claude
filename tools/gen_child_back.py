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

def swing(im, side, dy):
    """내린 팔의 아래쪽(소매 끝+손, 27~32줄)을 dy칸 올린다: 걸을 때 앞으로 나간 팔."""
    px = im.load(); xs = range(0, 7) if side == 'l' else range(17, 24)
    block = {(x, y): px[x, y] for x in xs for y in range(PAD + 29, PAD + 33)}
    for k in block: px[k] = CLEAR
    for (x, y), c in block.items():
        if c[3]: px[x, y - dy] = c

def bob(im, dy=1):
    out = Image.new('RGBA', im.size, CLEAR); out.alpha_composite(im, (0, -dy)) if dy > 0 else out.alpha_composite(im, (0, 0)); return out

def arm_fwd(im, side, top):
    """앞으로 내민 팔(의자 등받이를 잡음): 어깨에서 바깥 위로 짧게, 손은 가슴~어깨 높이. 소매 명암은 팔과 함께 움직인다."""
    drop_hand(im, side); arm_up(im, side, top)

def make():
    out = {}
    # 걷기 4장: 왼발 듦(+오른팔 앞으로, 몸 살짝 위) → 선 자세 → 오른발 듦(+왼팔 앞으로) → 선 자세
    w = []
    for side, other in (('l', 'r'), ('r', 'l')):
        im = base('child'); lift_leg(im, side, 3); swing(im, other, 2); w.append(bob(im, 1)); w.append(base('child'))
    out['walk'] = w
    out['idle'] = base('child')
    # 의자 밀기 2장: 두 손으로 등받이를 잡고, 한 발씩 내딛으며 팔을 굽혔다 폈다
    push = []
    for k, side in enumerate(('l', 'r')):
        im = base('child'); arm_fwd(im, 'l', PAD + (17 if k == 0 else 15)); arm_fwd(im, 'r', PAD + (17 if k == 0 else 15)); lift_leg(im, side, 2); push.append(im)
    out['push'] = push
    # 잡기(두 손 위로) / 발 올리기(잡은 채 한 발을 높이) / 매달려 당기기
    grab = base('child'); arm_fwd(grab, 'l', PAD + 13); arm_fwd(grab, 'r', PAD + 13); out['grab'] = out['reach'] = grab
    foot = []
    for side in ('l', 'r'):
        im = base('child'); arm_fwd(im, 'l', PAD + 12); arm_fwd(im, 'r', PAD + 12); lift_leg(im, side, 6); foot.append(im)
    out['foot'] = foot
    hang = []
    for k in range(2):
        im = base('child'); arm_fwd(im, 'l', PAD + 11); arm_fwd(im, 'r', PAD + 11); lift_leg(im, 'l' if k == 0 else 'r', 3); hang.append(im)
    out['hang'] = hang
    return out

if __name__ == '__main__':
    s = make()
    flat = [('walk%d' % i, im) for i, im in enumerate(s['walk'], 1)] + [('idle', s['idle'])] + [('push%d' % i, im) for i, im in enumerate(s['push'], 1)] + \
           [('grab', s['grab'])] + [('foot%d' % i, im) for i, im in enumerate(s['foot'], 1)] + [('hang%d' % i, im) for i, im in enumerate(s['hang'], 1)]
    for n, im in flat: im.save(os.path.join(SPR, 'child_b_' + n + '.png'))
    sheet = Image.new('RGBA', (len(flat) * 30 * 4, 46 * 4), (40, 44, 60, 255))
    for i, (n, im) in enumerate(flat): sheet.alpha_composite(im.resize((96, 168), Image.NEAREST), (i * 120 + 12, 8))
    sheet.save(os.path.join(SPR, '..', '..', '..', 'maps', 'out', 'child_back_poses.png')); print(len(flat), 'poses')
