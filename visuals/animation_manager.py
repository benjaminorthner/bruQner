import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy
import threading
import os
import importlib
from pythonosc import dispatcher, osc_server

from config import PERFORMANCE_MODULE, USE_OSC, RESOLUTION, MY_IP, MY_PORT

# Force the use of the NVIDIA GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["QT_OPENGL"] = "angle"  # Use ANGLE OpenGL for PyQt applications


# load the code for the current performance
def load_performance_module(module_name):
    module = importlib.import_module(f'performance_modules.{module_name}')
    return module.run_performance

# Pygame and OpenGL setup
def init_pygame_opengl():

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 0)  # Change (1920, 0) or (3072, 0) based on screen resolution

    pygame.init()
    screen = pygame.display.set_mode(RESOLUTION, DOUBLEBUF | OPENGL)
    glViewport(0, 0, 1920, 1080)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    return screen

def create_shader_program():
    # import GLSL fragment shader source code
    with open(os.path.join(os.path.dirname(__file__), 'fragment_shader.glsl'), 'r') as file:
        fragment_shader_code = file.read()

    # define vertex shader code
    vertex_shader_code = """
    #version 330 core
    layout(location = 0) in vec3 position;
    void main()
    {
        gl_Position = vec4(position, 1.0);
    }
    """
    vertex_shader = compileShader(vertex_shader_code, GL_VERTEX_SHADER)
    fragment_shader = compileShader(fragment_shader_code, GL_FRAGMENT_SHADER)
    shader_program = compileProgram(vertex_shader, fragment_shader)
    return shader_program

# Animation classes
class Animation:
    def __init__(self, start_time, parameters=None):
        self.start_time = start_time
        self.parameters = parameters
        self.complete = False

    def update(self, current_time):
        pass

    def is_complete(self):
        return self.complete

    def render(self, shader_program, index):
        pass

class RingAnimation(Animation):
    def __init__(self, start_time, parameters):
        super().__init__(start_time, parameters)
        self.initialSize = parameters.get('size', 0)
        self.size = self.initialSize
        self.opacity = 1.0
        self.initialThickness = parameters.get('thickness', 0.015)
        self.thickness = self.initialThickness
        self.color = parameters['color']
        self.rotationSpeed = parameters['rotationSpeed']
        self.armCount = parameters['armCount']
        self.position = parameters['position']
        self.homePosition = self.position

        self.growthSpeed = parameters.get('growthSpeed', 0.06)
        self.lifetime = parameters.get('lifetime', 8)

    def update(self, current_time):

        elapsed_time = current_time - self.start_time
        self.size = self.initialSize + elapsed_time * self.growthSpeed  # Scale factor for ring growth
        self.opacity = 1 #(1 - (elapsed_time / lifetime)) ** 0.5 # 
        self.thickness = self.initialThickness * (1 - elapsed_time / self.lifetime) ** 0.5

        if elapsed_time > self.lifetime:  # finish animation after lifetime
            self.complete = True

    def render(self, shader_program, index):
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 0)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)
        glUniform1f(glGetUniformLocation(shader_program, f"ringSizes[{index}]"), self.size)
        glUniform1f(glGetUniformLocation(shader_program, f"ringOpacities[{index}]"), self.opacity)
        glUniform1f(glGetUniformLocation(shader_program, f"ringThicknesses[{index}]"), self.thickness)
        glUniform1f(glGetUniformLocation(shader_program, f"rotationSpeeds[{index}]"), self.rotationSpeed)
        glUniform1f(glGetUniformLocation(shader_program, f"armCounts[{index}]"), self.armCount)
        glUniform3f(glGetUniformLocation(shader_program, f"ringColors[{index}]"), *self.color)
        glUniform2f(glGetUniformLocation(shader_program, f"ringPositions[{index}]"), *self.position)
        
class LineAnimation(Animation):
    def __init__(self, start_time, parameters):
        super().__init__(start_time, parameters)
        self.thickness= 0.01
        self.opacity = 1
        self.yPosition = parameters['yPosition']
        self.color = parameters['color']

    def update(self, current_time):
        # Example logic for completing an animation after a certain duration
        if current_time - self.start_time > 5:  # Line animation lasts 5 seconds
            self.complete = True

    def render(self, shader_program, index):
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 1)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)
        glUniform1f(glGetUniformLocation(shader_program, f"lineThicknesses[{index}]"), self.thickness)
        glUniform1f(glGetUniformLocation(shader_program, f"lineYPositions[{index}]"), self.yPosition)
        glUniform1f(glGetUniformLocation(shader_program, f"lineOpacities[{index}]"), self.opacity)
        glUniform3f(glGetUniformLocation(shader_program, f"lineColors[{index}]"), *self.color)

# Animation Manager
class AnimationManager:
    def __init__(self):
        self.animations = []
        self.current_section = 0

    def trigger_animation(self, animation_type, parameters=None):
        current_time = pygame.time.get_ticks() / 1000.0

        if 'delay' in parameters:
            current_time += parameters['delay']
        if animation_type == "ring":
            new_animation = RingAnimation(current_time, parameters)
        elif animation_type == "line":
            new_animation = LineAnimation(current_time, parameters)
        self.animations.append(new_animation)

    def update_animations(self):
        current_time = pygame.time.get_ticks() / 1000.0
        for animation in self.animations[:]:
            animation.update(current_time)
            if animation.is_complete():
                self.animations.remove(animation)

    def render_animations(self, shader_program):
        glUniform1i(glGetUniformLocation(shader_program, "animationCount"), len(self.animations))
        for i, animation in enumerate(self.animations):
            animation.render(shader_program, i)


# OSC handler functions
def change_section_handler(unused_addr, *args):
    animation_manager.current_section = int(args[0])
    print(f'Section changed to {animation_manager.current_section}')

def default_handler(addr, *args):
    print(f"Received OSC message: {addr} with arguments {args}")

def start_osc_server(run_performance, animation_manager):
    disp = dispatcher.Dispatcher()
    disp.map("/bruQner/visuals/ring", run_performance, animation_manager)
    disp.map("/bruQner/visuals/change_section", change_section_handler)
    disp.set_default_handler(default_handler)
    
    server = osc_server.ThreadingOSCUDPServer((MY_IP, MY_PORT), disp)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()


# Main loop
def main():
    global animation_manager
    screen = init_pygame_opengl()
    shader_program = create_shader_program()
    glUseProgram(shader_program)

    # Define a full-screen quad
    quad_vertices = [-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, 1, 0]
    quad_vertices = numpy.array(quad_vertices, dtype=numpy.float32)

    VBO = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)

    position = glGetAttribLocation(shader_program, "position")
    glEnableVertexAttribArray(position)
    glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 0, None)

    iResolution = glGetUniformLocation(shader_program, "iResolution")
    iTime = glGetUniformLocation(shader_program, "iTime")
    iMouse = glGetUniformLocation(shader_program, "iMouse")

    # init the animation manager
    animation_manager = AnimationManager()

    # load perforamnce setup in config file
    run_performance = load_performance_module(PERFORMANCE_MODULE)
    
    # Start OSC server in a separate thread
    if USE_OSC: 
        osc_thread = threading.Thread(target=start_osc_server, args=(run_performance, animation_manager))
        osc_thread.daemon = True
        osc_thread.start()

    clock = pygame.time.Clock()  # Create a Clock object to manage the frame rate
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:

                # manually trigger random measurement with 'r' key
                if event.key == K_r:
                    run_performance(animation_manager, 0)

                # manually change section with number keys
                elif event.key in [eval(f'K_{i}') for i in range(10)]:
                    section = event.key - 48
                    change_section_handler('', section)

                # quit if escape key is pressed 
                elif event.key == K_ESCAPE:
                    running = False

                # catch ctrl + c and exit
                mods = pygame.key.get_mods()
                if event.key == K_c and mods & KMOD_CTRL:
                    running = False

        glClear(GL_COLOR_BUFFER_BIT)
        current_time = pygame.time.get_ticks() / 1000.0

        glUniform2f(iResolution, RESOLUTION[0], RESOLUTION[1])
        glUniform1f(iTime, current_time)
        glUniform2f(iMouse, *pygame.mouse.get_pos())

        animation_manager.update_animations()
        animation_manager.render_animations(shader_program)

        glDrawArrays(GL_QUADS, 0, 4)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
