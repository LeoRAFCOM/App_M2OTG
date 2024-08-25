import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from const import *

class BaseWindow:
    def __init__(self, manager, screen, data):
        self.manager = manager
        self.screen = screen
        self.data = data

        self.elements = []
        self.create_scrolling_container()

        # Logo
        self.logo = pygame.image.load('ASSETS/logo_RAFCOM_#fff3d1.png').convert_alpha()
        self.logo = pygame.transform.rotozoom(self.logo, angle=0, scale=0.20)

        self.points = pygame.image.load('ASSETS/points.png').convert_alpha()
        self.points = pygame.transform.rotozoom(self.points, angle=0, scale=0.03)

        self.lines = pygame.image.load('ASSETS/lines.png').convert_alpha()
        self.lines = pygame.transform.rotozoom(self.lines, angle=0, scale=0.03)

        self.polygon = pygame.image.load('ASSETS/polygon.png').convert_alpha()
        self.polygon = pygame.transform.rotozoom(self.polygon, angle=0, scale=0.03)

    def handle_event(self, event):
        pass

    # display images
    def display_logo(self):
        image = pygame_gui.elements.UIImage(
            relative_rect=((50,50), (self.logo.width, self.logo.height)),
            manager=self.manager,
            container=self.scroll_container,
            image_surface=self.logo
        )
        self.elements.append(image)
        return image
    
    def display_picto_logo(self, topleft, image_surface, container='None'):
        if container == 'None':
            container = self.scroll_container
        image = pygame_gui.elements.UIImage(
            relative_rect=(topleft, (image_surface.width, image_surface.height)),
            image_surface=image_surface,
            manager=self.manager,
            container=container
        )
        self.elements.append(image)
        return image

    # containers
    def create_scrolling_container(self):
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect((0, 0), (WIDTH, HEIGHT)),
            manager=self.manager,
            allow_scroll_x=False,
            allow_scroll_y=True,
            should_grow_automatically=True,
            object_id='#scrolling_container'
        )
        self.elements.append(self.scroll_container)

    def create_panel(self, topleft, size, objectid, container='None'):
        if container == 'None':
            container = self.scroll_container
        panel = pygame_gui.elements.UIPanel(
            relative_rect=(topleft, size),
            manager=self.manager,
            container=container,
            object_id=ObjectID(class_id="@all_panels",
                               object_id=objectid)
        )
        self.elements.append(panel)
        return panel

    # buttons
    def create_button(self, topleft, objectid, text, size=(-1,-1)):
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(topleft, size),
            text=text,
            manager=self.manager,
            container=self.scroll_container,
            object_id=ObjectID(class_id="@all_buttons",
                               object_id=objectid)
        )
        self.elements.append(button)
        return button
    
    def cancel_button(self):
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH - 120, 20), (100,50)),
            text="Annuler",
            manager=self.manager,
            container=self.scroll_container,
            object_id=ObjectID(class_id="@all_buttons",
                               object_id="#cancel_button")
        )
        self.elements.append(button)
        return button
    
    def back_button(self):
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((WIDTH - 220, 20), (100,50)),
            text="Retour",
            manager=self.manager,
            container=self.scroll_container,
            object_id=ObjectID(class_id="@all_buttons",
                               object_id="#back_button")
        )
        self.elements.append(button)
        return button
    
    # labels
    def create_label(self, topleft, objectid, text, size=(-1,-1), class_id="@aal_labels", container='None'):
        if container == 'None':
            container = self.scroll_container
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(topleft, size),
            text=text,
            manager=self.manager,
            container=container,
            object_id=ObjectID(class_id=class_id,
                               object_id=objectid)
        )
        self.elements.append(label)
        return label
    
    def create_error1_label(self, topleft=(WIDTH/2-190, HEIGHT-200), objectid=("#error1_label"), text="Vous n'avez importé aucune donnée valide", size=(-1,-1), class_id="@error_labels", container='None'):
        if container == 'None':
            container = self.scroll_container
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(topleft, size),
            text=text,
            manager=self.manager,
            container = container,
            object_id=ObjectID(class_id=class_id,
                               object_id=objectid)
        )
        self.elements.append(label)
        return label

    # epsg entries
    def create_text_entry(self, topleft, size, text, objectid):
        entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(topleft, size),
            manager=self.manager,
            container = self.scroll_container,
            placeholder_text=text,
            object_id=ObjectID(class_id="@all_entries",
                               object_id=objectid)
        )
        self.elements.append(entry)
        return entry
    
    def update_tooltip(self, mouse_pos, data):
        # Initializing tooltip as a panel with a label inside
        tooltip_text = None
        for group in data:
            file_name = group
            for label in self.tooltip_elements:
                if label.rect.collidepoint(mouse_pos):
                    column_name = label.text
                    # print(f'file name : {file_name}')
                    # print(f"Hovering over: {column_name}")  # Debugging: print column name
                    for group in data:
                        for data_info in data[group]:
                            gdf = data_info[0]
                            if column_name in gdf.columns and file_name == group:
                                column_data = gdf[column_name].astype(str)
                                tooltip_text = '\n'.join(column_data[:20])
                                break  # Exit loop once the column data is found
                    break

        if tooltip_text:
            self.tooltip.set_position((mouse_pos[0], mouse_pos[1]))
            self.tooltip.set_dimensions((200, 205))
            self.tooltip_label.set_text(tooltip_text)
            self.tooltip.show()
        else:
            self.tooltip.hide()

    def update(self, dt):
        self.manager.update(dt)

    def draw(self):
        self.screen.fill((25,25,25))
        self.manager.draw_ui(self.screen)

    def clear_elements(self):
        for element in self.elements:
            element.kill()
        self.elements.clear()

    def resize(self, width, height):
        self.scroll_container.set_dimensions((width, height))
        self.reposition_elements(width, height)
        self.manager.set_window_resolution((width, height))

    def reposition_elements(self, width, height):
        pass

    def create_drop_down_menu_topo(self, file_name, options, pos_x, pos_y, width, height, data_info, dict, container, placeholder = 'None'):
        ddm = pygame_gui.elements.UIDropDownMenu(
            options_list=['None']+options,
            starting_option=placeholder,
            relative_rect=pygame.Rect((pos_x, pos_y), (width, height)),
            manager=self.manager,
            object_id=ObjectID(class_id='@drop_down_menu_topo', object_id=f'ddm_{file_name}'),
            container=container
        )
        dict[ddm] = [data_info, file_name]
        self.elements.append(ddm)
        return ddm
    
    def create_drop_down_menu_attrib(self, file_name, options, pos_x, pos_y, width, height, data_info, dict, container):
        ddm = pygame_gui.elements.UIDropDownMenu(
            options_list=['None', 'KEEP_FIELD']+options,
            starting_option='None',
            relative_rect=pygame.Rect((pos_x, pos_y), (width, height)),
            manager=self.manager,
            object_id=ObjectID(class_id='@drop_down_menu_topo', object_id=f'ddm_{file_name}'),
            container=container
        )
        dict[ddm] = [data_info, file_name]
        self.elements.append(ddm)
        return ddm
    
    def create_bar(self, posx, posy, percentage):
        outline_color = (255, 243, 209)
        if percentage <= 20:
            fill_color = (215, 25, 28)
        elif percentage <= 40:
            fill_color = (253, 174, 97)
        elif percentage <= 60:
            fill_color = (255, 255, 191)
        elif percentage <= 80:
            fill_color = (166, 217, 106)
        else:
            fill_color = (26, 150, 65)

        outline_rect = (outline_color, (posx, posy, 500, 50), 2)
        fill_rect = (fill_color, (posx + 5, posy + 5, 500 * (percentage / 100) - 10, 40))

        return outline_rect, fill_rect
    
    def create_binary_choice(self, posx, posy, size=(100,100)):
        choice1 = self.create_button(
            topleft=(posx, posy),
            objectid="#choice1_button",
            text="Oui",
            size=(size, size)
        )
        self.elements.append(choice1)
        choice2 = self.create_button(
            topleft=(posx+size + size*0.1, posy),
            objectid="#choice2_button",
            text="Non",
            size=(size, size)
        )
        self.elements.append(choice2)

        return choice1, choice2
    
    # tooltip
    def create_tooltip(self, objectid_panel, objectid_label, container):
        tooltip = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((0,0), (0,0)),
            manager=self.manager,
            starting_height=5,
            object_id=ObjectID(object_id=objectid_panel, class_id="@all_panels"),
            container = container
        )
        self.elements.append(tooltip)
        tooltip_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0,-190), (200, -1)),
            text="",
            manager=self.manager,
            container=tooltip,
            object_id=ObjectID(class_id="@all_labels", object_id=objectid_label)
        )
        self.elements.append(tooltip_label)

        tooltip.hide()

        return tooltip, tooltip_label
    
    def update_tooltip(self, mouse_pos, data, label_list, tooltip_panel, tooltip_label):
        tooltip_text = None
        column_name = None
        if label_list:
            for label in label_list:
                if label.rect.collidepoint(mouse_pos):
                    column_name = label.text
            
        if len(data) > 0 and column_name:
            column_data = data[column_name].astype(str)
            tooltip_text = '\n'.join(column_data[:20])

        if tooltip_text:
            tooltip_panel.set_position((mouse_pos[0], mouse_pos[1]))
            tooltip_panel.set_dimensions((200, 205))
            tooltip_label.set_text(tooltip_text)
            tooltip_panel.show()
        else:
            tooltip_panel.hide()

        
    def create_drop_down_menu_value(self, file_name, options, pos_x, pos_y, width, height, value, col, dict, container):
        ddm = pygame_gui.elements.UIDropDownMenu(
            options_list=['None', 'INDETERMINE', 'AUTRE']+options,
            starting_option='None',
            relative_rect=pygame.Rect((pos_x, pos_y), (width, height)),
            manager=self.manager,
            object_id=ObjectID(class_id='@drop_down_menu_topo', object_id=f'ddm_{file_name}'),
            container=container
        )
        dict[ddm] = [col, value, file_name]
        self.elements.append(ddm)
        return ddm