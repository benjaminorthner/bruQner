import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy
import time

speed = 1
running_animations = []

class RingAnimation:
    def __init__(self, color):
        self.start_time = time.time()
        self.color = color
        self.radius = 0
        self.thickness = 0.5
        self.opacity = 1

    def update(self, current_time):
        elapsed_time = current_time - self.start_time
        self.radius = elapsed_time * speed  # speed is a predefined constant

    def is_complete(self):
        # destroy animation once circle becomes invisible
        return self.opacity < 0  

def trigger_animation(measurement):
    color = measurement[0]

    new_animation = RingAnimation(color)
    running_animations.append(new_animation)

# GLSL fragment shader source code
fragment_shader_code = """
#version 330 core

uniform vec2 iResolution;
uniform float iTime;

out vec4 fragColor;

void main()
{
    vec2 uv = 1.5*(2.0*gl_FragCoord.xy - iResolution.xy) / iResolution.y;
    vec3 col = 0.5 + 0.5*cos(iTime + uv.xyx + vec3(0, 2, 4));
    fragColor = vec4(col, 1.0);
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

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        glClear(GL_COLOR_BUFFER_BIT)
        current_time = (pygame.time.get_ticks() - start_time) / 1000.0

        glUniform2f(iResolution, 1920, 1080)
        glUniform1f(iTime, current_time)

        glDrawArrays(GL_QUADS, 0, 4)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

