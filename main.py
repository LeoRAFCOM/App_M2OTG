import pygame
import pygame_gui
import sys
from pygame_gui.core import ObjectID

# window manager
from window_manager import WindowManager

# import const
from const import *

# import data
from data import Data

class App:
    def __init__(self):
        pygame.init()

        # initial setup -> main display / manager
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.new_width = WIDTH
        self.new_height = HEIGHT

        self.data = Data()

        self.window_manager = WindowManager(self.screen, self.data)

        self.clock = pygame.time.Clock()
        self.dt = self.clock.tick(60)/1000

        self.window_manager.switch_to('main')

        # map data
        self.map_data = None
        self.map_data_list = None
        self.dataset = None


    def run(self):
        while True:
            self.dt = self.clock.tick(60)/1000
 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # debug
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        pass
                    elif event.key == pygame.K_SPACE:
                        pass

                if event.type == pygame.VIDEORESIZE:
                    self.new_width = max(event.w, 800)
                    self.new_height = max(event.h, HEIGHT)  # Ensure the height is at least MIN_HEIGHT
                    self.screen = pygame.display.set_mode((self.new_width, self.new_height), pygame.RESIZABLE)
                    self.window_manager.resize(self.new_width, self.new_height)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # window switch
                    if event.ui_element == self.window_manager.windows['main'].attrib_button:
                        self.window_manager.switch_to('attrib')
                    if event.ui_element == self.window_manager.windows['main'].topo_button:
                        self.window_manager.switch_to('topo')          
                    if event.ui_element == self.window_manager.windows['main'].complet_button:
                        self.window_manager.complete_path = True
                        self.window_manager.switch_to('attrib')

                self.window_manager.handle_event(event)
                
            self.screen.fill((50,50,50))
            self.window_manager.update(self.dt)
            self.window_manager.draw()
            pygame.display.update()


if __name__ == '__main__':
    app = App()
    app.run()

