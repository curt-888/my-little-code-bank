#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "原图"
OUT_3X4_DIR = ROOT / "3x4_宽1440高1920_超高文件名待修改"
OUT_1X1_DIR = ROOT / "1x1_白底1440_图片高1440"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def image_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCE_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def output_path(base_dir: Path, source: Path, stem_suffix: str = "") -> Path:
    relative = source.relative_to(SOURCE_DIR)
    folder = base_dir / relative.parent
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{source.stem}{stem_suffix}.jpg"


def resize_to_width(image: Image.Image, width: int) -> Image.Image:
    ratio = width / image.width
    height = round(image.height * ratio)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def resize_to_height(image: Image.Image, height: int) -> Image.Image:
    ratio = height / image.height
    width = round(image.width * ratio)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def as_rgb_with_white_background(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        canvas = Image.new("RGB", image.size, "white")
        canvas.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
        return canvas
    return image.convert("RGB")


def save_jpeg(image: Image.Image, path: Path) -> None:
    image.save(path, "JPEG", quality=95, optimize=True, progressive=True)


def make_3x4(source: Path) -> tuple[Path, bool]:
    with Image.open(source) as opened:
        image = as_rgb_with_white_background(ImageOps.exif_transpose(opened))
        resized = resize_to_width(image, 1440)

    too_tall = resized.height > 1920
    stem_suffix = "_待修改" if too_tall else ""
    path = output_path(OUT_3X4_DIR, source, stem_suffix)

    if too_tall:
        final_image = resized
    else:
        final_image = Image.new("RGB", (1440, 1920), "white")
        top = (1920 - resized.height) // 2
        final_image.paste(resized, (0, top))

    save_jpeg(final_image, path)
    return path, too_tall


def make_1x1(source: Path) -> Path:
    with Image.open(source) as opened:
        image = as_rgb_with_white_background(ImageOps.exif_transpose(opened))
        resized = resize_to_height(image, 1440)

    if resized.width > 1440:
        resized = resize_to_width(resized, 1440)

    final_image = Image.new("RGB", (1440, 1440), "white")
    left = (1440 - resized.width) // 2
    top = (1440 - resized.height) // 2
    final_image.paste(resized, (left, top))

    path = output_path(OUT_1X1_DIR, source)
    save_jpeg(final_image, path)
    return path


def write_readme(processed_count: int, needs_edit_count: int) -> None:
    notes = {
        OUT_3X4_DIR
        / "规格说明.txt": "\n".join(
            [
                "3x4规格：目标画布宽1440，高1920。",
                "处理方式：原图按宽度1440等比缩放，不拉伸、不裁切。",
                "如果等比缩放后的高度不超过1920，会居中放到白底1440x1920画布。",
                "如果高度超过1920，会保留完整高度并在文件名加“_待修改”，方便后续人工调整。",
                "",
            ]
        ),
        OUT_1X1_DIR
        / "规格说明.txt": "\n".join(
            [
                "1x1规格：白底画布1440x1440。",
                "处理方式：先把原图高度等比调整到1440，再把宽度用纯白画布补齐到1440。",
                "如果高度调整到1440后宽度超过1440，会等比缩小到宽度1440，避免拉伸和裁切。",
                "",
            ]
        ),
    }

    for path, text in notes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(f"找不到原图文件夹：{SOURCE_DIR}")

    sources = image_files()
    if not sources:
        raise SystemExit(f"原图文件夹里没有找到图片：{SOURCE_DIR}")

    needs_edit_count = 0
    for source in sources:
        _, too_tall = make_3x4(source)
        make_1x1(source)
        needs_edit_count += int(too_tall)

    write_readme(len(sources), needs_edit_count)
    print(f"处理完成：{len(sources)}张图片")
    print(f"3x4需要人工修改：{needs_edit_count}张")
    print(f"输出文件夹：{OUT_3X4_DIR.name} / {OUT_1X1_DIR.name}")


if __name__ == "__main__":
    main()
