# dsh-jailbreak-workflow 的图标生成脚本：断链 + 三节点工作流。
# 运行后生成 assets/icon.webp（裁到主体）、assets/icon-full.webp（整幅）、assets/icon-art.png（画布原图）。
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# 全部按 8x 超采样绘制，最终缩到 448
S = 3584

C_BLUE = (62, 124, 228)
C_GREEN = (96, 186, 126)
C_GOLD = (205, 158, 112)
GOLD_DARK = (168, 128, 88)
GOLD_LIGHT = (240, 214, 160)
LINE = (52, 73, 103)
BG_TOP = (13, 20, 32)
BG_BOT = (30, 42, 68)

CHAIN_CX, CHAIN_CY = S * 0.5, S * 0.42
CHAIN_R = S * 0.24
CHAIN_W = S * 0.062
BREAK_ANGLE = -50  # 断口方向（右上）

NODE_Y = S * 0.80
NODES = [
    (S * 0.30, C_BLUE),
    (S * 0.50, C_GREEN),
    (S * 0.70, C_GOLD),
]
NODE_SIZE = S * 0.088
NODE_RADIUS = S * 0.022


def build_background():
    """对角渐变的圆角底板，外加一点暗角氛围。"""
    xs = np.linspace(0, 1, S)
    ys = np.linspace(0, 1, S)
    gx = np.tile(xs, (S, 1))
    gy = np.repeat(ys[:, None], S, 1)
    t = np.clip((gx + gy) / 2, 0, 1)
    top = np.array(BG_TOP, dtype=float)
    bot = np.array(BG_BOT, dtype=float)
    grad = (top[None, None, :] * (1 - t[..., None]) + bot[None, None, :] * t[..., None])

    # 微噪点避免大面积色带
    rng = np.random.default_rng(42)
    grad += rng.normal(0, 2.0, grad.shape)

    img = Image.fromarray(grad.astype(np.uint8), "RGB").convert("RGBA")
    # 圆角 alpha
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, S - 1, S - 1), radius=int(S * 104 / 448), fill=255
    )
    img.putalpha(mask)
    return img


def draw_glow(img, cx, cy, r, color, alpha):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        (cx - r, cy - r, cx + r, cy + r), fill=color + (alpha,)
    )
    return Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(r * 0.55)))


def draw_chain(img):
    """断成两截的链环，断口在右上，带闪光与迸射线。"""
    a = math.radians(BREAK_ANGLE)
    gap = math.radians(56)  # 断口总张角
    # 底层暗金宽环
    d = ImageDraw.Draw(img)
    d.arc(
        (CHAIN_CX - CHAIN_R, CHAIN_CY - CHAIN_R, CHAIN_CX + CHAIN_R, CHAIN_CY + CHAIN_R),
        BREAK_ANGLE + math.degrees(gap / 2),
        BREAK_ANGLE + math.degrees(gap / 2) + (360 - math.degrees(gap)),
        fill=GOLD_DARK + (255,),
        width=int(CHAIN_W),
    )
    # 亮金层，稍细、稍偏内，做出体积感
    rr = CHAIN_R - CHAIN_W * 0.12
    d.arc(
        (CHAIN_CX - rr, CHAIN_CY - rr, CHAIN_CX + rr, CHAIN_CY + rr),
        BREAK_ANGLE + math.degrees(gap / 2),
        BREAK_ANGLE + math.degrees(gap / 2) + (360 - math.degrees(gap)),
        fill=GOLD_LIGHT + (255,),
        width=int(CHAIN_W * 0.55),
    )
    # 断口两端的端帽
    for sign in (1, -1):
        ang = math.radians(BREAK_ANGLE + sign * math.degrees(gap) / 2 * sign) if False else math.radians(BREAK_ANGLE + sign * math.degrees(gap / 2))
        px = CHAIN_CX + (CHAIN_R) * math.cos(ang)
        py = CHAIN_CY + (CHAIN_R) * math.sin(ang)
        hw = CHAIN_W * 0.56
        d.ellipse(
            (px - hw, py - hw, px + hw, py + hw), fill=GOLD_LIGHT + (255,)
        )

    # �口处的迸射光
    flash_cx = CHAIN_CX + CHAIN_R * math.cos(math.radians(BREAK_ANGLE))
    flash_cy = CHAIN_CY + CHAIN_R * math.sin(math.radians(BREAK_ANGLE))
    d = ImageDraw.Draw(img)
    # 中心亮星
    star_r = CHAIN_W * 0.62
    d.ellipse(
        (flash_cx - star_r, flash_cy - star_r, flash_cx + star_r, flash_cy + star_r),
        fill=(255, 250, 235, 255),
    )
    spark_r = star_r * 0.35
    d.ellipse(
        (flash_cx - spark_r, flash_cy - spark_r, flash_cx + spark_r, flash_cy + spark_r),
        fill=(255, 255, 255, 255),
    )
    # 迸射线
    for ang_deg in (-20, 15, 60, -55, 110, -120):
        ang = math.radians(BREAK_ANGLE + ang_deg)
        x2 = flash_cx + CHAIN_W * 1.35 * math.cos(ang)
        y2 = flash_cy + CHAIN_W * 1.35 * math.sin(ang)
        w = max(6, int(CHAIN_W * 0.055))
        d.line(
            (flash_cx, flash_cy, x2, y2),
            fill=GOLD_LIGHT + (210,),
            width=w,
        )
        ang2 = ang + math.pi
        x2 = flash_cx + CHAIN_W * 0.62 * math.cos(ang2)
        y2 = flash_cy + CHAIN_W * 0.62 * math.sin(ang2)
        d.line(
            (flash_cx, flash_cy, x2, y2),
            fill=GOLD_LIGHT + (150,),
            width=w,
        )
    return img


def draw_workflow(img):
    """底部三节点流程线：蓝 -> 绿 -> 金，节点间连线穿过断链正下方。"""
    d = ImageDraw.Draw(img)
    lw = int(S * 0.026)
    for (x1, _), (x2, _) in zip(NODES, NODES[1:]):
        d.line((x1, NODE_Y, x2, NODE_Y), fill=LINE + (255,), width=lw)
    for cx, color in NODES:
        half = NODE_SIZE / 2
        pad = lw * 0.9
        d.rounded_rectangle(
            (cx - half - pad, NODE_Y - half - pad, cx + half + pad, NODE_Y + half + pad),
            radius=NODE_RADIUS + pad,
            fill=(20, 28, 44, 255),
        )
    for cx, color in NODES:
        half = NODE_SIZE / 2
        d.rounded_rectangle(
            (cx - half, NODE_Y - half, cx + half, NODE_Y + half),
            radius=NODE_RADIUS,
            fill=color + (255,),
        )
        inner = half * 0.34
        d.ellipse(
            (cx - inner, NODE_Y - inner, cx + inner, NODE_Y + inner),
            fill=(255, 255, 255, 235),
        )
    return img


def save_all(img, out_dir):
    # icon-full.webp：整幅 448，WebP 无损
    full = img.resize((448, 448), Image.LANCZOS)
    full.save(f"{out_dir}/icon-full.webp", "WEBP", lossless=True, quality=100, method=6)

    # icon.webp：裁到主体（断链 + 流程线）再缩 448；裁剪框保持图内居中
    side = int(S * 0.78) & ~1
    left = (S - side) // 2
    top = (S - side) // 2
    icon = img.crop((left, top, left + side, top + side))
    icon = icon.resize((448, 448), Image.LANCZOS)
    icon.save(f"{out_dir}/icon.webp", "WEBP", lossless=True, quality=100, method=6)


def make_wordmark(out_dir):
    """重做词标：dsh-jailbreak-workflow，三段词各一色（蓝/金/绿），4x 画缩 1/4。"""
    from PIL import ImageFont
    W, H = 4588, 520  # 4x of 1147x130
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    parts = [("dsh", C_BLUE), ("-jailbreak", GOLD_LIGHT), ("-workflow", C_GREEN)]
    size = 412
    while True:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
        total = sum(
            d.textbbox((0, 0), t, font=font)[2] - d.textbbox((0, 0), t, font=font)[0]
            for t, _ in parts
        )
        if total <= 4450 or size <= 100:
            break
        size -= 8
    x = 0
    for text, color in parts:
        bbox = d.textbbox((0, 0), text, font=font)
        d.text((x - bbox[0], 0), text, font=font, fill=color + (255,))
        x += bbox[2] - bbox[0]
    img = img.crop((0, 0, min(W, x + 40), H))
    img = img.resize((img.width // 4, H // 4), Image.LANCZOS)
    img.save(f"{out_dir}/wordmark.png")
    print("wordmark:", img.size)


def main():
    img = build_background()
    # 链环后面的暖色氛围光
    img = draw_glow(img, CHAIN_CX, CHAIN_CY, S * 0.3, (205, 158, 112), 26)
    img = draw_chain(img)
    img = draw_workflow(img)
    out_dir = "assets"
    save_all(img, out_dir)
    # 画布原图留作参照
    img.convert("RGB").save(f"{out_dir}/icon-art.png")
    make_wordmark(out_dir)
    print("done:", out_dir)


if __name__ == "__main__":
    main()
