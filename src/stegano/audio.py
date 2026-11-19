from fractions import Fraction
import numpy as np
import soundfile as sf
from scipy.signal import correlate, correlation_lags, resample_poly

def _overlap(a, b, lag):
    a0, b0 = max(lag, 0), max(-lag, 0)
    n = min(len(a)-a0, len(b)-b0)
    if n <= 0: raise ValueError('no target/reference overlap')
    return a[a0:a0+n], b[b0:b0+n], a0

def _align(target, sr, reference, ref_sr):
    if ref_sr != sr:
        ratio = Fraction(sr, ref_sr).limit_denominator(100000)
        reference = resample_poly(reference, ratio.numerator, ratio.denominator, axis=0)
    if target.shape[1] != reference.shape[1]:
        target, reference = target.mean(axis=1, keepdims=True), reference.mean(axis=1, keepdims=True)
    t, r = target.mean(axis=1), reference.mean(axis=1)
    factor = max(1, round(sr/4000))
    td, rd = resample_poly(t, 1, factor), resample_poly(r, 1, factor)
    td, rd = td-td.mean(), rd-rd.mean()
    corr = correlate(td, rd, mode='full', method='fft')
    lags = correlation_lags(len(td), len(rd), mode='full')
    coarse = int(lags[np.argmax(np.abs(corr))])*factor
    best, score = coarse, -1.0
    for lag in range(coarse-factor, coarse+factor+1):
        try: x, y, _ = _overlap(target, reference, lag)
        except ValueError: continue
        x, y = x.mean(axis=1), y.mean(axis=1)
        x, y = x-x.mean(), y-y.mean()
        den = np.linalg.norm(x)*np.linalg.norm(y)
        s = abs(float(np.dot(x,y)/den)) if den else 0.0
        if s > score: best, score = lag, s
    x, y, start = _overlap(target, reference, best)
    return x, y, {'lag_samples': best, 'correlation': score, 'target_start_sample': start}


def _project_symbol(samples, start_sample, sample_rate, carrier):
    """Measure one unfiltered ASK symbol against a globally phased carrier."""
    samples = np.asarray(samples, dtype=np.float64)
    sample_indices = np.arange(start_sample, start_sample + len(samples), dtype=np.float64)
    phase = 2 * np.pi * carrier * sample_indices / sample_rate
    centered = samples - samples.mean()
    in_phase = 2 * np.dot(centered, np.cos(phase)) / len(samples)
    quadrature = 2 * np.dot(centered, np.sin(phase)) / len(samples)
    return float(np.hypot(in_phase, quadrature))

def _decode_sleepy_alarm(path, reference_path=None, carrier=8000.0, baud=50.0, duration=7.0):
    target, sr = sf.read(path, always_2d=True, dtype='float64')
    signal, alignment = target, None
    if reference_path:
        ref, ref_sr = sf.read(reference_path, always_2d=True, dtype='float64')
        x, y, alignment = _align(target, sr, ref, ref_sr)
        # Keep every target sample before the overlap. The symbol clock and
        # carrier phase remain anchored at target sample zero.
        prefix = target[:alignment['target_start_sample']]
        if target.shape[1] != ref.shape[1]: prefix = prefix.mean(axis=1, keepdims=True)
        signal = np.concatenate((prefix, x-y), axis=0)
    if baud <= 0 or carrier <= 0 or carrier >= sr/2: raise ValueError('invalid baud/carrier')
    channel = signal[:,0]
    sps, count = sr/baud, round(duration*baud)
    levels=[]
    for i in range(count):
        a,b=round(i*sps),round((i+1)*sps)
        if b>len(channel): break
        z=channel[a:b]
        if len(z)<8: break
        # Project original samples per symbol; no whole-signal filter can
        # discard an edge or smear energy across adjacent symbol windows.
        levels.append(_project_symbol(z, a, sr, carrier))
    if len(levels)!=count: raise ValueError(f'expected {count} symbols, measured {len(levels)}')
    values=np.asarray(levels); centers=np.quantile(values,[.05,.5,.95])
    for _ in range(100):
        labels=np.argmin(np.abs(values[:,None]-centers[None,:]),axis=1)
        new=np.array([values[labels==k].mean() if np.any(labels==k) else centers[k] for k in range(3)])
        new.sort()
        if np.allclose(new,centers,rtol=1e-7,atol=1e-12): centers=new; break
        centers=new
    labels=np.argmin(np.abs(values[:,None]-centers[None,:]),axis=1)
    if len(np.unique(labels))!=3: raise ValueError('could not separate three ASK levels')
    symbols=[{0:' ',1:'0',2:'1'}[int(x)] for x in labels]
    chunks=[]; current=[]
    for bit in symbols:
        if bit==' ':
            if current: chunks.append(''.join(current)); current=[]
        else: current.append(bit)
    if current: chunks.append(''.join(current))
    errors=[]; chars=[]
    for i,bits in enumerate(chunks):
        if len(bits)!=8: errors.append({'byte_index':i,'bits':bits})
        else: chars.append(chr(int(bits,2)))
    text=''.join(chars)
    valid=len(chunks)==39 and not errors and len(text)==39 and text.startswith('ictf{') and text.endswith('}')
    result = {'decoded_text':text,'character_count':len(text),'format_valid':valid,'symbol_count':len(levels),'separator_count':symbols.count(' '),'reference_assisted':reference_path is not None,'alignment':alignment,'errors':errors,'amplitude_centers':centers.tolist()}
    groups=[]
    for i, bits in enumerate(chunks):
        character = chr(int(bits, 2)) if len(bits) == 8 else None
        groups.append({'byte_index':i,'bits':bits,'character':character,'codepoint':ord(character) if character is not None else None,'error':len(bits)!=8})
    diagnostics = {
        'sample_rate':int(sr),
        'symbol_rate':float(baud),
        'carrier_hz':float(carrier),
        'duration_seconds':float(duration),
        'symbol_times_seconds':((np.arange(len(values), dtype=np.float64)+0.5)/baud).tolist(),
        'amplitude_levels':values.tolist(),
        'symbol_labels':[symbols[i] for i in range(len(symbols))],
        'clusters':[{'label':{0:'separator',1:'0',2:'1'}[i],'center':float(centers[i])} for i in range(3)],
        'groups':groups,
    }
    return result, diagnostics


def decode_sleepy_alarm(path, reference_path=None, carrier=8000.0, baud=50.0, duration=7.0):
    """Return the Sleepy Alarm extraction result."""
    result, _ = _decode_sleepy_alarm(path, reference_path, carrier, baud, duration)
    return result


def diagnose_sleepy_alarm(path, reference_path=None, carrier=8000.0, baud=50.0, duration=7.0):
    """Return the decoder result plus the exact ASK measurements used to create it."""
    result, diagnostics = _decode_sleepy_alarm(path, reference_path, carrier, baud, duration)
    return {'result':result,'diagnostics':diagnostics}
