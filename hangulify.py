import fontforge
import psMat
import shutil
import os

from config import *

# JetBrains Mono weights that should use D2 Coding Bold
BOLD_WEIGHTS = {'Medium', 'SemiBold', 'Bold', 'ExtraBold'}
BUILD_WEIGHTS = {'Regular', 'Medium', 'Bold'}

# Codepoint ranges to pull from D2 Coding. JetBrains Mono has no glyphs at all
# for these blocks, so without this they render via OS font fallback at an
# inconsistent, undersized scale inside the monospace cell.
GLYPH_RANGES = [
    (0x3131, 0x318E),   # Hangul Compatibility Jamo
    (0xAC00, 0xD7A3),   # Hangul Syllables
    (0x2153, 0x215F),   # Fractions (⅓ ⅔ ⅛ ...)
    (0x2160, 0x2188),   # Roman Numerals (Ⅰ Ⅱ Ⅲ ...)
    (0x2460, 0x24FF),   # Enclosed Alphanumerics (①②③ ⓐⓑⓒ ...)
    (0x3200, 0x321E),   # Parenthesized Hangul/CJK
    (0x3251, 0x325F),   # Circled Numbers 21-35 (㉑~㉟)
    (0x3260, 0x327F),   # Circled Hangul Jamo/Syllables (㉠㉡㉢ ...)
]

# East Asian Ambiguous ranges: terminals give these one cell (wcwidth=1), so
# their advance must be a single JetBrains Mono cell or renderers shrink the
# glyph to half size. The rest of GLYPH_RANGES is EAW=Wide (two cells).
NARROW_RANGES = [
    (0x2153, 0x215F),   # Fractions
    (0x2160, 0x2188),   # Roman Numerals
    (0x2460, 0x24FF),   # Enclosed Alphanumerics
]

# Vertical center of JetBrains Mono digits, and the side bearing left around a
# full-width outline squeezed into a single cell. Used to place those squeezed
# glyphs; see prepare_hangul_glyphs.
NARROW_CENTER_Y = 365
NARROW_SIDE_BEARING = 10


def is_narrow(codepoint):
    return any(start <= codepoint <= end for start, end in NARROW_RANGES)


def select_glyph_ranges(selection):
    selection.select(("unicode", "ranges"), *GLYPH_RANGES[0])
    for start, end in GLYPH_RANGES[1:]:
        selection.select(("unicode", "ranges", "more"), start, end)
    return selection


def get_weight(filename):
    """Extract weight name from JetBrains Mono font filename."""
    base = os.path.splitext(filename)[0]
    parts = base.split('-')
    if len(parts) < 2:
        return 'Regular'
    style = parts[-1].replace('Italic', '')
    return style if style else 'Regular'


def is_bold_weight(filename):
    return get_weight(filename) in BOLD_WEIGHTS


def add_bearing(glyph, addition):
    glyph.left_side_bearing = addition // 2 + int(glyph.left_side_bearing)
    glyph.right_side_bearing = addition // 2 + int(glyph.right_side_bearing)


def prepare_hangul_glyphs(d2, scale=hangul_scale):
    """Scale glyph outlines slightly and center in target advance width.

    EAW=Wide glyphs land on two JetBrains Mono cells, EAW=Ambiguous ones on a
    single cell. The scale factor is normalized by each glyph's original D2
    advance so a full-width outline squeezed into one cell shrinks to fit.

    D2 draws the circled numbers (①②③) full-width even though terminals give
    them one cell. Scaling those by advance ratio alone leaves ink to spare in
    the cell and, since scaling happens about the baseline, drops them well
    below the digit axis. They are fit to the cell by ink width and re-centered
    on NARROW_CENTER_Y instead. Glyphs D2 already designed half-width (Ⅰ, ⅓)
    need neither and keep the plain advance-ratio scale.
    """
    glyphs = [i for i in select_glyph_ranges(d2.selection) if i in d2]

    # Unlink every composite up front. Ⅱ and Ⅲ reference Ⅰ, so unlinking them
    # mid-loop would copy an already-transformed Ⅰ and scale it twice.
    for i in glyphs:
        if d2[i].references:
            d2[i].unlinkRef()

    for i in glyphs:
        glyph = d2[i]
        narrow = is_narrow(i)
        target_width = jetbrains_mono_width // 2 if narrow \
                else jetbrains_mono_width
        d2_width = glyph.width if glyph.width > 0 else d2_coding_width
        squeezed = narrow and d2_width > d2_coding_width // 2
        bbox = glyph.boundingBox()
        if squeezed and bbox[2] > bbox[0]:
            eff_scale = (target_width - 2 * NARROW_SIDE_BEARING) \
                    / (bbox[2] - bbox[0])
        else:
            eff_scale = scale * (target_width / jetbrains_mono_width) \
                    * (d2_coding_width / d2_width)
        glyph.transform(psMat.scale(eff_scale))
        bbox = glyph.boundingBox()
        if bbox[2] > bbox[0]:
            body_width = bbox[2] - bbox[0]
            target_lsb = (target_width - body_width) / 2
            shift_x = target_lsb - bbox[0]
            shift_y = NARROW_CENTER_Y - (bbox[1] + bbox[3]) / 2 if squeezed \
                    else 0
            glyph.transform(psMat.translate(shift_x, shift_y))
        glyph.width = target_width


def replace_name(string):
    return string.replace("JetBrainsMono", "JetBrainsMonoBigHangul") \
            .replace("JetBrains Mono", "JetBrainsMonoBigHangul")


def build_font():
    if not os.path.exists(out_path):
        print(f'[INFO] Make \'{out_path}\' directory')
        os.makedirs(out_path)

    d2_regular_path = f'{download_path}/d2/D2Coding/D2Coding-Ver{d2_coding_version}-{d2_coding_date}.ttf'
    d2_bold_path = f'{download_path}/d2/D2Coding/D2CodingBold-Ver{d2_coding_version}-{d2_coding_date}.ttf'

    has_bold = os.path.exists(d2_bold_path)
    if not has_bold:
        print('[WARN] D2 Coding Bold not found, using Regular for all weights')

    jb_fonts = sorted(os.listdir(f'{download_path}/jb/fonts/ttf'))

    print("[INFO] Merge fonts and output")

    for use_bold in [False, True]:
        if use_bold and not has_bold:
            continue

        d2_path = d2_bold_path if use_bold else d2_regular_path
        d2 = fontforge.open(d2_path)
        prepare_hangul_glyphs(d2)

        select_glyph_ranges(d2.selection)
        d2.copy()

        for name in jb_fonts:
            weight = get_weight(name)
            if weight not in BUILD_WEIGHTS:
                continue
            if 'NL' in name:
                continue
            if has_bold and is_bold_weight(name) != use_bold:
                continue

            jb = fontforge.open(f"{download_path}/jb/fonts/ttf/{name}")
            select_glyph_ranges(jb.selection)
            jb.paste()

            namel = name.split(".")
            namel[-2] = replace_name(namel[-2])

            jb.familyname = replace_name(jb.familyname)
            jb.fontname = replace_name(jb.fontname)
            jb.fullname = replace_name(jb.fullname)

            subFamilyIdx = [x[1] for x in jb.sfnt_names].index("SubFamily")
            sfntNamesStringIdIdx = 2
            subFamily = jb.sfnt_names[subFamilyIdx][sfntNamesStringIdIdx]

            for (language, strid, string) in jb.sfnt_names:
                if strid == "UniqueID":
                    jb.appendSFNTName(language, strid, f"{jb.fullname} {version_name}")

                if strid == "Version":
                    jb.appendSFNTName(language, strid, f"{string};Hangulify {version_name}")

                if strid == "Preferred Family":
                    jb.appendSFNTName(language, strid, replace_name(string))

            jb.generate(".".join(namel))
            shutil.move(".".join(namel), out_path+"/"+".".join(namel))
            print("[INFO] Exported "+ ".".join(namel))

        d2.close()
