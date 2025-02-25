from manim import *
import numpy as np

class SpacetimeCurvature(ThreeDScene):
    def construct(self):
        # Set the camera orientation for better 3D viewing
        self.set_camera_orientation(phi=75 * DEGREES, theta=-30 * DEGREES)
        self.camera.frame_center = np.array([0, 0, -1])
        
        # Create a title and equations
        title = Text("Spacetime Curvature in General Relativity", font_size=36)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)
        
        # Einstein's field equation
        einstein_eq = MathTex(
            r"G_{\mu\nu} = \frac{8\pi G}{c^4}T_{\mu\nu}",
            font_size=32
        )
        einstein_eq.next_to(title, DOWN)
        self.add_fixed_in_frame_mobjects(einstein_eq)
        
        # Parameters for the grid
        grid_size = 8
        grid_density = 20
        
        # Create a flat spacetime grid initially
        # Use Surface instead of ParametricSurface for compatibility
        flat_grid = Surface(
            lambda u, v: np.array([u, v, 0]),
            u_range=[-grid_size/2, grid_size/2],
            v_range=[-grid_size/2, grid_size/2],
            resolution=(grid_density, grid_density)
        )
        flat_grid.set_fill_by_checkerboard(BLUE_D, BLUE_E, opacity=0.5)
        
        # Function to create a curved spacetime grid
        def curved_spacetime(u, v, mass_factor):
            # Distance from the center
            r = np.sqrt(u**2 + v**2)
            # Avoid division by zero at the center
            r = max(r, 0.1)
            # Curvature function (inverse square law-like)
            z = -mass_factor / r
            return np.array([u, v, z])
        
        # Create the massive object (star/planet)
        massive_object = Sphere(radius=0.5)
        massive_object.set_color(YELLOW)
        massive_object.set_opacity(1)
        massive_object.move_to(np.array([0, 0, 0]))
        
        # Initial setup: flat grid and labels
        self.play(
            Create(flat_grid, run_time=2),
            FadeIn(massive_object, run_time=1)
        )
        
        # Labels
        spacetime_label = Text("Flat Spacetime", font_size=24)
        spacetime_label.move_to(np.array([-3, 3, 0]))
        self.add_fixed_in_frame_mobjects(spacetime_label)
        
        mass_label = Text("Mass", font_size=24)
        mass_label_arrow = Arrow(start=np.array([2, 2, 0]), end=np.array([0.5, 0.5, 0]), buff=0.2)
        mass_label.next_to(mass_label_arrow.start, RIGHT)
        
        self.add_fixed_in_frame_mobjects(mass_label)
        self.play(Create(mass_label_arrow))
        
        self.wait(1)
        
        # Animate the transition to curved spacetime
        curved_grids = []
        mass_factors = np.linspace(0, 3, 10)  # Reduced number of steps for quicker rendering
        
        for i, mass_factor in enumerate(mass_factors):
            curved_grid = Surface(
                lambda u, v: curved_spacetime(u, v, mass_factor),
                u_range=[-grid_size/2, grid_size/2],
                v_range=[-grid_size/2, grid_size/2],
                resolution=(grid_density, grid_density)
            )
            curved_grid.set_fill_by_checkerboard(BLUE_D, BLUE_E, opacity=0.5)
            curved_grids.append(curved_grid)
        
        # Update spacetime label
        new_spacetime_label = Text("Curved Spacetime", font_size=24)
        new_spacetime_label.move_to(spacetime_label.get_center())
        
        # Animate the curvature transition
        self.play(
            Transform(flat_grid, curved_grids[0]),
            Transform(spacetime_label, new_spacetime_label),
            run_time=1
        )
        
        for i in range(1, len(curved_grids)):
            self.play(
                Transform(flat_grid, curved_grids[i]),
                massive_object.animate.move_to(np.array([0, 0, mass_factors[i] / -0.1])),
                run_time=0.3,
                rate_func=linear
            )
        
        self.wait(1)
        
        # Move the camera to show the curvature from different angles
        self.move_camera(phi=60 * DEGREES, theta=30 * DEGREES, run_time=3)
        self.wait(1)
        self.move_camera(phi=75 * DEGREES, theta=90 * DEGREES, run_time=3)
        self.wait(1)
        
        # Add geodesic particles
        geodesic_label = Text("Geodesics", font_size=24)
        geodesic_label.move_to(np.array([3, 3, 0]))
        self.add_fixed_in_frame_mobjects(geodesic_label)
        
        # Create test particles (small spheres)
        particles = []
        particle_paths = []
        
        # Create particles at different positions
        num_particles = 5
        for i in range(num_particles):
            angle = i * 2 * PI / num_particles
            radius = 3
            
            # Starting position
            start_pos = np.array([radius * np.cos(angle), radius * np.sin(angle), 
                                 curved_spacetime(radius * np.cos(angle), radius * np.sin(angle), mass_factors[-1])[2]])
            
            # Create particle
            particle = Sphere(radius=0.1)
            particle.set_color(RED)
            particle.set_opacity(1)
            particle.move_to(start_pos)
            particles.append(particle)
            
            # Create path for the particle
            path_points = []
            steps = 50  # Reduced number of steps
            for t in range(steps + 1):
                # Spiral inward
                curr_radius = radius * (1 - t/steps * 0.5)  # Reduce radius gradually
                curr_angle = angle + t/steps * 2 * PI  # Rotate around
                
                x = curr_radius * np.cos(curr_angle)
                y = curr_radius * np.sin(curr_angle)
                z = curved_spacetime(x, y, mass_factors[-1])[2]
                
                path_points.append(np.array([x, y, z]))
            
            path = VMobject()
            path.set_points_smoothly(path_points)
            path.set_color(RED)
            particle_paths.append(path)
        
        # Show particles and their paths
        for particle, path in zip(particles, particle_paths):
            self.play(
                FadeIn(particle, run_time=0.5),
                Create(path, run_time=1)
            )
        
        # Animate particles following geodesics
        path_animations = []
        for i, particle in enumerate(particles):
            path_animations.append(
                MoveAlongPath(particle, particle_paths[i])
            )
        
        self.play(*path_animations, run_time=5)
        
        # Light ray bending demonstration
        light_label = Text("Light Rays", font_size=24)
        light_label.move_to(np.array([-3, -3, 0]))
        self.add_fixed_in_frame_mobjects(light_label)
        
        # Create light rays passing near the massive object
        light_rays = []
        for offset in np.linspace(-2, 2, 5):
            # Create a path for the light ray that bends around the massive object
            ray_points = []
            steps = 30  # Reduced number of steps
            for t in range(steps + 1):
                x = -4 + t * 8 / steps  # Move from left to right
                y = offset  # Different vertical offsets
                
                # Calculate distance from the center
                r = np.sqrt(x**2 + y**2)
                
                # Bend more if closer to the mass
                bending = 0
                if r > 0.6:  # Avoid the center of the mass
                    bending = min(1.5 / r**2, 0.5) * np.sign(y)
                
                # Apply bending
                y_adjusted = y - bending * (1 - abs(x/4))  # Maximum bending at x=0
                z = curved_spacetime(x, y_adjusted, mass_factors[-1])[2]  # Height on the surface
                
                ray_points.append(np.array([x, y_adjusted, z + 0.05]))  # Slightly above the surface
            
            ray = VMobject()
            ray.set_points_smoothly(ray_points)
            ray.set_color(YELLOW)
            light_rays.append(ray)
        
        # Show light rays bending around the mass
        for ray in light_rays:
            self.play(Create(ray, run_time=1))
        
        # Final view
        self.move_camera(phi=60 * DEGREES, theta=-60 * DEGREES, run_time=3)
        self.wait(2)
        
        # Clean up and prepare for transition to comparative visualization
        self.play(
            *[FadeOut(ray) for ray in light_rays],
            *[FadeOut(particle) for particle in particles],
            *[FadeOut(path) for path in particle_paths],
            FadeOut(mass_label_arrow),
            run_time=1
        )
        
        # Transition title
        transition_title = Text("Newtonian Gravity vs. General Relativity", font_size=36)
        transition_title.move_to(title.get_center())
        self.play(Transform(title, transition_title))
        
        # Split screen comparison
        # Reset to neutral view
        self.move_camera(phi=75 * DEGREES, theta=0 * DEGREES, run_time=2)
        
        # Create Newtonian gravity visualization (flat grid with force arrows)
        newtonian_grid = Surface(
            lambda u, v: np.array([u, v, 0]),
            u_range=[-grid_size/2, grid_size/2],
            v_range=[-grid_size/2, grid_size/2],
            resolution=(grid_density, grid_density)
        )
        newtonian_grid.set_fill_by_checkerboard(GREEN_D, GREEN_E, opacity=0.5)
        
        newtonian_grid.shift(LEFT * 4)
        newtonian_object = Sphere(radius=0.5)
        newtonian_object.set_color(YELLOW)
        newtonian_object.set_opacity(1)
        newtonian_object.move_to(np.array([-4, 0, 0]))
        
        # Move the relativistic grid to the right
        self.play(
            flat_grid.animate.shift(RIGHT * 4),
            massive_object.animate.shift(RIGHT * 4),
            FadeIn(newtonian_grid),
            FadeIn(newtonian_object)
        )
        
        # Create force arrows for Newtonian model
        arrows = []
        for u in np.linspace(-grid_size/2, grid_size/2, 8):  # Reduced number of arrows
            for v in np.linspace(-grid_size/2, grid_size/2, 8):
                if abs(u) < 0.6 and abs(v) < 0.6:
                    continue  # Skip arrows at the center
                
                start_point = np.array([u - 4, v, 0])
                
                # Direction toward the center
                direction = np.array([-4, 0, 0]) - start_point
                direction = direction / np.linalg.norm(direction)
                
                # Arrow length inversely proportional to distance
                dist = np.linalg.norm(start_point - np.array([-4, 0, 0]))
                length = min(0.5 / dist, 0.4)
                
                end_point = start_point + direction * length
                
                arrow = Arrow(start=start_point, end=end_point, buff=0.05)
                arrow.set_color(YELLOW)
                arrows.append(arrow)
        
        # Newton label
        newton_label = Text("Newtonian Gravity:\nAction at a Distance", font_size=20)
        newton_label.move_to(np.array([-4, -3, 0]))
        
        # Einstein label
        einstein_label = Text("General Relativity:\nCurved Spacetime", font_size=20)
        einstein_label.move_to(np.array([4, -3, 0]))
        
        self.add_fixed_in_frame_mobjects(newton_label, einstein_label)
        
        # Show Newtonian arrows
        self.play(*[Create(arrow) for arrow in arrows], run_time=2)
        
        # Final camera movement to show both models
        self.move_camera(phi=60 * DEGREES, theta=-30 * DEGREES, run_time=3)
        self.wait(2)
        
        # Fade out all elements
        self.play(
            FadeOut(flat_grid),
            FadeOut(massive_object),
            FadeOut(newtonian_grid),
            FadeOut(newtonian_object),
            *[FadeOut(arrow) for arrow in arrows],
            run_time=2
        )
        
        # Final message
        final_message = Text("Einstein's key insight: Gravity is not a force,\nbut a manifestation of curved spacetime.", font_size=28)
        final_message.move_to(np.array([0, 0, 0]))
        self.add_fixed_in_frame_mobjects(final_message)
        
        self.wait(3)