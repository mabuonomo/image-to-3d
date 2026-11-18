from pathlib import Path
from PIL import Image


def preprocess_image(
    input_path: Path,
    output_path: Path,
    remove_bg: bool = True,
    target_size: int = 1024,
) -> Path:
    """
    Prepare an input image for 3D generation:
    1. Optionally remove background using rembg.
    2. Center and pad onto a square canvas.
    """
    img = Image.open(input_path).convert("RGBA")

    if remove_bg:
        try:
            from rembg import remove

            img = remove(img)
        except Exception as exc:
            # Fallback gracefully if rembg model download is offline
            print(f"[preprocess] rembg skipped ({exc}); using original image")

    # Crop to non-transparent bounding box if alpha channel has transparency
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # Fit inside target_size with 10% margin
    max_dim = int(target_size * 0.8)
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (target_size, target_size), (255, 255, 255, 0))
    offset_x = (target_size - img.width) // 2
    offset_y = (target_size - img.height) // 2
    canvas.paste(img, (offset_x, offset_y), img)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")
    return output_path
