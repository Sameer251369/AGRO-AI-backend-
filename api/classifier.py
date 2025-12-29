"""Improved lightweight heuristic classifier.

This is still a placeholder and should be replaced with a proper
ML model for production, but it's more reliable than the previous
random-based heuristic:

- Uses green-pixel ratio and edge density to decide plant vs non-plant.
- Uses yellow/brown pixel ratio to detect likely disease symptoms.
- Maps image content deterministically to an existing disease id
  using a stable hash so frontend will receive real DB entries.
"""
from PIL import Image, ImageFilter
import hashlib
from .models import Disease


def _stable_disease_id_for_image(img_bytes, pk_list):
    """Map image bytes deterministically to one of the available PKs.

    pk_list: a list/sequence of available primary keys (ints).
    Returns an element from pk_list or None if empty.
    """
    if not pk_list:
        return None
    h = hashlib.sha256(img_bytes).digest()
    num = int.from_bytes(h[:6], 'big')
    idx = num % len(pk_list)
    return pk_list[idx]


def classify_image(image_path):
    """Return a dict: is_plant, is_healthy, disease_id, confidence"""

    import logging
    try:
        img = Image.open(image_path).convert('RGB')
        thumb = img.resize((200, 200))
        pixels = list(thumb.getdata())
        total = len(pixels)
        green_count = 0
        brown_yellow_count = 0
        for (r, g, b) in pixels:
            if g > r + 15 and g > b + 15 and g > 80:
                green_count += 1
            if (r > g + 25 and r > b + 25 and r > 100) or (r > 120 and g > 100 and b < 120):
                brown_yellow_count += 1
        green_ratio = green_count / total
        discolor_ratio = brown_yellow_count / total
        gray = thumb.convert('L')
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_pixels = list(edges.getdata())
        edge_count = sum(1 for v in edge_pixels if v > 30)
        edge_ratio = edge_count / len(edge_pixels)
        is_plant = (
            (green_ratio > 0.22 and edge_ratio > 0.06) or
            (green_ratio > 0.32) or
            (green_ratio > 0.18 and edge_ratio > 0.09)
        )
        if green_ratio < 0.09 and edge_ratio < 0.02:
            is_plant = False
    except Exception as e:
        logging.error(f"Image processing failed: {e}")
        is_plant = False
        green_ratio = 0.0
        discolor_ratio = 0.0
        edge_ratio = 0.0

    if not is_plant:
        return {
            'is_plant': False,
            'is_healthy': False,
            'disease_id': None,
            'confidence': 0.98,
            'label': 'non-plant',
            'summary': 'This image does not appear to be a plant.',
            'green_ratio': round(green_ratio, 4),
            'discolor_ratio': round(discolor_ratio, 4),
            'edge_ratio': round(edge_ratio, 4),
        }

    # Determine healthy vs diseased using stronger discoloration and edge patterns
    # Use multiple signals to reduce false positives:
    # - discolor_ratio: fraction of brown/yellow pixels
    # - green_ratio: overall greenness
    # - edge_ratio: texture/vein visibility

    diseased = False
    # Make disease detection slightly stricter to avoid flagging healthy plants/background noise.
    if discolor_ratio > 0.08:
        diseased = True
    elif discolor_ratio > 0.05 and green_ratio < 0.14:
        diseased = True
    elif edge_ratio < 0.01 and green_ratio < 0.10:
        diseased = True

    # Get the number of diseases available in DB
    try:
        pk_list = list(Disease.objects.values_list('pk', flat=True))
    except Exception as e:
        logging.error(f"Could not fetch Disease PKs: {e}")
        pk_list = []

    # Read bytes for stable hashing
    try:
        with open(image_path, 'rb') as f:
            b = f.read()
    except Exception as e:
        logging.error(f"Could not read image bytes: {e}")
        b = hashlib.sha256((image_path or '').encode()).digest()

    if not diseased:
        # healthy confidence higher if green_ratio strong
        conf = min(0.99, max(0.75, 0.5 + (green_ratio - 0.1) * 2.0))
        summary = f"Healthy-looking plant (green_ratio={green_ratio:.2f}, edge_ratio={edge_ratio:.2f})"
        return {
            'is_plant': True,
            'is_healthy': True,
            'disease_id': None,
            'confidence': round(conf, 2),
            'label': 'healthy',
            'summary': summary,
            'green_ratio': round(green_ratio, 4),
            'discolor_ratio': round(discolor_ratio, 4),
            'edge_ratio': round(edge_ratio, 4),
        }

    # For diseased, pick a stable disease id based on image hash
    disease_id = _stable_disease_id_for_image(b, pk_list)
    # Confidence influenced by discoloration and edge_ratio
    conf = 0.55 + min(0.4, (discolor_ratio - 0.03) * 6.0 + edge_ratio * 0.5)
    conf = max(0.5, min(conf, 0.99))

    # severity: low/medium/high based on discoloration
    if discolor_ratio > 0.12:
        severity = 'high'
    elif discolor_ratio > 0.06:
        severity = 'medium'
    else:
        severity = 'low'

    summary = f"Signs of disease ({severity}) — discoloration={discolor_ratio:.3f}, green={green_ratio:.3f}, edges={edge_ratio:.3f}"

    return {
        'is_plant': True,
        'is_healthy': False,
        'disease_id': int(disease_id) if disease_id is not None else None,
        'confidence': round(conf, 2),
        'label': 'diseased',
        'summary': summary,
        'severity': severity,
        'green_ratio': round(green_ratio, 4),
        'discolor_ratio': round(discolor_ratio, 4),
        'edge_ratio': round(edge_ratio, 4),
    }
