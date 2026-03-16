# JetBrainsMonoBigHangul

[JetBrains Mono](https://github.com/JetBrains/JetBrainsMono)에 [D2Coding](https://github.com/naver/d2codingfont)의 한글 글리프를 합치되, 한글을 크고 굵게 표시하는 프로그래밍 폰트입니다.

## 원본 리포

이 프로젝트는 [@Jhyub](https://github.com/Jhyub)님의 [JetBrainsMonoHangul](https://github.com/Jhyub/JetBrainsMonoHangul)을 기반으로 만들어졌습니다. JetBrains Mono와 D2 Coding 한글을 합치는 훌륭한 아이디어와 구현은 원본의 것이며, 이 프로젝트는 거기에 한글 크기와 웨이트 조정만 추가한 것입니다.

대부분의 사용자에게는 균형 잡힌 외형의 원본을 추천합니다.

## 왜 만들었는가

미적으로는 별로지만, 실용성을 극대화하기 위해 만들었습니다.

Claude Code 등 바이브 코딩 도구를 쓰면서 터미널에서 한글을 읽을 일이 크게 늘었습니다. 영어는 다소 작아도 읽히는데, 한글은 터미널에 따라 흐려지기도 하여 미적인 기준을 낮추고 실용성을 높였습니다. 노안이 와서 한글이 잘 보이지 않기 때문이기도 합니다.

## 원본과의 차이

| | 원본 (JetBrainsMonoHangul) | 이 프로젝트 (BigHangul) |
|---|---|---|
| 한글 크기 | D2 Coding 원본 크기 유지 | 1.2배 확대 |
| 한글 웨이트 | 모든 웨이트에 Regular 사용 | Bold 웨이트에 D2 Coding Bold 매칭 |
| 빌드 대상 | 전체 웨이트 + NL 변형 | Regular, Medium, Bold (+Italic) |

### 글리프 스케일링 (기본 1.2x)

한글 글리프 아웃라인을 확대합니다. 기본값은 1.2배이며, 환경변수 `HANGUL_SCALE`로 오버라이드할 수 있습니다.

```shell
# 기본값 (1.2x)
$ uv run build.py all

# CLI 인자로 배율 지정
$ uv run build.py all 1.28

# 또는 환경변수
$ HANGUL_SCALE=1.28 uv run build.py all
```

배율은 영문 기준 최대 너비를 넘지 않는 선에서 정했습니다. 영문에서 가장 넓은 'W'가 셀의 93.3%를 채우는데, 1.2배 적용 시 한글에서 가장 넓은 '짜'가 91.5%로 이를 넘지 않습니다. 이로써 영문 2글자가 한글 1글자 너비와 시각적으로 비슷해 보이게 됩니다.

#### 스케일링 후보값

| 배율 | 너비 평균 | 너비 최대(짜) | 위쪽 여유 | 근거 |
|---|---|---|---|---|
| 1.00 | 68% | 76% | 224 | 원본과 동일 (스케일 없음) |
| 1.05 | 72% | 80% | 182 | 획 두께 보정. D2 Coding과 JetBrains Mono의 획 두께 차이(73 vs 80)를 맞추는 배율 |
| 1.10 | 75% | 84% | 144 | 보수적 확대. 한글 너비 평균이 영문 너비 평균(~78%)에 근접 |
| 1.15 | 78% | 88% | 104 | 한글 너비 평균이 영문 너비 평균과 일치 |
| **1.20** | **82%** | **92%** | **65** | **기본값. D2 Coding 셀 비율 보존 (1200/1000)** |
| 1.22 | 83% | 93% | 49 | 한글 최대 너비(짜)가 영문 최대 너비(W, 93.3%)와 일치 |
| 1.28 | 87% | 98% | 1 | 클리핑 없이 가능한 최대값. 가장 높은 글리프('훨')가 경계에 닿음 |

- **너비 평균/최대**: 한글 글리프가 1200 유닛 셀을 채우는 비율. 영문은 73~93% (평균 ~78%).
- **위쪽 여유**: 폰트 클리핑 경계(os2_winascent=1020)까지 남은 유닛. 0 이하면 글자가 잘립니다.

한글을 더 예쁘게 줄이고 싶다면 **1.05~1.10** 범위를, 한글이 더 부족하다면 **1.28까지 확대 가능**합니다.

### 웨이트 매칭

원본은 모든 JetBrains Mono 웨이트에 D2 Coding Regular 하나만 사용합니다. Bold 영문 옆에 Regular 한글이 붙으면 한글만 가늘어 보입니다.

이 프로젝트에서는:
- Thin ~ Regular (+ Italic) → D2 Coding **Regular**
- Medium ~ ExtraBold (+ Italic) → D2 Coding **Bold**

### 빌드 대상 축소

실제로 코딩에 쓰이는 웨이트만 빌드합니다: Regular, Medium, Bold (+ 각 Italic).

## Quick Start

```shell
$ sudo apt install python3-fontforge
$ git clone https://github.com/kochul2000/JetBrainsMonoBigHangul.git
$ cd JetBrainsMonoBigHangul

# uv 사용
$ uv venv --python 3.10 --system-site-packages
$ uv sync
$ uv run build.py all
$ uv run build.py all 1.28  # 배율 지정

# 또는 직접 실행
$ pip install wget
$ python3 build.py all
```

fontforge는 pip에서 제공하지 않으므로 시스템 패키지(`python3-fontforge`)를 설치해야 합니다. uv 사용 시 `--system-site-packages`로 시스템 fontforge에 접근합니다.

## License

OFL 하에 배포됩니다. LICENSE 파일을 참조해주세요.
