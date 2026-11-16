#!/usr/bin/env python3
"""괴물(나무 머리)과 조력자(토끼·고양이·곰)의 방향별 움직임 스프라이트를 정면 그림에서 절차적으로 만든다.  사용: python3 tools/gen_actor_dirs.py
출력: art/out/sprites/actors/<이름>_<방향>_<프레임>.png, art/out/sprites/actors/manifest.json, maps/out/actors_sheet.png
방향: d(정면) u(뒷모습) l r(옆).  프레임: idle, w1~w4(걷기), 괴물은 추가로 sway1~2(가만히 서서 흔들림), lurch1~2(덮치듯 앞으로 기울어짐).
조력자: 아이와 같은 차분한 걷기(한 발 2칸 들기 + 반대쪽 팔 1칸, 몸은 들썩이지 않음). 뒷모습 = 얼굴·옷 앞 장식을 지우고 꼬리, 옆모습 = 얼굴 요소를
오른쪽에 눈 하나·볼·코로 다시 찍고 몸통을 좁힘(SPECS 에 캐릭터별 좌표). 괴물: 걷기 8장(s1~s8, 원본 4장 + 사이 프레임), 옆모습은 가로로 눌러 좁힘 + 기울임(임시).
기준점은 모두 아래 가운데."""
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
for dd in ('d', 'u', 'r'):                                   # 부드러운 걷기: 원본 4장 사이에 몸이 좌우로 1칸 실리는 사이 프레임을 넣어 8장(s1~s8)
    seq = [cs[dd][f'w{k}'] for k in (1, 2, 3, 4)]
    for k in range(4):
        cs[dd][f's{2 * k + 1}'] = seq[k]; cs[dd][f's{2 * k + 2}'] = shift(seq[(k + 1) % 4], -1 if k % 2 == 0 else 1)
cs['l'] = {k: flip(v) for k, v in cs['r'].items()}
ACTORS['chaser'] = cs
# 조력자: 아이와 같은 방식의 차분한 걷기(한 발을 2칸 들고 반대쪽 팔을 1칸 흔듦, 몸은 들썩이지 않음), 뒷모습·옆모습은 캐릭터별 규칙으로 다시 그린다
def inner(px, x, y, W, H):
    return all(0 <= x + dx < W and 0 <= y + dy < H and px[x + dx, y + dy][3] for dx in (-1, 0, 1) for dy in (-1, 0, 1))
def wipe(im, y0, y1, fur, colors=(), eyes=True, x0=0, x1=None):
    """y0~y1 줄에서 얼굴 요소(안쪽 외곽선색 = 눈·입, colors 에 든 색 = 볼·코·주둥이)를 털색으로 덮는다."""
    out = im.copy(); px = out.load(); W, H = im.size; src = im.load(); x1 = W if x1 is None else x1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1):
            p = src[x, y]
            if not p[3]: continue
            if (eyes and p == OUTLINE and inner(src, x, y, W, H)) or p in colors: px[x, y] = fur
    return out
def move(im, box, dx=0, dy=0):
    """box(x0,y0,x1,y1) 안의 그림을 (dx,dy)만큼 옮긴다(원래 자리는 비움)."""
    out = im.copy(); blk = im.crop(box); out.paste(CLEAR, box); out.alpha_composite(blk, (box[0] + dx, box[1] + dy)); return out
def dots(im, pts, col):
    px = im.load()
    for (x, y) in pts:
        if 0 <= x < im.width and 0 <= y < im.height and px[x, y][3] and px[x, y] != OUTLINE: px[x, y] = col
    return im
def narrow(im, y0, y1, c0, c1):
    """y0~y1 줄에서 가운데 c0~c1 열을 빼고 좌우를 붙여 몸통을 좁힌다(옆모습)."""
    W, H = im.size; out = im.copy(); out.paste(CLEAR, (0, y0, W, y1 + 1)); n = c1 - c0 + 1
    out.alpha_composite(im.crop((0, y0, c0, y1 + 1)), (n // 2, y0)); out.alpha_composite(im.crop((c1 + 1, y0, W, y1 + 1)), (c0 + n // 2, y0)); return out
def puff(im, cx, cy, fur):                                    # 꼬리(뒷모습): 작은 털 뭉치 + 외곽선
    px = im.load()
    for dx in range(-2, 3):
        for dy in range(-1, 2):
            if abs(dx) == 2 or abs(dy) == 1: px[cx + dx, cy + dy] = OUTLINE if not (abs(dx) == 2 and abs(dy) == 1) else px[cx + dx, cy + dy]
    for dx in (-1, 0, 1): px[cx + dx, cy] = fur
    return im

def helper(name, sp):
    A_ = load(name + '_A'); W, H = A_.size; fur = sp['fur']
    legL, legR, armL, armR = sp['legL'], sp['legR'], sp.get('armL'), sp.get('armR')
    def cycle(base, lift=2):
        f1 = move(base, legL, 0, -lift); f3 = move(base, legR, 0, -lift)
        if armR: f1 = move(f1, armR, 0, -1)
        if armL: f3 = move(f3, armL, 0, -1)
        if sp.get('tail'): f1 = move(f1, sp['tail'], 0, -1); f3 = move(f3, sp['tail'], 0, 1 if sp['tail'][3] < H else 0)
        return {'idle': base, 'w1': f1, 'w2': base, 'w3': f3, 'w4': base}
    d = cycle(A_); d.update({f'face_{c}': load(f'{name}_{c}') for c in 'ABCDE'})
    # 뒷모습: 얼굴·귀 안쪽·옷 앞 장식을 지우고 꼬리를 단다
    bk = wipe(A_, 0, sp['face'][1], fur, sp['face_cols'] + sp.get('ear_cols', ()))
    if sp.get('front_cols'): bk = wipe(bk, sp['body'][0], sp['body'][1], sp['cloth'], sp['front_cols'], eyes=True, x0=sp['front_x'][0], x1=sp['front_x'][1])
    if sp.get('puff'): bk = puff(bk, *sp['puff'], fur)
    u = cycle(bk)
    # 옆모습(오른쪽을 봄): 얼굴 요소를 지우고 오른쪽에 눈 하나·볼·코를 다시 찍는다. 몸통은 좁히고 먼 쪽 팔은 숨긴다
    sd = wipe(A_, sp['face'][0], sp['face'][1], fur, sp['face_cols'])
    sd = dots(sd, sp['side_eye'], OUTLINE); sd = dots(sd, sp['side_blush'], sp['blush'])
    for col, pts in sp.get('side_extra', ()): sd = dots(sd, pts, col)
    if sp.get('flip_body'):                                  # 고양이: 몸통을 뒤집어 꼬리가 뒤(왼쪽)로 가게
        y0 = sp['body'][0]; body = flip(sd.crop((0, y0, W, H))); sd.paste(CLEAR, (0, y0, W, H)); sd.alpha_composite(body, (0, y0))
    if sp.get('narrow'): sd = narrow(sd, sp['body'][0], H - 1, *sp['narrow'])
    def side_cycle(base):
        if sp.get('flip_body'):
            bl, br = (W - legR[2], legR[1], W - legR[0], legR[3]), (W - legL[2], legL[1], W - legL[0], legL[3])
            return {'idle': base, 'w1': move(base, br, 0, -2), 'w2': base, 'w3': move(base, bl, 0, -2), 'w4': base}
        n = (sp['narrow'][1] - sp['narrow'][0] + 1) // 2 if sp.get('narrow') else 0
        nl = (legL[0] + n, legL[1], legL[2] + n, legL[3]); nr = (legR[0] - n, legR[1], legR[2] - n, legR[3])
        f1 = move(move(base, nr, 2, -1), nl, -1, 0); f3 = move(move(base, nl, 2, -1), nr, -1, 0)      # 한 발은 앞으로 나가며 들리고, 다른 발은 뒤로
        return {'idle': base, 'w1': f1, 'w2': base, 'w3': f3, 'w4': base}
    r = side_cycle(sd)
    return {'d': d, 'u': u, 'r': r, 'l': {k: flip(v) for k, v in r.items()}}

WHITE, PINK, TAN, CREAM = (247, 245, 240, 255), (232, 168, 152, 255), (211, 165, 116, 255), (242, 220, 180, 255)
SPECS = {
 'rabbit_red': dict(fur=WHITE, blush=PINK, face=(10, 23), face_cols=(PINK,), ear_cols=(), body=(24, 36), cloth=(216, 64, 58, 255),
                    front_cols=((216, 207, 192, 255), WHITE, (154, 59, 59, 255), (232, 207, 106, 255)), front_x=(7, 17), puff=(11, 33),
                    legL=(6, 37, 12, 42), legR=(12, 37, 18, 42), armL=(3, 31, 7, 36), armR=(17, 31, 21, 36), narrow=(10, 13),
                    side_eye=[(16, 16), (17, 16), (16, 17), (17, 17), (16, 18), (17, 18), (20, 19)], side_blush=[(17, 20), (18, 20), (19, 20), (17, 21), (18, 21), (19, 21)]),
 'cat_white': dict(fur=WHITE, blush=PINK, face=(6, 17), face_cols=(PINK, (199, 122, 154, 255)), body=(18, 29), legL=(6, 27, 12, 30), legR=(12, 27, 18, 30), tail=(18, 18, 26, 26), flip_body=True,
                   side_eye=[(17, 11), (16, 12), (17, 12), (18, 12), (17, 13)], side_blush=[(18, 15), (19, 15), (20, 15), (18, 16), (19, 16), (20, 16)],
                   side_extra=[((199, 122, 154, 255), [(21, 14)])]),
 'bear_green': dict(fur=TAN, blush=PINK, face=(7, 17), face_cols=(PINK, CREAM, (90, 70, 54, 255)), body=(18, 27), cloth=(111, 143, 88, 255), front_cols=(CREAM, (155, 199, 124, 255)), front_x=(9, 16), puff=(11, 25),
                    legL=(5, 28, 12, 32), legR=(12, 28, 20, 32), armL=(2, 20, 7, 28), armR=(17, 20, 22, 28), narrow=(10, 13),
                    side_eye=[(16, 11), (17, 11), (16, 12), (17, 12)], side_blush=[(13, 14), (14, 14), (15, 14), (13, 15), (14, 15)],
                    side_extra=[(CREAM, [(x, y) for x in range(18, 22) for y in range(12, 17)]), ((90, 70, 54, 255), [(20, 13), (21, 13)]), (OUTLINE, [(19, 16), (20, 16)])]),
}
for name, sp in SPECS.items(): ACTORS[name] = helper(name, sp)

if __name__ == '__main__':
    man = {}
    for name, dirs in ACTORS.items():
        man[name] = {'size': list(dirs['d']['idle'].size), 'anchor': 'bottom-center', 'directions': {d: sorted(fr) for d, fr in dirs.items()}, 'walk_cycle': ['w1', 'w2', 'w3', 'w4'] if name != 'chaser' else [f's{k}' for k in range(1, 9)], 'fps': 6 if name != 'chaser' else 8}
        for d, frs in dirs.items():
            for k, im in frs.items(): im.save(os.path.join(OUT, f'{name}_{d}_{k}.png'))
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1, ensure_ascii=False)
    S = 3; rows = [(n, d) for n in ACTORS for d in ('d', 'u', 'r', 'l')]
    cw = 32 * S; rh = 66 * S; cols = ['idle', 'w1', 'w2', 'w3', 'w4', 'lurch1', 'lurch2']
    sheet = Image.new('RGBA', (len(cols) * cw + 8, len(rows) * rh + 8), (44, 48, 64, 255))
    for r_, (n, d) in enumerate(rows):
        for c, k in enumerate(cols):
            im = ACTORS[n][d].get(k)
            if im: sheet.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (4 + c * cw, 4 + r_ * rh + (rh - im.height * S)))
    sheet.save(os.path.join(SPR, '..', '..', '..', 'maps', 'out', 'actors_sheet.png')); print('actors:', sum(len(f) for a in ACTORS.values() for f in a.values()), 'sprites')
