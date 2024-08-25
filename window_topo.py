import pygame
import pygame.locals
import pygame_gui
from pygame_gui.core import ObjectID
import numpy as np

from window_base import BaseWindow
from const import *
import threading

class TopoWindow(BaseWindow):

    def __init__(self, manager, screen, data, window_manager):
        super().__init__(manager, screen, data)
        self.window_manager = window_manager
        self.initialize()
        
    def initialize(self):
        self.clear_elements()
        self.create_scrolling_container()
        self.cancel = self.cancel_button()
        self.logo_image = self.display_logo()

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Topologique'
        )

        # import data label
        self.import_topo_data_button = self.create_button(
            topleft=(WIDTH/2-250, HEIGHT/2-100),
            objectid="#import_topo_data_button",
            text="IMPORTEZ VOS COUCHES",
            size=(500, 200)
        )

    def load_topo_data(self):
        self.data.get_topo_data()
        self.window_manager.set_data_loading_complete()
    

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.import_topo_data_button:
                self.window_manager.start_animation()
                threading.Thread(target=self.load_topo_data).start()

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.import_topo_data_button.set_position((width/2-250, height/2-100))

class TopoWindow1(BaseWindow):
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
        print(self.data.topo_initial_dataset)

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Topologique'
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

        data = self.data.topo_initial_dataset
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

            self.create_drop_down_menu_topo(
                file_name=file,
                options=list(data_file.columns),
                pos_x=self.x_offset + 500,
                pos_y=self.y_offset + 190,
                width=200,
                height=45,
                data_info=data[file],
                dict=self.data.ddm_dict_topo,
                container=self.scroll_container
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
            else:
                pass #error


            self.y_offset+=50
        
        self.topo_overview_panel.set_dimensions((WIDTH-20, self.y_offset))

        # missing geoms
        if 'MultiLineString' not in geoms and 'LineString' not in geoms:
            self.missing_geoms.append('Linéaire')
        if 'MultiPoint' not in geoms and 'Point' not in geoms:
            self.missing_geoms.append('Ponctuel')
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

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("topo")
            if event.ui_element == self.validate_epsg_button:
                epsg = self.ask_epsg_entry.get_text()
                self.data.reproject_data(epsg)
                self.initialize()
                self.window_manager.resize(self.screen.width, self.screen.height)
            if event.ui_element == self.validate_unique_id and not self.missing_geoms:
                self.window_manager.switch_to('topo2')

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in self.data.ddm_dict_topo:
                selected_option = event.text
                data_info = self.data.ddm_dict_topo[event.ui_element][0]
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

        if self.missing_geoms:
            self.error_label.set_position((self.validate_unique_id.rect.left, self.validate_unique_id.rect.bottom + 30))
            self.error_label_geom.set_position((self.error_label.rect.left, self.error_label.rect.bottom + 10))

class TopoWindow2(BaseWindow):

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
        print(self.data.topo_initial_dataset)

        self.export = False

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Topologique'
        )

        # data summary
        self.y_offset = 20
        self.x_offset = 60
        self.topo_overview_panel = self.create_panel(
            topleft=(10,200),
            size=(WIDTH-10,self.y_offset),
            objectid='#topo_overview_panel'
        )

        data = self.data.topo_initial_dataset
        for file in data:
            data_file = data[file][0]
            geomtype = data[file][1]
            entities = data[file][2]
            crs = data[file][3]
            id_unique = data[file][5]

            self.create_label(
                topleft=(self.x_offset, self.y_offset),
                objectid=f'#{file}_label',
                text=file,
                class_id="@topo_overview_label",
                container=self.topo_overview_panel
            )

            if geomtype in ['MultiLineString', 'LineString']:
                self.display_picto_logo(
                    topleft=(self.x_offset-40, self.y_offset),
                    image_surface=self.lines,
                    container=self.topo_overview_panel
                )
            elif geomtype in ['MultiPoint', 'Point']:
                self.display_picto_logo(
                    topleft=(self.x_offset-40, self.y_offset),
                    image_surface=self.points,
                    container=self.topo_overview_panel
                )
            elif geomtype in ['MultiPolygon', 'Polygon']:
                self.display_picto_logo(
                    topleft=(self.x_offset-40, self.y_offset),
                    image_surface=self.polygon,
                    container=self.topo_overview_panel
                )
            else:
                pass #error

            self.x_offset+=500

            self.create_label(
                topleft=(self.x_offset, self.y_offset),
                objectid=f'#{file}_{entities}_label',
                text=f'entities:{entities} ',
                class_id="@topo_overview_label",
                container=self.topo_overview_panel
            )

            self.x_offset+=250

            self.create_label(
                topleft=(self.x_offset, self.y_offset),
                objectid=f'#{file}_{id_unique}_label',
                text=f'key:{id_unique}',
                class_id="@topo_overview_label",
                container=self.topo_overview_panel
            )

            self.x_offset+=250

            self.create_label(
                topleft=(self.x_offset, self.y_offset),
                objectid=f'#{file}_crs_label',
                text=f'{crs}',
                class_id="@topo_overview_label",
                container=self.topo_overview_panel
            )
            self.y_offset+=50
            self.x_offset=60

        self.topo_overview_panel.set_dimensions((WIDTH-20, self.y_offset))

        # diag topo button
        self.diag_topo = self.create_button(
            topleft=(WIDTH/2-350, self.topo_overview_panel.rect.bottom+20),
            objectid="#diag_topo_button",
            text="LANCER LE DIAGNOSTIC TOPOLOGIQUE",
            size=(700, 180)
        )

        # export files or not
        
        self.label_export = self.create_label(
            topleft=(WIDTH/2-350, self.diag_topo.rect.bottom + 40),
            objectid="#export_or_not_label",
            text="Souhaitez-vous exporter les données du diagnostic ?",

        )

        self.choice1, self.choice2 = self.create_binary_choice(
            posx =self.label_export.rect.right + 10,
            posy=self.diag_topo.rect.bottom + 10,
            size=75
        )

        self.choice2.select()

    def load_diag_topo(self):
        print(self.data.topo_initial_dataset)
        self.data.diag_topo(self.data.topo_initial_dataset, self.export)
        self.window_manager.set_diag_topo_loading_complete()

    def draw(self):
        super().draw()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("topo1")
            if event.ui_element == self.diag_topo:
                self.window_manager.start_animation()
                threading.Thread(target=self.load_diag_topo).start()

            #binary_choice
            if event.ui_element == self.choice1:
                self.choice1.select()
                self.choice2.unselect()
                self.export = True
            if event.ui_element == self.choice2:
                self.choice2.select()
                self.choice1.unselect()
                self.export = False

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        self.topo_overview_panel.set_dimensions((width-20, self.y_offset))
        self.diag_topo.set_position((width/2-350, self.topo_overview_panel.rect.bottom+20))
        self.label_export.set_position((width/2-350, self.diag_topo.rect.bottom + 40))
        self.choice1.set_position((self.label_export.rect.right + 10, self.diag_topo.rect.bottom + 10))
        self.choice2.set_position((self.label_export.rect.right + 10+75+75*0.1, self.diag_topo.rect.bottom + 10))

class TopoWindow3(BaseWindow):
    correction_complete = False
    display_label = False
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

        # map
        self.overlay_data = None
        self.overlay_id = None
        self.map_type = None

        # title text
        self.main_title = self.create_label(
            topleft=(self.logo.get_frect().midright[0] + 100, self.logo.get_frect().centery + 20),
            objectid="#main_title",
            text='Diagnostic Topologique'
        )

        self.correction_button = self.create_button(
            topleft=(WIDTH-500, HEIGHT/2+50),
            objectid="#import_topo_data_button",
            text="Lancer les corrections",
            size=(450, 200)
        )

        self.map_indic_button = self.create_button(
            topleft=(WIDTH-500, 320),
            objectid="#map_button",
            text="",
            size=(50,50)
        )

        self.indic_panel = self.create_panel(
            topleft=(WIDTH-500,210),
            size=(450,100),
            objectid="#indic_panel"
        )

        # display bars
        self.percentages = []
        for i, gdf in enumerate(self.data.data_list_carto_topo):
            y_offset = 250 + i * 125  # Adjust y_offset for each bar
            if i == 1:
                percentage = (gdf[gdf['typo_can'].isin(["00", "03"])].shape[0] / gdf.shape[0]) * 100
            else:
                percentage = (gdf[gdf['RELIE'] == 1].shape[0] / gdf.shape[0]) * 100
            percentage = round(percentage, 1)
            self.percentages.append(percentage)
            outline_params, fill_params = self.create_bar(50, y_offset, percentage)
            self.bars_to_draw.append((outline_params, fill_params))

            if i == 0:
                text_percent = f"{percentage}% d'ouvrages reliés"
            elif i ==1:
                text_percent = f"{percentage}% de canalisations sans ouvrage manquant"
            elif i ==2:
                text_percent = f"{percentage}% de canalisations reliées"
            elif i ==3:
                text_percent = f"{percentage}% de réseaux sans ilots de canalisations non reliés"
            else:
                text_percent = 'error'

            self.label_percent = self.create_label(
                topleft=(50, y_offset-30),
                objectid="#label_percent",
                text=text_percent
            )

        self.map_button1 = self.create_button(
            topleft=(500 + 75, 250),
            objectid="#map_button",
            text="",
            size=(50,50)
        )

        self.map_button2 = self.create_button(
            topleft=(500 + 75, 375),
            objectid="#map_button",
            text="",
            size=(50,50)
        )

        self.map_button3 = self.create_button(
            topleft=(500 + 75, 500),
            objectid="#map_button",
            text="",
            size=(50,50)        
            )

        self.map_button4 = self.create_button(
            topleft=(500 + 75, 625),
            objectid="#map_button",
            text="",
            size=(50,50)        
            )

        indic_topo = round(np.mean(self.percentages), 1)
        self.data.indic_topo = indic_topo/100

        if indic_topo <= 20:
            self.indic_topo_label = self.create_label(
            topleft=(10,30),
            objectid="#indic_topo_label20",
            text=f"Qualité topologique : {indic_topo}%",
            container=self.indic_panel
        )
        elif indic_topo <= 40:
            self.indic_topo_label = self.create_label(
            topleft=(10,30),
            objectid="#indic_topo_label40",
            text=f"Qualité topologique : {indic_topo}%",
            container=self.indic_panel
        )
        elif indic_topo <= 60:
            self.indic_topo_label = self.create_label(
            topleft=(10,30),
            objectid="#indic_topo_label60",
            text=f"Qualité topologique : {indic_topo}%",
            container=self.indic_panel
        )
        elif indic_topo <= 80:
            self.indic_topo_label = self.create_label(
            topleft=(10,30),
            objectid="#indic_topo_label80",
            text=f"Qualité topologique : {indic_topo}%",
            container=self.indic_panel
        )
        else:
            self.indic_topo_label = self.create_label(
            topleft=(10,30),
            objectid="#indic_topo_label100",
            text=f"Qualité topologique : {indic_topo}%",
            container=self.indic_panel
        )


    def display_correction_label(self):

        self.data.correction_topo(self.data.topo_initial_dataset, complete=self.window_manager.complete_path)

        self.correction_complete = True
        self.display_label = True

        if self.data.corrected_points > 0:
            self.correction_label = self.create_label(
                topleft=(WIDTH-500, HEIGHT/2+275),
                objectid="#correction_label_plus",
                text=f"{self.data.corrected_points} / {self.data.non_relie_points} ouvrages ont été corrigés"
            )
        else:
            self.correction_label = self.create_label(
                topleft=(WIDTH-500, HEIGHT/2+275),
                objectid="#correction_label_moins",
                text=f"Aucun noeud n'a été corrigé automatiquement"
            )

    def draw(self):
        super().draw()
        for outline_params, fill_params in self.bars_to_draw:
            pygame.draw.rect(self.screen, *outline_params)
            pygame.draw.rect(self.screen, *fill_params)

        if self.correction_complete:
            self.correction_complete = False
            self.window_manager.stop_animation()
            
    def load_map1(self, insee_col, insee_alias, cell_col, cell_alias, typo_flag = 0, overlay = True):
        self.data.make_map(
            center=self.data.center,
            gdf_cell=self.data.gdf_cell,
            gdf_insee=self.data.gdf_insee,
            overlay_data=self.overlay_data,
            overlay_id=self.overlay_id,
            values_column_insee=insee_col,
            aliases_insee=insee_alias,
            values_column_cell=cell_col,
            aliases_cell=cell_alias,
            num_classes=5,
            layer_type=self.map_type,
            typo_flag=typo_flag,
            overlay=overlay
        )
        self.window_manager.set_map_loading_complete()
        

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.cancel:
                self.window_manager.switch_to("main")
            if event.ui_element == self.back:
                self.window_manager.switch_to("topo2")

            if event.ui_element == self.correction_button:
                self.window_manager.start_animation()
                threading.Thread(target=self.display_correction_label).start()

            if self.window_manager.complete_path:
                if event.ui_element == self.next:
                    self.window_manager.switch_to('complet')

            # map buttons
            if event.ui_element == self.map_button1:

                self.overlay_data = self.data.gdf_points
                self.overlay_id = 'point_id'
                self.map_type = 'point'

                insee_col = [
                    'points_relie_indic_compo_by_code_insee',
                    'points_relie_percentage_0_by_code_insee',
                    'points_relie_total_points_by_code_insee',
                    'points_relie_count_0_by_code_insee',
                    self.data.dataset['Polygon'][0][6]
                ]

                insee_alias = [
                    'Indicateur composite des points non reliés :',
                    'Part des points non reliés :',
                    'Nombre total de points :',
                    'Nombre de points non reliés :',
                    'Code INSEE :'
                ]

                cell_col = [
                    'points_relie_indic_compo_by_cell_id',
                    'points_relie_percentage_0_by_cell_id',
                    'points_relie_total_points_by_cell_id',
                    'points_relie_count_0_by_cell_id',
                    'cell_id'
                ]

                cell_alias = [
                    'Indicateur composite des points non reliés :',
                    'Part des points non reliés :',
                    'Nombre total de points :',
                    'Nombre de points non reliés :',
                    'Identifiant de cellule :'
                ]
                self.window_manager.start_animation()
                threading.Thread(target=self.load_map1, args=(insee_col, insee_alias, cell_col, cell_alias)).start()

            if event.ui_element == self.map_button2:

                self.overlay_data = self.data.gdf_lines
                self.overlay_id = 'line_id'
                self.map_type = 'line'

                insee_col = [
                        'lines_relie_indic_compo_by_code_insee',
                        'lines_relie_percentage_0_by_code_insee',
                        'lines_relie_total_points_by_code_insee',
                        'lines_relie_count_0_by_code_insee',
                        self.data.dataset['Polygon'][0][6]
                ]

                insee_alias = [
                    'Indicateur composite des extrémités sans ouvrages :',
                    'Part des extrémités sans ouvrages :',
                    'Nombre total des extrémités :',
                    "Nombre d'extrémités sans ouvrages :",
                    'Code INSEE :'
                ]

                cell_col = [
                    'lines_relie_indic_compo_by_cell_id',
                    'lines_relie_percentage_0_by_cell_id',
                    'lines_relie_total_points_by_cell_id',
                    'lines_relie_count_0_by_cell_id',
                    'cell_id'
                ]

                cell_alias = [
                    'Indicateur composite des extrémités sans ouvrages :',
                    'Part des extrémités sans ouvrages :',
                    'Nombre total des extrémités :',
                    "Nombre d'extrémités sans ouvrages :",
                    'Identifiant de cellule :'
                ]

                self.window_manager.start_animation()
                threading.Thread(target=self.load_map1, args=(insee_col, insee_alias, cell_col, cell_alias), kwargs={'typo_flag':1}).start()

            if event.ui_element == self.map_button3:

                self.overlay_data = self.data.gdf_can
                self.overlay_id = 'line_id'
                self.map_type = 'line'

                insee_col = [
                            'canalisation_relie_indic_compo_by_code_insee',
                            'canalisation_relie_percentage_0_by_code_insee',
                            'canalisation_relie_total_points_by_code_insee',
                            'canalisation_relie_count_0_by_code_insee',
                            self.data.dataset['Polygon'][0][6]
                ]

                insee_alias = [
                    'Indicateur composite des canalisations non reliées :',
                    'Part des canalisations non reliées :',
                    'Nombre total des canalisations non reliées :',
                    "Nombre de canalisations non reliées :",
                    'Code INSEE :'
                ]

                cell_col = [
                    'canalisation_relie_indic_compo_by_cell_id',
                    'canalisation_relie_percentage_0_by_cell_id',
                    'canalisation_relie_total_points_by_cell_id',
                    'canalisation_relie_count_0_by_cell_id',
                    'cell_id'
                ]

                cell_alias = [
                    'Indicateur composite des canalisations non reliées :',
                    'Part des canalisations non reliées :',
                    'Nombre total des canalisations non reliées :',
                    "Nombre de canalisations non reliées :",
                    'Identifiant de cellule :'
                ]
                self.window_manager.start_animation()
                threading.Thread(target=self.load_map1, args=(insee_col, insee_alias, cell_col, cell_alias)).start()
            if event.ui_element == self.map_button4:

                self.overlay_data = self.data.gdf_ilots
                self.overlay_id = 'line_id'
                self.map_type = 'line'

                insee_col = [
                    'ilots_indic_compo_by_code_insee',
                    'ilots_percentage_0_by_code_insee',
                    'ilots_total_points_by_code_insee',
                    'ilots_count_0_by_code_insee',
                    self.data.dataset['Polygon'][0][6]
                ]

                insee_alias = [
                    'Indicateur composite des îlots de canalisations non reliées :',
                    'Part des îlots de canalisations non reliées :',
                    'Nombre total des îlots de canalisations non reliées :',
                    "Nombre d'îlots de canalisations non reliées :",
                    'Code INSEE :'
                ]

                cell_col = [
                    'ilots_indic_compo_by_cell_id',
                    'ilots_percentage_0_by_cell_id',
                    'ilots_total_points_by_cell_id',
                    'ilots_count_0_by_cell_id',
                    'cell_id'
                ]

                cell_alias = [
                    'Indicateur composite des îlots de canalisations non reliées :',
                    'Part des îlots de canalisations non reliées :',
                    'Nombre total des îlots de canalisations non reliées :',
                    "Nombre d'îlots de canalisations non reliées :",
                    'Identifiant de cellule :'
                ]
                self.window_manager.start_animation()
                threading.Thread(target=self.load_map1, args=(insee_col, insee_alias, cell_col, cell_alias)).start()

            if event.ui_element == self.map_indic_button:

                self.overlay_data = self.data.gdf_lines
                self.overlay_id = 'line_id'
                self.map_type = 'line'

                insee_col = [
                    'indic_synth_insee',
                    'points_relie_indic_compo_by_code_insee', 
                    'lines_relie_indic_compo_by_code_insee',
                    'canalisation_relie_indic_compo_by_code_insee',
                    'ilots_indic_compo_by_code_insee'
                ]

                insee_alias = [
                    'indic_synth_insee',
                    'points_relie_indic_compo_by_code_insee', 
                    'lines_relie_indic_compo_by_code_insee',
                    'canalisation_relie_indic_compo_by_code_insee',
                    'ilots_indic_compo_by_code_insee'
                ]

                cell_col = [
                    'indic_synth_cell',
                    'points_relie_indic_compo_by_cell_id', 
                    'lines_relie_indic_compo_by_cell_id',
                    'canalisation_relie_indic_compo_by_cell_id',
                    'ilots_indic_compo_by_cell_id'
                ]

                cell_alias = [
                    'indic_synth_cell',
                    'points_relie_indic_compo_by_cell_id', 
                    'lines_relie_indic_compo_by_cell_id',
                    'canalisation_relie_indic_compo_by_cell_id',
                    'ilots_indic_compo_by_cell_id'
                ]

                self.window_manager.start_animation()
                threading.Thread(target=self.load_map1, args=(insee_col, insee_alias, cell_col, cell_alias), kwargs={'typo_flag':1, 'overlay':False}).start()

    def reposition_elements(self, width, height):
        self.cancel.set_position((width - 120, 20))
        self.back.set_position((width - 220, 20))
        if self.window_manager.complete_path:
            self.next.set_position((self.back.rect.left, self.back.rect.bottom +10))