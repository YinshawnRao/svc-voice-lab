"""Apply explicit, source-bound F0 repairs; never infer or smooth other frames."""
import json
import math


def apply_f0_repair(f0, specification, source_sha256):
    if specification.get('schema_version') != 1:
        raise ValueError('Unsupported F0 repair schema')
    if specification.get('source_sha256') != source_sha256:
        raise ValueError('F0 repair source hash mismatch')
    if specification.get('frame_seconds') != .01:
        raise ValueError('Expected RMVPE 10 ms frames')
    result = f0.copy()
    touched = set()
    evidence = []
    for repair in specification['repairs']:
        start, end = repair['start_frame'], repair['end_frame_exclusive']
        if not (0 < start < end < len(f0)):
            raise ValueError('Repair must have two surrounding frames')
        if touched.intersection(range(start, end)):
            raise ValueError('Overlapping F0 repairs')
        touched.update(range(start, end))
        low, high = repair['expected_original_hz_range']
        if not all(low <= float(v) <= high for v in f0[start:end]):
            raise ValueError('F0 anomaly does not match audited range')
        left, right = float(f0[start - 1]), float(f0[end])
        anchor_low, anchor_high = repair['expected_anchor_hz_range']
        if not all(anchor_low <= v <= anchor_high for v in (left, right)):
            raise ValueError('F0 anchors do not match audited range')
        for index in range(start, end):
            fraction = (index - start + 1) / (end - start + 1)
            result[index] = math.exp(math.log(left) * (1 - fraction) + math.log(right) * fraction)
        evidence.append({'start_frame': start, 'end_frame_exclusive': end,
                         'before_hz': [float(v) for v in f0[start:end]],
                         'after_hz': [float(v) for v in result[start:end]],
                         'anchor_hz': [left, right]})
    return result, evidence


def load_spec(path):
    return json.loads(path.read_text())
