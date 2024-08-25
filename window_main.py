import pygame
import pygame_gui

from const import *
from window_base import BaseWindow

class MainWindow(BaseWindow):
    state = 0
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        # clear
        self.clear_elements()

        # main container
        self.create_scrolling_container()
        self.display_logo()

        self.window_manager.complete_path = False

        self.topo_button = self.create_button(
            topleft=(WIDTH/2 - 150, 300),
            objectid="#topo_button",
            text='DIAGNOSTIC TOPOLOGIQUE',
            size=(300,300)
        )

        # diag attrib button
        self.attrib_button = self.create_button(
            topleft=(WIDTH*0.2 - 150, 300),
            objectid="#attrib_button",
            text='DIAGNOSTIC ATTRIBUTAIRE',
            size=(300,300)
        )

        # diag général
        self.complet_button = self.create_button(
            topleft=(WIDTH*0.8 - 150, 300),
            objectid="#general_button",
            text='DIAGNOSTIC COMPLET',
            size=(300,300)
        )


        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Sewer Data Quality Assessment'
        )


    def draw(self):
        super().draw()

    def reposition_elements(self, width, height):
        # buttons
        self.attrib_button.set_position((width*0.2 - 150, 300))
        self.topo_button.set_position((width/2 - 150, 300))
        self.complet_button.set_position((width*0.8 - 150, 300))



        