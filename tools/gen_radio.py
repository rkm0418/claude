"""라디오 소리 초안: 노이즈가 끼고 여러 소리(웅얼거리는 말소리, 종, 전화벨, 노크, 숨)가 한꺼번에 섞여 기괴하게 들리는 소리.
실행: python3 tools/gen_radio.py [노이즈 세기 0~1, 기본 1.0]  -> audio/radio_draft.wav (모노, 22050Hz 이상)
말소리는 TTS 없이 포먼트로 합성한 '알아들을 수 없는 웅얼거림'이다(실제 대사 녹음은 추후)."""
import sys, wave
import numpy as np
SR = 44100; DUR = 20.0; rng = np.random.default_rng(5)
N = int(SR * DUR); t = np.arange(N) / SR

def env(x, a=.01, r=.1):
    return x

def biquad_bp(x, f, q):
    """간단한 2차 밴드패스(직접형)."""
    w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q); b0, b2 = al, -al; a0, a1, a2 = 1 + al, -2 * np.cos(w), 1 - al
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for i, v in enumerate(x):
        o = (b0 * v + b2 * x2 - a1 * y1 - a2 * y2) / a0; x2, x1 = x1, v; y2, y1 = y1, o; y[i] = o
    return y

def fft_filter(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))

def voice(start, dur, pitch, vowels, speed=6.0, gain=.5):
    """웅얼거리는 말소리: 성문 펄스(피치가 흔들림) -> 모음 포먼트 -> 음절 박자 엔벨로프."""
    n = int(dur * SR); tt = np.arange(n) / SR
    f0 = pitch * (1 + .08 * np.sin(2 * np.pi * 1.7 * tt) + .05 * np.sin(2 * np.pi * .6 * tt + 1))
    ph = np.cumsum(f0) / SR; src = ((ph % 1.0) * 2 - 1) + .35 * rng.standard_normal(n) * .3
    out = np.zeros(n)
    seg = max(1, int(n / len(vowels)))
    for i, (f1, f2, f3) in enumerate(vowels):
        a, b = i * seg, min(n, (i + 1) * seg)
        if b <= a: continue
        out[a:b] = sum(g * biquad_bp(src[a:b], f, 9) for f, g in ((f1, 1.0), (f2, .7), (f3, .4)))
    syl = np.clip(np.sin(2 * np.pi * speed * tt) + .3, 0, 1) ** 1.5 * np.clip(np.minimum(tt, dur - tt) * 8, 0, 1)
    y = np.zeros(N); i0 = int(start * SR); y[i0:i0 + n] = (out * syl)[:max(0, N - i0)] if i0 + n > N else out * syl
    return y / (np.abs(y).max() + 1e-9) * gain

def tone(start, dur, f, gain=.3, decay=3.0, harm=((1, 1), (2.7, .5), (4.1, .3))):
    n = int(dur * SR); tt = np.arange(n) / SR; y = sum(g * np.sin(2 * np.pi * f * h * tt) for h, g in harm) * np.exp(-decay * tt)
    z = np.zeros(N); i0 = int(start * SR); z[i0:i0 + n] = y[:N - i0]; return z / (np.abs(z).max() + 1e-9) * gain

def knock(start, gain=.6):
    z = np.zeros(N); n = int(.12 * SR); tt = np.arange(n) / SR; k = np.sin(2 * np.pi * 110 * tt) * np.exp(-40 * tt) + .4 * rng.standard_normal(n) * np.exp(-90 * tt)
    i0 = int(start * SR); z[i0:i0 + n] = k[:N - i0]; return z * gain

def phone(start, rings=3, gain=.28):
    z = np.zeros(N)
    for r in range(rings):
        s = start + r * 1.4; n = int(.9 * SR); tt = np.arange(n) / SR
        y = (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * (np.sin(2 * np.pi * 20 * tt) > 0) * np.clip((.9 - tt) * 8, 0, 1)
        i0 = int(s * SR)
        if i0 < N: z[i0:i0 + n] = y[:N - i0]
    return z * gain

def breath(start, dur, gain=.35):
    n = int(dur * SR); tt = np.arange(n) / SR; y = fft_filter(rng.standard_normal(n), 800, 7000) * np.sin(np.pi * tt / dur) ** 2
    z = np.zeros(N); i0 = int(start * SR); z[i0:i0 + n] = y[:N - i0]; return z / (np.abs(z).max() + 1e-9) * gain

def build(noise=1.0):
    V = {'a': (800, 1200, 2500), 'i': (300, 2300, 3000), 'u': (320, 800, 2500), 'e': (500, 1800, 2500), 'o': (500, 900, 2400)}
    vs = lambda s: [V[c] for c in s]
    mix = np.zeros(N)
    mix += voice(.5, 5.5, 210, vs('aeiouao'), 5.5, .55)                    # 보호자(낮고 부드러운) : 중간 정도로 또렷
    mix += voice(2.0, 6.0, 330, vs('iuoeaiu'), 7.5, .45)                   # 아이 이름을 부르는 가는 목소리
    mix += voice(4.5, 7.0, 150, vs('oauiea'), 4.0, .5)                     # 낮은 남자 목소리(웅웅)
    mix += voice(8.0, 8.0, 260, vs('eiaouei'), 6.5, .5)                    # 병원/학교 안내처럼 평평한 목소리
    mix += voice(11.0, 6.0, 190, vs('uoaieo'), 5.0, .5)
    mix += voice(13.5, 6.0, 300, vs('aieuoa'), 8.0, .4)                    # 겹쳐 올라오는 또 하나
    mix += tone(3.0, 3.0, 880, .25) + tone(3.0, 3.0, 660, .2)               # 학교 종(두 음)
    mix += phone(6.0, 3) + phone(15.0, 3, .22)
    for k in (9.5, 9.9, 10.3, 16.5, 16.9, 17.3): mix += knock(k)           # 문 두드리는 소리
    mix += breath(12.0, 2.5, .4) + breath(18.0, 2.2, .45)                  # 숨소리
    # 전파 노이즈: 고음 중심 + 지직 튀는 소리 + 튜닝 휘파람
    white = rng.standard_normal(N); hiss = fft_filter(white, 2000, 9000) * (.18 + .1 * np.sin(2 * np.pi * .3 * t))
    crack = (rng.random(N) < 2e-4) * rng.standard_normal(N) * 1.4
    sweep = np.sin(2 * np.pi * np.cumsum(1500 + 1200 * np.sin(2 * np.pi * .23 * t) + 700 * np.sin(2 * np.pi * .071 * t)) / SR) * (np.sin(2 * np.pi * .15 * t) > .55) * .05
    drop = np.clip(np.sin(2 * np.pi * .21 * t + 2) * 3, 0, 1)             # 가끔 전파가 끊겨 말소리가 잠깐 사라지는 구간
    mix = mix * (1 - .75 * drop * noise)
    out = mix + noise * (hiss + crack * .6 + sweep)
    out = np.tanh(out * 1.6) * .8                                          # 살짝 찌그러뜨림
    out = fft_filter(out, 150, 11000)
    return out / (np.abs(out).max() + 1e-9) * .9

if __name__ == '__main__':
    nz = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    y = build(nz); pcm = (y * 32767).astype('<i2')
    with wave.open('audio/radio_draft.wav', 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
