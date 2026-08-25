import io
import base64
from PIL import Image, ImageOps

def preprocess_image(image_bytes, filename):
    """
    Validates, corrects EXIF orientation, resizes, and base64 encodes report images.
    """
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        raise ValueError("Unsupported file type. Only JPG, JPEG, PNG, and WEBP are supported.")
        
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise ValueError("Could not open image file. The file may be corrupt.")

    # Auto-orient based on EXIF tag
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        # EXIF transpose can fail on certain PIL versions or image types without EXIF
        pass

    # Convert paletted images (like some PNGs/GIFs) or RGBA to RGB for JPEG conversion if needed,
    # but we can save PNG as PNG and JPEG/WEBP as JPEG.
    save_format = 'PNG' if ext == 'png' else 'JPEG'
    if save_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')

    # Downscale if excessively large (e.g. > 1600px width/height) to stay within LLM token/payload limits
    max_dim = 1600
    if img.width > max_dim or img.height > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Output to buffer
    buffer = io.BytesIO()
    if save_format == 'PNG':
        img.save(buffer, format='PNG')
        mime_type = 'image/png'
    else:
        img.save(buffer, format='JPEG', quality=85)
        mime_type = 'image/jpeg'

    processed_bytes = buffer.getvalue()
    b64_data = base64.b64encode(processed_bytes).decode('utf-8')

    return {
        "base64": b64_data,
        "mime_type": mime_type,
        "width": img.width,
        "height": img.height,
        "size_bytes": len(processed_bytes)
    }
