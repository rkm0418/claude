#!/usr/bin/env python3
"""주인공 뒷모습 동작 스프라이트(컷신용, 24x42: 위쪽 4칸 여유).
팔은 '어깨→팔꿈치→손' 관절 선으로 그린다: 길이가 항상 같고(위팔 4 + 아래팔 4칸), 어깨에서 시작해 몸통과 이어진다.
사용: python3 tools/gen_child_back.py -> art/out/sprites/child_b_*.png, maps/out/child_back_poses.png"""
import os
from PIL import Image
SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'out', 'sprites')
A, HAIR = (26, 22, 32, 255), (90, 70, 54, 255)
SKIN, SKIN2, SH, SH2 = (242, 220, 180, 255), (211, 165, 116, 255), (47, 74, 58, 255), (31, 51, 41, 255)
PAD = 4; CLEAR = (0, 0, 0, 0)
SHL, SHR = (6, PAD + 22), (17, PAD + 22)                    # 어깨 관절(왼쪽, 오른쪽)

def base():
    src = Image.open(os.path.join(SPR, 'child.png')).convert('RGBA')
    im = Image.new('RGBA', (24, 38 + PAD), CLEAR); im.alpha_composite(src, (0, PAD)); px = im.load()
    for y in range(PAD, PAD + 24):                          # 얼굴·옷깃 -> 뒷머리·등판
        for x in range(24):
            if px[x, y] in (SKIN, SKIN2): px[x, y] = HAIR if y < PAD + 20 else SH
    return im

def strip_arms(im):
    """내린 팔(소매 21~28줄 바깥 3칸, 손 29~32줄)을 지우고 몸통 옆선을 다시 긋는다."""
    px = im.load()
    for y in range(PAD + 21, PAD + 33):
        for x in list(range(0, 6)) + list(range(18, 24)): px[x, y] = CLEAR
    for y in range(PAD + 21, PAD + 29): px[5, y] = A; px[18, y] = A
    return im

def limb(im, pts, over_head=True):
    """관절 선(어깨, 팔꿈치, 손)을 2칸 굵기 소매로 그리고 끝에 손을 그린다. 외곽선 포함."""
    px = im.load(); fill = {}
    def stamp(x, y):
        for dx in (0, 1):
            for dy in (0, 1): fill[(x + dx, y + dy)] = SH if dx == 0 else SH2
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n + 1): stamp(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n))
    hx, hy = pts[-1]
    hand = {(hx + dx, hy + dy): (SKIN if dx == 0 else SKIN2) for dx in (0, 1) for dy in (0, 1)}
    # 손은 팔 끝에서 진행 방향으로 한 칸 더 나가게
    ex, ey = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]; sx = (ex > 0) - (ex < 0); sy = (ey > 0) - (ey < 0)
    hand = {(x + sx, y + sy + (sy == 0) * 0): c for (x, y), c in hand.items()} if (sx or sy) else hand
    allp = dict(fill); allp.update(hand)
    for (x, y) in list(allp):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in allp and 0 <= q[0] < 24 and 0 <= q[1] < im.height: px[q] = A
    for (x, y), c in allp.items():
        if 0 <= x < 24 and 0 <= y < im.height: px[x, y] = c

def pose(arm_l, arm_r, leg=None, lean=0, raised=False):
    """arm_*: (팔꿈치, 손) 좌표(PAD 포함 전 기준 줄 번호). leg: ('l'|'r', dy). lean: 몸을 앞으로 숙인 칸 수. raised: 팔을 든 자세(어깨가 따라 올라감)"""
    im = strip_arms(base()); px = im.load()
    core = {(x, y): px[x, y] for x in range(5, 19) for y in range(PAD + 19, PAD + 29)}
    P = lambda p: (p[0], p[1] + PAD)
    sl, sr = (SHL[0], SHL[1] - (1 if raised else 0)), (SHR[0], SHR[1] - (1 if raised else 0))
    limb(im, [sl, P(arm_l[0]), P(arm_l[1])]); limb(im, [sr, P(arm_r[0]), P(arm_r[1])])
    for k, c in core.items():                               # 몸통을 팔 위에 다시 그려 어깨 이음매를 덮는다
        if c[3] and not (k[0] in (5, 18) and PAD + 20 <= k[1] <= PAD + 23): px[k] = c
    for x, sx in ((5, 4), (18, 19)):                        # 어깨: 팔이 향하는 쪽으로 옷이 이어진다
        for y in range(PAD + 21, PAD + 24): px[x, y] = SH if x == 5 else SH2
        if raised: px[x, PAD + 20] = A; px[sx, PAD + 21] = px[sx, PAD + 21] if px[sx, PAD + 21][3] else A
    if leg: lift_leg(im, *leg)
    if lean:
        out = Image.new('RGBA', im.size, CLEAR)
        out.alpha_composite(im.crop((0, 0, 24, PAD + 29)), (0, lean)); out.alpha_composite(im.crop((0, PAD + 29, 24, im.height)), (0, PAD + 29))
        im = out
    return im

def lift_leg(im, side, dy):
    """다리(29~37줄)를 dy칸 들어 올린다(무릎 굽힘)."""
    px = im.load(); xs = range(6, 12) if side == 'l' else range(12, 18)
    block = {(x, y): px[x, y] for x in xs for y in range(PAD + 29, PAD + 38)}
    for k in block: px[k] = CLEAR
    for (x, y), c in block.items():
        if y - dy >= PAD + 29 and c[3]: px[x, y - dy] = c
    for x in xs:
        if px[x, PAD + 37 - dy][3]: px[x, PAD + 37 - dy] = A

DOWN_L, DOWN_R = ((4, 26), (4, 29)), ((19, 26), (19, 29))          # 내린 팔
def make():
    out = {}
    out['idle'] = pose(DOWN_L, DOWN_R)
    # 걷기 4장: 왼발 듦 + 오른팔 앞으로(뒤에서 보면 짧아 보임), 선 자세, 반대
    w1 = pose(((3, 25), (3, 28)), ((19, 25), (20, 27)), ('l', 3)); w3 = pose(((4, 25), (3, 27)), ((20, 25), (20, 28)), ('r', 3))
    def bob(im):
        o = Image.new('RGBA', im.size, CLEAR); o.alpha_composite(im, (0, -1)); return o
    out['walk'] = [bob(w1), out['idle'], bob(w3), out['idle']]
    # 의자 밀기 2장: 몸을 앞으로 숙이고 두 손으로 등받이 양 끝을 잡는다. 팔꿈치가 굽혔다 펴지고 한 발씩 내딛는다
    out['push'] = [pose(((3, 25), (2, 22)), ((20, 25), (21, 22)), ('l', 2), lean=1),
                   pose(((3, 23), (2, 20)), ((20, 23), (21, 20)), ('r', 2), lean=2)]
    # 잡기: 두 팔을 위로(팔 길이 그대로), 어깨가 따라 올라간다
    up_l, up_r = ((4, 18), (4, 14)), ((19, 18), (19, 14))
    out['grab'] = out['reach'] = pose(up_l, up_r, raised=True)
    # 발 올리기: 잡은 채로 한 발을 높이 올린다
    out['foot'] = [pose(up_l, up_r, ('l', 6), raised=True), pose(up_l, up_r, ('r', 6), raised=True)]
    # 끌어올리기: 팔꿈치를 굽혀 당긴다(손은 같은 자리, 몸이 올라옴)
    bent_l, bent_r = ((2, 20), (4, 17)), ((21, 20), (19, 17))
    out['hang'] = [pose(bent_l, bent_r, ('l', 4), raised=True), pose(bent_l, bent_r, ('r', 4), raised=True)]
    return out

if __name__ == '__main__':
    s = make()
    flat = [('walk%d' % i, im) for i, im in enumerate(s['walk'], 1)] + [('idle', s['idle'])] + [('push%d' % i, im) for i, im in enumerate(s['push'], 1)] + \
           [('grab', s['grab'])] + [('foot%d' % i, im) for i, im in enumerate(s['foot'], 1)] + [('hang%d' % i, im) for i, im in enumerate(s['hang'], 1)]
    for n, im in flat: im.save(os.path.join(SPR, 'child_b_' + n + '.png'))
    sheet = Image.new('RGBA', (len(flat) * 120, 46 * 4), (40, 44, 60, 255))
    for i, (n, im) in enumerate(flat): sheet.alpha_composite(im.resize((96, 168), Image.NEAREST), (i * 120 + 12, 8))
    sheet.save(os.path.join(SPR, '..', '..', '..', 'maps', 'out', 'child_back_poses.png')); print(len(flat), 'poses')
