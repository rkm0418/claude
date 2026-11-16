#!/usr/bin/env python3
"""수미상관 컷신(본편 끝, 숲 베란다, 게임 모드 사선 시점).  사용: python3 tools/gen_cutscene_ending.py
출력: maps/out/ending_cutscene.gif (10fps, 320x240), maps/out/ending_cutscene_sheet.png
프롤로그(아파트 베란다 추락)와 같은 순서를 숲에서 되풀이한다: 달려 들어옴 → 무너진 울타리에 막혀 매달려 보며 낑낑 →
뒤를 돌아봄(추격자는 화면에 없음) → 기울어진 옆의 그루터기를 발견해 밟고 울타리에 오름 → 울타리 위에서 잠깐 멈춤 → 기울어지며 울타리 너머로 떨어짐 → 흰 화면."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_balcony_forest as F, gen_child_back as CB, render_maps as R

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out')
LIB = R.load_library()
P = CB.make()                                                    # 아이는 프롤로그와 같은 크기(24x38)로 쓴다
BWALK, BIDLE, BREACH, BHANG, BFOOT = P['walk'], P['idle'], P['reach'], P['hang'], P['foot']
FWALK = [LIB[f'child_w{i}'] for i in (1, 2, 3, 4)]; FIDLE = LIB['child']
CHASER = [LIB[f'chaser_w{i}'] for i in (1, 2, 3, 4)]; CH_IDLE = LIB['chaser']
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
            for dx in (0, 1):
                for dy in (0, 1, 2, 3, 4, 6): img.putpixel((int(bx) + dx, int(by_ + dy)), (240, 240, 220, 255))
    sc = F.scene(actors=actors, flick=(n // 3) % 2).convert('RGB')
    c = Image.new('RGB', (320, 240), (6, 6, 14)); c.paste(sc.resize((232, 204), Image.NEAREST), (44, 18))
    if st.get('white'): c = Image.blend(c, Image.new('RGB', c.size, (255, 255, 255)), st['white'])
    return c

def add(st, n=1, label=''):
    for i in range(n): frames.append(st); labels.append(label if i == 0 else '')
def kid(pos, spr, layer='front', ang=0): return (pos[0], pos[1], spr, layer, ang)

# 자리(화면 좌표): 울타리 앞에서 매달려 보는 곳, 그루터기(의자 역할) 앞과 위, 울타리 윗줄 위
SPOT = S(56, 44)
STUMP = S(34, 41); ST_FRONT = (STUMP[0] + 2, STUMP[1] + 6); ST_TOP = (STUMP[0], STUMP[1] - 11); FTOP = (STUMP[0] + 4, TOP)
RUN, WALK_V, CH_V = 3.0, 1.6, 0.7                                    # 속도(칸/프레임): 달리기, 걷기, 나무 머리(느리지만 멈추지 않음)
chaser_path = [S(-16, -34), S(14, 4), S(30, 30)]
seg_len = [math.dist(chaser_path[k], chaser_path[k + 1]) for k in range(2)]; total = sum(seg_len)
CD = [None]                                                          # 나무 머리가 걸어온 거리(None = 아직 안 나타남)
def chaser(n, moving=True):
    if CD[0] is None: return []
    if moving: CD[0] = min(total, CD[0] + CH_V)
    d = CD[0]; k = 0 if d < seg_len[0] else 1; f = d / seg_len[0] if k == 0 else (d - seg_len[0]) / seg_len[1]
    a, b2 = chaser_path[k], chaser_path[k + 1]
    return [kid((lerp(a[0], b2[0], f), lerp(a[1], b2[1], f)), CHASER[(n // 4) % 4] if moving and d < total else CH_IDLE)]
def go(a, b2, speed, sprites, label='', every=2):
    """a에서 b까지 일정한 속도로 이동(프레임 수 = 거리/속도)."""
    n = max(1, round(math.dist(a, b2) / speed))
    for i in range(n):
        t = (i + 1) / n; add(dict(actors=[kid((lerp(a[0], b2[0], t), lerp(a[1], b2[1], t)), sprites[(i // every) % len(sprites)])] + chaser(len(frames))), 1, label if i == 0 else '')
def hold(pos, spr, n, label='', **kw):
    for i in range(n): add(dict(actors=[kid(pos, spr)] + chaser(len(frames)), **kw), 1, label if i == 0 else '')

# 1. 어두운 숲 베란다, 횃불만 흔들림
add(dict(actors=[]), 10, '1 숲 베란다 (횃불만 흔들림)')
# 2. 아이가 앞쪽에서 달려 들어와 울타리로(뒷모습, 달리기 속도)
go(S(20, -22), SPOT, RUN, BWALK, '2 달려 들어옴', every=1)
# 3. 무너진 울타리에 막힘: 매달려 보며 낑낑(두 번, 사이에 팔을 내리지 않음)
for k in range(2):
    hold(SPOT, BREACH, 3, '3 울타리에 막혀 낑낑' if k == 0 else '')
    for i in range(8): hold((SPOT[0] + (1 if i % 2 else 0), SPOT[1] - 4), BHANG[(i // 2) % 2], 1)
hold(SPOT, BREACH, 4)
# 4. 아이가 뒤를 돌아봄(추격자는 화면에 넣지 않음)
# (추격자는 일단 넣지 않는다: CD[0] 을 0.0 으로 두면 이 시점부터 나타나 다가온다)
hold(SPOT, BIDLE, 6, '4 뒤를 돌아봄'); hold(SPOT, FIDLE, 12)
# 5. 옆의 그루터기를 발견(느낌표) → 그루터기로 걸음을 재촉
hold(SPOT, BIDLE, 6, '5 그루터기를 발견', bang=(SPOT[0] + 10, SPOT[1] - 46))
go(SPOT, ST_FRONT, WALK_V * 1.4, FWALK)
# 6. 그루터기를 잡고 발을 올려 올라섬 → 울타리 윗줄을 잡고 발을 걸쳐 올라섬(프롤로그의 의자·철창과 같은 순서)
hold(ST_FRONT, BREACH, 3, '6 그루터기를 밟고 울타리에 오름'); hold(ST_FRONT, BFOOT[0], 4)
hold(((ST_FRONT[0] + ST_TOP[0]) / 2, (ST_FRONT[1] + ST_TOP[1]) / 2 + 2), BHANG[0], 3); hold(ST_TOP, BIDLE, 5)
def rail(fy, leg=None, lean=0): return CB.hold(round(TOP + 1 - (fy - 42)) - CB.PAD, leg, lean)      # 손이 울타리 윗줄을 놓지 않는 자세
hold(ST_TOP, rail(ST_TOP[1]), 4); hold(ST_TOP, rail(ST_TOP[1], ('r', 6)), 5)
for fy, leg in ((ST_TOP[1] - 6, ('r', 5)), (ST_TOP[1] - 12, ('l', 4)), (TOP + 6, ('r', 4))):
    hold((lerp(ST_TOP[0], FTOP[0], (ST_TOP[1] - fy) / (ST_TOP[1] - TOP)), fy), rail(fy, leg), 4)
hold(FTOP, CB.hold(31, None, 3), 4); hold(FTOP, BIDLE, 2)
# 7. 울타리 위에서 결심한 듯 잠깐 멈춤(프롤로그와 같은 1.6초)
hold(FTOP, BIDLE, 16, '7 울타리 위에서 멈춤')
# 8. 옆으로 기울어지며 울타리 너머로 떨어짐(프롤로그와 같은 동작). 나무 머리는 멈춰 선다
for i in range(8):
    add(dict(actors=[kid((FTOP[0] + i * .4, FTOP[1]), BIDLE, 'front', -(i + 1) * 3)] + chaser(len(frames), False)), 1, '8 기울어지며 떨어짐' if i == 0 else '')
yy, v, ang = FTOP[1], .6, -24
for i in range(14):
    yy += v; v += .8; ang -= 4
    add(dict(actors=[kid((FTOP[0] + 4 + i * .3, yy), BIDLE, 'behind', ang)] + chaser(len(frames), False)))
add(dict(actors=chaser(0, False)), 10)
# 9. 흰 화면(프롤로그의 암전과 대비)
for i in range(12): add(dict(actors=chaser(0, False), white=(i + 1) / 12), 1, '9 흰 화면' if i == 0 else '')
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
