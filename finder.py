"""
find_nearby_centers.py

Given a known (approximate) view center and zoom level, refines the seed
to sufficient precision, derives a search region sized appropriately for
that zoom, and finds hyperbolic centers close to it.
"""

from mpmath import mp, mpc, mpf
import math


def find_hyperbolic_center_precise(c_guess, period, prec_digits, iterations=200):
    mp.dps = prec_digits + 10
    c = mpc(c_guess)
    tol = mpf(10) ** (-(prec_digits - 5))

    for _ in range(iterations):
        z = mpc(0, 0)
        dz_dc = mpc(0, 0)

        for _ in range(period):
            dz_dc = 2 * z * dz_dc + 1
            z = z * z + c

        if abs(dz_dc) < mpf(10) ** (-(prec_digits + 5)):
            return None

        c_new = c - z / dz_dc
        if abs(c_new - c) < tol:
            c = c_new
            break
        c = c_new

    z = mpc(0, 0)
    for _ in range(period):
        z = z * z + c
    if abs(z) > mpf(10) ** (-(prec_digits - 10)):
        return None

    return c


def find_closest_center(target, periods, prec_digits):
    """target: mpc. Returns (period, center, distance) for the closest match."""
    best = None
    best_dist = None

    for period in periods:
        result = find_hyperbolic_center_precise(target, period, prec_digits)
        if result is None:
            continue
        dist = abs(result - target)
        if best_dist is None or dist < best_dist:
            best = (period, result, dist)
            best_dist = dist

    return best


if __name__ == "__main__":
    # --- Your known point and zoom ---
    center_x_str = "-1.5226942242603805"
    center_y_str = "1.6447649956728682e-07"
    zoom = 4.000401786318653e+21

    # --- Derive precision needed just to represent this zoom depth ---
    # log10(zoom) tells you how many digits are needed to resolve individual
    # pixels at this depth; add generous margin for the search itself.
    digits_for_zoom = int(math.log10(zoom))
    prec_digits = digits_for_zoom + 25   # margin for Newton's method + search precision

    print(f"zoom requires ~{digits_for_zoom} digits, using prec_digits={prec_digits}")

    mp.dps = prec_digits + 10
    target = mpc(mpf(center_x_str), mpf(center_y_str))

    # --- Derive search region size from zoom ---
    # At this zoom, the visible complex-plane width is roughly base_width/zoom.
    # base_width ~4.0 is the rough width of the whole Mandelbrot set on the real axis.
    base_width = mpf(4.0)
    view_width = base_width / mpf(zoom)

    print(f"view width at this zoom: {mp.nstr(view_width, 10)}")

    # --- Search for the closest hyperbolic center across a range of periods ---
    # Higher periods = smaller, more numerous, more likely to be VERY close.
    periods = range(2, 300)

    result = find_closest_center(target, periods, prec_digits)

    if result is None:
        print("No hyperbolic center found — try a wider period range or a different seed.")
    else:
        period, center, dist = result
        print(f"\nClosest hyperbolic center found:")
        print(f"  period: {period}")
        print(f"  real:   {mp.nstr(center.real, prec_digits)}")
        print(f"  imag:   {mp.nstr(center.imag, prec_digits)}")
        print(f"  distance from target: {mp.nstr(dist, 10)}")
        print(f"  (view width at target zoom: {mp.nstr(view_width, 10)})")

        if dist < view_width:
            print("  -> distance is SMALLER than the view width: this center is visible in-frame.")
        else:
            print("  -> distance is LARGER than the view width: this center may be off-screen at this zoom.")