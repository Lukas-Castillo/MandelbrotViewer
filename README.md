# MandelbrotViewer
A python program that renders the mandelbrot set with perubation theory

Based on this: https://www.superfractalthing.co.nf/sft_maths.pdf

# Compiling 

```bash
sudo pacman -S gmp mpfr gcc make
```

```bash
gcc -O3 -shared -fPIC native/orbit_lib.c -lmpfr -lgmp -o native/liborbit.so
```

```bash
pip install -r requirements.txt
```

# Running
```bash
python main.py
```

- Change camera position in main.py.
- Set recording to True to record frames.
