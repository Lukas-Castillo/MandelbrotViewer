import ctypes
import numpy as np
import platform

from decimal import Decimal, getcontext

getcontext().prec = 60  # significant digits

# Pick the right extension for your OS
lib_name = {
    "Linux": "native/liborbit.so",
    "Darwin": "native/liborbit.dylib",
    "Windows": "native/liborbit.dll",
}[platform.system()]

lib = ctypes.CDLL(lib_name)

# Declare the function signature — this must match the C signature exactly
lib.computeOrbit.argtypes = [
    ctypes.c_char_p,                  # cre_str
    ctypes.c_char_p,                  # cim_str
    ctypes.c_int,                     # max_iter
    ctypes.c_int,                     # prec_bits
    ctypes.POINTER(ctypes.c_float),   # out_buf
    ctypes.POINTER(ctypes.c_int),     # out_len
]
lib.computeOrbit.restype = None

def computeOrbit(cre: str, cim: str, max_iter: int, prec_bits: int):
    buf = (ctypes.c_float * (2 * max_iter))()
    out_len = ctypes.c_int()

    lib.computeOrbit(
        cre.encode("utf-8"),
        cim.encode("utf-8"),
        max_iter,
        prec_bits,
        buf,
        ctypes.byref(out_len)
    )

    n = out_len.value
    print(f"length: {n}")
    arr = np.frombuffer(buf, dtype=np.float32, count=2*n).reshape(n, 2)
    return arr  # shape (n, 2): columns are Re(Z_n), Im(Z_n)

# # --- test it ---
# if __name__ == "__main__":
#     orbit = computeOrbit(
#         "0.7436438870371587047496605404481696998585993054489562",
#         "0.1318259042053101228924070199088500985419036866312666",
#         max_iter=1000,
#         prec_bits=256
#     )

#     cX = "-0.7436438870371587047496605404481696998585993054489562"
#     cY = "0.1318259042053101228924070199088500985419036866312666"
#     cX = Decimal(cX)
#     cY = Decimal(cY)

#     mxOrbit = []

#     for x in range(10):
#         for y in range(10):
#             for s in range(10):
#                 orbit = computeOrbit(
#                     format(cX +(Decimal("10")**-s)*x, "f"),
#                     format(cY +(Decimal("10")**-s)*y, "f"),
#                     max_iter=1000,
#                     prec_bits=256
#                 )
#                 print(x,y,s, len(orbit))

#                 if len(orbit) > len(mxOrbit): mxOrbit = orbit
                


#     print("orbit length:", len(orbit))
#     # print("first 5 points:\n", orbit)
#     for x in orbit: print(x)

print(computeOrbit("-0.000040271844371", "0.075993857174199", 1000, 256))
