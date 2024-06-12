import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy
import random

# GLSL fragment shader source code
fragment_shader_code = """
#version 330 core

#define MAX_ANIMATIONS 30

uniform vec2 iResolution;
uniform float iTime;
uniform int animationCount; // Number of active animations
uniform int animationTypes[MAX_ANIMATIONS]; // 0 for ring, 1 for line
uniform vec3 animationColors[MAX_ANIMATIONS];

uniform float animationStartTimes[MAX_ANIMATIONS];
uniform float ringSizes[MAX_ANIMATIONS];
uniform float ringOpacities[MAX_ANIMATIONS];
uniform float ringThicknesses[MAX_ANIMATIONS];

out vec4 fragColor;

void main()
{
    // Convert fragment coordinates to UV coordinates with (0, 0) in the center
    vec2 uv = (gl_FragCoord.xy / iResolution.xy) * 2.0 - 1.0;
    uv.y *= iResolution.y / iResolution.x; // Maintain aspect ratio
    vec2 center = vec2(0.0, 0.0);
    float time = iTime;
    
    vec3 color = vec3(0.0);

    for (int i = 0; i < animationCount; i++) {
        if (animationTypes[i] == 0) { // Ring Animation
            float dist = length(uv - center);
            float ringRadius = ringSizes[i];
            float ringThickness = ringThicknesses[i];
            float alpha = step(ringRadius - ringThickness, dist) - step(ringRadius + ringThickness, dist);
            color += animationColors[i] * ringOpacities[i] * alpha;

        } else if (animationTypes[i] == 1) { // Line Animation
            float lineTime = time - animationStartTimes[i];
            float y = uv.y;
            float alpha = step(0.0, y - lineTime * 0.2) - step(0.02, y - lineTime * 0.2); // Adjust thickness as needed
            color += animationColors[i] * alpha;
        }
    }
    
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
"""

# Pygame and OpenGL setup
def init_pygame_opengl():
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
    def __init__(self, start_time, color):
        self.start_time = start_time
        self.color = color
        self.complete = False

    def update(self, current_time):
        pass

    def is_complete(self):
        return self.complete

    def render(self, shader_program, index):
        pass

class RingAnimation(Animation):
    def __init__(self, start_time, color):
        super().__init__(start_time, color)
        self.size = 0.0
        self.opacity = 1.0
        self.thickness= 0.01

    def update(self, current_time):
        lifetime = 4 # time the ring is visible for
        growth_speed = 0.1

        elapsed_time = current_time - self.start_time
        self.size = elapsed_time * growth_speed  # Scale factor for ring growth
        self.opacity = (1 - (elapsed_time / lifetime)) ** 2 # sort of like exponential decay but slower

        if elapsed_time > lifetime:  # finish animation after lifetime
            self.complete = True

    def render(self, shader_program, index):
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 0)
        glUniform3f(glGetUniformLocation(shader_program, f"animationColors[{index}]"), *self.color)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)
        glUniform1f(glGetUniformLocation(shader_program, f"ringSizes[{index}]"), self.size)
        glUniform1f(glGetUniformLocation(shader_program, f"ringOpacities[{index}]"), self.opacity)
        glUniform1f(glGetUniformLocation(shader_program, f"ringThicknesses[{index}]"), self.thickness)
        

class LineAnimation(Animation):
    def update(self, current_time):
        # Example logic for completing an animation after a certain duration
        if current_time - self.start_time > 5:  # Line animation lasts 5 seconds
            self.complete = True

    def render(self, shader_program, index):
        glUniform1i(glGetUniformLocation(shader_program, f"animationTypes[{index}]"), 1)
        glUniform3f(glGetUniformLocation(shader_program, f"animationColors[{index}]"), *self.color)
        glUniform1f(glGetUniformLocation(shader_program, f"animationStartTimes[{index}]"), self.start_time)

# Animation Manager
class AnimationManager:
    def __init__(self):
        self.animations = []

    def trigger_animation(self, animation_type, color):
        current_time = pygame.time.get_ticks() / 1000.0
        if animation_type == "ring":
            new_animation = RingAnimation(current_time, color)
        elif animation_type == "line":
            new_animation = LineAnimation(current_time, color)
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

# Main loop
def main():
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
