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

const int REC_LIMIT = 1000;
const float LN2 = 0.69314718;

const int PALETTE_SIZE = 16;
const vec3 c0  = vec3(0.0980, 0.0275, 0.1020); // boundary dark purple  #19071A
const vec3 c1  = vec3(0.2588, 0.1176, 0.0588); // flat brown corner     #421E0F
const vec3 c2  = vec3(0.0353, 0.0039, 0.1843); // blue 1 (darkest)      #09012F
const vec3 c3  = vec3(0.0157, 0.0157, 0.2863); // blue 2                #040449
const vec3 c4  = vec3(0.0000, 0.0275, 0.3922); // blue 3                #000764
const vec3 c5  = vec3(0.0471, 0.1725, 0.5412); // blue 4                #0C2C8A
const vec3 c6  = vec3(0.0941, 0.3216, 0.6941); // blue 5                #1852B1
const vec3 c7  = vec3(0.2235, 0.4902, 0.8196); // blue 6                #397DD1
const vec3 c8  = vec3(0.5255, 0.7098, 0.8980); // blue 7                #86B5E5
const vec3 c9  = vec3(0.8275, 0.9255, 0.9725); // blue 8 (lightest)     #D3ECF8
const vec3 c10 = vec3(0.4157, 0.2039, 0.0118); // orange 1 (darkest)    #6A3403
const vec3 c11 = vec3(0.6000, 0.3412, 0.0000); // orange 2              #995700
const vec3 c12 = vec3(0.8000, 0.5020, 0.0000); // orange 3              #CC8000
const vec3 c13 = vec3(1.0000, 0.6667, 0.0000); // orange 4              #FFAA00
const vec3 c14 = vec3(0.9725, 0.7882, 0.3725); // orange 5              #F8C95F
const vec3 c15 = vec3(0.9451, 0.9137, 0.7490); // orange 6 (lightest)   #F1E9BF
const vec3 c16 = vec3(0.0, 0.0, 0.0);          // interior black        #000000

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

vec2 fetchOrbit(int n) {
    // Convert integer iteration index to normalized texture coordinate.
    // +0.5 centers the sample on the texel, avoiding edge-interpolation issues
    // (though NEAREST filtering makes this less critical, still good practice).

    n = min(u_orbitLength, n-1);

    float u = (float(n) + 0.5) / float(u_orbitLength);
    return texture(u_orbit, vec2(u, 0.5)).xy;
}

void main (void) {
    // Camera position in double precision
    // dvec2 cam = dvec2(0.743643887037151lf, -0.131825904205330lf);
    // dvec2 cam = dvec2(1.8, 0);

    // zoom must be computed in float (exp2 has no double overload),
    // then promoted to double for the actual math
    double zoom = double(exp2(min(u_time - 3.0, 50.0)));

    dvec2 st = dvec2(gl_FragCoord.xy / u_resolution.xy) - dvec2(0.5lf, 0.5lf);
    st = st / zoom;

    double aspect = double(u_resolution.x / u_resolution.y);
    st.x *= aspect;

    st += cam;

    if (inPeriodBulb(st.x, st.y)) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); // same as interior color below
        return;
    }

    vec3 color = vec3(0.0);
    dvec2 z = dvec2(0.0lf, 0.0lf);
    int count = 0;

    for (int i = 0; i < REC_LIMIT; i++) {
        z = dvec2(z.x * z.x - z.y * z.y, 2.0lf * z.x * z.y) + st;
        count++;
        if (z.x * z.x + z.y * z.y > 4.0lf) break;
    }

    if (count == REC_LIMIT) {
        color = vec3(0.0, 0.0, 0.0);
    } else {
        // Drop back to float for the smoothing math — log/exp have no
        // double-precision overload under GL_ARB_gpu_shader_fp64
        float zx = float(z.x);
        float zy = float(z.y);

        float log_zn = log(zx * zx + zy * zy) / 2.0;
        float nu = log(log_zn / LN2) / LN2;
        float nCount = float(count) + 1.0 - nu;

        int i1 = int(mod(nCount, float(PALETTE_SIZE)));
        int i2 = int(mod(nCount + 1.0, float(PALETTE_SIZE)));
        color = mix(gCol(i1), gCol(i2), fract(nCount));
    }

    vec2 testOrbit = fetchOrbit(0);
    color += testOrbit.x * 0.0001;

    gl_FragColor = vec4(color, 1.0);
}