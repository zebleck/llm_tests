import pygame
from pygame.locals import *
import numpy as np
import sys
import time
import moderngl
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random

# Constants
WIDTH, HEIGHT = 1200, 800
FPS = 60
TRAIL_LENGTH = 1000
BG_COLOR = (0, 0, 0, 1)  # Black background

# Initialize pygame
pygame.init()
pygame.display.set_caption("Figure-8 Three-Body Problem Simulation")
display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
clock = pygame.time.Clock()

# Load shaders
def load_shader(shader_file):
    with open(shader_file, 'r') as file:
        return file.read()

# Vertex Shader for particles and trails
vertex_shader = """
#version 330

uniform mat4 projection;
uniform mat4 view;
attribute vec2 in_vert;
attribute vec4 in_color;
varying vec4 color;

void main() {
    gl_Position = projection * view * vec4(in_vert, 0.0, 1.0);
    color = in_color;
}
"""

# Fragment Shader for particles
particle_fragment_shader = """
#version 330

varying vec4 color;
void main() {
    float r = length(gl_PointCoord - vec2(0.5));
    if (r > 0.5) {
        discard;
    }
    
    float intensity = 1.0 - 2.0 * r;
    gl_FragColor = vec4(color.rgb, color.a * pow(intensity, 2.0));
}
"""

# Fragment Shader for trails
trail_fragment_shader = """
#version 330

varying vec4 color;
void main() {
    gl_FragColor = color;
}
"""

# Physics class for Three-Body Problem
class ThreeBodySystem:
    def __init__(self):
        # Initial conditions for Figure-8 solution
        # These are specific initial conditions for the Figure-8 solution
        self.masses = np.array([1.0, 1.0, 1.0])  # Equal masses
        
        # Initial positions (x, y) for each body
        self.positions = np.array([
            [-0.97000436, 0.24308753],
            [0.0, 0.0],
            [0.97000436, -0.24308753]
        ])
        
        # Initial velocities (vx, vy) for each body
        self.velocities = np.array([
            [0.46620368, 0.43236573],
            [-0.93240737, -0.86473146],
            [0.46620368, 0.43236573]
        ]) * 0.5  # Scale velocities for better visualization
        
        # For storing trajectories
        self.trails = [[] for _ in range(3)]
        
        # Colors for the bodies
        self.colors = [
            (0.0, 0.7, 1.0, 1.0),  # Blue
            (1.0, 0.3, 0.0, 1.0),  # Orange
            (0.2, 1.0, 0.2, 1.0)   # Green
        ]
        
        # Gravitational constant
        self.G = 1.0
        
        # Softening parameter to prevent singularities
        self.softening = 0.01

    def acceleration(self, positions):
        # Calculate accelerations for all bodies using soft-body gravity
        acc = np.zeros_like(positions)
        for i in range(3):
            for j in range(3):
                if i != j:
                    r = positions[j] - positions[i]
                    dist = np.sqrt(np.sum(r**2) + self.softening**2)
                    acc[i] += self.G * self.masses[j] * r / dist**3
        return acc

    def update(self, dt):
        # RK4 integrator for accurate physics simulation
        k1_v = self.acceleration(self.positions)
        k1_r = self.velocities
        
        k2_v = self.acceleration(self.positions + 0.5 * dt * k1_r)
        k2_r = self.velocities + 0.5 * dt * k1_v
        
        k3_v = self.acceleration(self.positions + 0.5 * dt * k2_r)
        k3_r = self.velocities + 0.5 * dt * k2_v
        
        k4_v = self.acceleration(self.positions + dt * k3_r)
        k4_r = self.velocities + dt * k3_v
        
        # Update velocities and positions
        self.velocities += dt * (k1_v + 2 * k2_v + 2 * k3_v + k4_v) / 6
        self.positions += dt * (k1_r + 2 * k2_r + 2 * k3_r + k4_r) / 6
        
        # Update trails
        for i in range(3):
            self.trails[i].append(self.positions[i].copy())
            if len(self.trails[i]) > TRAIL_LENGTH:
                self.trails[i].pop(0)

# Renderer using ModernGL for efficient shader-based rendering
class Renderer:
    def __init__(self, system):
        self.system = system
        self.zoom = 1.0
        self.pan_x, self.pan_y = 0.0, 0.0
        
        # Setup ModernGL context
        self.ctx = moderngl.create_context()
        
        # Compile shaders
        self.particle_program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=particle_fragment_shader
        )
        
        self.trail_program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=trail_fragment_shader
        )
        
        # Create projection matrix
        self.projection = np.identity(4, dtype=np.float32)
        self.update_projection()
        
        # Create view matrix
        self.view = np.identity(4, dtype=np.float32)
        self.update_view()
        
        # Set projection and view uniforms
        self.particle_program['projection'].write(self.projection)
        self.particle_program['view'].write(self.view)
        self.trail_program['projection'].write(self.projection)
        self.trail_program['view'].write(self.view)
        
        # Setup blending for glow effects
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE
        
        # Create vertex buffers for particles and trails
        self.setup_buffers()

    def setup_buffers(self):
        # Particle VBO setup
        particle_vertices = np.array([
            self.system.positions[0][0], self.system.positions[0][1],
            self.system.positions[1][0], self.system.positions[1][1],
            self.system.positions[2][0], self.system.positions[2][1],
        ], dtype=np.float32)
        
        particle_colors = np.array([
            *self.system.colors[0],
            *self.system.colors[1],
            *self.system.colors[2],
        ], dtype=np.float32)
        
        self.particle_vbo = self.ctx.buffer(particle_vertices)
        self.particle_color_vbo = self.ctx.buffer(particle_colors)
        
        self.particle_vao = self.ctx.vertex_array(
            self.particle_program,
            [
                (self.particle_vbo, '2f', 'in_vert'),
                (self.particle_color_vbo, '4f', 'in_color'),
            ]
        )
        
        # Trail VBOs will be updated dynamically
        self.trail_vbos = []
        self.trail_color_vbos = []
        self.trail_vaos = []
        
        for i in range(3):
            trail_vbo = self.ctx.buffer(reserve=TRAIL_LENGTH * 2 * 4)
            trail_color_vbo = self.ctx.buffer(reserve=TRAIL_LENGTH * 4 * 4)
            
            trail_vao = self.ctx.vertex_array(
                self.trail_program,
                [
                    (trail_vbo, '2f', 'in_vert'),
                    (trail_color_vbo, '4f', 'in_color'),
                ]
            )
            
            self.trail_vbos.append(trail_vbo)
            self.trail_color_vbos.append(trail_color_vbo)
            self.trail_vaos.append(trail_vao)
    
    def update_projection(self):
        aspect = WIDTH / HEIGHT
        self.projection = np.identity(4, dtype=np.float32)
        self.projection[0, 0] = 1.0 / (aspect * self.zoom)
        self.projection[1, 1] = 1.0 / self.zoom
        
        if self.particle_program:
            self.particle_program['projection'].write(self.projection)
        if self.trail_program:
            self.trail_program['projection'].write(self.projection)
    
    def update_view(self):
        self.view = np.identity(4, dtype=np.float32)
        self.view[0, 3] = self.pan_x
        self.view[1, 3] = self.pan_y
        
        if self.particle_program:
            self.particle_program['view'].write(self.view)
        if self.trail_program:
            self.trail_program['view'].write(self.view)
    
    def update_buffers(self):
        # Update particle positions
        particle_vertices = np.array([
            self.system.positions[0][0], self.system.positions[0][1],
            self.system.positions[1][0], self.system.positions[1][1],
            self.system.positions[2][0], self.system.positions[2][1],
        ], dtype=np.float32)
        
        self.particle_vbo.write(particle_vertices)
        
        # Update trail data
        for i in range(3):
            if len(self.system.trails[i]) > 1:
                trail_vertices = np.zeros(len(self.system.trails[i]) * 2, dtype=np.float32)
                trail_colors = np.zeros(len(self.system.trails[i]) * 4, dtype=np.float32)
                
                for j, pos in enumerate(self.system.trails[i]):
                    trail_vertices[j*2] = pos[0]
                    trail_vertices[j*2+1] = pos[1]
                    
                    # Fade trail alpha based on position in trail
                    alpha = 0.8 * (j / len(self.system.trails[i]))
                    trail_colors[j*4] = self.system.colors[i][0]
                    trail_colors[j*4+1] = self.system.colors[i][1]
                    trail_colors[j*4+2] = self.system.colors[i][2]
                    trail_colors[j*4+3] = alpha
                
                self.trail_vbos[i].write(trail_vertices)
                self.trail_color_vbos[i].write(trail_colors)
    
    def render(self):
        # Clear the screen
        self.ctx.clear(*BG_COLOR)
        
        # Draw trails
        for i in range(3):
            if len(self.system.trails[i]) > 1:
                self.trail_vaos[i].render(moderngl.LINE_STRIP, vertices=len(self.system.trails[i]))
        
        # Draw particles (bodies)
        glPointSize(15.0)  # Set particle size
        self.particle_vao.render(moderngl.POINTS)
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            # Zoom controls
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.zoom *= 1.1
                self.update_projection()
            elif event.key == pygame.K_MINUS:
                self.zoom /= 1.1
                self.update_projection()
            
            # Pan controls
            elif event.key == pygame.K_LEFT:
                self.pan_x += 0.1 * self.zoom
                self.update_view()
            elif event.key == pygame.K_RIGHT:
                self.pan_x -= 0.1 * self.zoom
                self.update_view()
            elif event.key == pygame.K_UP:
                self.pan_y -= 0.1 * self.zoom
                self.update_view()
            elif event.key == pygame.K_DOWN:
                self.pan_y += 0.1 * self.zoom
                self.update_view()
            
            # Reset view
            elif event.key == pygame.K_r:
                self.zoom = 1.0
                self.pan_x, self.pan_y = 0.0, 0.0
                self.update_projection()
                self.update_view()
        
        # Mouse wheel for zooming
        elif event.type == pygame.MOUSEWHEEL:
            zoom_factor = 1.1 if event.y > 0 else 0.9
            self.zoom *= zoom_factor
            self.update_projection()

# Main function
def main():
    # Create shader files
    with open('vertex_shader.glsl', 'w') as f:
        f.write(vertex_shader)
    
    with open('fragment_shader.glsl', 'w') as f:
        f.write(particle_fragment_shader)
    
    # Create physics system and renderer
    system = ThreeBodySystem()
    renderer = Renderer(system)
    
    # Simulation timestep
    dt = 0.01
    
    # Main game loop
    running = True
    
    # Display controls
    print("\nControls:")
    print("  +/- : Zoom in/out")
    print("  Arrow keys : Pan view")
    print("  R : Reset view")
    print("  Mouse wheel : Zoom in/out")
    print("  ESC : Quit\n")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # Handle input events for the renderer
            renderer.handle_input(event)
        
        # Update physics system
        system.update(dt)
        
        # Update renderer buffers
        renderer.update_buffers()
        
        # Render the scene
        renderer.render()
        
        # Swap the buffers to display what we just rendered
        pygame.display.flip()
        
        # Maintain frame rate
        clock.tick(FPS)
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()