"""Read only technical EXIF fields. Do not expose GPS, serial numbers or owner data."""
import math
from datetime import datetime
from fractions import Fraction


def technical_metadata(image):
    exif = image.getexif()
    try:
        camera = exif.get_ifd(34665)
    except (ValueError, TypeError, OSError):
        camera = {}
    def value(tag):
        return camera.get(tag, exif.get(tag))
    def clean(raw):
        return str(raw).replace('\x00', '').strip()[:160] if raw is not None else ''
    result = {}
    model = clean(value(272))
    make = clean(value(271))
    result['camera_body'] = f'{make} {model}'.strip() if make and model and not model.lower().startswith(make.lower()) else model or make
    result['lens'] = clean(value(42036))
    raw_date = clean(value(36867))
    if raw_date:
        try:
            result['taken_at'] = datetime.strptime(raw_date, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    for field, tag in [('shutter_speed', 33434), ('aperture', 33437), ('iso', 34855), ('focal_length', 37386)]:
        try:
            number = float(value(tag))
            if not math.isfinite(number) or number <= 0:
                continue
            if field == 'shutter_speed':
                fraction = Fraction(number).limit_denominator(100000)
                result[field] = f'{fraction.numerator}/{fraction.denominator} s' if number < 1 else f'{number:g} s'
            elif field == 'aperture':
                result[field] = f'f/{number:g}'
            elif field == 'focal_length':
                result[field] = f'{number:g} mm'
            else:
                result[field] = f'{number:g}'
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            pass
    return {k: v for k, v in result.items() if v}
