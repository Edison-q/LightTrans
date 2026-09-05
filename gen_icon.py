"""生成 LightTrans 图标：icon.png（PWA 用，180px）+ icon.ico（Windows 快捷方式用，16-256px 多尺寸）。

用法: uv run python gen_icon.py
高清源图以 512px 绘制再下采样，保证 Windows 桌面/任务栏大图标清晰。
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent


def draw(size: int) -> Image.Image:
    """星际跃迁风格：深空蓝 -> 青渐变 + 星空 + 光带 + 四角跃迁星。"""
    c1, c2 = (10, 42, 74), (6, 182, 212)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / size
        color = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
        d.line([(0, y), (size, y)], fill=color + (255,))
    # 星空（按比例缩放）
    random.seed(42)
    s = size / 180.0
    for _ in range(26):
        x = random.randint(int(6 * s), int(174 * s))
        y = random.randint(int(6 * s), int(174 * s))
        r = random.choice((1, 1, 2)) * s
        a = random.randint(90, 190)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 240, 255, a))
    # 跃迁光带
    bands = (((28, 58, 78, 63), 190), ((96, 118, 168, 123), 160), ((30, 150, 64, 154), 140))
    for box, alpha in bands:
        x1, y1, x2, y2 = (int(v * s) for v in box)
        d.rounded_rectangle([x1, y1, x2, y2], radius=2, fill=(180, 240, 255, alpha))
    # 四角跃迁星
    cx, cy, ro, ri = 90 * s, 95 * s, 58 * s, 17 * s
    pts = [(cx, cy - ro), (cx + ri, cy - ri), (cx + ro, cy), (cx + ri, cy + ri),
           (cx, cy + ro), (cx - ri, cy + ri), (cx - ro, cy), (cx - ri, cy - ri)]
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.ellipse([cx - 6 * s, cy - 6 * s, cx + 6 * s, cy + 6 * s], fill=(200, 245, 255, 255))
    # 圆角遮罩
    mask = Image.new("L", (size, size), 0)
    dm = ImageDraw.Draw(mask)
    dm.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(40 * s), fill=255)
    img.putalpha(mask)
    return img


def main() -> None:
    # PWA 图标：180px（仅当不存在时生成，避免覆盖用户自绘图标）
    png_path = BASE_DIR / "icon.png"
    if not png_path.exists():
        draw(180).save(png_path)
        print(f"[gen_icon] 生成 {png_path.name} (180x180)")
    else:
        print(f"[gen_icon] {png_path.name} 已存在，跳过（如需重建请先删除）")

    # Windows 快捷方式图标：512px 高清绘制 -> 多尺寸 ICO
    hi = draw(512)
    ico_path = BASE_DIR / "icon.ico"
    hi.save(ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                             (64, 64), (128, 128), (256, 256)])
    print(f"[gen_icon] 生成 {ico_path.name} (16-256 多尺寸, 512px 源图)")

    # PWA 安装图标（manifest 引用）
    draw(192).save(BASE_DIR / "icon-192.png")
    draw(512).save(BASE_DIR / "icon-512.png")
    print("[gen_icon] 生成 icon-192.png / icon-512.png")


if __name__ == "__main__":
    main()
