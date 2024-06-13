import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy
import random
import threading
import os
import time
from pythonosc import dispatcher, osc_server

# GLSL fragment shader source code
fragment_shader_code = """
#version 330 core

#define MAX_ANIMATIONS 30

uniform vec2 iResolution;
uniform float iTime;

// SHARED UNIFORMS
uniform int animationCount; // Number of active animations
uniform int animationTypes[MAX_ANIMATIONS]; // 0 for ring, 1 for line
uniform float animationStartTimes[MAX_ANIMATIONS];

// RING UNIFORMS
uniform vec3 ringColors[MAX_ANIMATIONS];
uniform vec2 ringPositions[MAX_ANIMATIONS];
uniform float ringSizes[MAX_ANIMATIONS];
uniform float ringOpacities[MAX_ANIMATIONS];
uniform float ringThicknesses[MAX_ANIMATIONS];
uniform float rotationSpeeds[MAX_ANIMATIONS];
uniform float armCounts[MAX_ANIMATIONS];

// LINE UNIFORMS
uniform vec3 lineColors[MAX_ANIMATIONS];
uniform float lineThicknesses[MAX_ANIMATIONS];
uniform float lineYPositions[MAX_ANIMATIONS];
uniform float lineOpacities[MAX_ANIMATIONS];

out vec4 fragColor;

void main()
{
    // Convert fragment coordinates to UV coordinates with (0, 0) in the center
    vec2 uv = (gl_FragCoord.xy / iResolution.xy) * 4.0 - 2.0;
    uv.y *= iResolution.y / iResolution.x; // Maintain aspect ratio
    float time = iTime;
    
    vec3 color = vec3(0.0);

    for (int i = 0; i < animationCount; i++) {
        
        // Ring Animation
        if (animationTypes[i] == 0) { 
            
            vec2 p = uv - ringPositions[i];
            float dist = length(p);
            float ringRadius = ringSizes[i];
            float ringThickness = ringThicknesses[i];
            float ringAlpha = step(ringRadius - ringThickness, dist) - step(ringRadius + ringThickness, dist);

            // pinwheel ring
            float angle = atan(p.y, p.x) + 0.2 * time * rotationSpeeds[i];
            float arm_count = armCounts[i];

            float pinwheelAlpha = 1;
            if (arm_count > 1) {
                pinwheelAlpha = step(0.5 + 0.5* sin(arm_count * angle + 0.2 * time * rotationSpeeds[i]), 0.5);
            }

            color += ringColors[i] * ringOpacities[i] * ringAlpha * pinwheelAlpha;
 
        // Line Animation
        } else if (animationTypes[i] == 1) { 
            float lineTime = time - animationStartTimes[i];
            float y = uv.y - lineYPositions[i];
            float thickness = lineThicknesses[i];
            float alpha = step(- thickness / 2.0, y) - step(thickness / 2.0, y); 
            color += lineColors[i] * lineOpacities[i] * alpha;
        }
    }
    
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
"""

# Pygame and OpenGL setup
def init_pygame_opengl():

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (3072, 0)  # Change (1920, 0) based on your setup

    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), DOUBLEBUF | OPENGL)
    glViewport(0, 0, 1920, 1080)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    return screen


def create_shader_program():
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


# OSC handler function
def trigger_ring_handler(unused_addr, *args):

    # for phone triggers
    if len(args) == 1:
        args = [random.choice([1,2]), random.choice([1,2]), random.choice([-1,1]), random.choice([-1,1])]
        """
        if args[0] == 0:
            args = [1,1,1,1]
        if args[0] == 1:
            args = [1,2,-1,1]
        if args[0] == 2:
            args = [2,1,1,-1]
        if args[0] == 3:
            args = [1,2,-1,-1]
        """

    # process measurement
    alice_basis = args[0]
    bob_basis = args[1]
    alice_measurement = args[2]
    bob_measurement = args[3]
    white = (1,1,1)
    red = (1,0.1,0.1)
    blue = (0.2,0.2,1)
    purple = (0.5, 0, 0.5)

    # Measurement animation for first section
    if animation_manager.current_section == 0:
        outer_color = red if alice_measurement == 1 else blue
        
        inner_color = white
        if bob_measurement == -1:
            if outer_color == red:
                inner_color = blue
            else:
                inner_color = red 

        animation_manager.trigger_animation("ring", {'color': outer_color,
                                                      'rotationSpeed' : 0.5,
                                                      'armCount': 10 * (alice_basis - 1),
                                                      'position': (0, 0.5)
                                                    })
        time.sleep(0.8)
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : -0.5,
                                                      'armCount' : 10 * (bob_basis - 1),
                                                      'position' : (0, 0.5)})

    if animation_manager.current_section == 2:
        outer_color = red if alice_measurement == 1 else blue
        
        inner_color = white
        if bob_measurement == -1:
            if outer_color == red:
                inner_color = blue
            else:
                inner_color = red 

        xPositions = numpy.linspace(-0.9, 0.9, 4)
        if random.choice([0, 1]) == 1:
            xPositions = numpy.flip(xPositions)

        initialSize = random.uniform(0.1, 0.28)
        growthSpeed = random.uniform(-0.03, -0.05) 
        animation_manager.trigger_animation("ring", {'color': outer_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (alice_basis - 1),
                                                      'position': [xPositions[0], 0.45],
                                                      'growthSpeed' : growthSpeed, 
                                                      'size' : initialSize, 
                                                    })
        time.sleep(random.uniform(0.2, 1))
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (alice_basis - 1),
                                                      'position' : [xPositions[1], 0.6],
                                                      'growthSpeed' : growthSpeed,
                                                      'size' : initialSize,
                                                      })

        time.sleep(random.uniform(0.2, 1))
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (bob_basis - 1),
                                                      'position' : [xPositions[2], 0.6],
                                                      'growthSpeed' : growthSpeed,
                                                      'size' : initialSize,
                                                      })
        
        time.sleep(random.uniform(0.2, 1))
        animation_manager.trigger_animation("ring", {'color': inner_color,
                                                      'rotationSpeed' : 0.5 * random.choice([0.5, 1, 2]) * random.choice([1, -1]),
                                                      'armCount': random.choice([10, 30]) * (bob_basis - 1),
                                                      'position' : [xPositions[3], 0.45],
                                                      'growthSpeed' : growthSpeed,
                                                      'size' : initialSize, 
                                                      })

    if animation_manager.current_section == 1:
    
        pol = (alice_measurement, bob_measurement)
        
        if pol == (1,1):
            color = white
        elif pol == (1,-1):
            color = red
        elif pol == (-1, 1):
            color = blue
        elif pol == (-1, -1):
            color = purple

        xPosShift = 1.5*(2*random.random() - 1)
        yPosShift = 0.5*(2*random.random() - 1)
        lifetime = random.uniform(0.8, 1.5)
        growthSpeed = random.uniform(0.25, 0.15)

        animation_manager.trigger_animation("ring", {'color': color,
                                                      'rotationSpeed' : alice_basis * 5,
                                                      'armCount': 20 * (bob_basis-1),
                                                      'position': (xPosShift, 0.5 + yPosShift),
                                                      'growthSpeed' : growthSpeed,
                                                      'lifetime' : lifetime,
                                                      'thickness' : 0.1
                                                    })

def trigger_setup_measurement_handler(unused_addr, *args):
    if animation_manager.current_section == 2:
        trigger_ring_handler(unused_addr, *args)

def trigger_line_handler(unused_addr, *args):
    parameters = {
                'color': (1.0,1.0,1.0),
                'yPosition': 1
                }
    # animation_manager.trigger_animation("line", parameters)

def change_section_handler(unused_addr, *args):
    animation_manager.current_section = int(args[0])
    print(f'Section changed to {animation_manager.current_section}')

def default_handler(addr, *args):
    print(f"Received OSC message: {addr} with arguments {args}")

def start_osc_server():
    disp = dispatcher.Dispatcher()
    disp.map("/bruQner/visuals/ring", trigger_ring_handler)
    disp.map("/bruQner/visuals/line", trigger_line_handler)
    disp.map("/bruQner/visuals/setup_measurement", trigger_setup_measurement_handler)
    disp.map("/bruQner/visuals/change_section", change_section_handler)
    disp.set_default_handler(default_handler)
    
    server = osc_server.ThreadingOSCUDPServer(("192.168.0.2", 7403), disp)
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

    animation_manager = AnimationManager()

    # Start OSC server in a separate thread
    osc_thread = threading.Thread(target=start_osc_server)
    osc_thread.daemon = True
    osc_thread.start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_r:
                    color = (random.random(), random.random(), random.random())
                    animation_manager.trigger_animation("ring", color)
                elif event.key == K_l:
                    color = (random.random(), random.random(), random.random())
                    animation_manager.trigger_animation("line", color)

        glClear(GL_COLOR_BUFFER_BIT)
        current_time = pygame.time.get_ticks() / 1000.0

        glUniform2f(iResolution, 1920, 1080)
        glUniform1f(iTime, current_time)
        glUniform2f(iMouse, *pygame.mouse.get_pos())

        animation_manager.update_animations()
        animation_manager.render_animations(shader_program)

        glDrawArrays(GL_QUADS, 0, 4)
        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()
