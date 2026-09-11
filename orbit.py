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
    ctypes.POINTER(ctypes.c_double),   # out_buf
    ctypes.POINTER(ctypes.c_int),     # out_len
]
lib.computeOrbit.restype = None

def computeOrbit(cre: str, cim: str, max_iter: int, prec_bits: int):
    buf = (ctypes.c_double * (2 * max_iter))()
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
    arr = np.frombuffer(buf, dtype=np.float64, count=2*n).reshape(n, 2)
    return arr  # shape (n, 2): columns are Re(Z_n), Im(Z_n)