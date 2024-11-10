import pygame
import math
import sys

# Initialize PyGame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 1000
CENTER = (WIDTH // 2, HEIGHT // 2)  # Center of screen
BG_COLOR = (0, 0, 0)  # Black background
GRAVITATIONAL_CONSTANT = 5  # Gravity constant
MASS_MULTIPLIER = 1  # Mass multiplier for planet calculations
TIME_STEP = 1  # Time step for movement calculations
MIN_RADIUS = 5  # Minimum planet radius
DAMPING_FACTOR = 0.2  # Slows large planet near center
CENTER_THRESHOLD = 10  # Distance threshold to stop center gravity

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # Screen size
pygame.display.set_caption("Planetary Simulation")  # Window title
clock = pygame.time.Clock()  # Used to limit frame rate

# Function for color gradient
def get_color_from_radius(radius):
    max_radius_for_color = 200  # Max radius for color scaling
    factor = min(1, radius / max_radius_for_color)  # Scale factor for color
    r = int(128 + factor * 127)  # Red color component
    g = int(0)  # Green color component
    b = int(128 - factor * 128)  # Blue color component
    return (r, g, b)  # Return color as RGB tuple

class Planet:
    def __init__(self, x, y, radius, vx=0, vy=0):
        self.x = x  # Planet x position
        self.y = y  # Planet y position
        self.radius = radius  # Planet's radius
        self.mass = self.radius * MASS_MULTIPLIER  # Planet's mass
        self.vx = vx  # Planet's velocity in x direction
        self.vy = vy  # Planet's velocity in y direction
        self.ax = 0  # Planet's acceleration in x direction
        self.ay = 0  # Planet's acceleration in y direction
        self.color = get_color_from_radius(self.radius)  # Color based on radius
        self.is_largest = False  # Flag if it's the largest planet
        self.is_collidable = True  # Flag for collision detection

    def apply_gravity(self, other):
        if other.is_collidable:  # Skip non-collidable planets
            dx = other.x - self.x  # X distance to other planet
            dy = other.y - self.y  # Y distance to other planet
            distance = math.sqrt(dx ** 2 + dy ** 2) + 1e-2  # Distance between planets

            force = GRAVITATIONAL_CONSTANT * self.mass * other.mass / distance ** 2  # Gravity force

            ax = force * dx / (distance * self.mass)  # X acceleration
            ay = force * dy / (distance * self.mass)  # Y acceleration

            self.ax += ax  # Add to planet's total x acceleration
            self.ay += ay  # Add to planet's total y acceleration

    def apply_gravity_to_center(self):
        if self.is_largest:  # Only apply to the largest planet
            dx = CENTER[0] - self.x  # X distance to center
            dy = CENTER[1] - self.y  # Y distance to center
            distance = math.sqrt(dx ** 2 + dy ** 2) + 1e-2  # Distance to center

            # Stop gravity if within threshold distance
            if distance < CENTER_THRESHOLD:
                return

            force = 0.5 * GRAVITATIONAL_CONSTANT * self.mass * self.mass / distance ** 2  # Gravity force

            ax = force * dx / (distance * self.mass)  # X acceleration
            ay = force * dy / (distance * self.mass)  # Y acceleration

            self.ax += ax  # Add to planet's x acceleration
            self.ay += ay  # Add to planet's y acceleration

    def update_position(self, dt):
        self.vx += self.ax * dt  # Update x velocity
        self.vy += self.ay * dt  # Update y velocity
        self.x += self.vx * dt  # Update x position
        self.y += self.vy * dt  # Update y position

        self.ax = 0  # Reset x acceleration
        self.ay = 0  # Reset y acceleration

    def check_collision(self, other):
        dx = other.x - self.x  # X distance between planets
        dy = other.y - self.y  # Y distance between planets
        distance = math.sqrt(dx ** 2 + dy ** 2)  # Total distance

        if distance < self.radius + other.radius:  # If colliding
            self.merge(other)  # Merge the two planets
            return True
        return False

    def merge(self, other):
        new_radius = math.sqrt(self.radius**2 + other.radius**2)  # New radius
        new_mass = self.mass + other.mass  # Combined mass

        self.radius = int(new_radius)  # Set new radius
        self.mass = new_mass  # Set new mass
        self.color = get_color_from_radius(self.radius)  # Update color

        # Merge velocities weighted by mass
        self.vx = (self.vx * self.mass + other.vx * other.mass) / new_mass
        self.vy = (self.vy * self.mass + other.vy * other.mass) / new_mass

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)  # Draw planet

class NonCollidingPlanet(Planet):
    def __init__(self, x, y, radius, vx=0, vy=0):
        super().__init__(x, y, radius, vx, vy)  # Inherit planet properties
        self.is_collidable = False  # Set as non-collidable
        self.color = (255, 255, 255)  # White color for non-collidable

    def check_collision(self, other):
        return False  # Never collide with other planets

class GhostPlanet(NonCollidingPlanet):
    def __init__(self, x, y, radius, vx=0, vy=0):
        super().__init__(x, y, radius, vx, vy)  # Inherit non-collidable
        self.is_collidable = False  # Set as non-collidable
        self.color = (255, 255, 255)  # White color for ghost planets

    def apply_gravity(self, other):
        if not other.is_collidable:  # Skip gravity on non-collidable planets
            return

        dx = other.x - self.x  # X distance to other planet
        dy = other.y - self.y  # Y distance to other planet
        distance = math.sqrt(dx ** 2 + dy ** 2) + 1e-2  # Total distance

        force = GRAVITATIONAL_CONSTANT * self.mass * other.mass / distance ** 2  # Gravity force

        ax = force * dx / (distance * self.mass)  # X acceleration
        ay = force * dy / (distance * self.mass)  # Y acceleration

        self.ax += ax  # Add to x acceleration
        self.ay += ay  # Add to y acceleration

def main():
    running = True  # Flag for simulation running
    planets = []  # List of all planets
    largest_planet = None  # Track largest planet

    creating_planet = False  # Flag for planet creation
    creation_start_time = 0  # Time when planet creation started
    creation_start_pos = (0, 0)  # Start position for planet creation

    setting_velocity = False  # Flag for setting velocity
    velocity_target_pos = (0, 0)  # Target position for velocity

    while running:
        screen.fill(BG_COLOR)  # Clear screen

        for event in pygame.event.get():  # Process events
            if event.type == pygame.QUIT:  # Quit the simulation
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not creating_planet and not setting_velocity:
                    creating_planet = True  # Start creating planet
                    creation_start_time = pygame.time.get_ticks()  # Start time for creation
                    creation_start_pos = pygame.mouse.get_pos()  # Initial mouse position

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if creating_planet:
                    creation_duration = (pygame.time.get_ticks() - creation_start_time) / 100  # Calculate duration
                    radius = max(MIN_RADIUS, int(creation_duration))  # Set radius
                    creating_planet = False  # Stop creating planet
                    setting_velocity = True  # Start setting velocity

                elif setting_velocity:
                    velocity_target_pos = pygame.mouse.get_pos()  # Get velocity target
                    setting_velocity = False  # Stop setting velocity

                    dx = velocity_target_pos[0] - creation_start_pos[0]  # X difference for velocity
                    dy = velocity_target_pos[1] - creation_start_pos[1]  # Y difference for velocity
                    velocity_scale = 0.05  # Scale factor for velocity
                    vx = dx * velocity_scale  # Velocity in x direction
                    vy = dy * velocity_scale  # Velocity in y direction

                    new_planet = Planet(creation_start_pos[0], creation_start_pos[1], radius, vx, vy)  # Create planet
                    planets.append(new_planet)  # Add to planet list

                    if largest_planet is None or new_planet.radius > largest_planet.radius:
                        if largest_planet:  # Update largest planet flag
                            largest_planet.is_largest = False
                        largest_planet = new_planet  # Set new largest planet
                        largest_planet.is_largest = True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Space clears all planets
                   planets.clear()

                elif event.key == pygame.K_p:  # 'p' creates non-collidable planet
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    new_planet = NonCollidingPlanet(mouse_x, mouse_y, MIN_RADIUS)
                    planets.append(new_planet)
                
                elif event.key == pygame.K_o:  # 'o' creates ghost planet
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    new_planet = GhostPlanet(mouse_x, mouse_y, MIN_RADIUS)
                    planets.append(new_planet)

        if creating_planet:
            current_time = pygame.time.get_ticks()
            creation_duration = (current_time - creation_start_time) / 100  # Calculate radius while creating
            current_radius = max(MIN_RADIUS, int(creation_duration))  # Current planet radius
            pygame.draw.circle(screen, get_color_from_radius(current_radius), creation_start_pos, current_radius)  # Draw circle
            pygame.draw.circle(screen, get_color_from_radius(current_radius), creation_start_pos, current_radius, 2)

        if setting_velocity:
            mouse_pos = pygame.mouse.get_pos()  # Get current mouse position
            pygame.draw.line(screen, (255, 255, 255), creation_start_pos, mouse_pos, 2)  # Draw velocity line

        to_remove = set()  # Set to store planets to be removed
        for i, planet in enumerate(planets):
            for other_planet in planets[i + 1:]:  # Compare each planet with others
                if planet.check_collision(other_planet):  # If planets collide
                    to_remove.add(other_planet)  # Add to removal set

        for planet in to_remove:
            planets.remove(planet)  # Remove colliding planets

        for planet in planets:
            for other_planet in planets:
                if planet != other_planet:  # Apply gravity only to different planets
                    planet.apply_gravity(other_planet)

            planet.apply_gravity_to_center()  # Apply gravity to the center for largest planet

        for planet in planets:
            planet.update_position(TIME_STEP)  # Update planet position

        for planet in planets:
            planet.draw(screen)  # Draw planet on screen

        font = pygame.font.SysFont(None, 24)  # Font for instructions
        instructions = [
            "Left Click and Hold to Create a Planet",
            "Release to set size, then Left Click to set initial velocity"
        ]
        for i, text in enumerate(instructions):
            img = font.render(text, True, (255, 255, 255))  # Render text
            screen.blit(img, (10, 10 + i * 20))  # Display text

        pygame.display.flip()  # Update screen
        clock.tick(60)  # Limit frame rate to 60 FPS

    pygame.quit()  # Quit pygame
    sys.exit()  # Exit program

if __name__ == "__main__":
    main()
