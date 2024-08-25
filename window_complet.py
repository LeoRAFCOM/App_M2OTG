import pygame_gui
import numpy as np

from window_base import BaseWindow
from const import *

class CompletWindow(BaseWindow):
    state = 0
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.logo_image = self.display_logo()
        self.cancel = self.cancel_button()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Indicateur synthétique'
        )

        self.panel = self.create_panel(
            topleft=(WIDTH*0.2, 200),
            size=(WIDTH*0.6, 200),
            objectid="#indic_final_panel"
        )


        if self.data.indic_topo and self.data.indic_attrib2:
            indic_final = np.mean([self.data.indic_attrib2, self.data.indic_topo])
            indic_final = round(indic_final*100, 2)
            print(indic_final)

            if indic_final <= 20:
                self.label = self.create_label(
                topleft=(20,80),
                objectid="#indic_topo_label20",
                text=f"La qualité estimée de votre réseau est de {indic_final}%",
                container=self.panel
            )
            elif indic_final <= 40:
                self.label = self.create_label(
                topleft=(20,80),
                objectid="#indic_topo_label40",
                text=f"La qualité estimée de votre réseau est de {indic_final}%",
                container=self.panel
            )
            elif indic_final <= 60:
                self.label = self.create_label(
                topleft=(20,80),
                objectid="#indic_topo_label60",
                text=f"La qualité estimée de votre réseau est de {indic_final}%",
                container=self.panel
            )
            elif indic_final <= 80:
                self.label = self.create_label(
                topleft=(20,80),
                objectid="#indic_topo_label80",
                text=f"La qualité estimée de votre réseau est de {indic_final}%",
                container=self.panel
            )
            else:
                self.label = self.create_label(
                topleft=(20,80),
                objectid="#indic_topo_label100",
                text=f"La qualité estimée de votre réseau est de {indic_final}%",
                container=self.panel
            )
            

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.panel.set_position((width*0.2, 200))
        self.panel.set_dimensions((width*0.6, 200))