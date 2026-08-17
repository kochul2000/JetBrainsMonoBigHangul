"""미디어 컨트롤 글리프(U+23F4~U+23FA) 보충.

JetBrains Mono에는 ⏵(U+23F5) 같은 Miscellaneous Technical 미디어 기호가
없어서, 터미널 TUI(예: Claude Code 상태줄의 ⏵⏵)가 이 문자를 쓰면 OS 폰트
폴백에 걸리거나 — 폴백이 없는 환경(원격 WebView 등)에서는 통째로 네모(tofu)가
된다. 폰트가 직접 갖고 있게 만든다.

새로 그리는 대신 JetBrains Mono가 이미 가진 기하 도형(▶◀▲▼■●)을 복사해
파생한다 — 획 두께·시각 크기·베이스라인이 원본 디자인과 자동으로 일치한다.
⏸(pause)만 대응 도형이 없어 ■의 잉크 박스에 맞춘 세로 막대 두 개를 합성한다.
"""

import fontforge

# 파생 대상 → 원본 코드포인트. U+23F4~7은 '중간 크기' 삼각형이지만 터미널
# 셀에서는 ◀▶▲▼와 같은 크기가 오히려 일관돼 보여 1:1로 복사한다.
DERIVED_SYMBOLS = {
    0x23F4: 0x25C0,  # ⏴ ← ◀
    0x23F5: 0x25B6,  # ⏵ ← ▶
    0x23F6: 0x25B2,  # ⏶ ← ▲
    0x23F7: 0x25BC,  # ⏷ ← ▼
    0x23F9: 0x25A0,  # ⏹ ← ■
    0x23FA: 0x25CF,  # ⏺ ← ●
}

PAUSE_CODEPOINT = 0x23F8  # ⏸
PAUSE_SOURCE = 0x25A0     # ■ 의 잉크 박스를 기준 틀로 쓴다
# ■ 잉크 폭 대비 막대 하나의 폭 비율. 두 막대 + 가운데 간격이 잉크 폭을
# 채우도록 (bar, gap, bar) = (0.32, 0.36, 0.32) 로 나눈다.
PAUSE_BAR_RATIO = 0.32


def _has(font, codepoint):
    try:
        return codepoint in font
    except TypeError:
        return False


def _copy_glyph(font, source, target):
    # 클립보드(copy/paste)를 쓰면 안 된다 — fontforge 클립보드는 전역이라,
    # build_font()가 D2 한글 selection을 복사해 둔 것을 여기서 덮어쓰면
    # 같은 패스의 다음 폰트부터 한글 대신 도형 하나가 붙는다.
    glyph = font.createChar(target)
    pen = glyph.glyphPen()
    font[source].draw(pen)
    pen = None
    glyph.width = font[source].width


def _build_pause(font):
    source = font[PAUSE_SOURCE]
    x_min, y_min, x_max, y_max = source.boundingBox()
    ink_width = x_max - x_min
    if ink_width <= 0:
        return
    bar = ink_width * PAUSE_BAR_RATIO

    glyph = font.createChar(PAUSE_CODEPOINT)
    pen = glyph.glyphPen()
    for left in (x_min, x_max - bar):
        pen.moveTo((left, y_min))
        pen.lineTo((left, y_max))
        pen.lineTo((left + bar, y_max))
        pen.lineTo((left + bar, y_min))
        pen.closePath()
    pen = None
    glyph.width = source.width
    glyph.correctDirection()


def add_media_symbols(font):
    """이미 글리프가 있으면 건드리지 않는다 — 업스트림이 추가하면 그쪽이 이긴다."""
    for target, source in DERIVED_SYMBOLS.items():
        if _has(font, target) or not _has(font, source):
            continue
        _copy_glyph(font, source, target)
    if not _has(font, PAUSE_CODEPOINT) and _has(font, PAUSE_SOURCE):
        _build_pause(font)
