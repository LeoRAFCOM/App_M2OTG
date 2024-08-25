import pygame
import pygame_gui

from window_main import MainWindow
from window_attrib import *
from window_topo import *
from window_complet import CompletWindow
from window_loading import LoadingWindow
from const import *

from loading_animation import LoadingAnimation

class WindowManager:
    complete_path = False
    def __init__(self, screen, data):
        self.screen = screen
        self.data = data
        self.manager = pygame_gui.UIManager((WIDTH, HEIGHT), theme_path='themes.json')

        self.windows = {
            'main': MainWindow(self.manager, self.screen, self.data, self),
            'attrib': AttribWindow(self.manager, self.screen, self.data, self),
            'attrib1': AttribWindow1(self.manager, self.screen, self.data, self),
            'attrib2': AttribWindow2(self.manager, self.screen, self.data, self),
            'attrib3': AttribWindow3(self.manager, self.screen, self.data, self),
            'attrib4': AttribWindow4(self.manager, self.screen, self.data, self),
            'attrib5': AttribWindow5(self.manager, self.screen, self.data, self),
            'attrib6': AttribWindow6(self.manager, self.screen, self.data, self),
            'attrib7': AttribWindow7(self.manager, self.screen, self.data, self),
            'attrib8': AttribWindow8(self.manager, self.screen, self.data, self),
            'attrib9': AttribWindow9(self.manager, self.screen, self.data, self),
            'attrib_crs': AttribWindowCrs(self.manager, self.screen, self.data, self),
            'topo': TopoWindow(self.manager, self.screen, self.data, self),
            'topo1': TopoWindow1(self.manager, self.screen, self.data, self),
            'topo2': TopoWindow2(self.manager, self.screen, self.data, self),
            'topo3': TopoWindow3(self.manager, self.screen, self.data, self),
            'complet': CompletWindow(self.manager, self.screen, self.data, self),
            'loading': LoadingWindow(self.manager, self.screen, self.data, self)
        }

        self.loading_animation = LoadingAnimation(self.screen, self.manager, (self.screen.get_width()-35, self.screen.get_height()-35))
        self.loading = False

        # load topo data
        self.data_loading_complete = False
        self.data_attrib_loading_complete = False

        # diag topo
        self.diag_topo_loading_complete = False

        # maps
        self.map_loading_complete = False

        # get standard
        self.standard_loading_complete = False
        self.new_dataset_loading_complete = False
        self.enum_loading_complete = False
        self.diag_attrib_complete = False
        self.load_attrib_map_complete = False

        self.current_window = self.windows['main']
        self.current_window.initialize()

        # error messages
        self.error1 = self.current_window.create_error1_label()
        self.error1.hide()
        self.error2 = self.current_window.create_error1_label()
        self.error2.hide()

    def stop_animation(self):
        self.loading = False

    def set_load_attrib_map_complete(self):
        self.load_attrib_map_complete = True
    
    def set_diag_attrib_complete(self):
        self.diag_attrib_complete = True

    def start_animation(self):
        self.loading = True

    def set_data_loading_complete(self):
        self.data_loading_complete = True

    def set_diag_topo_loading_complete(self):
        self.diag_topo_loading_complete = True

    def set_standard_loading_complete(self):
        self.standard_loading_complete = True

    def set_map_loading_complete(self):
        self.map_loading_complete = True

    def set_data_attrib_loading_complete(self):
        self.data_attrib_loading_complete = True

    def set_new_dataset_loading_complete(self):
        self.new_dataset_loading_complete = True

    def set_enum_loading_complete(self):
        self.enum_loading_complete = True

    def switch_to(self, window_name):
        self.current_window = self.windows[window_name]
        self.manager.clear_and_reset()
        self.current_window.initialize()
        self.resize(self.screen.get_width(), self.screen.get_height())

    def handle_event(self, event):
        self.current_window.handle_event(event)
        self.manager.process_events(event)

    def update(self, dt):
        self.current_window.update(dt)

        # animation
        if self.loading:
            self.loading_animation.update(dt)

        # topo data loading
        if self.data_loading_complete:
            self.data_loading_complete = False
            self.stop_animation()
            if self.data.topo_initial_dataset:
                self.switch_to("topo1")
            else:
                self.error1 = self.current_window.create_error1_label()

        if self.diag_topo_loading_complete:
            self.diag_topo_loading_complete = False
            self.stop_animation()
            self.switch_to('topo3')

        if self.map_loading_complete:
            self.map_loading_complete = False
            self.stop_animation()

        if self.standard_loading_complete:
            self.standard_loading_complete = False
            self.stop_animation()
            self.switch_to('attrib1')

        if self.new_dataset_loading_complete:
            self.new_dataset_loading_complete = False
            self.stop_animation()
            self.switch_to('attrib4')

        if self.enum_loading_complete:
            self.enum_loading_complete = False
            self.stop_animation()
            self.switch_to('attrib6')

        if self.data_attrib_loading_complete:
            self.data_attrib_loading_complete = False
            self.stop_animation()
            if self.data.attrib_initial_dataset:
                self.switch_to('attrib_crs')
            else:
                self.error2 = self.current_window.create_error1_label(topleft=(self.screen.width/2-190, self.screen.height-100))

        if self.diag_attrib_complete:
            self.diag_attrib_complete = False
            self.stop_animation()
            self.switch_to('attrib9')

        if self.load_attrib_map_complete:
            self.load_attrib_map_complete = False
            self.stop_animation()
            
    def draw(self):
        self.current_window.draw()

        # animation
        if self.loading:
            self.loading_animation.draw()

    def resize(self, width, height):
        for window in self.windows.values():
            window.resize(width, height)
        self.loading_animation.center = (width-35, height-35)
        self.error1.set_position((width/2-190, height-200))
        self.error2.set_position((width/2-190, height-100))