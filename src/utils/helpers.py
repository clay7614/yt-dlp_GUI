import math

def convert_size(size):
    """バイト単位の数値を読みやすい単位（MB, GBなど）に変換する。"""
    if not size or size == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB")
    i = math.floor(math.log(size, 1024)) if size > 0 else 0
    return f"{round(size / 1024**i, 2)} {units[i]}"

def hex_to_rgb(hex_str):
    """#RRGGBB 形式の文字列を (R, G, B) の 0.0-1.0 のタプルに変換する。"""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """(R, G, B) の 0.0-1.0 のタプルを #RRGGBB 形式の文字列に変換する。"""
    return '#{:02x}{:02x}{:02x}'.format(
        int(round(rgb[0] * 255)),
        int(round(rgb[1] * 255)),
        int(round(rgb[2] * 255))
    )

def version_compare(v1, v2):
    """バージョン文字列を比較する。 v1 > v2 なら 1, v1 < v2 なら -1, 等しければ 0。"""
    from packaging.version import parse
    v1 = parse(v1)
    v2 = parse(v2)
    return (v1 > v2) - (v1 < v2)
