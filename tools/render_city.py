#!/usr/bin/env python3
"""추락 이후(본편 시작): 밤의 현대 도시. 사용자 스케치 구조 — 왼쪽: 인공 수풀 화단에 떨어져 시작하는 작은 광장(오른쪽이 출구),
오른쪽: 세로로 긴 거리(왼쪽 인도 | 도로 | 오른쪽 인도, 도로 위에 서 있는 차 네 대, 위로 이어짐).
사용: python3 tools/render_city.py -> maps/out/city_landing.png, city_street.png, city_overview.png (+ _x2, _x4 확대)
크기: 광장 160x120(2배로 320x240 화면 한 장), 거리 96x320(세로 스크롤, 2배로 192x640)."""
import math, os, random, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'out'); SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art', 'out', 'sprites')
PAVE, PAVE2, JOINT = (40, 44, 66), (34, 38, 58), (26, 29, 46)
ASPH, ASPH2 = (26, 28, 42), (30, 32, 48)
CURB, CURBL = (74, 78, 104), (104, 108, 138)
WIN_OFF, WIN_W, WIN_B = (22, 26, 50), (236, 200, 124), (118, 168, 206)
WALL, WALLD = (28, 32, 60), (20, 23, 44)
LAMP = (255, 214, 140)

def glow(img, cx, cy, r, col=LAMP, power=.55):
    """따뜻한 불빛 웅덩이: 중심에서 멀어질수록 약해지게 색을 섞는다(도트 느낌을 위해 5단계로 끊음)."""
    px = img.load()
    for y in range(max(0, cy - r), min(img.height, cy + r + 1)):
        for x in range(max(0, cx - r), min(img.width, cx + r + 1)):
            d = math.hypot(x - cx, y - cy)
            if d < r:
                f = round((1 - d / r) ** 2.2 * power * 8) / 8; p = px[x, y]
                px[x, y] = (int(p[0] + (col[0] - p[0]) * f), int(p[1] + (col[1] - p[1]) * f), int(p[2] + (col[2] - p[2]) * f))
def facade(d, x0, y0, x1, y1, rng, lit=.28):
    """건물 외벽: 어두운 남색 벽 + 층 구분선 + 창(드물게 켜짐: 따뜻한 노랑 / 차가운 파랑)."""
    d.rectangle([x0, y0, x1, y1], fill=WALL)
    for y in range(y0 + 8, y1, 10): d.line([x0, y, x1, y], fill=WALLD)
    for y in range(y0 + 3, y1 - 6, 10):
        for x in range(x0 + 3, x1 - 5, 12):
            r = rng.random(); c = WIN_W if r < lit else WIN_B if r < lit + .1 else WIN_OFF
            d.rectangle([x, y, x + 6, y + 5], fill=c); d.line([x, y + 5, x + 6, y + 5], fill=tuple(int(v * .6) for v in c))
def tiles(d, x0, y0, x1, y1, step=16, off=0):
    d.rectangle([x0, y0, x1, y1], fill=PAVE)
    for y in range(y0, y1, step):
        for x in range(x0 + ((y // step + off) % 2) * (step // 2), x1, step):
            d.rectangle([x, y, min(x1, x + step - 1), min(y1, y + step - 1)], fill=PAVE2 if ((x // step) + (y // step)) % 3 == 0 else PAVE)
            d.line([x, y, min(x1, x + step - 1), y], fill=JOINT); d.line([x, y, x, min(y1, y + step - 1)], fill=JOINT)
def streetlamp(img, d, x, y, h=34):
    """가로등: 어두운 기둥 + 꺾인 팔 + 따뜻한 등. (x, y) = 기둥 밑."""
    d.rectangle([x - 1, y - h, x, y], fill=(52, 56, 80)); d.rectangle([x - 1, y, x + 1, y + 1], fill=(38, 40, 60))
    d.line([x, y - h, x + 7, y - h - 2], fill=(52, 56, 80), width=2)
    d.rectangle([x + 5, y - h - 2, x + 11, y - h], fill=(255, 226, 160)); d.rectangle([x + 5, y - h - 3, x + 11, y - h - 3], fill=(90, 92, 118))
    return (x + 8, y - h + 1)
def hedge(d, cx, cy, r, rng, bright=1.0):
    """인공 수풀(조화): 동그랗게 깎은 균일한 덩어리 + 규칙적인 밝은 점(플라스틱 잎 반짝임). 진짜 숲과 달리 색이 너무 선명하고 모양이 똑같다."""
    B, L, D = (46, 122, 66), (84, 176, 98), (26, 78, 48)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=B)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 200, 330, fill=L); d.pieslice([cx - r, cy - r, cx + r, cy + r], 20, 150, fill=D)
    d.arc([cx - r, cy - r, cx + r, cy + r], 0, 360, fill=(20, 60, 38))
    for k in range(0, r * 2, 3):
        for j in range(0, r * 2, 3):
            if (k + j) % 6 == 0 and math.hypot(k - r, j - r) < r - 1: d.point((cx - r + k, cy - r + j), fill=(150, 214, 150))

# ---------------- 장면 1: 추락 직후의 광장 (160x120) ----------------
def landing():
    W, H = 160, 120; img = Image.new('RGB', (W, H), PAVE); d = ImageDraw.Draw(img); rng = random.Random(3)
    facade(d, 0, 0, W - 1, 38, rng); d.rectangle([0, 36, W - 1, 38], fill=WALLD)               # 뒤쪽 건물 줄
    d.rectangle([96, 9, 134, 17], fill=(70, 18, 52)); d.rectangle([98, 11, 132, 15], fill=(236, 84, 150)); d.rectangle([100, 12, 104, 14], fill=(255, 220, 240))
    for x in range(108, 132, 6): d.rectangle([x, 12, x + 3, 14], fill=(255, 190, 220))       # 네온 간판(글자 대신 막대)
    d.rectangle([144, 21, 156, 33], fill=(40, 120, 150)); d.rectangle([146, 23, 154, 31], fill=(120, 214, 232))                 # 가게 불빛
    tiles(d, 0, 39, 126, H - 1)
    d.rectangle([127, 39, 131, H - 1], fill=CURB); d.line([127, 39, 127, H - 1], fill=CURBL); d.rectangle([132, 39, W - 1, H - 1], fill=ASPH)  # 도로(오른쪽 출구)
    for y in range(44, H - 4, 16): d.rectangle([138, y, 156, y + 5], fill=(190, 192, 206)); d.rectangle([138, y + 5, 156, y + 5], fill=(120, 122, 140))   # 횡단보도
    lamp = streetlamp(img, d, 114, 92); lamp2 = streetlamp(img, d, 20, 98, 30)
    # 화단 + 인공 수풀(왼쪽 위): 화단 상자
    d.rectangle([6, 52, 54, 66], fill=(86, 90, 112)); d.rectangle([6, 52, 54, 55], fill=(122, 126, 150)); d.rectangle([6, 66, 54, 67], fill=(52, 54, 72)); d.line([6, 56, 54, 56], fill=(60, 62, 82))
    for x in (6, 54): d.rectangle([x, 52, x, 67], fill=(60, 62, 82))
    for (cx, cy, r) in ((11, 46, 6), (19, 44, 6), (41, 44, 6), (49, 46, 6), (13, 52, 5), (47, 52, 5)): hedge(d, cx, cy, r, rng)        # 양옆은 멀쩡한 덩어리
    for (cx, cy, r) in ((26, 41, 5), (34, 41, 5)): hedge(d, cx, cy, r, rng)                                                            # 뒤쪽 덩어리
    d.rectangle([21, 44, 39, 56], fill=(18, 54, 36))                                                                                      # 움푹 꺼진 자리(아이가 떨어진 곳)
    # 아이(앉은 채 깨어남): 화단 안에서 머리·어깨만 보인다
    kid = Image.open(os.path.join(SPR, 'child.png')).convert('RGBA'); img.paste(kid.crop((0, 0, 24, 24)), (18, 36), kid.crop((0, 0, 24, 24)))
    for (cx, cy, r) in ((24, 52, 5), (36, 52, 5), (30, 54, 5)): hedge(d, cx, cy, r, rng)                                                # 앞쪽 덩어리가 아이의 몸을 가린다
    for (x, y) in ((14, 62), (46, 63), (8, 70), (52, 72), (30, 70), (22, 76), (40, 74)): d.rectangle([x, y, x + 2, y + 1], fill=(84, 176, 98)); d.point((x + 1, y), fill=(150, 214, 150))   # 흩어진 잎
    glow(img, *lamp, 34, power=.5); glow(img, *lamp2, 24, power=.4)
    return img

# ---------------- 장면 2: 세로로 긴 거리 (96x320) ----------------
def car(img, d, x, y, w, l, col, tilt=0, rng=None):
    """위에서 비스듬히 내려다본 서 있는 차(불 꺼짐). x,y = 왼쪽 위. tilt != 0 이면 비스듬히 선 차(사다리꼴 모양)."""
    dk = tuple(int(v * .62) for v in col); lt = tuple(min(255, int(v * 1.3)) for v in col)
    body = [(x, y), (x + w, y), (x + w, y + l), (x, y + l)] if not tilt else [(x + tilt, y), (x + w, y), (x + w, y + l), (x, y + l)]
    d.polygon([(a + 2, b + 3) for a, b in body], fill=(14, 15, 26))                                  # 바닥에 놓인 그림자
    d.polygon(body, fill=col); d.line(body + [body[0]], fill=dk)
    ry = y + l * .25; rh = l * .5; ix = x + 3
    d.rectangle([ix + (tilt // 2), int(ry), x + w - 3, int(ry + rh)], fill=dk)                                       # 지붕(어두운 면)
    d.rectangle([ix + 1 + (tilt // 2), int(ry + 1), x + w - 4, int(ry + 3)], fill=lt)
    d.rectangle([ix + 1 + (tilt // 2), int(y + 3), x + w - 4, int(ry - 1)], fill=(38, 52, 78)); d.rectangle([ix + 1 + (tilt // 2), int(ry + rh + 1), x + w - 4, int(y + l - 3)], fill=(38, 52, 78))   # 앞·뒷유리
    d.line([ix + 1 + (tilt // 2), int(y + 4), x + w - 4, int(y + 4)], fill=(86, 104, 140))
    for tx in (x + 1, x + w - 3): d.rectangle([tx, y + l - 3, tx + 1, y + l - 1], fill=(96, 26, 32))                  # 꺼진 미등
    for tx in (x + 1, x + w - 3): d.rectangle([tx, y, tx + 1, y + 1], fill=(120, 126, 150))                          # 꺼진 전조등
    for ty in (y + 4, y + l - 6): d.rectangle([x - 1, ty, x, ty + 2], fill=(10, 10, 20)); d.rectangle([x + w, ty, x + w + 1, ty + 2], fill=(10, 10, 20))   # 바퀴
def street():
    W, H = 96, 320; img = Image.new('RGB', (W, H), ASPH); d = ImageDraw.Draw(img); rng = random.Random(8)
    L0, L1, R0, R1 = 28, 28, 68, 68                          # 왼쪽 인도 0~27, 도로 28~67, 오른쪽 인도 68~95
    tiles(d, 0, 0, L0 - 1, H - 1); tiles(d, R0, 0, W - 1, H - 1, off=1)
    for y in range(0, H): d.line([28, y, 67, y], fill=ASPH if (y // 40) % 2 == 0 else ASPH2)
    d.rectangle([L0 - 3, 0, L0 - 1, H - 1], fill=CURB); d.line([L0 - 3, 0, L0 - 3, H - 1], fill=CURBL); d.rectangle([R0, 0, R0 + 2, H - 1], fill=CURB); d.line([R0, 0, R0, H - 1], fill=CURBL)
    for y in range(10, H, 34): d.rectangle([47, y, 49, y + 13], fill=(170, 160, 96))                      # 가운데 차선(점선)
    for y in range(H - 54, H - 30, 6): d.rectangle([32, y, 64, y + 3], fill=(176, 178, 194))             # 아래 끝의 횡단보도(광장 쪽)
    d.rectangle([0, 0, 3, H - 1], fill=WALLD); d.rectangle([W - 4, 0, W - 1, H - 1], fill=WALLD)           # 양옆 건물 벽(가장자리)
    for y in range(8, H, 22): d.rectangle([0, y, 2, y + 8], fill=WIN_W if rng.random() < .3 else WIN_OFF); d.rectangle([W - 3, y + 4, W - 1, y + 12], fill=WIN_B if rng.random() < .25 else WIN_OFF)
    # 서 있는 차 네 대(스케치의 네 개의 직사각형): 위부터 비스듬히 선 차, 보통 차, 큰 차, 큰 차(아래로 갈수록 크게 그려짐)
    car(img, d, 36, 34, 22, 31, (58, 74, 122), tilt=5, rng=rng)
    car(img, d, 34, 104, 24, 34, (112, 50, 62), rng=rng)
    car(img, d, 33, 174, 30, 38, (70, 96, 92), rng=rng)
    car(img, d, 33, 246, 31, 40, (96, 98, 110), rng=rng)
    lamps = []
    for y in (40, 130, 220, 300): lamps.append(streetlamp(img, d, 12, y)); lamps.append(streetlamp(img, d, 83, y + 40 if y < 300 else y))
    for (x, y) in lamps: glow(img, x, y, 26, power=.42)
    for y in (70, 190): d.rectangle([5, y, 22, y + 3], fill=(58, 44, 36)); d.rectangle([5, y + 4, 6, y + 7], fill=(40, 30, 26)); d.rectangle([21, y + 4, 22, y + 7], fill=(40, 30, 26))    # 벤치
    d.ellipse([72, 112, 80, 120], fill=(20, 22, 36)); d.ellipse([73, 113, 79, 119], outline=(46, 50, 72))         # 맨홀
    return img

def main():
    a, b = landing(), street()
    for n, im in (('city_landing', a), ('city_street', b)):
        im.save(os.path.join(OUT, n + '.png')); im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(OUT, n + '_x2.png')); im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(OUT, n + '_x4.png'))
    ov = Image.new('RGB', (a.width * 2 + b.width * 2 + 50, max(a.height, b.height) * 2 + 20), (40, 40, 48))
    ov.paste(a.resize((a.width * 2, a.height * 2), Image.NEAREST), (10, 10)); ov.paste(b.resize((b.width * 2, b.height * 2), Image.NEAREST), (a.width * 2 + 40, 10)); ov.save(os.path.join(OUT, 'city_overview.png')); print('city ok')
if __name__ == '__main__': main()
