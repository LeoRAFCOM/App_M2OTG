import pygame
import pygame_gui
import threading
import os
import pandas as pd

from window_base import BaseWindow
from const import *

class AttribWindow(BaseWindow):
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
            text='Diagnostic Attributaire'
        )

        # import standard
        self.import_standard_button = self.create_button(
            topleft=(WIDTH/2-250, HEIGHT/2-100),
            objectid="#import_standard_button",
            text="IMPORTEZ VOTRE STANDARD",
            size=(500, 200)
        )
    
    def load_standard(self):
        self.data.get_standard()
        self.window_manager.set_standard_loading_complete()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.import_standard_button:
                self.window_manager.start_animation()
                threading.Thread(target=self.load_standard).start()
                

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.import_standard_button.set_position((width/2-250, height/2-100))


class AttribWindow1(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.logo_image = self.display_logo()
        self.cancel = self.cancel_button()
        self.back = self.back_button()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Attributaire'
        )

        self.standard_point_panel = self.create_panel(
            topleft=(50, 200),
            size=(0,0),
            objectid="#standard_point_panel"
        )
        self.standard_line_panel = self.create_panel(
            topleft=(50, 200),
            size=(0,0),
            objectid="#standard_line_panel"
        )

        # valider le standard
        self.validate_standard = self.create_button(
            topleft=(self.back.rect.left, self.back.rect.bottom +10),
            objectid="#validate_standard",
            text="Valider",
            size=(200, 50)
        )

        # afficher les colonnes

        # line
        if len(self.data.standard)>0:
            self.y_offset = 70
            self.x_offset = 10
            lines = self.data.standard[0].dropna().to_list()
            self.line_title = self.create_label(
                topleft=((WIDTH-100)/2-120,10),
                text='Standard linéaire',
                objectid="#label_std",
                container=self.standard_line_panel
            )
            for i, col in enumerate(lines):
                self.create_label(
                    topleft=(self.x_offset, self.y_offset),
                    text=f'{i+1}. {col}',
                    objectid="#label_col_std",
                    container=self.standard_line_panel
                )
                # self.create_drop_down_menu_topo(
                #     file_name="lines_std",
                #     options=['0','1','2','3','4','5'],
                #     pos_x=self.x_offset+110,
                #     pos_y=self.y_offset-5,
                #     width=80,
                #     height=30,
                #     data_info=col,
                #     dict=self.data.weights_ddm_dict,
                #     container=self.standard_line_panel,
                #     placeholder='1'
                # )
                if i%8 == 0 and i != 0:
                    self.y_offset+=30
                    self.x_offset=10
                else:
                    self.x_offset+=150
                

            self.standard_line_panel.set_dimensions((WIDTH-100, self.y_offset+50))

            # point
            self.y_offset = 70
            self.x_offset = 10
            points = self.data.standard[1].dropna().to_list()
            self.point_title = self.create_label(
                topleft=((WIDTH-100)/2-120,10),
                text='Standard ponctuel',
                objectid="#label_std",
                container=self.standard_point_panel
            )
            for i, col in enumerate(points):
                self.create_label(
                    topleft=(self.x_offset, self.y_offset),
                    text=f'{i+1}. {col}',
                    objectid="#label_col_std",
                    container=self.standard_point_panel
                )
                # self.create_drop_down_menu_topo(
                #     file_name="points_std",
                #     options=['0','1','2','3','4','5'],
                #     pos_x=self.x_offset+110,
                #     pos_y=self.y_offset-5,
                #     width=80,
                #     height=30,
                #     data_info=col,
                #     dict=self.data.weights_ddm_dict,
                #     container=self.standard_point_panel,
                #     placeholder='1'
                # )
                if i%8 == 0 and i != 0:
                    self.y_offset+=30
                    self.x_offset=10
                else:
                    self.x_offset+=150

            self.standard_point_panel.set_position((50, self.standard_line_panel.rect.bottom+50))
            self.standard_point_panel.set_dimensions((WIDTH-100, self.y_offset+50))
            




    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("attrib")
            if event.ui_element == self.validate_standard:
                self.window_manager.switch_to("attrib2")

                

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.standard_line_panel.set_position((width/2-((WIDTH-100)/2),200))
        self.standard_point_panel.set_position((width/2-((WIDTH-100)/2),self.standard_line_panel.rect.bottom+50))
        self.validate_standard.set_position((self.back.rect.left, self.back.rect.bottom))

class AttribWindow2(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()
        
    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.logo_image = self.display_logo()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Attributaire'
        )

        # import data label
        self.import_topo_data_button = self.create_button(
            topleft=(WIDTH/2-250, HEIGHT/2-100),
            objectid="#import_topo_data_button",
            text="IMPORTEZ VOS COUCHES",
            size=(500, 200)
        )

        self.ask_standard_form_label = self.create_label(
            topleft=(self.import_topo_data_button.rect.left-70, self.import_topo_data_button.rect.bottom+80),
            objectid="#export_or_not_label",
            text="Vos données sont-elles dans la forme du standard ?"
        )

        # forme standard ou non des données
        self.oui, self.non = self.create_binary_choice(
            posx=self.ask_standard_form_label.rect.right+10,
            posy=self.import_topo_data_button.rect.bottom+50,
            size=(75)
        )
        self.non.select()

    def load_attrib_data(self):
        self.data.get_attrib_data()
        self.window_manager.set_data_attrib_loading_complete()
    

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("attrib1")
            if event.ui_element == self.import_topo_data_button:
                self.window_manager.start_animation()
                threading.Thread(target=self.load_attrib_data).start()
            if event.ui_element == self.oui:
                self.data.standard_form = True
                print(self.data.standard_form)
                self.non.unselect()
                self.oui.select()
            if event.ui_element == self.non:
                self.data.standard_form = False
                print(self.data.standard_form)
                self.oui.unselect()
                self.non.select()

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.import_topo_data_button.set_position((width/2-250, height/2-100))
        self.ask_standard_form_label.set_position((self.import_topo_data_button.rect.left-70, self.import_topo_data_button.rect.bottom+80))
        self.oui.set_position((self.ask_standard_form_label.rect.right+50, self.import_topo_data_button.rect.bottom+50))
        self.non.set_position((self.ask_standard_form_label.rect.right+50+75+75*0.1, self.import_topo_data_button.rect.bottom+50))

class AttribWindowCrs(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.logo_image = self.display_logo()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Attributaire'
        )

        # preview the dataset
        self.y_offset = 20
        self.x_offset = 60
        geoms = []
        self.missing_geoms =[]
        self.topo_overview_panel = self.create_panel(
            topleft=(10,200),
            size=(WIDTH-10,self.y_offset),
            objectid='#topo_overview_panel'
        )

        data = self.data.attrib_initial_dataset
        for file in data:
            data_file = data[file][0]
            geomtype = data[file][1]
            entities = data[file][2]
            crs = data[file][3]

            self.create_label(
                topleft=(self.x_offset, self.y_offset),
                objectid=f'#{file}_label',
                text=file,
                class_id="@topo_overview_label",
                container=self.topo_overview_panel
            )

            self.create_label(
                topleft=(WIDTH-150, self.y_offset),
                objectid=f'#{file}_crs_label',
                text=f'{crs}',
                class_id="@topo_overview_label",
                container=self.topo_overview_panel
            )

            if geomtype in ['MultiLineString', 'LineString']:
                self.display_picto_logo(
                    topleft=(self.x_offset-40, self.y_offset),
                    image_surface=self.lines,
                    container=self.topo_overview_panel
                )
                geoms.append(geomtype)
            elif geomtype in ['MultiPoint', 'Point']:
                self.display_picto_logo(
                    topleft=(self.x_offset-40, self.y_offset),
                    image_surface=self.points,
                    container=self.topo_overview_panel
                )
                geoms.append(geomtype)
            elif geomtype in ['MultiPolygon', 'Polygon']:
                self.display_picto_logo(
                    topleft=(self.x_offset-40, self.y_offset),
                    image_surface=self.polygon,
                    container=self.topo_overview_panel
                )
                geoms.append(geomtype)
                self.create_drop_down_menu_topo(
                    file_name=file,
                    options=list(data_file.columns),
                    pos_x=self.x_offset + 500,
                    pos_y=self.y_offset + 190,
                    width=200,
                    height=45,
                    data_info=self.data.attrib_initial_dataset[file],
                    dict=self.data.ddm_dict_crs,
                    container=self.scroll_container
                )
            else:
                pass #error


            self.y_offset+=50
        
        self.topo_overview_panel.set_dimensions((WIDTH-20, self.y_offset))

        # missing geoms
        if self.window_manager.complete_path:
            if 'MultiLineString' not in geoms and 'LineString' not in geoms:
                self.missing_geoms.append('Linéaire')
            if 'MultiPoint' not in geoms and 'Point' not in geoms:
                self.missing_geoms.append('Ponctuel')
            if 'MultiPolygon' not in geoms and 'Polygon' not in geoms:
                self.missing_geoms.append('Surfacique')
        else:
            if 'MultiPolygon' not in geoms and 'Polygon' not in geoms:
                self.missing_geoms.append('Surfacique')

        # epsg 
        self.ask_epsg_entry = self.create_text_entry(
            topleft=(10,self.topo_overview_panel.rect.bottom + 20),
            size=(400,100),
            text="Veuillez entrer l'EPSG de votre projet",
            objectid="#ask_epsg_entry"
        )
        self.validate_epsg_button = self.create_button(
            topleft=(self.ask_epsg_entry.rect.topright[0]+10, self.ask_epsg_entry.rect.topleft[1]),
            objectid="#validate_epsg_button",
            text="OK",
            size=(100,100)
        )

        # check id_unique
        self.validate_unique_id = self.create_button(
            topleft=(self.topo_overview_panel.rect.right - 400, self.topo_overview_panel.rect.bottom + 20),
            objectid="#validate_unique_id_button",
            text="Valider les champs uniques",
            size = (400, 100)
        )

        # error
        if self.missing_geoms:
            self.error_label = self.create_error1_label(
                topleft = (self.validate_unique_id.rect.left, self.validate_unique_id.rect.bottom + 30),
                text="Géométrie(s) manquante(s) :"
            )
            self.error_label_geom = self.create_error1_label(
                topleft = (self.error_label.rect.left, self.error_label.rect.bottom + 10),
                text=f'{self.missing_geoms}'
            )
    
    def create_cor_weights(self):
        data = self.data.attrib_initial_dataset
        for layer in data:
            cols = data[layer][0].columns
            geom_type = data[layer][1]

            if geom_type in ['MultiPoint', 'Point', 'MultiLineString', 'LineString']:

                if layer not in self.data.correspond_weights:
                    self.data.correspond_weights[layer] = {}

                    for col in cols:
                        if col != 'geometry':
                            self.data.correspond_weights[layer][col] = 1

                print(self.data.correspond_weights[layer].keys())
            

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
                self.data.standard_form = False
            if event.ui_element == self.back:
                self.window_manager.switch_to("attrib2")
                self.data.standard_form = False
            if event.ui_element == self.validate_epsg_button:
                epsg = self.ask_epsg_entry.get_text()
                self.data.reproject_data_attrib(epsg)
                self.initialize()
                self.window_manager.resize(self.screen.width, self.screen.height)
            if event.ui_element == self.validate_unique_id and not self.missing_geoms:
                if not self.data.standard_form:
                    self.window_manager.switch_to('attrib3')
                else:
                    self.create_cor_weights()
                    self.window_manager.switch_to('attrib4')

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in self.data.ddm_dict_crs:
                selected_option = event.text
                data_info = self.data.ddm_dict_crs[event.ui_element][0]
            # remplacer la valeur si elle a déjà été attribué
            if len(data_info) > 5:
                data_info[5] = selected_option
            else:
                data_info.append(selected_option)


    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.topo_overview_panel.set_dimensions((width-20, self.y_offset))
        self.ask_epsg_entry.set_position((10,self.topo_overview_panel.rect.bottom + 20))
        self.validate_epsg_button.set_position((self.ask_epsg_entry.rect.topright[0]+10, self.ask_epsg_entry.rect.topleft[1]))
        self.validate_unique_id.set_position((self.topo_overview_panel.rect.right - 400, self.topo_overview_panel.rect.bottom + 20))

class AttribWindow3(BaseWindow):
    step=0
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()
        
    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.logo_image = self.display_logo()
        self.i = None
        self.tooltip_data = None

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Attributaire'
        )

        self.panel_height = 20

        self.std_panel = self.create_panel(
            topleft=(WIDTH*0.2, 200),
            size=(WIDTH*0.6, self.panel_height),
            objectid="#std_panel"
        )

        self.tooltip, self.tooltip_label = self.create_tooltip(
            objectid_panel="#tooltip_panel",
            objectid_label="#tooltip_label",
            container=self.std_panel
        )

        # next / previous
        self.next = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Suivant',
            size=(120,50)
        )
        self.previous = self.create_button(
            topleft=(WIDTH/2-230, 140),
            objectid="#back_button",
            text='Précédent',
            size=(120,50)
        )


        self.x_offset = 20
        self.y_offset = 20

        # display data cols
        self.label_list = []
        self.data_attrib = {}
        self.count=0
        for file in self.data.attrib_initial_dataset:
            if self.data.attrib_initial_dataset[file][1] in ['MultiLineString', 'LineString', 'MultiPoint', 'Point']:
                self.data_attrib[file] = self.data.attrib_initial_dataset[file]
                self.count+=1

        # display labels and ddms
        for i, file in enumerate(self.data_attrib):
            data_file = self.data_attrib[file][0]
            geomtype = self.data_attrib[file][1]

            if i == self.step:
                self.i = i
                self.tooltip_data = self.data_attrib[file][0]
                if geomtype in ['MultiLineString', 'LineString']:                
                    standard = self.data.standard[0].dropna().to_list()
                elif geomtype in ['MultiPoint', 'Point']:
                    standard = self.data.standard[1].dropna().to_list()
                else:
                    pass

                # count label
                self.count_label = self.create_label(
                    topleft=(WIDTH/2-70, 150),
                    objectid="#count_label",
                    text=f"Couche {self.step+1} / {self.count}",
                )

                cols = data_file.columns
                # nom de la couche
                self.layer_title = self.create_label(
                    topleft=(20, self.y_offset),
                    objectid="#label_std",
                    text=f'{file}',
                    container=self.std_panel
                )
                self.y_offset+=60
                # valeurs de colonne
                for j, col in enumerate(cols):
                    label = self.create_label(
                        topleft=(self.x_offset, self.y_offset),
                        objectid="#label_col_std",
                        text=f'{col}',
                        container=self.std_panel
                    )
                    self.label_list.append(label)

                    self.create_drop_down_menu_attrib(
                        file_name=file,
                        options=standard,
                        pos_x=self.x_offset + 100,
                        pos_y=self.y_offset,
                        width=200,
                        height=30,
                        data_info=col,
                        dict=self.data.ddm_dict_attrib,
                        container=self.std_panel
                    )
                    if j%15 == 0 and j != 0:
                        self.x_offset+=375
                        self.y_offset=80
                    else:
                        self.y_offset+=40

                    self.panel_height = max(self.y_offset, self.panel_height)

        self.std_panel.set_dimensions((WIDTH*0.6, self.panel_height+200))

        # validate button
        if self.count == self.step+1:
            self.next.hide()

            self.validate = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Terminer',
            size=(120,50)
            )

        if self.step-1 < 0:
            self.previous.hide()

    def draw(self):
        super().draw()
        mouse_pos = pygame.mouse.get_pos()
        self.update_tooltip(
            mouse_pos=mouse_pos,
            data=self.tooltip_data,
            label_list=self.label_list,
            tooltip_panel=self.tooltip,
            tooltip_label=self.tooltip_label
        )

    def clear_labels(self):
        for label in self.label_list:
            label.kill()
        self.label_list.clear()

    def load_new_dataset(self):
        self.data.setup_standard_shape(self.data.correspond, self.data.attrib_initial_dataset, self.data.standard)

        data = self.data.new_dataset
        for layer in data:
            cols = data[layer].columns
            geom_type = data[layer].geom_type[0]

            if geom_type in ['MultiPoint', 'Point', 'MultiLineString', 'LineString']:

                if layer not in self.data.correspond_weights:
                    self.data.correspond_weights[layer] = {}

                    for col in cols:
                        if col != 'geometry':
                            self.data.correspond_weights[layer][col] = 1

        print(self.data.correspond_weights)

        self.window_manager.set_new_dataset_loading_complete()

        
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("attrib_crs")
            if self.count == self.step+1:
                if event.ui_element == self.validate:
                    self.window_manager.start_animation()
                    threading.Thread(target=self.load_new_dataset).start()

            if event.ui_element == self.next:
                if self.step+1 < len(self.data_attrib):
                    self.step+=1
                    self.clear_labels()
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)

            if event.ui_element == self.previous:
                if self.step-1 >= 0:
                    self.step-=1
                    self.clear_labels()
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in self.data.ddm_dict_attrib:
                new_field_name = event.text
                layer = self.data.ddm_dict_attrib[event.ui_element][1]
                field_name = self.data.ddm_dict_attrib[event.ui_element][0]
                print(f'layer : {layer}\nfield_name : {field_name}\nnew_field_name : {new_field_name}')
                if layer in self.data.correspond:
                    # Check if field_name already exists
                    field_found = False
                    for i, pair in enumerate(self.data.correspond[layer]):
                        if pair[0] == field_name:
                            self.data.correspond[layer][i][1] = new_field_name
                            field_found = True
                            break
                    if not field_found:
                        self.data.correspond[layer].append([field_name, new_field_name])
                else:
                    self.data.correspond[layer] = [[field_name, new_field_name]]

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.logo_image.set_position((50,50))
        self.main_title.set_position((self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20))
        self.std_panel.set_dimensions((width*0.6, self.panel_height+200))
        self.std_panel.set_position((width*0.2, 200))
        self.next.set_position((width/2+100, 140))
        self.previous.set_position((width/2-230, 140))
        if self.i == self.step:
            self.layer_title.set_relative_position((20, 20))
            self.count_label.set_position((width/2-70, 150))
        if self.count == self.step+1:
            self.validate.set_position((width/2+100, 140))

class AttribWindow4(BaseWindow):
    step = 0
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.logo_image = self.display_logo()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.i = None
        self.label_list = []

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic attributaire'
        )

        self.panel_height = 20

        self.std_panel = self.create_panel(
            topleft=(WIDTH*0.2, 200),
            size=(WIDTH*0.6, self.panel_height),
            objectid="#std_panel"
        )

        # next / previous
        self.next = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Suivant',
            size=(120,50)
        )
        self.previous = self.create_button(
            topleft=(WIDTH/2-230, 140),
            objectid="#back_button",
            text='Précédent',
            size=(120,50)
        )

        self.x_offset = 20
        self.y_offset = 20

        self.data_weights = self.data.correspond_weights

        self.count = len(self.data_weights)
        for i, layer_name in enumerate(self.data_weights):
            cols = self.data_weights[layer_name].keys()

            if i == self.step:
                self.i = i
                # count label
                self.count_label = self.create_label(
                    topleft=(WIDTH/2-70, 150),
                    objectid="#count_label",
                    text=f"Couche {self.step+1} / {self.count}",
                )

                # nom de la couche
                self.layer_title = self.create_label(
                    topleft=(20, self.y_offset),
                    objectid="#label_std",
                    text=f'{layer_name}',
                    container=self.std_panel
                )
                self.y_offset+=60

                for j, col in enumerate(cols):

                    self.create_label(
                        topleft=(self.x_offset, self.y_offset),
                        objectid="#label_col_std",
                        text=f'{col}',
                        container=self.std_panel
                    )

                    self.create_drop_down_menu_topo(
                        file_name=layer_name,
                        options=["0", "1", "2", "3", "4", "5"],
                        pos_x=self.x_offset + 90,
                        pos_y=self.y_offset-3,
                        width=100,
                        height=30,
                        data_info=col,
                        dict=self.data.weights_ddm_dict,
                        container=self.std_panel,
                        placeholder="1"
                    )

                    self.y_offset+=30
                    self.panel_height = max(self.y_offset, self.panel_height)

                    if j%8 == 0 and j != 0:
                        self.x_offset+=265
                        self.y_offset=80
                    else:
                        self.y_offset+=30

        self.std_panel.set_dimensions((WIDTH*0.6, self.panel_height+200))
            
        # validate button
        if self.count == self.step+1:
            self.next.hide()
            self.validate = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Terminer',
            size=(120,50)
            )

        if self.step-1 < 0:
            self.previous.hide()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                if self.data.standard_form:
                    self.window_manager.switch_to('attrib_crs')
                else:
                    self.window_manager.switch_to('attrib3')

            if self.count == self.step+1:
                if event.ui_element == self.validate:
                    self.window_manager.switch_to('attrib5')

            if event.ui_element == self.next:
                if self.step+1 < len(self.data_weights):
                    self.step+=1
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)

            if event.ui_element == self.previous:
                if self.step-1 >= 0:
                    self.step-=1
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in self.data.weights_ddm_dict:
                weight = event.text
                if weight == "0":
                    w=0
                elif weight == "1":
                    w=1
                elif weight == "2":
                    w=2
                elif weight == "3":
                    w=3
                elif weight == "4":
                    w=4
                elif weight == "5":
                    w=5
                
                layer = self.data.weights_ddm_dict[event.ui_element][1]
                col = self.data.weights_ddm_dict[event.ui_element][0]

                self.data.correspond_weights[layer][col] = w
                print(self.data.correspond_weights)

                

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.main_title.set_position((self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20))
        self.std_panel.set_dimensions((width*0.6, self.panel_height+200))
        self.std_panel.set_position((width*0.2, 200))
        self.next.set_position((width/2+100, 140))
        self.previous.set_position((width/2-230, 140))
        if self.i == self.step:
            self.layer_title.set_relative_position((20, 20))
            self.count_label.set_position((width/2-70, 150))
        if self.count == self.step+1:
            self.validate.set_position((width/2+100, 140))

class AttribWindow5(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.logo_image = self.display_logo()
        self.cancel = self.cancel_button()
        self.back = self.back_button()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic attributaire'
        )

        # import enums
        self.import_enum = self.create_button(
            topleft=(WIDTH/2-300, HEIGHT/2-100),
            objectid="#import_topo_data_button",
            text="importez vos énumérations",
            size=(600, 200)
        )

    def load_enum(self):
        self.data.load_enum_data()
        self.window_manager.set_enum_loading_complete()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                if self.data.standard_form:      
                    self.window_manager.switch_to('attrib_crs')
                else:
                    self.window_manager.switch_to('attrib3')

            if event.ui_element == self.import_enum:
                self.window_manager.start_animation()
                threading.Thread(target=self.load_enum).start()
                

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.import_enum.set_position((width/2-300, height/2-100))

class AttribWindow6(BaseWindow):
    step = 0
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.logo_image = self.display_logo()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.i = None
        self.label_list = []

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic attributaire'
        )

        self.panel_height = 20

        self.std_panel = self.create_panel(
            topleft=(WIDTH*0.2, 200),
            size=(WIDTH*0.6, self.panel_height),
            objectid="#std_panel"
        )

        self.tooltip, self.tooltip_label = self.create_tooltip(
            objectid_panel="#tooltip_panel",
            objectid_label="#tooltip_label",
            container=self.std_panel
        )

        # next / previous
        self.next = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Suivant',
            size=(120,50)
        )
        self.previous = self.create_button(
            topleft=(WIDTH/2-230, 140),
            objectid="#back_button",
            text='Précédent',
            size=(120,50)
        )

        self.x_offset = 20
        self.y_offset = 20

        # correspondance enum / fields
        if self.data.standard_form:
            self.data_enum_temp = self.data.attrib_initial_dataset
            self.data_enum = {}
            for layer_name in self.data_enum_temp:
                if self.data_enum_temp[layer_name][0].geom_type[0] in ['MultiLineString', 'LineString', 'MultiPoint', 'Point']:
                    self.data_enum[layer_name] = self.data_enum_temp[layer_name][0]
            self.data.new_dataset = self.data_enum
        else:

            self.data_enum = self.data.new_dataset
        self.count = len(self.data_enum)
        for i, layer_name in enumerate(self.data_enum):
            cols = self.data_enum[layer_name].columns

            if i == self.step:
                self.i = i
                # count label
                self.count_label = self.create_label(
                    topleft=(WIDTH/2-70, 150),
                    objectid="#count_label",
                    text=f"Couche {self.step+1} / {self.count}",
                )

                # nom de la couche
                self.layer_title = self.create_label(
                    topleft=(20, self.y_offset),
                    objectid="#label_std",
                    text=f'{layer_name}',
                    container=self.std_panel
                )
                self.y_offset+=60

                for col in cols:
                    if any(self.data_enum[layer_name][col]) and not col.endswith('_KEEP_FIELD') and col != 'geometry' and self.data_enum[layer_name][col].dtype in ['string', 'object']:
                        label = self.create_label(
                            topleft=(self.x_offset, self.y_offset),
                            objectid="#label_col_std",
                            text=f'{col}',
                            container=self.std_panel
                        )
                        self.label_list.append(label)

                        self.create_drop_down_menu_topo(
                            file_name=layer_name,
                            options=[enum[1] for enum in self.data.enum_list],
                            pos_x=self.x_offset + 100,
                            pos_y=self.y_offset,
                            width=300,
                            height=30,
                            data_info=col,
                            dict=self.data.ddm_dict_enum,
                            container=self.std_panel
                        )

                        self.y_offset+=60
                        self.panel_height = max(self.y_offset, self.panel_height)

        self.std_panel.set_dimensions((WIDTH*0.6, self.panel_height+200))
            
        # validate button
        if self.count == self.step+1:
            self.next.hide()
            self.validate = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Terminer',
            size=(120,50)
            )

        if self.step-1 < 0:
            self.previous.hide()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                if self.data.standard_form:
                    self.window_manager.switch_to('attrib5')
                else:
                    self.window_manager.switch_to('attrib3')

            if self.count == self.step+1:
                if event.ui_element == self.validate:
                    self.window_manager.switch_to('attrib7')

            if event.ui_element == self.next:
                if self.step+1 < len(self.data_enum):
                    self.step+=1
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)

            if event.ui_element == self.previous:
                if self.step-1 >= 0:
                    self.step-=1
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in self.data.ddm_dict_enum:
                new_field_name = event.text
                layer = self.data.ddm_dict_enum[event.ui_element][1]
                field_name = self.data.ddm_dict_enum[event.ui_element][0]
                if layer in self.data.correspond_enum:
                    # Check if field_name already exists
                    field_found = False
                    for i, pair in enumerate(self.data.correspond_enum[layer]):
                        if pair[0] == field_name:
                            self.data.correspond_enum[layer][i][1] = new_field_name
                            field_found = True
                            break
                    if not field_found:
                        self.data.correspond_enum[layer].append([field_name, new_field_name])
                else:
                    self.data.correspond_enum[layer] = [[field_name, new_field_name]]
                

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.main_title.set_position((self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20))
        self.std_panel.set_dimensions((width*0.6, self.panel_height+200))
        self.std_panel.set_position((width*0.2, 200))
        self.next.set_position((width/2+100, 140))
        self.previous.set_position((width/2-230, 140))
        if self.i == self.step:
            self.layer_title.set_relative_position((20, 20))
            self.count_label.set_position((width/2-70, 150))
        if self.count == self.step+1:
            self.validate.set_position((width/2+100, 140))


class AttribWindow7(BaseWindow):
    step = 0
    step_value = 0
    step_count = 0
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()

    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.logo_image = self.display_logo()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.i = None
        self.j = None
        self.length = None
        self.label_list = []

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic attributaire'
        )

        self.panel_height = 20

        self.std_panel = self.create_panel(
            topleft=(WIDTH*0.2, 200),
            size=(WIDTH*0.6, self.panel_height),
            objectid="#std_panel"
        )

        self.tooltip, self.tooltip_label = self.create_tooltip(
            objectid_panel="#tooltip_panel",
            objectid_label="#tooltip_label",
            container=self.std_panel
        )

        # next / previous
        self.next = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Suivant',
            size=(120,50)
        )
        self.previous = self.create_button(
            topleft=(WIDTH/2-230, 140),
            objectid="#back_button",
            text='Précédent',
            size=(120,50)
        )

        self.x_offset = 20
        self.y_offset = 20

        # prendre les bonnes données en fonction de standard_form
        if self.data.standard_form:
            self.data_enum_temp = self.data.attrib_initial_dataset
            self.data_enum = {}
            for layer_name in self.data_enum_temp:
                if self.data_enum_temp[layer_name][0].geom_type[0] in ['MultiLineString', 'LineString', 'MultiPoint', 'Point']:
                    self.data_enum[layer_name] = self.data_enum_temp[layer_name][0]
            # self.data.new_dataset = self.data_enum
        else:
            self.data_enum = self.data.new_dataset

        self.data.correspond_enum = self.data.filter_none(self.data.correspond_enum)

        # ajouter les layers manquantes à correspond enum
        for layer_name in self.data_enum:
            if layer_name not in self.data.correspond_enum:
                self.data.correspond_enum[layer_name] = []

        # compter le nombre de colonnes à faire et mettre en forme le dataset que l'on veut tester
        self.data_enum_col = {}
        self.count = 0
        for layer_name in self.data_enum:
            cols_to_keep = []
            for col in self.data_enum[layer_name].columns:
                if layer_name in self.data.correspond_enum:
                    if col in [col_enum[0] for col_enum in self.data.correspond_enum[layer_name]]:
                        self.count+=1
                        cols_to_keep.append(col)

                if any(self.data_enum[layer_name][col]) and len(self.data_enum[layer_name][col].unique().tolist()) < 40 and self.data_enum[layer_name][col].dtype in ['string', 'object']:
                    if col not in cols_to_keep:
                        self.count+=1
                        cols_to_keep.append(col)

            self.data_enum_col[layer_name] = self.data_enum[layer_name][cols_to_keep]

        if len(self.data_enum_col) > 0 and self.step+1<=len(self.data_enum_col):
            self.key = list(self.data_enum_col.keys())[self.step]
            if self.step>0:
                self.previous_key = list(self.data_enum_col.keys())[self.step-1]

        # for layer_name in self.data_enum_col:
        #     print(f'{layer_name} : {self.data_enum_col[layer_name].columns}')
        
        for i, layer_name in enumerate(self.data_enum_col):
            self.length = len(self.data_enum_col[layer_name].columns)-1 # -1 pour enlever la géométrie
            if i == self.step:
                self.i = i
                for j, col in enumerate(self.data_enum_col[layer_name].columns):
                    print(f' test colonne : {col}')
                    if j == self.step_value:
                        print(f'layer : {layer_name}\ncol : {col}')
                        self.title_label = self.create_label(
                            topleft=(20, self.y_offset),
                            objectid="#label_std",
                            text=f'{layer_name} : {col}',
                            container=self.std_panel
                        )
                        self.y_offset+=60
                        if col in [col_enum[0] for col_enum in self.data.correspond_enum[layer_name]]:
                            csv_file = [col_enum[1] for col_enum in self.data.correspond_enum[layer_name] if col_enum[0] == col]
                            csv_file = csv_file[0]
                            full_path = self.data.files_csv[0]
                            folder = os.path.dirname(full_path)
                            df = pd.read_csv(os.path.join(folder, csv_file), header=None)
                            values = df[0].dropna().to_list()
                        else:
                            values = []
                        other_values = list(self.data_enum_col[layer_name][col].dropna().unique())
                        print(f"values : {values}\nother_values : {other_values}\nvalues+other_values : {['None', 'INDETERMINE', 'AUTRE']+values+other_values}")
                        # valeurs uniques
                        for k, value in enumerate(self.data_enum_col[layer_name][col].dropna().unique().tolist()):

                            self.create_label(
                                topleft=(self.x_offset, self.y_offset),
                                objectid='#label_col_std',
                                text=f'{value}',
                                container=self.std_panel
                            )
                            self.create_drop_down_menu_value(
                                file_name=layer_name,
                                options=values+["----------------"]+other_values,
                                pos_x=self.x_offset+200,
                                pos_y=self.y_offset,
                                width=200,
                                height=30,
                                value=value,
                                col=col,
                                dict=self.data.ddm_dict_value,
                                container=self.std_panel
                            )

                            if k%15 == 0 and k != 0:
                                self.x_offset+=375
                                self.y_offset=80
                            else:
                                self.y_offset+=40

                            self.panel_height = max(self.y_offset, self.panel_height)

        self.std_panel.set_dimensions((WIDTH*0.6, self.panel_height+200))

        
        self.count_label = self.create_label(
            topleft=(WIDTH/2-70, 150),
            objectid="#count_label",
            text=f"Champ {self.step_count+1} / {self.count}",
        )


            
        # validate button
        if self.count == self.step_count+1:
            self.next.hide()
            self.validate = self.create_button(
            topleft=(WIDTH/2+100, 140),
            objectid="#back_button",
            text='Terminer',
            size=(120,50)
            )

        if self.step_count-1 < 0:
            self.previous.hide()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to('attrib6')

            if self.count == self.step_count+1:
                if event.ui_element == self.validate:
                    self.window_manager.switch_to('attrib8')


            if event.ui_element == self.next:
                self.step_count+=1
                if self.step_value+1 <= len(self.data_enum_col[self.key].columns)-1:
                    self.step_value+=1
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)
                else:
                    if self.step+1 <= len(self.data_enum_col):
                        self.step+=1
                        self.step_value=0
                        self.initialize()
                        self.window_manager.resize(self.screen.width, self.screen.height)
                

                print(f'step : {self.step}\nstep value : {self.step_value}\nlen : {len(self.data_enum_col)}\n longueur valeurs : {self.length}')


            if event.ui_element == self.previous:
                self.step_count-=1
                if self.step_value-1 >= 0:
                    self.step_value-=1
                    self.initialize()
                    self.window_manager.resize(self.screen.width, self.screen.height)
                else:
                    if self.step-1 >= 0:
                        self.step-=1
                        self.step_value = len(self.data_enum_col[self.previous_key].columns)-1
                        self.initialize()
                        self.window_manager.resize(self.screen.width, self.screen.height)

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in self.data.ddm_dict_value:
                new_value = event.text
                col = self.data.ddm_dict_value[event.ui_element][0]
                value = self.data.ddm_dict_value[event.ui_element][1]
                layer_name = self.data.ddm_dict_value[event.ui_element][2]
                
                print(f"Dropdown changed: new_value={new_value}, col={col}, value={value}, layer_name={layer_name}")

                # Check if layer_name exists in correspond_enum
                if layer_name in self.data.correspond_value:
                    # Check if col exists in the layer
                    if col in self.data.correspond_value[layer_name]:
                        # Update the existing value
                        updated = False
                        for item in self.data.correspond_value[layer_name][col]:
                            if item[0] == value:
                                item[1] = new_value
                                updated = True
                                print(f"Updated existing value for layer '{layer_name}', column '{col}': {self.data.correspond_value[layer_name][col]}")
                                break
                        # If value not found, append the new pair
                        if not updated:
                            self.data.correspond_value[layer_name][col].append([value, new_value])
                            print(f"Appended new value for layer '{layer_name}', column '{col}': {self.data.correspond_value[layer_name][col]}")
                    else:
                        # Add new col with the value
                        self.data.correspond_value[layer_name][col] = [[value, new_value]]
                        print(f"Added new column for layer '{layer_name}': {self.data.correspond_value[layer_name]}")
                else:
                    # Add new layer with the col and value
                    self.data.correspond_value[layer_name] = {col: [[value, new_value]]}
                    print(f"Added new layer '{layer_name}': {self.data.correspond_value[layer_name]}")
                

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.logo_image.set_position((50,50))
        self.main_title.set_position((self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20))
        self.std_panel.set_dimensions((width*0.6, self.panel_height+200))
        self.std_panel.set_position((width*0.2, 200))
        self.next.set_position((width/2+100, 140))
        self.previous.set_position((width/2-230, 140))
        if self.i == self.step:
            self.count_label.set_position((width/2-70, 150))
        if self.count == self.step_count+1:
            self.validate.set_position((width/2+100, 140))

class AttribWindow8(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()
        
    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.logo_image = self.display_logo()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Attributaire'
        )

        # import data label
        self.import_topo_data_button = self.create_button(
            topleft=(WIDTH/2-325, HEIGHT/2-100),
            objectid="#import_topo_data_button",
            text="Lancer le diagnostic attributaire",
            size=(650, 200)
        )

    def launch_diag_attrib(self):
        self.data.load_diag_attrib(self.window_manager.complete_path)
        self.window_manager.set_diag_attrib_complete()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("attrib7")
            if event.ui_element == self.import_topo_data_button:
                self.window_manager.start_animation()
                threading.Thread(target=self.launch_diag_attrib).start()

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.import_topo_data_button.set_position((width/2-325, height/2-100))

class AttribWindow9(BaseWindow):
    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()
        
    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()
        self.back = self.back_button()
        self.logo_image = self.display_logo()
        self.next = self.create_button(
            topleft=(self.back.rect.left, self.back.rect.bottom +10),
            objectid="#validate_standard",
            text="Suivant",
            size=(200, 50)
        )
        self.next.hide()

        # passer au diag topo
        if self.window_manager.complete_path:
            self.next.show()

        self.bars_to_draw = []

        percentage1 = 0
        percentage2 = 0

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Attributaire'
        )

        # display bars

        # diag1
        if self.data.indic_attrib1:
            percentage1 = round(self.data.indic_attrib1*100, 2)
            outline_params, fill_params = self.create_bar(50, 300, percentage1)
            self.bars_to_draw.append((outline_params, fill_params))

            self.label_percent = self.create_label(
                topleft=(50, 300-30),
                objectid="#label_percent",
                text=f'Diagnostic 1 : {percentage1}% de qualité attribuataire'
            )


        # carto button
        self.carto_button = self.create_button(
            topleft=(WIDTH/2+150, 320),
            objectid="#import_topo_data_button",
            text="Afficher la carte",
            size=(350, 200)
        )

    def display_map(self):
        self.data.make_attrib_map(
            self.data.diag_attrib_layer1,
            self.data.cols_values,
            self.data.cols_aliases,
            5
        )

        self.window_manager.set_load_attrib_map_complete()

    def draw(self):
        super().draw()
        for outline_params, fill_params in self.bars_to_draw:
            pygame.draw.rect(self.screen, *outline_params)
            pygame.draw.rect(self.screen, *fill_params)

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("attrib8")
            if event.ui_element == self.carto_button:
                self.window_manager.start_animation()
                threading.Thread(target=self.display_map).start()

            if self.window_manager.complete_path:
                if event.ui_element == self.next:
                    self.window_manager.switch_to('topo1')

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.carto_button.set_position((width/2+150, 320))
        if self.window_manager.complete_path:
            self.next.set_position((self.back.rect.left, self.back.rect.bottom +10))