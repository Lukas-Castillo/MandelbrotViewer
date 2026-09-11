#version 400
#extension GL_ARB_gpu_shader_fp64 : enable

#ifdef GL_ES
precision highp float;
#endif

uniform vec2 u_resolution;
uniform float u_time;
uniform dvec2 cam;

uniform sampler2D u_orbit;
uniform int u_orbitLength;

uniform bool pertube;

uniform int u_recLimit;
const float LN2 = 0.69314718;

const int PALETTE_SIZE = 16;
const vec3 c0  = vec3(0.0980, 0.0275, 0.1020); #19071A
const vec3 c1  = vec3(0.2588, 0.1176, 0.0588); #421E0F
const vec3 c2  = vec3(0.0353, 0.0039, 0.1843); #09012F
const vec3 c3  = vec3(0.0157, 0.0157, 0.2863); #040449
const vec3 c4  = vec3(0.0000, 0.0275, 0.3922); #000764
const vec3 c5  = vec3(0.0471, 0.1725, 0.5412); #0C2C8A
const vec3 c6  = vec3(0.0941, 0.3216, 0.6941); #1852B1
const vec3 c7  = vec3(0.2235, 0.4902, 0.8196); #397DD1
const vec3 c8  = vec3(0.5255, 0.7098, 0.8980); #86B5E5
const vec3 c9  = vec3(0.8275, 0.9255, 0.9725); #D3ECF8
const vec3 c10 = vec3(0.4157, 0.2039, 0.0118); #6A3403
const vec3 c11 = vec3(0.6000, 0.3412, 0.0000); #995700
const vec3 c12 = vec3(0.8000, 0.5020, 0.0000); #CC8000
const vec3 c13 = vec3(1.0000, 0.6667, 0.0000); #FFAA00
const vec3 c14 = vec3(0.9725, 0.7882, 0.3725); #F8C95F
const vec3 c15 = vec3(0.9451, 0.9137, 0.7490); #F1E9BF
const vec3 c16 = vec3(0.0, 0.0, 0.0);          #000000

vec3 gCol(int i) {
    if (i == 0)  return c0;
    if (i == 1)  return c1;
    if (i == 2)  return c2;
    if (i == 3)  return c3;
    if (i == 4)  return c4;
    if (i == 5)  return c5;
    if (i == 6)  return c6;
    if (i == 7)  return c7;
    if (i == 8)  return c8;
    if (i == 9)  return c9;
    if (i == 10) return c10;
    if (i == 11) return c11;
    if (i == 12) return c12;
    if (i == 13) return c13;
    if (i == 14) return c14;
    if (i == 15) return c15;
    return c16;
}

bool inPeriodBulb(double x, double y) {
    double xShift = x - 0.25lf;
    double q = xShift * xShift + y * y;

    if (q * (q + xShift) <= 0.25lf * y * y) return true;

    double xPlus1 = x + 1.0lf;
    if (xPlus1 * xPlus1 + y * y <= 0.0625lf) return true;

    return false;
}

dvec2 fetchOrbit(int n) {
    n = min(u_orbitLength - 1, n);
    float u = (float(n) + 0.5) / float(u_orbitLength);
    vec4 orbitData = texture(u_orbit, vec2(u, 0.5));
    double x = double(orbitData.x) + double(orbitData.z);
    double y = double(orbitData.y) + double(orbitData.w);
    return dvec2(x, y);
}

double pow2Double(double exponent) {
    if(exponent < 0){
        return double(exp2(float(exponent)));
    }

    double wholePart = floor(exponent);
    double fracPart = exponent - wholePart;

    int e = int(wholePart);
    double result = 1.0lf;
    double base = 2.0lf;
    for (int i = 0; i < 32; i++) {
        if ((e & 1) == 1) result *= base;
        base *= base;
        e >>= 1;
        if (e == 0) break;
    }

    float fracScale = exp2(float(fracPart));
    result *= double(fracScale);

    return result;
}

void main (void) {
    double zoom = pow2Double(u_time - 3.0);

    dvec2 st = dvec2(gl_FragCoord.xy / u_resolution.xy) - dvec2(0.5lf, 0.5lf);
    double aspect = double(u_resolution.x / u_resolution.y);
    st.x *= aspect;
    st = st / zoom;
    st += cam;

    dvec2 dz0 = dvec2(gl_FragCoord.xy / u_resolution.xy) - dvec2(0.5lf, 0.5lf);
    dz0.x *= aspect;
    dz0 = dz0 / zoom;

    if (inPeriodBulb(st.x, st.y)) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); // same as interior color below
        return;
    }

    vec3 color = vec3(0.0);
    dvec2 z = dvec2(0.0lf, 0.0lf);
    int count = 0;

    if(zoom > 1000 && pertube){
    // if(pertube){
        dvec2 dz = dvec2(0.0lf, 0.0lf);
        dvec2 zPrev = dvec2(0.0lf, 0.0lf); 

        for (int i = 0; i < u_recLimit; i++) {
            if (i >= u_orbitLength) break;

            dz = 2.0lf*dvec2(zPrev.x*dz.x - zPrev.y*dz.y, zPrev.x*dz.y + zPrev.y*dz.x)
                + dvec2(dz.x*dz.x - dz.y*dz.y, 2.0lf*dz.x*dz.y)
                + dz0;
            count++;

            z = fetchOrbit(i);
            zPrev = z;
            z += dz;

            if (z.x*z.x + z.y*z.y > 4.0lf) break;
        }
    }else{
        for (int i = 0; i < u_recLimit; i++) {
            z = dvec2(z.x * z.x - z.y * z.y, 2.0lf * z.x * z.y) + st;
            count++;
            if (z.x * z.x + z.y * z.y > 4.0lf) break;
        }
    }

    if (count == u_recLimit) {
        color = vec3(0.0, 0.0, 0.0);
    } else {
        float zx = float(z.x);
        float zy = float(z.y);

        float log_zn = log(zx * zx + zy * zy) / 2.0;
        float nu = log(log_zn / LN2) / LN2;
        float nCount = float(count) + 1.0 - nu;

        int i1 = int(mod(nCount, float(PALETTE_SIZE)));
        int i2 = int(mod(nCount + 1.0, float(PALETTE_SIZE)));
        color = mix(gCol(i1), gCol(i2), fract(nCount));
    }

    if(pertube) gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);

    if (any(isnan(color)) || any(isinf(color))) {
        color = vec3(1.0, 0.0, 1.0);
    }

    gl_FragColor = vec4(color, 1.0);
}