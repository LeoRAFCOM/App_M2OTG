import pygame
import pygame_gui

class LoadingAnimation:
    def __init__(self, screen, manager, center, radius=20, num_circles=8, circle_radius=5, color=(255, 243, 209), label_text="CHARGEMENT"):
        self.screen = screen
        self.manager = manager
        self.center = center
        self.radius = radius
        self.num_circles = num_circles
        self.circle_radius = circle_radius
        self.color = color
        self.angle = 0  # Initialize the loading animation angle
        self.label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((center[0] - 65, center[1] + 100), (-1, -1)),
            text=label_text,
            manager=self.manager,
            object_id=pygame_gui.core.ObjectID(class_id="@all_labels", object_id="#loading_label")
        )

    def update(self, dt):
        # Update the loading animation angle
        self.angle += 180 * dt  # Speed of the rotation
        if self.angle >= 360:
            self.angle -= 360

    def draw(self):
        # Draw loading animation with little circles
        for i in range(self.num_circles):
            current_angle = (self.angle + (i * 360 / self.num_circles)) % 360
            x = self.center[0] + self.radius * pygame.math.Vector2(1, 0).rotate(current_angle)[0]
            y = self.center[1] + self.radius * pygame.math.Vector2(1, 0).rotate(current_angle)[1]
            pygame.draw.circle(self.screen, self.color, (int(x), int(y)), self.circle_radius)

    def set_position(self, width, height):
        self.label.set_position((width // 2 - 65, height // 2 + 100))
