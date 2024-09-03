import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy
import threading
import os
import importlib
import random
from pythonosc import dispatcher, osc_server

from visuals_config import PERFORMANCE_MODULE, USE_OSC, RESOLUTION, MY_IP, MY_PORT, MAX_ANIMATIONS, ENABLE_RUNTIME_UPDATES

# Force the use of the NVIDIA GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["QT_OPENGL"] = "angle"  # Use ANGLE OpenGL for PyQt applications


# load the code for the current performance
def load_performance_module(module_name, reload=False):
    module = importlib.import_module(f'performance_modules.{module_name}')
    # if reload flag is used
    if reload: 
        module = importlib.reload(module)

    return module.run_performance


# detect changes in a file (for updating shader and performance module at runtime)
def watch_file(path, last_mtime):
    current_mtime = os.path.getmtime(path)
    if current_mtime != last_mtime:
        return True, current_mtime
    return False, last_mtime

# Pygame and OpenGL setup
def init_pygame_opengl():

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (int(1920/1.25), 0)  # Change (1920, 0) or (3072, 0) based on screen resolution

    pygame.init()


    # setup icon
    icon_path = os.path.join(os.path.dirname(__file__), 'visuals_icon.png')
    icon = pygame.image.load(icon_path)
    pygame.display.set_icon(icon)

    # create viewport
    screen = pygame.display.set_mode(RESOLUTION, DOUBLEBUF | OPENGL)
    #glViewport(0, 0, 1920, 1080)
    glViewport(0, 0, *RESOLUTION)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    return screen

def create_shader_program(shader_path):
    # import GLSL fragment shader source code
    with open(shader_path, 'r') as file:
        fragment_shader_code = file.read()

    # Add the MAX_ANIMATIONS value to the shader code
    fragment_shader_code = fragment_shader_code.replace('#define MAX_ANIMATIONS __MAX_ANIMATIONS__', f'#define MAX_ANIMATIONS {MAX_ANIMATIONS}')

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

def setup_shader_program(shader_path):
    try:
        new_shader_program = create_shader_program(shader_path)
        glUseProgram(new_shader_program)
        
        # Re-setup the attribute locations and uniforms
        position = glGetAttribLocation(new_shader_program, "position")
        glEnableVertexAttribArray(position)
        glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 0, None)

        iResolution = glGetUniformLocation(new_shader_program, "iResolution")
        iTime = glGetUniformLocation(new_shader_program, "iTime")
        iMouse = glGetUniformLocation(new_shader_program, "iMouse")
        
        print('------------\nShader reloaded successfully!\n------------')
        return new_shader_program, iResolution, iTime, iMouse
    except Exception as e:
        print(f"Error reloading shader: {e}")
        return None, None, None, None

# Animation classes
class Animation:

    allowed_parameters = ['color', 'opacity', 'position', 'lifetime', 'delay', 'dynamic']

    def __init__(self, start_time, parameters=None):
        self.start_time = start_time
        self.parameters = parameters
        self.complete = False

        if parameters is not None:
            self.validate_parameters(self.parameters)

        self.color = parameters.get('color', (1,1,1))
        self.opacity = parameters.get('opacity', 1.0)
        self.delay = parameters.get('delay', 0)
        self.position = parameters.get('position', (0,0))
        self.lifetime = parameters.get('lifetime', 8)
        
        self.dynamic_parameters = parameters.get('dynamic', {})

    def update(self, current_time):
        elapsed_time = current_time - self.start_time - self.delay

        # If delay not elapsed yet then elapsed time will be negative
        # Set opacity to 0 during this time. Afterwards get opacity 
        # set by user from parameters
        if elapsed_time < 0:
            self.opacity = 0
            return
        else:
            self.opacity = self.parameters.get('opacity', 1) 

        # Update dynamic parameters. If they are callable (i.e. lambda functions)
        # then put call them with elapsed_time parameter, else just set their value
        # Note: previously set non-dynamic parameters will be overwritten
        for key, value in self.dynamic_parameters.items():
            if callable(value):
                setattr(self, key, value(elapsed_time))
            else:
                setattr(self, key, value)
        
        # finish animation after lifetime. Triggers deletion
        if elapsed_time > self.lifetime:  
            self.complete = True

    # checks if the passed parameters are all valid
    def validate_parameters(self, parameters):
        # get allowed parameters from subclass and add base class allowed parameters
        allowed_parameters = getattr(self, 'allowed_parameters', []) + Animation.allowed_parameters

        for parameter, value in parameters.items():
            if parameter not in allowed_parameters:
                raise ValueError(f"Invalid parameter '{parameter}'. Allowed parameters are {allowed_parameters}")

            # if parameter is dynamic, validate all those nested parameters too
            if parameter == 'dynamic' and isinstance(value, dict):
                self.validate_parameters(value)

    def is_complete(self):
        return self.complete

    def render(self, shader_program, index):
        pass

class RingAnimation(Animation):

    allowed_parameters = ['size', 'thickness', 'rotation_speed', 'arm_count']

    def __init__(self, start_time, parameters):
        super().__init__(start_time, parameters)

        self.size = parameters.get('size', 1)
        self.thickness = parameters.get('thickness', 0.015)
        # TODO use absolute angle instead of built in rotation. Update with dynamic parameter
        self.rotation_speed = parameters.get('rotation_speed', 0)
        self.arm_count = parameters.get('arm_count', 0)


    def render(self, shader_program, index):
        # pass shared uniforms
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 0)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)
        # pass ring uniforms
        glUniform1f(glGetUniformLocation(shader_program, f"ringSizes[{index}]"), self.size)
        glUniform1f(glGetUniformLocation(shader_program, f"ringOpacities[{index}]"), self.opacity)
        glUniform1f(glGetUniformLocation(shader_program, f"ringThicknesses[{index}]"), self.thickness)
        glUniform1f(glGetUniformLocation(shader_program, f"rotationSpeeds[{index}]"), self.rotation_speed)
        glUniform1f(glGetUniformLocation(shader_program, f"armCounts[{index}]"), self.arm_count)
        glUniform2f(glGetUniformLocation(shader_program, f"ringPositions[{index}]"), *self.position)
        glUniform3f(glGetUniformLocation(shader_program, f"ringColors[{index}]"), *self.color)
        
class DotRingAnimation(Animation):

    allowed_parameters = ['dot_size', 'dot_thickness', 'dot_count', 'ring_radius', 'angle']

    def __init__(self, start_time, parameters):
        super().__init__(start_time, parameters)

        self.dot_count = parameters.get('dot_count', 10)
        self.ring_radius = parameters.get('ring_radius', 1.0)
        self.dot_size = parameters.get('dot_size', 0.03)
        self.dot_thickness = parameters.get('dot_thickness', 0.03)
        self.angle = parameters.get('angle', 0.0)


    def render(self, shader_program, index):
        # pass shared uniforms
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 2)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)
        # pass ring uniforms
        glUniform1f(glGetUniformLocation(shader_program, f"dotRingSizes[{index}]"), self.dot_size)
        glUniform1i(glGetUniformLocation(shader_program, f"dotRingDotCounts[{index}]"), self.dot_count)
        glUniform1f(glGetUniformLocation(shader_program, f"dotRingOpacities[{index}]"), self.opacity)
        glUniform1f(glGetUniformLocation(shader_program, f"dotRingThicknesses[{index}]"), self.dot_thickness)
        glUniform1f(glGetUniformLocation(shader_program, f"dotRingAngles[{index}]"), self.angle)
        glUniform1f(glGetUniformLocation(shader_program, f"dotRingRadii[{index}]"), self.ring_radius)
        glUniform2f(glGetUniformLocation(shader_program, f"dotRingPositions[{index}]"), *self.position)
        glUniform3f(glGetUniformLocation(shader_program, f"dotRingColors[{index}]"), *self.color)

class LineAnimation(Animation):

    allowed_parameters = ['thickness', 'length', 'angle']

    def __init__(self, start_time, parameters):
        super().__init__(start_time, parameters)
        self.thickness = parameters.get('thickness', 0.1)
        self.length = parameters.get('length', 0.1)
        self.angle = parameters.get('angle', 0.0)

    def render(self, shader_program, index):
        # pass shared uniformsr
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 1)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)
        # pass line uniforms
        glUniform1f(glGetUniformLocation(shader_program, f"lineThicknesses[{index}]"), self.thickness)
        glUniform1f(glGetUniformLocation(shader_program, f"lineOpacities[{index}]"), self.opacity)
        glUniform1f(glGetUniformLocation(shader_program, f"lineLengths[{index}]"), self.length)
        glUniform1f(glGetUniformLocation(shader_program, f"lineAngles[{index}]"), self.angle)
        glUniform2f(glGetUniformLocation(shader_program, f"linePositions[{index}]"), *self.position)
        glUniform3f(glGetUniformLocation(shader_program, f"lineColors[{index}]"), *self.color)

# Animation Manager
class AnimationManager:
    def __init__(self):
        self.animations = []
        self.current_section = 1 # indexing sections starting from 1
        self.total_trigger_count = 0 # counts total number of animations
        self.section_trigger_count = 0 # counts number of animations in current section
        self.is_quantum = 1 # 1 if setup is currenlty producing entangles particles, 0 if state is classical
        self.current_motif_set = 1 # each section has a variety of motif sets. The number differs but its at least 1

    def trigger_animation(self, animation_type, parameters=None):
        current_time = pygame.time.get_ticks() / 1000.0

        if animation_type == "ring":
            new_animation = RingAnimation(current_time, parameters)
        elif animation_type == "line":
            new_animation = LineAnimation(current_time, parameters)
        elif animation_type == "dot_ring":
            new_animation = DotRingAnimation(current_time, parameters)
        
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

    def clear_all_animations(self):
        for animation in self.animations[:]:
            self.animations.remove(animation)

    def count_trigger(self):
        self.section_trigger_count+= 1
        self.total_trigger_count += 1

    def update_section(self, new_section:int):
        self.current_section = new_section
        self.section_trigger_count = 0

    def set_quantum_classical(self, is_quantum:int):
        self.is_quantum = is_quantum
    
    def get_random_state(self, full_random_no_control=False, max_section=None):

        alice = random.choice([1,2,3,4])
        bob = random.choice([1,2,3,4])
        section = self.current_section
        qc_state = 'Q' if self.is_quantum == 1 else 'C' 
        motif_set = self.current_motif_set

        # produces fullly random state that does not let section and is_quantum be keyboard controlled (simulates real signal from clemens)
        if full_random_no_control:
            assert max_section != None 

            section = random.choice([i+1 for i in range(max_section)])
            qc_state = random.choice(['Q', 'C'])
        
        return [section, alice, bob, qc_state, motif_set]

# OSC handler functions
def change_section_handler(unused_addr, *args):
    animation_manager.update_section(int(args[0]))
    print(f'Section changed to {animation_manager.current_section}')

# args[0] == 0 if classical, args[0] == 1 if quantum
def quantum_classical_handler(unused_addr, *args):
    is_quantum = int(args[0])
    animation_manager.set_quantum_classical(is_quantum)
    print(f"Setup is {'QUANTUM' if is_quantum == 1 else 'CLASSICAL'}")

def clear_visuals_handler(unused_addr, *args):
    animation_manager.clear_all_animations()

def measurement_handler(unused_addr, *args):
    print(args)
    # check if a section change has occured (first argument)
    if args[0] != animation_manager.current_section:
        animation_manager.update_section(args[0])

    # check if a change from quantum to classical has occured
    if args[3] != ('Q' if animation_manager.is_quantum == 1 else 'C'):
        animation_manager.set_quantum_classical(1 if args[3] == 'Q' else 0)

    run_performance()('', [animation_manager], args)

# handle visual triggers from phone and other manual triggers
def manual_trigger_handler(addr, *args):
    print("Manual Trigger Received")
    run_performance()('', [animation_manager], animation_manager.get_random_state())

def default_handler(addr, *args):
    print(f"Received OSC message: {addr} with arguments {args}")

def start_osc_server(run_performance, animation_manager):
    disp = dispatcher.Dispatcher()
    disp.map("/bruQner/visuals/ring", run_performance, animation_manager)
    disp.map("/bruQner/visuals/manual", manual_trigger_handler)
    disp.map("/bruQner/graphics/", measurement_handler)
    disp.map("/bruQner/visuals/change_section", change_section_handler)
    disp.map("/bruQner/visuals/is_quantum", quantum_classical_handler)
    disp.map("/bruQner/visuals/clear", clear_visuals_handler)
    disp.set_default_handler(default_handler)
    
    server = osc_server.ThreadingOSCUDPServer((MY_IP, MY_PORT), disp)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()


# Main loop
def main():
    global animation_manager
    global run_performance

    # init pygame
    screen = init_pygame_opengl()

    # init shader -----------------------------
    shader_path = os.path.join(os.path.dirname(__file__), 'fragment_shader.glsl')
    shader_program = create_shader_program(shader_path)
    last_shader_mtime = os.path.getmtime(shader_path)
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
    # ----------------------------------------

    # setup perforamnce module runtime update monitoring variables
    performance_module_path = os.path.join(os.path.dirname(__file__), f'performance_modules\\{PERFORMANCE_MODULE}.py')
    last_performance_mtime  =os.path.getmtime(performance_module_path)

    # init the animation manager
    animation_manager = AnimationManager()

    # load perforamnce setup in config file.
    # first run the trigger counter and return the performance function
    def run_performance():
        animation_manager.count_trigger()
        return load_performance_module(PERFORMANCE_MODULE)
    
    # Start OSC server in a separate thread
    if USE_OSC: 
        osc_thread = threading.Thread(target=start_osc_server, args=(run_performance(), animation_manager))
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
                    random_state = animation_manager.get_random_state()
                    run_performance()('', [animation_manager], random_state)

                elif event.key == K_x:
                    clear_visuals_handler('')

                # toggle between quantum and non quantum system 
                elif event.key == K_q:
                    is_quantum = animation_manager.is_quantum
                    quantum_classical_handler('', 0 if is_quantum == 1 else 1)

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

        if ENABLE_RUNTIME_UPDATES:
            # check for updates in shader file
            shader_changed, last_shader_mtime = watch_file(shader_path, last_shader_mtime)
            if shader_changed:
                new_shader_program, new_iResolution, new_iTime, new_iMouse = setup_shader_program(shader_path)
                if new_shader_program is not None:
                    # If shader reloaded successfully, update the program and uniform locations
                    glDeleteProgram(shader_program)  # Delete the old program
                    shader_program = new_shader_program
                    iResolution = new_iResolution
                    iTime = new_iTime
                    iMouse = new_iMouse
                else:
                    print("Shader reload failed. Continuing with the previous version.")
                # Regardless of success or failure, don't skip the frame
                continue
            
            # check for updates in performance module
            performance_changed, last_performance_mtime = watch_file(performance_module_path, last_performance_mtime)
            if performance_changed:
                reloaded_performance = load_performance_module(PERFORMANCE_MODULE, reload=True)
                def run_performance():
                    animation_manager.count_trigger()
                    return reloaded_performance
                print('----------------------------\nPerformance module reloaded!\n---------------------------')

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
