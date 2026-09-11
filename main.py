import moderngl_window as mglw
import moderngl
import numpy as np
import orbit
import os
from PIL import Image
class Window(mglw.WindowConfig):
    gl_version = (3, 3)          # or (4, 0) if you need fp64 extensions
    window_size = (1920, 1080)
    aspect_ratio = None          # None = don't letterbox/enforce aspect
    resource_dir = "."           # base path for load_program etc.

    time = 0
    offTime = 0
    renderNow = True
    pause = False
    pertube = True

    recLimit = 5000

    recording = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prog = self.ctx.program(
        vertex_shader='''
            #version 330

            in vec2 in_pos;

            void main() {
                gl_Position = vec4(in_pos, 0.0, 1.0);
            }
        ''',
        fragment_shader=open("shaders/main.frag").read()
        );

        # 4 verts covering NDC space, drawn as a triangle strip
        vertices = np.array([
            -1.0, -1.0,
            1.0, -1.0,
            -1.0,  1.0,
            1.0,  1.0,
        ], dtype='f4')

        self.quad_vbo = self.ctx.buffer(vertices.tobytes())
        self.quad_vao = self.ctx.vertex_array(
            self.prog, [(self.quad_vbo, '2f', 'in_pos')]
        )

        # self.cam = ("-1.85", "0")
        # self.cam = ("0", "0")
        # self.cam = ("-0.743643887037151", "-0.131825904205330")
        # self.cam = ("-1.2838811641996977", "-0.42738475450183155")
        self.cam = ("-1.522694224260380500000056614138599655817571524", "0.000000164476499567286829777023116989463437026398358")
        self.cam_float = tuple(map(float, self.cam))
        refOrbit = orbit.computeOrbit(*self.cam, self.recLimit, 256)
        self.prog['cam'] = self.cam_float
        
        print(refOrbit)

        self.orbit_len = refOrbit.shape[0]

        self.orbit_tex = self.genTex(refOrbit)
        self.orbit_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.orbit_tex.repeat_x = False
        self.orbit_tex.repeat_y = False

        # recording
        self.output_dir = "frames"
        os.makedirs(self.output_dir, exist_ok=True)

        self.start_seconds = 0

        self.render_fps = 60
        self.duration_seconds = 148.39
        self.frame_index = 6080
        self.total_frames = self.render_fps * self.duration_seconds

        self.wnd.fullscreen = True

    def genTex(self, refOrbit):
        hi = refOrbit.astype(np.float32)
        lo = (refOrbit - hi.astype(np.float64)).astype(np.float32)

        packed = np.zeros((refOrbit.shape[0], 4), dtype=np.float32)
        packed[:, 0] = hi[:, 0]
        packed[:, 1] = hi[:, 1]
        packed[:, 2] = lo[:, 0]
        packed[:, 3] = lo[:, 1]

        return self.ctx.texture(
            size=(refOrbit.shape[0], 1),
            components=4,           # was 2
            data=packed.tobytes(),
            dtype='f4'
        )

        # one-time setup goes here: load shaders, create buffers/textures

    def renderSet(self, t):
        self.prog['u_resolution'].value = self.wnd.buffer_size
        self.prog['u_time'].value = t
        self.prog['pertube'].value = self.pertube
        self.prog['u_orbitLength'] = self.orbit_len
        self.orbit_tex.use(location=0)
        self.prog['u_orbit'] = 0
        self.prog['u_recLimit'].value = self.recLimit

        self.quad_vao.render(moderngl.TRIANGLE_STRIP)

    def recenter_camera(self, x, y):
        self.cam = (repr(x), repr(y))
        self.cam_float = (x, y)

        self.prog['cam'] = self.cam_float

        refOrbit = orbit.computeOrbit(*self.cam, 1000, 256)
        self.orbit_len = refOrbit.shape[0]

        self.orbit_tex.release()
        self.orbit_tex = self.genTex(refOrbit)
        self.orbit_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.orbit_tex.repeat_x = False
        self.orbit_tex.repeat_y = False

        print(f"recentered to {x}, {y} — new orbit length: {self.orbit_len}")
        
    
    def saveToDisk(self):
        w, h =self.ctx.viewport[2], self.ctx.viewport[3]
        data = self.ctx.screen.read(components=3)

        print(len(data), w, h)
        img = Image.frombytes('RGB', (w, h), data)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)  # GL's origin is bottom-left, images expect top-left
        img.save(f"{self.output_dir}/frame_{self.frame_index:05d}.png")

    def on_render(self, time: float, frametime: float):
        if not self.recording:
            if self.pause: self.offTime = time - (self.time - self.offTime)
            self.time = time
            self.renderSet(self.time-self.offTime)
            print(2**(self.time - self.offTime - 3.0 + 120))

        else:
            if time < 1: return
            if self.frame_index < self.total_frames:
                self.renderSet(self.frame_index / self.render_fps)
                self.saveToDisk()
                self.frame_index+=1
                if self.frame_index % 10 == 0: print(f"{self.frame_index / self.total_frames*100}%")
            else:
                self.wnd.close()

    



    
    def on_key_event(self, key, action, modifiers):
    # Key presses
        if action == self.wnd.keys.ACTION_PRESS:
            if key == self.wnd.keys.SPACE:
                print("SPACE key was pressed")
                self.pause = not self.pause

            if key == self.wnd.keys.ENTER:
                self.offTime = self.time
            # Using modifiers (shift and ctrl)

            if key == self.wnd.keys.G:
                self.pertube = not self.pertube

            if key == self.wnd.keys.Z and modifiers.shift:
                print("Shift + Z was pressed")

            if key == self.wnd.keys.Z and modifiers.ctrl:
                print("ctrl + Z was pressed")

        # Key releases
        elif action == self.wnd.keys.ACTION_RELEASE:
            if key == self.wnd.keys.SPACE:
                print("SPACE key was released")

    def on_mouse_press_event(self, x, y, button):
        if not self.pause:
            return 
        
        w, h = self.wnd.buffer_size


        y = h - y

        nx = (x / w) - 0.5
        ny = (y / h) - 0.5

        aspect = w / h
        nx *= aspect

        t = self.time - self.offTime
        log_zoom_exponent = t - 3.0
        zoom = 1.0 / (2.0 ** log_zoom_exponent)

        dx = nx * zoom
        dy = ny * zoom

        new_cam_x = self.cam_float[0] + dx
        new_cam_y = self.cam_float[1] + dy

        self.recenter_camera(new_cam_x, new_cam_y)

if __name__ == "__main__":
    mglw.run_window_config(Window)