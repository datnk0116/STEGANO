from pathlib import Path
import numpy as np
from PIL import Image

def _decode_blue3(path):
    with Image.open(path) as im:
        pixels = np.asarray(im.convert('RGB'), dtype=np.int16)
    h, w, _ = pixels.shape
    colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    base = colors[int(np.argmax(counts))].astype(np.int16)
    attempts = []
    selected_blocks = []
    for n in range(2, min(w, h) + 1):
        cw, ch = w // n, h // n
        chars = []
        blocks = []
        for i in range(n):
            block = pixels[i*ch:(i+1)*ch, i*cw:(i+1)*cw]
            channel_delta = (block - base).sum(axis=(0, 1))
            value = int(channel_delta.sum())
            if not 0 <= value <= 0x10ffff:
                chars = []
                break
            chars.append(chr(value))
            blocks.append({
                'index':i,
                'x0':i*cw,
                'y0':i*ch,
                'x1':(i+1)*cw,
                'y1':(i+1)*ch,
                'rgb_delta':[int(v) for v in channel_delta],
                'value':value,
                'character':chr(value),
            })
        candidate = ''.join(chars)
        if candidate:
            attempts.append({'length': n, 'candidate': candidate})
        if candidate.startswith('byuctf{') and candidate.endswith('}') and all(c.isalnum() or c in '_{}' for c in candidate):
            selected_blocks = blocks
            return (
                {'flag': candidate, 'format_valid': True, 'attempts': attempts},
                pixels,
                tuple(int(v) for v in base),
                int(counts[int(np.argmax(counts))]),
                selected_blocks,
            )
    return (
        {'flag': None, 'format_valid': False, 'attempts': attempts},
        pixels,
        tuple(int(v) for v in base),
        int(counts[int(np.argmax(counts))]),
        selected_blocks,
    )


def decode_blue3(path):
    """Return the Blue 3 extraction result."""
    result, _, _, _, _ = _decode_blue3(path)
    return result


def diagnose_blue3(path):
    """Return the decoder result and the exact baseline/block values it used."""
    result, pixels, baseline, baseline_count, blocks = _decode_blue3(path)
    return {
        'result':result,
        'pixels':pixels.astype(np.uint8),
        'baseline':baseline,
        'baseline_count':baseline_count,
        'blocks':blocks,
    }
