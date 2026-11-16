#!/usr/bin/env python3
"""괴물(나무 머리)과 조력자(토끼·고양이·곰)의 방향별 움직임 스프라이트를 정면 그림에서 절차적으로 만든다.  사용: python3 tools/gen_actor_dirs.py
출력: art/out/sprites/actors/<이름>_<방향>_<프레임>.png, art/out/sprites/actors/manifest.json, maps/out/actors_sheet.png
방향: d(정면) u(뒷모습) l r(옆).  프레임: idle, w1~w4(걷기), 괴물은 추가로 sway1~2(가만히 서서 흔들림), lurch1~2(덮치듯 앞으로 기울어짐).
정면만 손으로 그린 원본이고 나머지는 자동 변환(임시 품질)이다: 뒷모습 = 머리 안쪽을 털/머리 색으로 덮음, 옆모습 = 가로로 눌러 좁힘 + 앞으로 기울임.
걷기(조력자) = 한쪽 다리를 2칸 들고 몸을 1칸 올림. 기준점은 모두 아래 가운데."""
import json, os
from collections import Counter
from PIL import Image
SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'out', 'sprites')
OUT = os.path.join(SPR, 'actors'); os.makedirs(OUT, exist_ok=True)
CLEAR = (0, 0, 0, 0); OUTLINE = (26, 22, 32, 255)
load = lambda n: Image.open(os.path.join(SPR, n + '.png')).convert('RGBA')
flip = lambda im: im.transpose(Image.FLIP_LEFT_RIGHT)

def step(im, side, leg_h=5, lift=2, bob=1):
    """한쪽 다리(아래 leg_h 줄의 왼/오른 절반)를 lift칸 들고, 몸 전체를 bob칸 올린 걷기 한 장."""
    W, H = im.size; out = Image.new('RGBA', (W, H), CLEAR)
    body = im.crop((0, 0, W, H - leg_h)); out.alpha_composite(body, (0, -bob))
    cx = W // 2
    for s, box in (('l', (0, H - leg_h, cx, H)), ('r', (cx, H - leg_h, W, H))):
        leg = im.crop(box); out.alpha_composite(leg, (box[0], box[1] - (lift if s == side else 0)))
    return out
def walk4(im, **kw): return [step(im, 'l', **kw), im, step(im, 'r', **kw), im]

def back(im, head_h, keep=()):
    """뒷모습: 머리(위 head_h 줄) 안쪽 색을 가장 많은 색 하나로 덮어 얼굴을 지운다. keep 색은 남긴다(귀 안쪽 등)."""
    out = im.copy(); px = out.load(); W, H = im.size
    inner = [px[x, y] for y in range(head_h) for x in range(W) if px[x, y][3] and px[x, y] != OUTLINE]
    fur = Counter(inner).most_common(1)[0][0]
    for y in range(head_h):
        for x in range(W):
            if px[x, y][3] and px[x, y] != OUTLINE and px[x, y] not in keep: px[x, y] = fur
    return out
def side(im, fx=.7, lean=.06):
    """옆모습(오른쪽을 봄): 가로를 fx 배로 눌러 좁히고, 위로 갈수록 앞(오른쪽)으로 기울인다."""
    W, H = im.size; nw = max(2, round(W * fx)); sq = im.resize((nw, H), Image.NEAREST); out = Image.new('RGBA', (W, H), CLEAR)
    for y in range(H):
        row = sq.crop((0, y, nw, y + 1)); out.alpha_composite(row, ((W - nw) // 2 + round((H - y) * lean), y))
    return out
def lean_fwd(im, k):
    """정면에서 덮치듯 앞으로 숙임: 위쪽을 아래로 눌러 짧아 보이게(k = 0~1)."""
    W, H = im.size; nh = round(H * (1 - .18 * k)); out = Image.new('RGBA', (W, H), CLEAR)
    out.alpha_composite(im.resize((W, nh), Image.NEAREST), (0, H - nh)); return out
def shift(im, dx):
    out = Image.new('RGBA', im.size, CLEAR); out.alpha_composite(im, (dx, 0)); return out

ACTORS = {}
# 괴물: 정면 걷기 4장은 원본(chaser_w1~4). 뒷모습은 가슴 무늬만 지움(머리는 나무라 앞뒤가 같다)
ch = {'idle': load('chaser'), **{f'w{i}': load(f'chaser_w{i}') for i in (1, 2, 3, 4)}}
def chaser_back(im):
    out = im.copy(); px = out.load(); W, H = im.size
    body = [px[x, y] for y in range(28, 44) for x in range(W) if px[x, y][3]]
    dark = Counter(body).most_common(1)[0][0]
    for y in range(28, 42):
        for x in range(9, 21):
            if px[x, y][3] and sum(px[x, y][:3]) > sum(dark[:3]) + 60: px[x, y] = dark
    return out
cs = {'d': dict(ch), 'u': {k: chaser_back(v) for k, v in ch.items()}, 'r': {k: side(v, .62, .08) for k, v in ch.items()}}
cs['d'].update(sway1=shift(ch['idle'], -1), sway2=shift(ch['idle'], 1), lurch1=lean_fwd(ch['w1'], .5), lurch2=lean_fwd(ch['w3'], 1))
cs['u'].update(sway1=shift(cs['u']['idle'], -1), sway2=shift(cs['u']['idle'], 1))
cs['r'].update(lurch1=side(ch['w1'], .62, .16), lurch2=side(ch['w3'], .62, .24))
cs['l'] = {k: flip(v) for k, v in cs['r'].items()}
ACTORS['chaser'] = cs
# 조력자: 표정 A~E 중 A(기본)로 걷기·방향을 만들고, 표정 5종은 정면 서기로 그대로 둔다
for name, head_h, keep in (('rabbit_red', 28, ()), ('cat_white', 19, ()), ('bear_green', 19, ())):
    base = load(name + '_A'); w = walk4(base)
    d = {'idle': base, 'w1': w[0], 'w2': w[1], 'w3': w[2], 'w4': w[3], **{f'face_{c}': load(f'{name}_{c}') for c in 'ABCDE'}}
    core = {k: d[k] for k in ('idle', 'w1', 'w2', 'w3', 'w4')}
    u = {k: back(v, head_h, keep) for k, v in core.items()}; r = {k: side(v, .72, .03) for k, v in core.items()}
    ACTORS[name] = {'d': d, 'u': u, 'r': r, 'l': {k: flip(v) for k, v in r.items()}}

if __name__ == '__main__':
    man = {}
    for name, dirs in ACTORS.items():
        man[name] = {'size': list(dirs['d']['idle'].size), 'anchor': 'bottom-center', 'directions': {d: sorted(fr) for d, fr in dirs.items()}, 'walk_cycle': ['w1', 'w2', 'w3', 'w4'], 'fps': 6 if name != 'chaser' else 4}
        for d, frs in dirs.items():
            for k, im in frs.items(): im.save(os.path.join(OUT, f'{name}_{d}_{k}.png'))
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1, ensure_ascii=False)
    S = 2; rows = [(n, d) for n in ACTORS for d in ('d', 'u', 'r', 'l')]
    cw = 34 * S; rh = 68 * S; cols = ['idle', 'w1', 'w2', 'w3', 'w4', 'sway1', 'lurch1', 'lurch2']
    sheet = Image.new('RGBA', (len(cols) * cw + 8, len(rows) * rh + 8), (44, 48, 64, 255))
    for r_, (n, d) in enumerate(rows):
        for c, k in enumerate(cols):
            im = ACTORS[n][d].get(k)
            if im: sheet.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (4 + c * cw, 4 + r_ * rh + (rh - im.height * S)))
    sheet.save(os.path.join(SPR, '..', '..', '..', 'maps', 'out', 'actors_sheet.png')); print('actors:', sum(len(f) for a in ACTORS.values() for f in a.values()), 'sprites')
