import fontforge
import psMat
import shutil
import os

from config import *

# JetBrains Mono weights that should use D2 Coding Bold
BOLD_WEIGHTS = {'Medium', 'SemiBold', 'Bold', 'ExtraBold'}
BUILD_WEIGHTS = {'Regular', 'Medium', 'Bold'}


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


def prepare_hangul_glyphs(d2, scale=1.200):
    """Scale Hangul glyph outlines slightly and center in target advance width."""
    hangul = d2.selection.select(("unicode", "ranges"), 0x3131, 0x318E) \
            .select(("unicode", "ranges", "more"), 0xAC00, 0xD7A3)

    for i in hangul:
        glyph = d2[i]
        if glyph.references:
            glyph.unlinkRef()
        glyph.transform(psMat.scale(scale))
        bbox = glyph.boundingBox()
        if bbox[2] > bbox[0]:
            body_width = bbox[2] - bbox[0]
            target_lsb = (jetbrains_mono_width - body_width) / 2
            shift_x = target_lsb - bbox[0]
            glyph.transform(psMat.translate(shift_x, 0))
        glyph.width = jetbrains_mono_width


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

        d2.selection.select(("unicode", "ranges"), 0x3131, 0x318E) \
            .select(("unicode", "ranges", "more"), 0xAC00, 0xD7A3)
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
            jb.selection.select(("unicode", "ranges"), 0x3131, 0x318E) \
                .select(("unicode", "ranges", "more"), 0xAC00, 0xD7A3)
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
