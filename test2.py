import numpy as np
from scipy.optimize import brentq


def critical_orbit(c, p):
    z = 0.0
    for _ in range(p):
        z = z*z + c
    return z


def exact_center(c, p, tol=1e-10):
    """
    Check whether c is a center of exact period p.
    """
    z = 0.0

    for k in range(1, p):
        z = z*z + c

        if abs(z) < tol:
            return False

    z = z*z + c

    return abs(z) < tol


def find_period_p_centers(
    p,
    target=-1.8,
    radius=0.5,
    samples=1_000_000
):
    """
    Search for real centers of exact period p.

    c is restricted to the real axis.
    """

    left = max(-2.0, target - radius)
    right = min(0.25, target + radius)

    xs = np.linspace(left, right, samples)

    roots = []

    previous_c = xs[0]
    previous_f = critical_orbit(previous_c, p)

    for c in xs[1:]:

        f = critical_orbit(c, p)

        # Detect a sign change
        if previous_f * f < 0:

            root = brentq(
                lambda x: critical_orbit(x, p),
                previous_c,
                c,
                xtol=1e-14
            )

            if exact_center(root, p):

                if all(abs(root-r) > 1e-9 for r in roots):
                    roots.append(root)

        previous_c = c
        previous_f = f

    roots.sort(key=lambda c: abs(c-target))

    return roots


if __name__ == "__main__":

    p = 50

    centers = find_period_p_centers(
        p=p,
        target=-1.8,
        radius=0.5,
        samples=1_000_000
    )

    print("Found", len(centers), "centers")

    for c in centers:
        print(
            f"c = {c:.15f}, "
            f"distance = {abs(c + 1.8):.15e}"
        )
