import pygame
import pygame_gui

from window_base import BaseWindow


class LoadingWindow(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.loading_animation_angle = 0  # Initialize the loading animation angle
        self.initialize()
        
    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()

        self.loading_label = self.create_label(
            topleft=(self.screen.get_width() // 2 - 65, self.screen.get_height() // 2 + 100),
            objectid="#loading_label",
            text="CHARGEMENT",
        )

    def update(self, dt):
        super().update(dt)
        # Update the loading animation angle
        self.loading_animation_angle += 180 * dt  # Speed of the rotation
        if self.loading_animation_angle >= 360:
            self.loading_animation_angle -= 360

    def draw(self):
        super().draw()

        # Draw loading animation with little circles
        center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        num_circles = 8
        radius = 60
        circle_radius = 10
        for i in range(num_circles):
            angle = (self.loading_animation_angle + (i * 360 / num_circles)) % 360
            x = center[0] + radius * pygame.math.Vector2(1, 0).rotate(angle)[0]
            y = center[1] + radius * pygame.math.Vector2(1, 0).rotate(angle)[1]
            pygame.draw.circle(self.screen, (255, 243, 209), (int(x), int(y)), circle_radius)

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                pass

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.loading_label.set_position(((self.screen.get_width() // 2 - 65, self.screen.get_height() // 2 + 100)))