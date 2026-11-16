#!/usr/bin/env python3
"""괴물(나무 머리)의 기괴한 움직임. 정면 걷기 원본을 변형해 만든다.  사용: python3 tools/gen_chaser_creepy.py
출력: art/out/sprites/actors/chaser_d_<동작><번호>.png (+ 옆모습 chaser_r_/chaser_l_), art/out/sprites/actors/chaser_creepy.json(프레임 순서와 장당 시간),
      maps/out/chaser_creepy.gif, maps/out/chaser_creepy_strip.png
동작: tw(경련 걸음: 몸이 좌우로 꺾이며 불규칙한 박자) / tilt(고개 꺾임: 나무 머리가 천천히 기울다 툭 꺾임) /
      st(늘어남: 몸이 위로 길게 늘어났다가 툭 떨어짐) / gl(끊김: 가로줄이 어긋나는 화면 깨짐, 라디오 잡음과 짝) / cr(기어옴: 허리가 꺾여 낮게 다가옴) /
      ooze(목이 꺾이며 안에서 탁한 청록빛 진액이 흘러나와 몸을 타고 발밑에 고임)"""
import json, os, random, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_actor_dirs as G
OUT = G.OUT; CLEAR = (0, 0, 0, 0); NECK_Y = 27                 # 0~26줄 = 나무 머리, 27줄부터 몸
W, H = 30, 64; PADX, PADT = 10, 14                             # 변형이 잘리지 않게 여유를 둔 캔버스(50x78), 발 기준점은 아래 가운데
CW, CHh = W + PADX * 2, H + PADT
base = {k: G.load('chaser' + ('' if k == 'idle' else '_' + k)) for k in ('idle', 'w1', 'w2', 'w3', 'w4')}
def canvas(im, dx=0, dy=0):
    out = Image.new('RGBA', (CW, CHh), CLEAR); out.alpha_composite(im, (PADX + dx, PADT + dy)); return out
def shear(im, top_dx, pivot=H):
    """발(pivot 줄)은 그대로 두고 위로 갈수록 top_dx 까지 옆으로 밀린다: 몸이 옆으로 꺾임."""
    out = Image.new('RGBA', (CW, CHh), CLEAR)
    for y in range(im.height):
        t = max(0, (pivot - y) / pivot); out.alpha_composite(im.crop((0, y, im.width, y + 1)), (PADX + round(top_dx * t), PADT + y))
    return out
def tilt_head(im, ang, drop=0):
    """나무 머리만 목을 축으로 ang 도 기울인다(drop: 머리가 아래로 처지는 칸 수)."""
    out = Image.new('RGBA', (CW, CHh), CLEAR); out.alpha_composite(im.crop((0, NECK_Y, W, H)), (PADX, PADT + NECK_Y))
    head = Image.new('RGBA', (CW, CHh), CLEAR); head.alpha_composite(im.crop((0, 0, W, NECK_Y)), (PADX, PADT))
    head = head.rotate(ang, resample=Image.NEAREST, center=(PADX + W / 2, PADT + NECK_Y))
    out.alpha_composite(head, (0, drop)); return out
def stretch(im, f):
    """몸(목 아래)을 세로로 f 배 늘린다. 발은 그대로, 머리가 위로 올라간다."""
    body = im.crop((0, NECK_Y, W, H)); nh = round(body.height * f); body = body.resize((W, nh), Image.NEAREST)
    out = Image.new('RGBA', (CW, CHh), CLEAR); out.alpha_composite(body, (PADX, CHh - nh)); out.alpha_composite(im.crop((0, 0, W, NECK_Y)), (PADX, CHh - nh - NECK_Y)); return out
def glitch(im, seed, amp=5):
    """가로줄 몇 묶음이 좌우로 어긋난다(화면 깨짐)."""
    r = random.Random(seed); out = Image.new('RGBA', (CW, CHh), CLEAR); y = 0
    while y < im.height:
        hgt = r.randrange(2, 9); dx = r.choice((0, 0, -amp, amp, amp // 2, -amp // 2))
        out.alpha_composite(im.crop((0, y, W, min(H, y + hgt))), (PADX + dx, PADT + y)); y += hgt
    return out
def crawl(im, k):
    """허리가 앞으로 꺾여 낮아진다(k=0~1): 윗몸을 세로로 눌러 낮추고 머리를 아래로 떨군다."""
    top = im.crop((0, 0, W, 44)); legs = im.crop((0, 44, W, H)); nh = round(44 * (1 - .45 * k)); top = top.resize((W, nh), Image.NEAREST)
    out = Image.new('RGBA', (CW, CHh), CLEAR); out.alpha_composite(legs, (PADX, PADT + 44)); out.alpha_composite(top, (PADX + round(3 * k), PADT + 44 - nh)); return out

SEQ = {}      # 이름 -> [(그림, 밀리초)]
w = [base['w1'], base['w2'], base['w3'], base['w4']]
# 경련 걸음: 한쪽으로 꺾인 채 버티다(길게) 반대쪽으로 툭(짧게). 박자가 고르지 않다
SEQ['tw'] = [(shear(w[0], -4), 260), (shear(w[0], -5), 60), (shear(w[1], 3), 60), (shear(w[2], 5), 300), (shear(w[2], 6), 60), (shear(w[3], -2), 60), (shear(w[0], -6), 420), (canvas(w[1], 0, 2), 80)]
# 고개 꺾임: 천천히 기울다가 툭 꺾이고, 떨다가 제자리로
SEQ['tilt'] = [(tilt_head(base['idle'], a), ms) for a, ms in ((0, 500), (-6, 220), (-12, 220), (-18, 260), (-52, 60), (-48, 90), (-52, 90), (-50, 600), (-20, 90), (0, 400))]
# 늘어남: 몸이 위로 길게 늘어났다가 툭 떨어짐
SEQ['st'] = [(stretch(base['idle'], f), ms) for f, ms in ((1.0, 400), (1.08, 160), (1.18, 160), (1.3, 200), (1.36, 500), (1.0, 60), (.94, 90), (1.0, 300))]
# 끊김: 화면이 깨지듯 가로줄이 어긋나며 한 걸음씩 다가옴
SEQ['gl'] = [(canvas(w[0]), 240), (glitch(w[0], 1), 50), (glitch(w[1], 2, 8), 50), (canvas(w[2]), 240), (glitch(w[2], 3), 50), (glitch(w[3], 4, 9), 60), (canvas(w[0]), 120), (glitch(w[0], 5, 3), 40)]
# 기어옴: 허리가 꺾여 낮아지며 다가옴(걸음마다 더 낮아졌다 조금 일어남)
SEQ['cr'] = [(crawl(w[k % 4], kk), ms) for k, (kk, ms) in enumerate(((0, 300), (.35, 140), (.7, 140), (1, 220), (.85, 140), (1, 220), (.8, 140), (1, 300)))]

# 목이 꺾이며 안에서 이상한 액체가 흘러나옴: 꺾인 목 틈에서 탁한 청록빛 진액이 몸을 타고 흘러 발밑에 고인다. 방울이 떨어지고, 머리 아래 끝에서도 맺혀 떨어진다
import math
LQ, LQL, LQD = (70, 150, 130, 255), (160, 225, 195, 255), (30, 72, 70, 255)
def ooze(im, n):
    """n: 0부터 커지는 진행 단계. 줄기 세 가닥이 목(가운데)에서 아래로 자라고, 발에 닿으면 웅덩이가 넓어진다."""
    out = im.copy(); px = out.load(); nx, ny = PADX + W // 2, PADT + NECK_Y - 1; foot = CHh - 2
    def put(x, y, c):
        if 0 <= x < CW and 0 <= y < CHh: px[x, y] = c
    for k, (ox, delay, speed, ph) in enumerate(((-2, 0, 5, 0.0), (2, 2, 4, 1.7), (5, 5, 3, 3.1))):
        ln = max(0, (n - delay) * speed)
        if ln <= 0: continue
        end = min(foot, ny + ln)
        for y in range(ny, int(end) + 1):
            x = nx + ox + round(1.2 * math.sin((y - ny) * .35 + ph))
            put(x, y, LQ); put(x + 1, y, LQD if (y + k) % 3 else LQ)               # 줄기(2칸, 한쪽은 어두운 가장자리)
            if y % 9 == k * 3 % 9: put(x, y, LQL)                                   # 드문 반짝임
        if end < foot: x = nx + ox + round(1.2 * math.sin((end - ny) * .35 + ph)); put(x, int(end) + 1, LQL); put(x + 1, int(end) + 1, LQL); put(x, int(end) + 2, LQ)    # 줄기 끝의 맺힌 방울
    reach = max(0, n - 10)                                                            # 첫 줄기가 발에 닿은 뒤: 웅덩이
    if reach:
        rx = min(16, 3 + reach * 2)
        for x in range(nx - rx, nx + rx + 1):
            put(x, foot, LQ); put(x, foot + 1, LQD)
            if abs(x - nx) < rx - 2 and (x + n) % 5 == 0: put(x, foot, LQL)
    for k, (dx, t0) in enumerate(((9, 3), (12, 8), (7, 13))):                      # 꺾인 머리 아래 끝에서 맺혀 떨어지는 방울
        t = n - t0
        if t >= 0:
            y = ny - 6 + min(60, t * t // 2 + t * 2)
            if y < foot: put(nx + dx, y, LQL); put(nx + dx, y - 1, LQ)
    for dx in (-1, 0, 1, 2):                                                          # 목 틈에 고여 번들거림
        put(nx + dx, ny, LQL if (dx + n) % 2 else LQ)
    return out
snap = [(tilt_head(base['idle'], a), ms) for a, ms in ((0, 500), (-6, 220), (-12, 220), (-18, 300), (-54, 60), (-50, 90), (-54, 200))]
SEQ['ooze'] = snap + [(ooze(tilt_head(base['idle'], -52 + (1 if n % 4 == 0 else 0)), n), 110) for n in range(20)] + [(ooze(tilt_head(base['idle'], -52), 20), 900)]

if __name__ == '__main__':
    man = {'size': [CW, CHh], 'anchor': 'bottom-center', 'note': '캔버스가 기본 스프라이트(30x64)보다 크다: 좌우 10칸, 위 14칸 여유', 'sequences': {}}
    for name, seq in SEQ.items():
        man['sequences'][name] = [{'frame': f'{name}{i + 1}', 'ms': ms} for i, (_, ms) in enumerate(seq)]
        for i, (im, _) in enumerate(seq):
            im.save(os.path.join(OUT, f'chaser_d_{name}{i + 1}.png'))
            r = G.side(im, .62, .06); r.save(os.path.join(OUT, f'chaser_r_{name}{i + 1}.png')); G.flip(r).save(os.path.join(OUT, f'chaser_l_{name}{i + 1}.png'))
    json.dump(man, open(os.path.join(OUT, 'chaser_creepy.json'), 'w'), indent=1, ensure_ascii=False)
    mo = os.path.join(G.SPR, '..', '..', '..', 'maps', 'out'); S = 3
    from PIL import ImageDraw, ImageFont
    Fnt = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 14)
    labels = {'tw': '경련 걸음', 'tilt': '고개 꺾임', 'st': '늘어남', 'gl': '끊김', 'cr': '기어옴', 'ooze': '목이 꺾이며 흘러나옴'}
    # 미리보기 GIF: 다섯 동작을 나란히, 20ms 단위 시간표로 재생
    total = max(sum(ms for _, ms in seq) for seq in SEQ.values()); tick = 20; frames = []
    def at(seq, t):
        t %= sum(ms for _, ms in seq)
        for im, ms in seq:
            if t < ms: return im
            t -= ms
    for t in range(0, total, tick * 2):
        fr = Image.new('RGBA', (len(SEQ) * (CW * S + 8) + 8, CHh * S + 30), (24, 26, 40, 255)); d = ImageDraw.Draw(fr)
        for c, (name, seq) in enumerate(SEQ.items()):
            fr.alpha_composite(at(seq, t).resize((CW * S, CHh * S), Image.NEAREST), (8 + c * (CW * S + 8), 26)); d.text((8 + c * (CW * S + 8) + 40, 4), labels[name], fill=(220, 220, 200), font=Fnt)
        frames.append(fr.convert('RGB'))
    frames[0].save(os.path.join(mo, 'chaser_creepy.gif'), save_all=True, append_images=frames[1:], duration=tick * 2, loop=0)
    strip = Image.new('RGBA', (28 * (CW * 2 + 4) + 90, len(SEQ) * (CHh * 2 + 6) + 6), (24, 26, 40, 255)); d = ImageDraw.Draw(strip)
    for r_, (name, seq) in enumerate(SEQ.items()):
        d.text((6, 6 + r_ * (CHh * 2 + 6) + 60), labels[name], fill=(220, 220, 200), font=Fnt)
        for c, (im, ms) in enumerate(seq): strip.alpha_composite(im.resize((CW * 2, CHh * 2), Image.NEAREST), (86 + c * (CW * 2 + 4), 6 + r_ * (CHh * 2 + 6)))
    strip.save(os.path.join(mo, 'chaser_creepy_strip.png')); print('creepy:', sum(len(s) for s in SEQ.values()), 'frames x 3 dirs')
