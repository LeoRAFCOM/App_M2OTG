from action import Action
import threading

class Data(Action):
    def __init__(self):
        super().__init__()
        # topo
        self.topo_initial_dataset = {}
        self.ddm_dict_topo = {}
        self.table_diag_topo = None
        self.data_list_carto_topo = []

        self.corrected_points = None
        self.non_relie_points = None

        # map data
        self.geodata = None
        self.gdf_cell = None
        self.gdf_insee = None
        self.gdf_points = None
        self.gdf_lines = None
        self.gdf_can = None
        self.gdf_ilots = None
        self.center = None
        self.indic_topo = None

        # attrib
        self.data_path = []
        self.files_csv = []
        self.standard_form = False
        self.standard = []
        self.attrib_initial_dataset = {}
        self.ddm_dict_attrib = {}
        self.correspond = {}
        self.new_dataset = {}
        self.enum_list = []
        self.ddm_dict_enum = {}
        self.correspond_enum = {}
        self.ddm_dict_value = {}
        self.correspond_value = {}

        self.ddm_dict_crs = {}

        self.weights_ddm_dict = {}
        self.correspond_weights = {}

        self.diag_attrib_layer1 = None
        self.diag_attrib_layer2 = None
        self.diag_attrib_layerdt = None
        self.indic_attrib1 = None
        self.indic_attrib2 = None
        self.cols_values = None

        self.cols_aliases = [
            "Identifiant du territoire : ",
            "Redondance globale d'identifiant unique : ",
            "Exhaustivité : ",
            "Exhaustivité sans les colonnes vides :",
            "Précision numérique : ",
            "Redondance sémantique : ",
            "Précision sémantique : ",
            "Précision syntaxique : ",
            "Indice de qualité attributaire :"
        ]
        

    def get_topo_data(self):
        files = self.get_file_path()
        self.topo_initial_dataset = self.load_files(files)

    def correction_topo(self, dataset, complete=False):
        self.corrected_points, self.non_relie_points =  super().correction_topo(dataset, complete)

    def load_enum_data(self):
        self.files_csv = self.get_file_path_csv()
        self.enum_list = self.load_csv_files(self.files_csv)

    def get_attrib_data(self):
        self.data_path = self.get_file_path()
        self.attrib_initial_dataset = self.load_files(self.data_path)

    def reproject_data(self, epsg):
        self.topo_initial_dataset = self.reproject(epsg, self.topo_initial_dataset)

    def reproject_data_attrib(self, epsg):
        self.attrib_initial_dataset = self.reproject(epsg, self.attrib_initial_dataset)

    def diag_topo(self, topo_initial_dataset, export):
        self.table_diag_topo = self.diag_ouvrage_relie(topo_initial_dataset, export)
        self.setup_map_data()

    def setup_map_data(self):
        self.data_list_carto_topo = self.list_carto_topo
        # initialisation des couches pour la carto
        self.geodata = self.table_diag_topo
        self.geodata = self.geodata.to_crs(4326)
        self.gdf_cell = self.geodata.dissolve(by='cell_id')
        self.gdf_cell = self.gdf_cell.reset_index()
        self.gdf_insee = self.geodata.dissolve(by=self.dataset['Polygon'][0][6])
        self.gdf_insee = self.gdf_insee.reset_index()

        geodata_point = self.list_carto_topo[0]
        self.gdf_points = geodata_point.to_crs(4326)

        geodata_lines = self.list_carto_topo[1]
        self.gdf_lines = geodata_lines.to_crs(4326)
        self.gdf_lines = self.gdf_lines.explode()

        geodata_can = self.list_carto_topo[2]
        self.gdf_can = geodata_can.to_crs(4326)
        self.gdf_can = self.gdf_can.explode()

        geodata_ilots = self.list_carto_topo[3]
        self.gdf_ilots = geodata_ilots.to_crs(4326)
        self.gdf_ilots = self.gdf_ilots.explode()

        self.center = [self.geodata.unary_union.convex_hull.centroid.y, self.geodata.unary_union.convex_hull.centroid.x]

    def get_standard(self, message='Sélectionnez le csv avec votre standard'):
        self.standard=  super().get_standard(message)
        

    def setup_standard_shape(self, correspond, dataset, standard):
        self.new_dataset =  super().setup_standard_shape(correspond, dataset, standard)

    def load_diag_attrib(self, complete):
        for layer_name in self.attrib_initial_dataset:
            if self.attrib_initial_dataset[layer_name][1] in ['Polygon', 'MultiPolygon']:
                id_surf_unique = self.attrib_initial_dataset[layer_name][5]
                surf_layer = self.attrib_initial_dataset[layer_name][0]

        if not complete:
            self.diag_attrib_layer1, self.indic_attrib1, self.cols_values = super().diag_attrib(id_surf_unique, surf_layer, self.correspond_value, self.new_dataset, self.standard, self.data_path, self.correspond_weights, complete=complete)
        else:
           self.diag_attrib_layer1, self.indic_attrib1, self.cols_values, self.topo_initial_dataset = super().diag_attrib(id_surf_unique, surf_layer, self.correspond_value, self.new_dataset, self.standard, self.data_path, self.correspond_weights, complete=complete) 

