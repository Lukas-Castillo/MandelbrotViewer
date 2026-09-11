//gcc -O3 -shared -fPIC native/orbit_lib.c -lmpfr -lgmp -o native/liborbit.so

#include <stdio.h>
#include <mpfr.h>

int main() { 
    printf("MPFR %s\n", mpfr_get_version()); return 0;
}

void computeOrbit(const char* cxS, const char* cyS, int maxIter, int prec, double* out, int* len){
    mpfr_set_default_prec(prec);
    mpfr_t zx, zy, sqx, sqy, cx, cy, mag;
    mpfr_inits(zx, zy, sqx, sqy, cx, cy, mag, NULL);
    mpfr_set_str(cx, cxS, 10, MPFR_RNDN);
    mpfr_set_str(cy, cyS, 10, MPFR_RNDN);
    mpfr_set_zero(zx, 1);
    mpfr_set_zero(zy, 1);

    int i;
    for(i = 0; i < maxIter; i++){
        mpfr_sqr(sqx, zx, MPFR_RNDN);
        mpfr_sqr(sqy, zy, MPFR_RNDN);

        //y
        mpfr_mul(zy, zy, zx, MPFR_RNDN);
        mpfr_mul_ui(zy, zy, 2, MPFR_RNDN);
        mpfr_add(zy, zy, cy, MPFR_RNDN);

        //x
        mpfr_sub(zx, sqx, sqy, MPFR_RNDN);
        mpfr_add(zx, zx, cx, MPFR_RNDN);
        
        out[i*2] = mpfr_get_d(zx, MPFR_RNDN);
        out[i*2+1] = mpfr_get_d(zy, MPFR_RNDN);

        mpfr_add(mag, sqx, sqy, MPFR_RNDN);
        if(mpfr_get_d(mag, MPFR_RNDN) > 4.0) {i++;break;}
    }

    *len = i;
    mpfr_clears(zx, zy, sqx, sqy, cx, cy, mag, NULL);
}