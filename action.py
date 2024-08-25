from tkinter import Tk
from tkinter import filedialog
import shapely.wkb
from shapely import Polygon, Point, LineString
import geopandas as gpd
import pandas as pd
import numpy as np
import gemgis as gg
import os, time
import copy
import rasterio.sample
import rasterio.vrt

# map
import folium
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import jenkspy
import webbrowser
import os
import Levenshtein
import json
from unidecode import unidecode

from collections import Counter

class Action:
    def __init__(self):
        self.list_carto_topo = []
        self.dataset = {}
        self.files = []
        self.data_files = []
        self.csv_files = []
        self.new_dataset_copy = None

    def get_data_files(self):
        return self.data_files

    def get_file_path(self, message='Sélectionnez vos fichiers'):
        root = Tk()
        root.withdraw()
        list = filedialog.askopenfilenames(parent=root, title=message)
        self.data_files = list
        return list
    
    def get_file_path_csv(self, message='Sélectionnez vos fichiers'):
        root = Tk()
        root.withdraw()
        list = filedialog.askopenfilenames(parent=root, title=message)
        self.csv_files = list
        return list
    
    def drop_z(self, data):
        geometry = data['geometry']
        geom = shapely.wkb.loads(
        shapely.wkb.dumps(geometry, output_dimension=2))
        data.geometry = geom
        return data
    
    def filter_none(self, data):
        return {k: [lst for lst in v if 'None' not in lst] for k, v in data.items()}
    
    def load_files(self, files):
        dataset = {}
        for file in files:
            # load file
            data = gpd.read_file(file)

            # drop z
            data = self.drop_z(data)

            # data info
            geom_type = data.geom_type[0]
            file_name = os.path.basename(file)
            entities = data.shape[0]
            crs = data.crs
            col = data.columns.to_list()

            file_info = [data, geom_type, entities, crs, col]

            dataset[file_name] = file_info
        
        return dataset

    def load_csv_files(self, files_path, csv_list):
        for file in files_path:
            data = pd.read_csv(file, header=None)
            csv_list.append([data, os.path.basename(file)])

        return csv_list
    
    
    def get_standard(self, message = 'Sélectionnez le csv avec votre standard'):
        root = Tk()
        root.withdraw()
        csv = filedialog.askopenfilename(parent=root, title=message)
        df = pd.read_csv(csv, header=None)
        return df

    def reproject(self, epsg, dataset):
        for layer_name in dataset:
            if epsg:
                if dataset[layer_name][0].crs != f'EPSG:{epsg}':
                    dataset[layer_name][0] = dataset[layer_name][0].to_crs(epsg)
                    dataset[layer_name][3] = dataset[layer_name][0].crs
        return dataset
    
    def merge(self, *layers):
        layers_list = []
        for layer in layers:
            layers_list.append(layer)
        merged = pd.concat(layers_list)
        return merged
    
    def make_grid(self, surface, resolution):
        # Get the bounds of the surface
        minx, miny, maxx, maxy = surface.total_bounds

        # Define the size of the grid cells (in the same units as the CRS of your GeoDataFrame)
        cell_size = resolution

        # Create grid cells
        x_range = np.arange(minx, maxx + cell_size, cell_size)
        y_range = np.arange(miny, maxy + cell_size, cell_size)

        # Create a list to hold the grid cells
        grid_cells = []
        grid_ids = []
        cell_id = 1
        for x in x_range:
            for y in y_range:
                cell = Polygon([(x, y), (x + cell_size, y), (x + cell_size, y + cell_size), (x, y + cell_size)])
                grid_cells.append(cell)
                grid_ids.append(cell_id)
                cell_id += 1

        # Create a GeoDataFrame from the grid cells
        grid_gdf = gpd.GeoDataFrame({'geometry': grid_cells, 'cell_id': grid_ids}, crs=surface.crs)

        # Intersect the grid with the surface to get only the grid cells that cover the surface
        grid_intersect = gpd.overlay(grid_gdf, surface, how='intersection')

        return grid_intersect

        # # si je veux juste avoir les cellules sans les communes
        # # Merge cells by cell_id (dissolve)
        # merged_cells = grid_intersect.dissolve(by='cell_id')

    def line_to_point(self, lines, id_lines):
        # Explode the lines to handle MultiLineString geometries
        exploded_lines = lines.explode(index_parts=False).reset_index(drop=True)
        exploded_lines = gg.vector.extract_xy_linestring(gdf=exploded_lines)

        new_gdf = {"ID": [], "geometry": []}

        new_gdf = {"ID": [], "geometry": []}

        # Extract start and end points
        for idx, line in exploded_lines.iterrows():
            if isinstance(line["geometry"], LineString):
                new_gdf['geometry'].append(Point(line["geometry"].coords[0]))
                new_gdf['ID'].append(line[id_lines])
                new_gdf['geometry'].append(Point(line["geometry"].coords[-1]))
                new_gdf['ID'].append(line[id_lines])
                
        new_gdf = gpd.GeoDataFrame(new_gdf, crs=lines.crs)
        new_gdf.columns = [id_lines, 'geometry']
        merged_df = lines.merge(new_gdf, on=id_lines, how='inner')
        merged_df = merged_df.drop(columns=['geometry_x'])
        merged_gdf = gpd.GeoDataFrame(merged_df, geometry='geometry_y', crs=lines.crs)
        merged_gdf.rename_geometry('geometry', inplace=True)

        return merged_gdf
    
    def check_relie(self, layer1, layer2, drop=True):
        inter = layer1.sjoin(layer2, how='left', predicate='intersects')

        # RELIE col to assess the boolean connectivity
        inter['RELIE'] = inter['index_right'].apply(lambda x: 0 if pd.isna(x) else 1)

        # keep the layer1 cols and add RELIE
        left = inter.iloc[:,0:len(layer1.columns)]
        right = inter.iloc[:,-1:]
        inter_selec = pd.concat([left, right], axis=1)

        # rename the cols
        cols = inter_selec.columns.tolist()
        rename_cols = layer1.columns.tolist()
        rename_cols.append('RELIE')
        rename_dict = {col: rename_col for col, rename_col in zip(cols, rename_cols)}
        inter_export = inter_selec.rename(columns=rename_dict)

        if drop:
            # drop duplicates geometries
            inter_export = inter_export.drop_duplicates(subset='geometry')

        return inter_export
    
    def inter_relies_grid(self, grid, **layers_relie):
        # Donner le nom appropiré dans l'appel de la fonction
        #test = inter_relies_grid(grid, points_relie = points_relie, lines_relie = line_relie)

        grid_join = grid.copy()  # Copier la grille originale pour éviter de modifier l'original
        insee = self.dataset['Polygon'][0][6]

        print(self.dataset['Polygon'])

        for name, layer in layers_relie.items():
            # Effectuer une jointure spatiale entre la couche actuelle et la grille
            join = gpd.sjoin(layer, grid, how='inner', predicate='intersects')
            
            # Compter le nombre total de points par cell_id et par code_insee
            total_by_cell_id = join.groupby('cell_id').size().reset_index(name=f'{name}_total_points_by_cell_id')
            total_by_code_insee = join.groupby(insee).size().reset_index(name=f'{name}_total_points_by_code_insee')

            # Compter le nombre de zéros (0) dans la colonne RELIE
            count_by_cell_id = join.pivot_table(index='cell_id', values='RELIE', aggfunc=lambda x: (x == 0).sum())
            count_by_cell_id = count_by_cell_id.rename(columns={'RELIE': f'{name}_count_0_by_cell_id'})

            count_by_code_insee = join.pivot_table(index=insee, values='RELIE', aggfunc=lambda x: (x == 0).sum())
            count_by_code_insee = count_by_code_insee.rename(columns={'RELIE': f'{name}_count_0_by_code_insee'})

            # Ajouter les totaux par cell_id et par code_insee aux compteurs de zéros
            count_by_cell_id = count_by_cell_id.merge(total_by_cell_id, on='cell_id', how='left')
            count_by_code_insee = count_by_code_insee.merge(total_by_code_insee, on=insee, how='left')

            # Calculer les pourcentages de zéros par rapport à la population totale
            count_by_cell_id[f'{name}_percentage_0_by_cell_id'] = (count_by_cell_id[f'{name}_count_0_by_cell_id'] / count_by_cell_id[f'{name}_total_points_by_cell_id']) * 100
            count_by_code_insee[f'{name}_percentage_0_by_code_insee'] = (count_by_code_insee[f'{name}_count_0_by_code_insee'] / count_by_code_insee[f'{name}_total_points_by_code_insee']) * 100

            # Cacluler l'indicateur composite 
            count_by_cell_id[f'{name}_indic_compo_by_cell_id'] = 1 - (count_by_cell_id[f'{name}_percentage_0_by_cell_id'] / 100)# * count_by_cell_id[f'{name}_count_0_by_cell_id'] 
            count_by_code_insee[f'{name}_indic_compo_by_code_insee'] = 1 - (count_by_code_insee[f'{name}_percentage_0_by_code_insee'] / 100)# * count_by_code_insee[f'{name}_count_0_by_code_insee']

            # Fusionner les résultats avec la grille originale
            grid_join = grid_join.merge(count_by_cell_id, on='cell_id', how='left')
            grid_join = grid_join.merge(count_by_code_insee, on=insee, how='left')
            
        return grid_join

    def check_relie_lin(self, line, id_lines):
        # Convertir les lignes en points et les joindre entre elles
        line_points = self.line_to_point(line, id_lines)
        line_on_line = gpd.sjoin(line_points, line_points, how='inner', predicate='intersects')
        
        # Compter le nombre de points au même endroit
        counts = line_on_line[f'{id_lines}_left'].value_counts()
        
        # convertir la series en df
        counts_df = counts.reset_index()
        counts_df.columns = [id_lines, 'count']
        
        # merge avec les lignes d'origine
        merged = counts_df.merge(line, on=id_lines)
        
        # Binariser la connectivité
        merged['RELIE'] = merged['count'].apply(lambda x: 0 if x<=2 else 1)

        # convertir en gdf
        merged = gpd.GeoDataFrame(merged, geometry='geometry', crs=line.crs)
        
        return merged

    def check_doublon_id(self, layer, id_layer):
        '''
        ENTREE la couche et son id unique

        SORTIE la couche avec tous les objets dont l'identifiant apparaît plus d'une fois
        '''
        count_ident = layer.groupby(id_layer).size().reset_index()
        count_ident.columns = [id_layer, 'count']
        ident_dupli = count_ident[count_ident['count'] > 1]

        layer_ident_dupli = ident_dupli.merge(layer, on=id_layer)
        layer_ident_dupli = gpd.GeoDataFrame(layer_ident_dupli, geometry='geometry')

        return layer_ident_dupli

    def isolated_network(self, line, id_line):
        # Convert line to points pairs
        point_line = self.line_to_point(line, id_line)

        # Compute the geometries at the same location
        count = point_line['geometry'].value_counts().reset_index()
        count.columns = ['geometry', 'count']

        # Identify isolated lines (size = 2) and those linked to a segment (size = 1)
        geom_count = count.merge(point_line[[id_line, 'geometry']], on='geometry', how='inner')
        impasse = geom_count[geom_count['count'] == 1].groupby(id_line).size().reset_index()
        impasse.columns = [id_line, 'count']
        impasse_true = impasse[impasse['count'] == 1]

        impasse_true_line = impasse_true.merge(line, on=id_line)
        impasse_true_line = gpd.GeoDataFrame(impasse_true_line, geometry='geometry')

        # Isolated lines
        isole = impasse[impasse['count'] == 2]
        isole_line = isole.merge(line, on=id_line, how='left')
        isole_line = gpd.GeoDataFrame(isole_line, geometry='geometry')

        # Lines that are neither isolated nor dead ends
        ident_isole_impasse = impasse_true[id_line].tolist() + isole[id_line].tolist()
        line_no_isole_impasse = line[~line[id_line].isin(ident_isole_impasse)]
        line_no_isole_impasse = gpd.GeoDataFrame(line_no_isole_impasse, geometry='geometry')

        # Detect central lines of isolated areas (Iter 2)
        point_line_2 = self.line_to_point(line_no_isole_impasse, id_line)

        count2 = point_line_2['geometry'].value_counts().reset_index()
        count2.columns = ['geometry', 'count']

        geom_count_2 = count2.merge(point_line_2[[id_line, 'geometry']], on='geometry', how='inner')
        impasse_2 = geom_count_2[geom_count_2['count'] == 1].groupby(id_line).size().reset_index()
        impasse_2.columns = [id_line, 'count']

        isole_2 = impasse_2[impasse_2['count'] == 2]
        isole_2_line = isole_2.merge(line, on=id_line)
        isole_2_line = gpd.GeoDataFrame(isole_2_line, geometry='geometry')

        # Recreate isolated areas
        edge_points = self.line_to_point(impasse_true_line, id_line)
        core_points = self.line_to_point(isole_2_line, id_line)

        join = gpd.sjoin(edge_points, core_points, predicate='intersects')

        ident_join = join[f'{id_line}_left'].tolist() + join[f'{id_line}_right'].unique().tolist()

        ilots_line = line[line[id_line].isin(ident_join)]
        no_ilots_line = line[~line[id_line].isin(ident_join)]

        # dissolve ilots
        def dissolve_ilots(layer):
            # Calculate the groups of touching geometries
            def find_group(gdf):
                gdf['group'] = -1
                group_id = 0
                
                for idx, row in gdf.iterrows():
                    if gdf.at[idx, 'group'] == -1:
                        group_geom = gdf[gdf.geometry.touches(row.geometry)]
                        gdf.loc[group_geom.index, 'group'] = group_id
                        gdf.at[idx, 'group'] = group_id
                        group_id += 1
                        
                return gdf
            
            layer['group'] = layer.apply(lambda row: layer.sindex.query(row.geometry, predicate='touches'), axis=1)
            
            layer = find_group(layer)

            dissolved = layer.dissolve(by='group')
            
            dissolved['group'] = dissolved.apply(lambda row: dissolved.sindex.query(row.geometry, predicate='touches'), axis=1)

            dissolved = find_group(dissolved)
            dissolved.index.names = ['index']

            dissolved_2 = dissolved.dissolve(by='group')
            
            return dissolved_2
        
        # si c'est un ilot attribuer 0 à RELIE
        ilots_line['RELIE'] = 0
        no_ilots_line['RELIE'] = 1

        # concat + conversion en gdf
        ilots_line = pd.concat([ilots_line, no_ilots_line])
        ilots_line = gpd.GeoDataFrame(ilots_line, geometry='geometry')


        return ilots_line # Utiliser la fonction dissolve ilots si chaque ilot doit être représenté par une ligne unique -> ie : return dissolve_ilots(ilots_line)

    def diag_ouvrage_relie(self, topo_initial_dataset, export):

        # dataset par géométries
        self.dataset = {
            'Point': [],
            'Line': [],
            'Polygon': []
        }

        for file in topo_initial_dataset:
            file_name = file,
            data_file = topo_initial_dataset[file][0]
            geom_type = topo_initial_dataset[file][1]
            entities = topo_initial_dataset[file][2]
            crs = topo_initial_dataset[file][3]
            col = topo_initial_dataset[file][4]
            ident = topo_initial_dataset[file][5]

            data_info = [data_file, file_name, geom_type, entities, crs, col, ident]
        # append dataset
            if geom_type in ['MultiLineString', 'LineString']:
                self.dataset['Line'].append(data_info)
            elif geom_type in ['MultiPoint', 'Point']:
                self.dataset['Point'].append(data_info)
            elif geom_type in ['MultiPolygon', 'Polygon']:
                self.dataset['Polygon'].append(data_info)
            else:
                self.dataset['Unknown'].append(data_info)

        # listes pour le merge
        line_list = []
        point_list = []
        line_id = 'line_id'
        point_id = 'point_id'

        # définir la grille
        grid = self.make_grid(self.dataset['Polygon'][0][0], 900)
        id_surf = self.dataset['Polygon'][0][6]

        # # constantes pour l'identifiant unique de la ligne pour le line_to_point
        # line_id = self.dataset['Line'][0][6]

        # remplir les listes de lignes et de points
        for data_info in self.dataset['Line']:
            # changer l'id pour qu'il soit le même
            layer_ident = data_info[6]
            data_info[0] = data_info[0].rename(columns = {layer_ident : line_id})
            line_list.append(data_info[0])
        for data_info in self.dataset['Point']:
            layer_ident = data_info[6]
            data_info[0] = data_info[0].rename(columns = {layer_ident : point_id})
            point_list.append(data_info[0])
        
        # merge les couches linéaires et ponctuelles
        merged_lines = self.merge(*line_list)
        merged_points = self.merge(*point_list)

        # Convertir les lignes en extrémités
        line_points = self.line_to_point(merged_lines, line_id)
        line_points_unique = line_points.drop_duplicates(subset='geometry')

        # calculer les layers_relie
        points_relie = self.check_relie(merged_points, line_points_unique)
        lines_relie = self.check_relie(line_points_unique, merged_points)
        can_relie = self.check_relie_lin(merged_lines, line_id)

        # calculer les ilots isolés
        ilots = self.isolated_network(merged_lines, line_id)

        # intersection avec la gille
        grid_percent = self.inter_relies_grid(grid, points_relie=points_relie, lines_relie=lines_relie, canalisation_relie = can_relie, ilots = ilots)

        # repasser les lines_relie en lignes et calculer la typo
        def typo_value(row):
            if row['RELIE'] == 1 and row['RELIE_count'] >= 2:
                return '00'
            elif row['RELIE'] == 1 and row['RELIE_count'] == 1:
                return '01'
            elif row['RELIE'] == 1 and row['RELIE_count'] >= 0:
                return '02'
            elif row['RELIE'] == 0 and row['RELIE_count'] >= 2:
                return '03'
            elif row['RELIE'] == 0 and row['RELIE_count'] == 1:
                return '04'
            elif row['RELIE'] == 0 and row['RELIE_count'] >= 0:
                return '05'
        
        lines_relie = self.check_relie(line_points, merged_points, drop=False)
        aggregated = lines_relie.groupby('line_id').agg({'RELIE': 'sum'}).reset_index()
        aggregated.columns = ['line_id', 'RELIE_count']
        lines_relie = can_relie.merge(aggregated, on='line_id', how='left')
        lines_relie['typo_can'] = lines_relie.apply(typo_value, axis=1)
        lines_relie = gpd.GeoDataFrame(lines_relie, geometry='geometry')

        # ajouter les couches à la liste de carto
        self.list_carto_topo = [points_relie, lines_relie, can_relie, ilots]

        # ajouter l'indicateur synthétique à grid percent
        # insee
        cols = ['points_relie_indic_compo_by_code_insee', 
                'lines_relie_indic_compo_by_code_insee',
                'canalisation_relie_indic_compo_by_code_insee',
                'ilots_indic_compo_by_code_insee']

        insee_grid = grid_percent.groupby(id_surf)[cols].mean()

        new_cols = []

        for col in cols:
            mean_value = np.mean(insee_grid[col])
            std_value = np.std(insee_grid[col])
            insee_grid[f"{col}_standard"] = (insee_grid[col] - mean_value) / std_value
            new_cols.append(f"{col}_standard")


        insee_grid['indic_synth_insee'] = insee_grid[new_cols].mean(axis=1)
        # Move the new column to the first position
        columns = ['indic_synth_insee'] + [col for col in insee_grid.columns if col != 'indic_synth_insee']
        insee_grid = insee_grid[columns]
        insee_grid = insee_grid.drop(columns=cols)

        print(insee_grid)

        insee_grid = insee_grid.merge(grid_percent, on=id_surf)
        print(insee_grid.columns)
        # cell_id
        cols = ['points_relie_indic_compo_by_cell_id', 
                'lines_relie_indic_compo_by_cell_id',
                'canalisation_relie_indic_compo_by_cell_id',
                'ilots_indic_compo_by_cell_id']

        cell_grid = grid_percent.groupby('cell_id')[cols].mean()


        new_cols = []
        for col in cols:
            mean_value = np.mean(cell_grid[col])
            std_value = np.std(cell_grid[col])
            cell_grid[f"{col}_standard"] = (cell_grid[col] - mean_value) / std_value
            new_cols.append(f"{col}_standard")

        cell_grid['indic_synth_cell'] = cell_grid[cols].mean(axis=1)
        # Move the new column to the first position
        columns = ['indic_synth_cell'] + [col for col in cell_grid.columns if col != 'indic_synth_cell']
        cell_grid = cell_grid[columns]
        cell_grid = cell_grid.drop(columns=cols)

        grid_percent = cell_grid.merge(insee_grid, on='cell_id')
        grid_percent = gpd.GeoDataFrame(grid_percent, geometry='geometry')
        
        # Export
        if export:
            full_path = self.data_files[0]
            folder = os.path.dirname(full_path)
            points_relie.to_file(os.path.join(folder, 'points_relie.gpkg'), driver='GPKG')
            lines_relie.to_file(os.path.join(folder, 'lines_relie.gpkg'), driver='GPKG')
            can_relie.to_file(os.path.join(folder, 'can_relie.gpkg'), driver='GPKG')
            ilots.to_file(os.path.join(folder, 'ilots.gpkg'), driver='GPKG')
            grid_percent.to_file(os.path.join(folder, 'grid_percent.gpkg'), driver='GPKG')
            
        return grid_percent

    def line_to_point_modif(self, lines, id_lines):
        # Explode the lines to handle MultiLineString geometries
        exploded_lines = lines.explode(index_parts=False).reset_index(drop=True)
        exploded_lines = gg.vector.extract_xy_linestring(gdf=exploded_lines)

        new_gdf = {"ID": [], "extremity": [], "geometry": []}

        new_gdf = {"ID": [], "extremity": [], "geometry": []}

        # Extract start and end points
        for idx, line in exploded_lines.iterrows():
            if isinstance(line["geometry"], LineString):
                new_gdf['geometry'].append(Point(line["geometry"].coords[0]))
                new_gdf['ID'].append(line[id_lines])
                new_gdf['extremity'].append('start')
                new_gdf['geometry'].append(Point(line["geometry"].coords[-1]))
                new_gdf['ID'].append(line[id_lines])
                new_gdf['extremity'].append('end')
                
        new_gdf = gpd.GeoDataFrame(new_gdf, crs=lines.crs)
        new_gdf.columns = [id_lines, 'extremity', 'geometry']
        merged_df = lines.merge(new_gdf, on=id_lines, how='inner')
        merged_df = merged_df.drop(columns=['geometry_x'])
        merged_gdf = gpd.GeoDataFrame(merged_df, geometry='geometry_y', crs=lines.crs)
        merged_gdf.rename_geometry('geometry', inplace=True)

        for idx, line in merged_gdf.iterrows():
            merged_gdf.loc[idx, 'extremity'] = f"{line[id_lines]}_{line['extremity']}"

        return merged_gdf

    def correction_topo(self, dataset, complete=False):
        line_id = 'line_id'
        point_id = 'point_id'
        point_list = []
        line_list = []
        full_path = self.data_files[0]
        folder = os.path.dirname(full_path)
        # remplir les listes de lignes et de points
        for layer in dataset:

            datafile = dataset[layer][0]
            geomtype = dataset[layer][1]
            layer_id = dataset[layer][5]

            if geomtype in ['MultiLineString', 'LineString']:
                datafile = datafile.rename(columns = {layer_id : line_id})
                line_list.append(datafile)
                dataset[layer][0] = datafile
            if geomtype in ['MultiPoint', 'Point']:
                datafile = datafile.rename(columns = {layer_id : point_id})
                point_id_std = layer_id
                point_list.append(datafile)
                dataset[layer][0] = datafile

        merged_points = self.merge(*point_list)
        merged_lines = self.merge(*line_list)

        line_points = self.line_to_point_modif(merged_lines, line_id)
        line_points_minimal = line_points[[line_id, 'extremity', 'geometry']]

        points_relie = self.check_relie(merged_points, line_points)

        non_relie = points_relie[[point_id, 'RELIE', 'geometry']].loc[points_relie['RELIE'] == 0]

        nearest = gpd.sjoin_nearest(non_relie, line_points_minimal, how='left', distance_col="distances")

        nearest = nearest.drop_duplicates(subset=point_id)

        nearest01 = nearest.loc[nearest['distances'] <= 0.1]

        test = nearest01.merge(line_points_minimal, how='left', on='extremity')

        for layer in dataset:
            datafile = dataset[layer][0]
            geomtype = dataset[layer][1]

            if geomtype in ['Point', 'MultiPoint']:
                for idx, row in test.iterrows():
                    id_ouvrage = row[point_id]
                    new_geometry_y = row['geometry_y']
                    new_geometry_x = row['geometry_x']

                    if id_ouvrage in datafile[point_id].to_list():
                        datafile.loc[datafile[point_id] == id_ouvrage, 'geometry'] = new_geometry_y

                if complete:
                    datafile = datafile.rename(columns = {point_id : point_id_std})
                dataset[layer][0] = datafile
    
                datafile.to_file(os.path.join(folder, f'corrected_{layer}'), driver='GPKG')

        nb_correct = nearest01.shape[0]
        nb_non_relie = non_relie.shape[0]
        

        return nb_correct, nb_non_relie

    def setup_standard_shape(self, correspond, dataset, standard):

        missing_standard_fields = {}
        for key_cor, value_cor in correspond.items():
            for layer_name in dataset:
                for data in dataset[layer_name]:
                    if key_cor == layer_name:
                        
                        # isolate selected standard field
                        selected_standard_fields = [field[1] for field in correspond[key_cor] if field[1] not in ['None', 'KEEP_FIELD' ]]
                        
                        # define standard field for each group
                        if dataset[layer_name][1] in ['MultiPoint', 'Point']:
                            standard_fields = standard[1].dropna()
                            
                        elif dataset[layer_name][1] in ['MultiLineString', 'LineString']:
                            standard_fields = standard[0].dropna()
                        
                        missing = [[field] for field in standard_fields if field not in selected_standard_fields]
                        missing_standard_fields[key_cor] = missing
                



        # rename fields
        new_fields = {}
        for layer_name in dataset:
            data_file = dataset[layer_name][0]
            if layer_name in correspond:
                # Compter les champs en double
                values = [sublist[1] for sublist in correspond[layer_name]]
                counter = Counter(values)
                values_2 = [key for key in counter if counter[key] >= 2]
                
                # créer les clés
                new_fields[layer_name] = []
                
                # rename les champs
                for original_field, new_field in correspond[layer_name]:
                    
                    if new_field != 'None' and new_field != 'KEEP_FIELD':
                        
                        # check si le champ est double
                        if new_field in values_2:
                            new_field_unique = f'{new_field}_{original_field}'
                            data_file = data_file.rename(columns={original_field: new_field_unique})
                            new_fields[layer_name].append([new_field_unique, new_field])
                        else:
                            data_file = data_file.rename(columns={original_field: new_field})
                            new_fields[layer_name].append([new_field, new_field])
                    # drop les champs None
                    elif new_field == 'None':
                        data_file = data_file.drop(columns=[original_field])
                        
                    # renames les champs hors standard
                    elif new_field == 'KEEP_FIELD':
                        new_field_keep = f'{original_field}_{new_field}'
                        data_file = data_file.rename(columns={original_field: new_field_keep})
                        new_fields[layer_name].append([new_field_keep, new_field])
                        
                dataset[layer_name][0] = data_file
                            
        # ajout de l'index aux new_fields
        for layer_name in dataset:
            
            # juste pour les lignes
            if dataset[layer_name][1] in ['MultiLineString', 'LineString']:
                std = standard[0].dropna().to_list()
                len_std = len(std)
                data_file = dataset[layer_name][0]
                for pairs in new_fields[layer_name]:
                    rename_field, standard_field = pairs
                    if standard_field in std:
                        pairs.append(std.index(standard_field))
                    else :
                        len_std += 1
                        pairs.append(len_std)
            
            if dataset[layer_name][1] in ['MultiPoint', 'Point']:
                std = standard[1].dropna().to_list()
                len_std = len(std)
                data_file = dataset[layer_name][0]
                for pairs in new_fields[layer_name]:
                    rename_field, standard_field = pairs
                    if standard_field in std:
                        pairs.append(std.index(standard_field))
                    else:
                        len_std += 1
                        pairs.append(len_std)
                

        # ajout de l'index aux missing_standard_fields
        for layer_name in dataset:
            
            # juste pour les lignes
            if dataset[layer_name][1] in ['MultiLineString', 'LineString']:
                std = standard[0].dropna().to_list()
                # len_std = len(std)
                data_file = dataset[layer_name][0]
                for missing in missing_standard_fields[layer_name]:
                    missing_str = missing[0]
                    if missing_str in std:
                        missing.append(std.index(missing_str))
                    # else :
                    #     len_std += 1
                    #     pairs.append(len_std)
            
            if dataset[layer_name][1] in ['MultiPoint', 'Point']:
                std = standard[1].dropna().to_list()
                # len_std = len(std)
                data_file = dataset[layer_name][0]
                for missing in missing_standard_fields[layer_name]:
                    missing_str = missing[0]
                    if missing_str in std:
                        missing.append(std.index(missing_str))
                    # else:
                    #     len_std += 1
                    #     pairs.append(len_std)                     


        # supprimer les standard_field de new_fields
        for key in new_fields:
            for lists in new_fields[key]:
                del lists[1]
                        
        # Combinaison des deux dict
        for key in new_fields:
            new_fields[key].append(missing_standard_fields[key])

        # cleanup et tri en fonction de l'index
        final_mapping = {}
        for key in new_fields:
            final_mapping[key] = new_fields[key][:-1] + new_fields[key][-1]
            final_mapping[key] = sorted(final_mapping[key], key=lambda t: t[1])  

        
        # création des nouveaux gdf
        new_dataset = {}
        for layer_name in dataset:
            data_file = dataset[layer_name][0]
            if dataset[layer_name][1] in ['MultiLineString', 'LineString', 'MultiPoint', 'Point']:
                new_gdf = gpd.GeoDataFrame(geometry=data_file.geometry)
                for col, index in final_mapping[layer_name]:
                    if col in data_file.columns:
                        new_gdf[col] = data_file[col]
                    else:
                        new_gdf[col] = None

                new_dataset[layer_name] = new_gdf


        # Exporter pour debug
        full_path = self.data_files[0]
        folder = os.path.dirname(full_path)

        for layer_name in new_dataset:
            name = layer_name.split('.')[0]
            new_dataset[layer_name].to_file(os.path.join(folder, f'{name}_std_shape.gpkg'), driver='GPKG')      

        return new_dataset
    
    def make_map(self, center, gdf_cell, gdf_insee, overlay_data, overlay_id, values_column_insee, aliases_insee, values_column_cell, aliases_cell, num_classes, layer_type, typo_flag=0, overlay=True):  

        # convert datetime dtypes to strings (serialize json)
        datetime_cols_gdf_cell = gdf_cell.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
        gdf_cell[datetime_cols_gdf_cell] = gdf_cell[datetime_cols_gdf_cell].astype(str)

        datetime_cols_gdf_insee = gdf_insee.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
        gdf_insee[datetime_cols_gdf_insee] = gdf_insee[datetime_cols_gdf_insee].astype(str)

        datetime_cols_overlay_data = overlay_data.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
        overlay_data[datetime_cols_overlay_data] = overlay_data[datetime_cols_overlay_data].astype(str)

        # Function to perform Jenks natural breaks classification
        def get_jenks_breaks(values, num_classes):
            breaks = jenkspy.jenks_breaks(values, num_classes-1)
            return breaks
        
        # Function to generate a color gradient from a colormap
        def generate_color_gradient(num_steps, colormap_name='YlOrBr'):
            cmap = plt.get_cmap(colormap_name)
            norm = mcolors.Normalize(vmin=0, vmax=num_steps - 1)
            return [mcolors.rgb2hex(cmap(norm(i))) for i in range(num_steps)]
        
        # Function to get color based on Jenks breaks
        def get_color_for_value(value, breaks, colors):
            if value is None:
                return '#808080'
            for i in range(len(breaks)):
                if value <= breaks[i]:
                    return colors[i]
            return colors[-1]
        
        # Function to define style for GeoJSON features
        def style_geojson(feature, gdf, values_column, num_classes, colormap_name='YlOrBr'):
            values = gdf[values_column[0]].dropna().values
            breaks = get_jenks_breaks(values, num_classes)
            colors = generate_color_gradient(num_classes, colormap_name)
            value = feature['properties'][values_column[0]]
            color = get_color_for_value(value, breaks, colors)
            return {
                'fillColor': color,
                'color': '#000000',
                'weight': 2,
                'fillOpacity': 0.7,
            }

        # def discretize(data, bins):
        #     split = np.array_split(np.sort(data), bins)
        #     cutoffs = [x[-1] for x in split]
        #     cutoffs = cutoffs[:-1]
        #     return cutoffs
        
        # # Function to generate a color gradient from a colormap
        # def generate_color_gradient(num_steps, colormap_name='YlOrBr'):
        #     cmap = plt.get_cmap(colormap_name)
        #     norm = mcolors.Normalize(vmin=0, vmax=num_steps - 1)
        #     return [mcolors.rgb2hex(cmap(norm(i))) for i in range(num_steps)]
        
        # # Function to get color based on Jenks breaks
        # def get_color_for_value(value, breaks, colors):
        #     if value is None:
        #         return '#808080'
        #     for i in range(len(breaks)):
        #         if value <= breaks[i]:
        #             return colors[i]
        #     return colors[-1]
        
        # # Function to define style for GeoJSON features
        # def style_geojson(feature, gdf, values_column, num_classes, colormap_name='YlOrBr'):
        #     values = gdf[values_column[0]].dropna().values
        #     breaks = discretize(values, num_classes)
        #     colors = generate_color_gradient(num_classes, colormap_name)
        #     value = feature['properties'][values_column[0]]
        #     color = get_color_for_value(value, breaks, colors)
        #     return {
        #         'fillColor': color,
        #         'color': '#000000',
        #         'weight': 2,
        #         'fillOpacity': 0.7,
        #     }
        
        # Function to add GeoJSON layer to Folium map
        def add_geojson_layer(map_object, name, gdf, values_column, aliases, num_classes, show, colormap_name='YlOrBr'):
            geojson = folium.GeoJson(
                gdf,
                name=name,
                style_function=lambda feature: style_geojson(feature, gdf, values_column, num_classes, colormap_name),
                highlight_function=lambda x: {
                    'color': '#000000',
                    'weight': 5
                },
                # tooltip=folium.GeoJsonTooltip(fields=values_column, aliases=aliases, localize=True),
                popup_keep_highlighted=True,
                popup=folium.GeoJsonPopup(fields=values_column, aliases=aliases, localize=True),
                overlay=False,
                control=True,
                show=show
            )
            geojson.add_to(map_object)
            return geojson
    
        if layer_type == 'point' and not typo_flag and overlay:
            feature_group = folium.FeatureGroup(name='Ouvrages', show=False)

            overlay_data.apply(lambda row: folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=2,  # radius of the circle marker
                color='red' if row['RELIE'] == 0 else 'green',  # color based on RELIE field
                fill=False,  # no fill color
                popup=folium.Popup(f"Identifiant : {row[overlay_id]} \n Etat de liaison : {row['RELIE']}", parse_html=True)
            ).add_to(feature_group), axis=1)
                         

            # Generate the legends
            values_insee = gdf_insee[values_column_insee[0]].dropna().values
            values_insee = [round(value, 2) for value in values_insee]
            breaks_insee = get_jenks_breaks(values_insee, num_classes)
            # breaks_insee = discretize(values_insee, num_classes)
            colors_insee = generate_color_gradient(num_classes, 'YlOrBr')

            values_cell = gdf_cell[values_column_cell[0]].dropna().values
            values_cell = [round(value, 2) for value in values_cell]
            breaks_cell = get_jenks_breaks(values_cell, num_classes)
            # breaks_cell = discretize(values_cell, num_classes)
            colors_cell = generate_color_gradient(num_classes, 'YlOrBr')

            legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; z-index: 1000; font-size: 14px; background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 5px;">'
            
            legend_html += '<b>Indicateur composite par commune</b><br>'
            for i in range(len(breaks_insee) - 1):
                legend_html += f'<i style="background:{colors_insee[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_insee[i]} ; {breaks_insee[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_insee[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_insee[-1]}<br>'
            # legend_html += '<br>'
            
            legend_html += '<b>Indicateur composite par cellule</b><br>'
            for i in range(len(breaks_cell) - 1):
                legend_html += f'<i style="background:{colors_cell[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_cell[i]} ; {breaks_cell[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_cell[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_cell[-1]}<br>'
            legend_html += '<br>'
            
            # legend_html += '<b>Points Legend</b><br>'
            legend_html += '<i style="background:green;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Points reliés<br>'
            legend_html += '<i style="background:red;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Points non reliés<br>'
            
            legend_html += '</div>'
            
        elif layer_type == 'line' and not typo_flag and overlay:
            feature_group = folium.FeatureGroup(name='Canalisations', show=False)

            def add_polyline(row):
                locations = [(coord[1], coord[0]) for coord in row['geometry'].coords]
                color = 'red' if row['RELIE'] == 0 else 'green'
                popup = folium.Popup(f"Identifiant : {row['line_id']} \n Etat de liaison : {row['RELIE']}", parse_html=True)
                polyline = folium.PolyLine(locations=locations, color=color, weight=7, popup=popup)
                polyline.add_to(feature_group)
            
            overlay_data.apply(add_polyline, axis=1)
    
            # Generate the legends
            values_insee = gdf_insee[values_column_insee[0]].dropna().values
            values_insee = [round(value, 2) for value in values_insee]
            breaks_insee = get_jenks_breaks(values_insee, num_classes)
            # breaks_insee = discretize(values_insee, num_classes)
            colors_insee = generate_color_gradient(num_classes, 'YlOrBr')

            values_cell = gdf_cell[values_column_cell[0]].dropna().values
            values_cell = [round(value, 2) for value in values_cell]
            breaks_cell = get_jenks_breaks(values_cell, num_classes)
            # breaks_cell = discretize(values_cell, num_classes)
            colors_cell = generate_color_gradient(num_classes, 'YlOrBr')

            legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; z-index: 1000; font-size: 14px; background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 5px;">'
            
            legend_html += '<b>Indicateur composite par commune</b><br>'
            for i in range(len(breaks_insee) - 1):
                legend_html += f'<i style="background:{colors_insee[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_insee[i]} ; {breaks_insee[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_insee[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_insee[-1]}<br>'
            # legend_html += '<br>'
            
            legend_html += '<b>Indicateur composite par cellule</b><br>'
            for i in range(len(breaks_cell) - 1):
                legend_html += f'<i style="background:{colors_cell[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_cell[i]} ; {breaks_cell[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_cell[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_cell[-1]}<br>'
            legend_html += '<br>'
            
            # legend_html += '<b>Points Legend</b><br>'
            legend_html += '<i style="background:green;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Canalisations reliées<br>'
            legend_html += '<i style="background:red;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Canalisations non reliées<br>'
            
            legend_html += '</div>'

        elif layer_type == 'line' and typo_flag and overlay:
            feature_group = folium.FeatureGroup(name='Canalisations', show=False)

            def add_polyline(row):
                locations = [(coord[1], coord[0]) for coord in row['geometry'].coords]
                if row['typo_can'] == '01':
                    color = '#fb6a4a'
                elif row['typo_can'] == '02':
                    color = '#cb181d'
                elif row['typo_can'] == '04':
                    color = '#fb6a4a'
                elif row['typo_can'] == '05':
                    color = '#cb181d'
                else:
                    color = 'green'
                popup_text = f"Identifiant : {row['line_id']}\nTypologie : {row['typo_can']}"
                popup = folium.Popup(popup_text, parse_html=True)
                polyline = folium.PolyLine(locations=locations, color=color, weight=4, popup=popup)
                polyline.add_to(feature_group)
            
            overlay_data.apply(add_polyline, axis=1)
    
            
                        

            # Generate the legends
            values_insee = gdf_insee[values_column_insee[0]].dropna().values
            values_insee = [round(value, 2) for value in values_insee]
            breaks_insee = get_jenks_breaks(values_insee, num_classes)
            # breaks_insee = discretize(values_insee, num_classes)
            colors_insee = generate_color_gradient(num_classes, 'YlOrBr')

            values_cell = gdf_cell[values_column_cell[0]].dropna().values
            values_cell = [round(value, 2) for value in values_cell]
            breaks_cell = get_jenks_breaks(values_cell, num_classes)
            # breaks_cell = discretize(values_cell, num_classes)
            colors_cell = generate_color_gradient(num_classes, 'YlOrBr')

            legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; z-index: 1000; font-size: 14px; background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 5px;">'
            
            legend_html += '<b>Indicateur composite par commune</b><br>'
            for i in range(len(breaks_insee) - 1):
                legend_html += f'<i style="background:{colors_insee[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_insee[i]} ; {breaks_insee[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_insee[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_insee[-1]}<br>'
            # legend_html += '<br>'
            
            legend_html += '<b>Indicateur composite par cellule</b><br>'
            for i in range(len(breaks_cell) - 1):
                legend_html += f'<i style="background:{colors_cell[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_cell[i]} ; {breaks_cell[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_cell[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_cell[-1]}<br>'
            legend_html += '<br>'
            
            # legend_html += '<b>Points Legend</b><br>'
            legend_html += '<i style="background:green;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Canalisations liées à 2 ouvrages<br>'
            legend_html += '<i style="background:#fb6a4a;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Canalisations liées à 1 ouvrages<br>'
            legend_html += '<i style="background:#cb181d;width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i>Canalisations liées à aucun ouvrage<br>'

            legend_html += '</div>'
            
        if not overlay:
            # Generate the legends
            values_insee = gdf_insee[values_column_insee[0]].dropna().values
            values_insee = [round(value, 2) for value in values_insee]
            breaks_insee = get_jenks_breaks(values_insee, num_classes)
            # breaks_insee = discretize(values_insee, num_classes)
            colors_insee = generate_color_gradient(num_classes, 'YlOrBr')

            values_cell = gdf_cell[values_column_cell[0]].dropna().values
            values_cell = [round(value, 2) for value in values_cell]
            breaks_cell = get_jenks_breaks(values_cell, num_classes)
            # breaks_cell = discretize(values_cell, num_classes)
            colors_cell = generate_color_gradient(num_classes, 'YlOrBr')

            legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; z-index: 1000; font-size: 14px; background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 5px;">'
            
            legend_html += '<b>Indicateur composite par commune</b><br>'
            for i in range(len(breaks_insee) - 1):
                legend_html += f'<i style="background:{colors_insee[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_insee[i]} ; {breaks_insee[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_insee[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_insee[-1]}<br>'
            # legend_html += '<br>'
            
            legend_html += '<b>Indicateur composite par cellule</b><br>'
            for i in range(len(breaks_cell) - 1):
                legend_html += f'<i style="background:{colors_cell[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_cell[i]} ; {breaks_cell[i+1]}[<br>'
            legend_html += f'<i style="background:{colors_cell[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_cell[-1]}<br>'
            legend_html += '<br>'
        
        # Create a Folium map centered on a location
        m = folium.Map(location=center, zoom_start=11, control_scale=True)

        if overlay:
            feature_group.add_to(m)

        # Add GeoJSON layers
        add_geojson_layer(m, 'Communes', gdf_insee, values_column_insee, aliases_insee, num_classes, True)
        add_geojson_layer(m, 'Carroyage', gdf_cell, values_column_cell, aliases_cell, num_classes, False)
        
        # Add different tile layers to the map
        folium.TileLayer('openstreetmap').add_to(m)
        
        # Add Layer Control to toggle layers
        folium.LayerControl(collapsed=False).add_to(m)

        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save the map to an HTML file
        map_path = 'map_with_geojson.html'
        m.save(map_path)
        
        # # Use pywebview to open the map in a new browser window
        # webview.create_window('Map Viewer', url=f'file://{os.path.abspath(map_path)}', width=1280, height=720, resizable=True)
        # webview.start()

        webbrowser.open(f'file://{os.path.abspath(map_path)}', new=2)

    def load_csv_files(self, files_path):
        csv_list = []
        for file in files_path:
            data = pd.read_csv(file, header=None)
            csv_list.append([data, os.path.basename(file)])

        return csv_list

    def diag_attrib(self, id_surf_unique, surf_layer, cor, dataset, standard, data_path, cor_weights, complete=False):

        full_path = data_path[0]
        folder = os.path.dirname(full_path)
        id_line = standard[0][0]
        id_point = standard[1][0]

        def change_duplicated(dataset, standard):
            for layer in dataset:
                datafile = dataset[layer]

                # Determine the correct ID column based on geometry type
                if datafile.geom_type[0] in ['MultiLineString', 'LineString']:
                    id_col = standard[0][0]
                elif datafile.geom_type[0] in ['MultiPoint', 'Point']:
                    id_col = standard[1][0]

                total = datafile.shape[0]

                duplicated = datafile[datafile.duplicated(subset=id_col, keep=False)]
                new_ids = [f"NEW_ID_{i+1}" for i in range(len(duplicated))]
                datafile.loc[duplicated.index, id_col] = new_ids

                dataset[layer] = {
                    "data_file": datafile,
                    "count_duplicates": 1 - len(duplicated) / total
                }

            return dataset

        # Appliquer la fonction au dataset
        new_dataset = change_duplicated(dataset, standard)
        new_dataset_copy = copy.deepcopy(new_dataset)

        rafcom_minimal = surf_layer[[id_surf_unique, 'geometry']]

        diag_dict = {}

        for layer_name in new_dataset:
            # supression de l'id_unique surfacique s'il existe
            if id_surf_unique in new_dataset[layer_name]['data_file'].columns:
                new_dataset[layer_name]['data_file'].drop(columns=[id_surf_unique], inplace=True)

            # jointure spatiale avec la couche surfacique
            join = gpd.sjoin(new_dataset[layer_name]['data_file'], rafcom_minimal, how='inner', predicate='intersects')

            if join.geom_type[0] in ['MultiLineString', 'LineString']:
                id_col = standard[0][0]
            elif join.geom_type[0] in ['MultiPoint', 'Point']:
                id_col = standard[1][0]

            join = join.drop(columns={'index_right'}).drop_duplicates(subset=[id_col])

            new_dataset[layer_name]['data_file'] = join
            new_dataset_copy[layer_name]['data_file'] = join.copy()
            data_file = new_dataset[layer_name]['data_file']

            # ajout de la couche au dictionnaire du diagnostic
            diag_dict[layer_name] = {}

            for insee in data_file[id_surf_unique].unique():
                insee_layer = join.loc[join[id_surf_unique] == insee]
                diag_dict[layer_name][insee] = {}

                for col in insee_layer:
                    if col not in diag_dict[layer_name][insee] and col not in ['geometry', id_surf_unique]:
                        diag_dict[layer_name][insee][col] = [None , None, None, None, None]

                    # champ d'énumération
                    if col in cor[layer_name]:

                        # calcul de la précision sémantique
                        other_vals = [value for value, new_value in cor[layer_name][col] if new_value == 'AUTRE']
                        if other_vals:
                            count_other = insee_layer.loc[insee_layer[col].isin(other_vals), col].count()
                            prec_semant = count_other / insee_layer.shape[0]
                            ponder = cor_weights[layer_name][col]
                            if ponder > 0:
                                diag_dict[layer_name][insee][col][3] = 1 - prec_semant * ponder

                        # compte des redondances sémantiques
                        count = Counter([new_value for value, new_value in cor[layer_name][col]])
                        filtered_count = {key:cnt for key, cnt in count.items() if cnt > 1}

                        # calcul de la redondance sémantique
                        if filtered_count:
                            count = 0
                            for key in filtered_count:

                                if key != 'AUTRE' and key != 'None':
                                    redond = filtered_count[key]
                                    vals = [value for value, new_value in cor[layer_name][col] if new_value == key]
                                    count += insee_layer.loc[insee_layer[col].isin(vals), col].count() * ((redond-1)/redond)                
                            
                            redond_semant = count/insee_layer.shape[0]
                            redond_semant = round(redond_semant, 4)
                            
                            ponder = cor_weights[layer_name][col]
                            if ponder > 0:
                                diag_dict[layer_name][insee][col][2] = (1 - redond_semant)*ponder

                        for value, new_value in cor[layer_name][col]:
                            
                            # changer les valeurs pour l'export
                            if new_value in ['INDETERMINE', 'None']:
                                new_dataset_copy[layer_name]['data_file'].loc[new_dataset_copy[layer_name]['data_file'][col] == value, col] = None
                            elif new_value == 'AUTRE' and not value.startswith('AUTRE_'): # ne rajouter le suffixe que s'il n'existe pas encore
                                new_dataset_copy[layer_name]['data_file'].loc[new_dataset_copy[layer_name]['data_file'][col] == value, col] = f"AUTRE_{value}"
                            else:
                                new_dataset_copy[layer_name]['data_file'].loc[new_dataset_copy[layer_name]['data_file'][col] == value, col] = new_value


                        # calcul de la précision syntaxique
                        prec_values = []
                        for value, new_value in cor[layer_name][col]:
            
                            if new_value not in ['AUTRE', 'INDETERMINE', 'None']:
                                nb_value = insee_layer.loc[insee_layer[col] == value, col].count()
                                distance = Levenshtein.ratio(unidecode(value.upper()), unidecode(new_value.upper()))
                                # print(layer_name, insee, col, distance, nb_value, value, new_value)
                                prec_value = nb_value*distance

                                # vérifier que la valeur existe dans cette partie du tableau
                                if nb_value:
                                    prec_values.append(prec_value)


                        if prec_values:
                            # chercher le nombre de champs renseignés
                            insee_data = new_dataset_copy[layer_name]['data_file'].loc[new_dataset_copy[layer_name]['data_file'][id_surf_unique] == insee, col]
                            count_insee_data = insee_data.shape[0] - insee_data.isna().sum()
                            tot_prec = np.sum(prec_values)
                            prec_syntax = tot_prec/count_insee_data
                            prec_syntax = round(prec_syntax, 4)
                            ponder = cor_weights[layer_name][col]
                            if ponder > 0:
                                diag_dict[layer_name][insee][col][4] = prec_syntax * ponder

                    # calcul de l'exhaustivité
                    exhaust = 1 - new_dataset_copy[layer_name]['data_file'][col].loc[new_dataset_copy[layer_name]['data_file'][id_surf_unique]==insee].isna().sum() / insee_layer.shape[0]
                    exhaust = round(exhaust, 4)
                    if col not in ['geometry', id_surf_unique]:
                        ponder = cor_weights[layer_name][col]
                        if ponder > 0:
                            diag_dict[layer_name][insee][col][0] = exhaust * ponder

                    # champs numériques
                    if pd.api.types.is_numeric_dtype(insee_layer[col]) and col not in ['geometry', id_surf_unique]:

                        # changer les valeurs pour l'export
                        condition = (new_dataset_copy[layer_name]['data_file'][col] <= 0) & (new_dataset_copy[layer_name]['data_file'][id_surf_unique] == insee)
                        new_dataset_copy[layer_name]['data_file'].loc[condition, col] = None
                        # new_dataset_copy[layer_name]['data_file'].loc[new_dataset_copy[layer_name]['data_file'][col] <= 0 and new_dataset_copy[layer_name]['data_file'][id_surf_unique] == insee, col] = None

                        # calcul de l'aberration numérique
                        exhaust_num = 1 - new_dataset_copy[layer_name]['data_file'][col].loc[new_dataset_copy[layer_name]['data_file'][id_surf_unique]==insee].isna().sum() / insee_layer.shape[0]
                        exhaust_num = round(exhaust_num, 4)
                        ponder = cor_weights[layer_name][col]
                        if ponder > 0:
                            aber_num = 1 - (diag_dict[layer_name][insee][col][0]/ponder - exhaust_num)
                            diag_dict[layer_name][insee][col][1] = aber_num * ponder

                        # changement de la valeur d'exhaustivité
                        new_exhaust = 1 - new_dataset_copy[layer_name]['data_file'][col].loc[new_dataset_copy[layer_name]['data_file'][id_surf_unique]==insee].isna().sum() / insee_layer.shape[0]
                        new_exhaust = round(new_exhaust, 4)
                        diag_dict[layer_name][insee][col][0] = new_exhaust

                    # mettre 100% à la redond semant et la prec semant pour les champs non numériques avec moins de 40 valeurs unique
                    if col not in ['geometry', id_surf_unique]:
                        if not diag_dict[layer_name][insee][col][1] and diag_dict[layer_name][insee][col][0] > 0:
                                ponder = cor_weights[layer_name][col]
                                if ponder > 0:
                                    if not diag_dict[layer_name][insee][col][2]:
                                        diag_dict[layer_name][insee][col][2] = 1.0 * ponder
                                    if not diag_dict[layer_name][insee][col][3]: 
                                        diag_dict[layer_name][insee][col][3] = 1.0 * ponder



        # créer les tableaux de synthèse
        # df avec les synthèses par code insee [redondance id_unique globale / exhaustivité / précision synthaxique / redondance / précision sémantique / valeurs aberrantes numériques]
        df_diag_attrib = {'ID': surf_layer[id_surf_unique].unique()}
        df_diag_attrib = pd.DataFrame.from_dict(df_diag_attrib)

        # global unique_id redundancy
        redundancy_values = [new_dataset[layer_name]['count_duplicates'] for layer_name in new_dataset]
        df_diag_attrib['unique_id_redundancy'] = np.mean(redundancy_values)
        # Initialize columns for metrics to analyze
        metrics = ['exhaust', 'exhaust_no_empty', 'aber_num', 'redond_semant', 'prec_semant', 'prec_syntax']
        for metric in metrics:
            df_diag_attrib[metric] = None

        dict_diag_attrib = {}
        dict_diag_attrib['exhaust'] = {}
        dict_diag_attrib['exhaust_no_empty'] = {}
        dict_diag_attrib['aber_num'] = {}
        dict_diag_attrib['redond_semant'] = {}
        dict_diag_attrib['prec_semant'] = {}
        dict_diag_attrib['prec_syntax'] = {}

        for layer in diag_dict:

            # création des df de détail
            df_detail = {'column': new_dataset_copy[layer]['data_file'].columns}
            df_detail = pd.DataFrame.from_dict(df_detail)
            df_detail['pondération'] = None
            for col in cor_weights[layer]:
                df_detail.loc[df_detail['column'] == col, 'pondération'] = cor_weights[layer][col]
            df_detail.drop(df_detail.loc[df_detail['column'].isin([id_surf_unique, id_line, id_point, 'geometry'])].index, inplace=True)
            for metric in metrics:
                df_detail[metric] = None
            df_detail['typologie'] = None

            col_dict = {}
            col_dict[layer] = {}

            for insee in diag_dict[layer]:

                exhaust_list = []
                exhaust_no_empty_list = []
                aber_num_list = []
                redond_semant_list = []
                prec_semant_list = []
                prec_syntax_list = []

                for col in diag_dict[layer][insee]:
                    if col not in [id_line, id_point]:

                        # metrics
                        exhaust = diag_dict[layer][insee][col][0]
                        aber_num = diag_dict[layer][insee][col][1]
                        redond_semant = diag_dict[layer][insee][col][2]
                        prec_semant = diag_dict[layer][insee][col][3]
                        prec_syntax = diag_dict[layer][insee][col][4]

                        weight = cor_weights[layer][col]

                        # remplir le col dict
                        # exhaust
                        if col in col_dict[layer]:

                            if exhaust != None:
                                if 'exhaust' in col_dict[layer][col]:
                                    col_dict[layer][col]['exhaust'].append([exhaust, weight])
                                else:
                                    col_dict[layer][col]['exhaust'] = [[exhaust, weight]]

                            if exhaust:
                                if 'exhaust_no_empty' in col_dict[layer][col]:
                                    col_dict[layer][col]['exhaust_no_empty'].append([exhaust, weight])
                                else:
                                    col_dict[layer][col]['exhaust_no_empty'] = [[exhaust, weight]]

                            if aber_num != None:
                                if 'aber_num' in col_dict[layer][col]:
                                    col_dict[layer][col]['aber_num'].append([aber_num, weight])
                                else:
                                    col_dict[layer][col]['aber_num'] = [[aber_num, weight]]

                            if redond_semant != None:
                                if 'redond_semant' in col_dict[layer][col]:
                                    col_dict[layer][col]['redond_semant'].append([redond_semant, weight])
                                else:
                                    col_dict[layer][col]['redond_semant'] = [[redond_semant, weight]]

                            if prec_semant != None:
                                if 'prec_semant' in col_dict[layer][col]:
                                    col_dict[layer][col]['prec_semant'].append([prec_semant, weight])
                                else:
                                    col_dict[layer][col]['prec_semant'] = [[prec_semant, weight]]

                            if prec_syntax != None:
                                if 'prec_syntax' in col_dict[layer][col]:
                                    col_dict[layer][col]['prec_syntax'].append([prec_syntax, weight])
                                else:
                                    col_dict[layer][col]['prec_syntax'] = [[prec_syntax, weight]]

                        else:
                            col_dict[layer][col] = {}


                        #add to lists
                        if exhaust != None:
                            exhaust_list.append([exhaust, weight])

                        if exhaust:
                            exhaust_no_empty_list.append([exhaust, weight])
                        
                        if aber_num != None:
                            aber_num_list.append([aber_num, weight])

                        if redond_semant != None:
                            redond_semant_list.append([redond_semant, weight])

                        if prec_semant != None:
                            prec_semant_list.append([prec_semant, weight])

                        if prec_syntax != None:
                            prec_syntax_list.append([prec_syntax, weight])

                # mean with weights

                # exhaust
                if exhaust_list:
                    somme = np.sum([value for value, weight in exhaust_list])
                    poids = np.sum([weight for value, weight in exhaust_list])
                    mean = somme/poids
                    if insee in dict_diag_attrib['exhaust']:
                        dict_diag_attrib['exhaust'][insee].append([mean, layer])
                    else:
                        dict_diag_attrib['exhaust'][insee] = [[mean, layer]]

                # exhaust no empty
                if exhaust_no_empty_list:
                    somme = np.sum([value for value, weight in exhaust_no_empty_list])
                    poids = np.sum([weight for value, weight in exhaust_no_empty_list])
                    mean = somme/poids
                    if insee in dict_diag_attrib['exhaust_no_empty']:
                        dict_diag_attrib['exhaust_no_empty'][insee].append([mean, layer])
                    else:
                        dict_diag_attrib['exhaust_no_empty'][insee] = [[mean, layer]]
                
                # aber_num
                if aber_num_list:
                    somme = np.sum([value for value, weight in aber_num_list])
                    poids = np.sum([weight for value, weight in aber_num_list])
                    mean = somme/poids
                    if insee in dict_diag_attrib['aber_num']:
                        dict_diag_attrib['aber_num'][insee].append([mean, layer])
                    else:
                        dict_diag_attrib['aber_num'][insee] = [[mean, layer]]

                # redond_semant
                if redond_semant_list:
                    somme = np.sum([value for value, weight in redond_semant_list])
                    poids = np.sum([weight for value, weight in redond_semant_list])
                    mean = somme/poids
                    if insee in dict_diag_attrib['redond_semant']:
                        dict_diag_attrib['redond_semant'][insee].append([mean, layer])
                    else:
                        dict_diag_attrib['redond_semant'][insee] = [[mean, layer]]

                # prec_semant
                if prec_semant_list:
                    somme = np.sum([value for value, weight in prec_semant_list])
                    poids = np.sum([weight for value, weight in prec_semant_list])
                    mean = somme/poids
                    
                    if insee in dict_diag_attrib['prec_semant']:
                        dict_diag_attrib['prec_semant'][insee].append([mean, layer])
                    else:
                        dict_diag_attrib['prec_semant'][insee] = [[mean, layer]]

                # prec_semant
                if prec_syntax_list:
                    somme = np.sum([value for value, weight in prec_syntax_list])
                    poids = np.sum([weight for value, weight in prec_syntax_list])
                    mean = somme/poids
                    
                    if insee in dict_diag_attrib['prec_syntax']:
                        dict_diag_attrib['prec_syntax'][insee].append([mean, layer])
                    else:
                        dict_diag_attrib['prec_syntax'][insee] = [[mean, layer]]


            # mettre en forme les detail df
            for col in col_dict[layer]:
                for metric in col_dict[layer][col]:

                    mean = np.mean([value for value, weight in col_dict[layer][col][metric]])
                    df_detail.loc[df_detail['column'] == col, metric] = mean

            # Mise à jour de la typologie
            for col in col_dict[layer]:
                df_detail.loc[
                    (df_detail['column'] == col) & 
                    (df_detail['exhaust'] == 0), 'typologie'
                ] = 'champ vide'
                
                df_detail.loc[
                    (df_detail['column'] == col) & 
                    (~df_detail['aber_num'].isna()), 'typologie'
                ] = 'champ numérique'
                
                df_detail.loc[
                    (df_detail['column'] == col) & 
                    (df_detail['aber_num'].isna()) & 
                    (~df_detail['prec_syntax'].isna()) & 
                    (df_detail['typologie'].isna()), 
                    'typologie'
                ] = 'champ avec correspondance'
                
                df_detail.loc[
                    (df_detail['column'] == col) & 
                    (df_detail['aber_num'].isna()) & 
                    (df_detail['prec_syntax'].isna()) & 
                    (df_detail['typologie'].isna()), 
                    'typologie'
                ] = 'champ sans correspondance'

            # print(df_detail)

            df_detail.to_csv(os.path.join(folder, f'detail_{layer.split('.')[0]}.csv'), encoding='latin1')

                    
        # remplir le tableau final
        df_diag_attrib['indicateur'] = None
        for insee in surf_layer[id_surf_unique]:

            # exhaust
            mean_layer = np.mean([value for value, layer in dict_diag_attrib['exhaust'][insee]])
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'exhaust'] = mean_layer
            # min_value, min_layer = min(dict_diag_attrib['exhaust'][insee], key=lambda x: x[0])

            # exhaust no empty
            mean_layer = np.mean([value for value, layer in dict_diag_attrib['exhaust_no_empty'][insee]])
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'exhaust_no_empty'] = mean_layer

            # aber_num
            mean_layer = np.mean([value for value, layer in dict_diag_attrib['aber_num'][insee]])
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'aber_num'] = mean_layer

            # redond semant
            mean_layer = np.mean([value for value, layer in dict_diag_attrib['redond_semant'][insee]])
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'redond_semant'] = mean_layer

            # prec semant
            mean_layer = np.mean([value for value, layer in dict_diag_attrib['prec_semant'][insee]])
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'prec_semant'] = mean_layer

            # prec semant
            mean_layer = np.mean([value for value, layer in dict_diag_attrib['prec_syntax'][insee]])
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'prec_syntax'] = mean_layer

            # indicateur
            df_diag_attrib.loc[df_diag_attrib['ID'] == insee, 'indicateur'] = df_diag_attrib.loc[df_diag_attrib['ID'] == insee, metrics].mean(axis=1)*np.mean(redundancy_values)



        # for layer_name in new_dataset_copy:
        #     if id_surf_unique in new_dataset_copy[layer_name]['data_file'].columns:
        #         new_dataset_copy[layer_name]['data_file'].drop(columns=[id_surf_unique], inplace=True)
        #     new_dataset_copy[layer_name]['data_file'].to_file(f"data/test_{layer_name}")
                            
        # print(df_diag_attrib)
        # print(diag_dict)


        df_diag_attrib.to_csv(os.path.join(folder, 'diag_attrib.csv'), encoding='latin1')
        cols = list(df_diag_attrib.columns)
        indic = np.mean(df_diag_attrib['indicateur'])

        # merge pour la carto
        merged = rafcom_minimal.merge(df_diag_attrib, how='left', left_on=id_surf_unique, right_on='ID')

        merged.to_file(os.path.join(folder, "diag_attrib.gpkg"), driver='GPKG')

        if not complete:
            for layer in new_dataset_copy:
                name = layer.split('.')[0]
                data_file=new_dataset_copy[layer]['data_file']
                data_file.to_file(os.path.join(folder, f'{name}_diag_attrib_maj.gpkg'), driver='GPKG')

            return merged, indic, cols
        
        else:
            # si complete_path formater le dictionnaire pour le diag topo
            for layer in new_dataset_copy:
                name = layer.split('.')[0]
                data_file=new_dataset_copy[layer]['data_file']
                data_file.to_file(os.path.join(folder, f'{name}_diag_attrib_maj.gpkg'), driver='GPKG')
                data_file = new_dataset_copy[layer]['data_file']
                geom_type = data_file.geom_type[0]
                file_name = layer
                entities = data_file.shape[0]
                crs = data_file.crs
                col = data_file.columns.to_list()
                if id_surf_unique in col:
                    data_file = data_file.drop(columns = [id_surf_unique])

                file_info = [data_file, geom_type, entities, crs, col]

                self.dataset[file_name] = file_info

            surf_geom_type = surf_layer.geom_type[0]
            surf_entities = surf_layer.shape[0]
            surf_crs = surf_layer.crs
            surf_col = data_file.columns.to_list()
            
            surf_file_info = [surf_layer, surf_geom_type, surf_entities, surf_crs, surf_col]

            self.dataset['Polygon data'] = surf_file_info
            print(self.dataset['Polygon data'])


            return merged, indic, cols, self.dataset

    def make_attrib_map(self, data_layer1, cols_values1, cols_aliases1, num_class):

        # convert datetime dtypes to strings (serialize json)
        datetime_cols_gdf_cell = data_layer1.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns
        data_layer1[datetime_cols_gdf_cell] = data_layer1[datetime_cols_gdf_cell].astype(str)

        data_layer1 = data_layer1.to_crs(4326)

        def discretize(data, bins):
            split = np.array_split(np.sort(data), bins)
            cutoffs = [x[-1] for x in split]
            cutoffs = cutoffs[:-1]
            return cutoffs
        
        # Function to generate a color gradient from a colormap
        def generate_color_gradient(num_steps, colormap_name='YlOrBr'):
            cmap = plt.get_cmap(colormap_name)
            norm = mcolors.Normalize(vmin=0, vmax=num_steps - 1)
            return [mcolors.rgb2hex(cmap(norm(i))) for i in range(num_steps)]
        
        # Function to get color based on Jenks breaks
        def get_color_for_value(value, breaks, colors):
            if value is None:
                return '#808080'
            for i in range(len(breaks)):
                if value <= breaks[i]:
                    return colors[i]
            return colors[-1]
        
        # Function to define style for GeoJSON features
        def style_geojson(feature, gdf, values_column, num_classes, colormap_name='YlOrBr'):
            values = gdf[values_column[8]].dropna().values
            breaks = discretize(values, num_classes)
            colors = generate_color_gradient(num_classes, colormap_name)
            value = feature['properties'][values_column[8]]
            color = get_color_for_value(value, breaks, colors)
            return {
                'fillColor': color,
                'color': '#000000',
                'weight': 2,
                'fillOpacity': 0.7,
            }
        
        # Function to add GeoJSON layer to Folium map
        def add_geojson_layer(map_object, name, gdf, values_column, aliases, num_classes, show, colormap_name='YlOrBr'):
            geojson = folium.GeoJson(
                gdf,
                name=name,
                style_function=lambda feature: style_geojson(feature, gdf, values_column, num_classes, colormap_name),
                highlight_function=lambda x: {
                    'color': '#000000',
                    'weight': 5
                },
                tooltip=folium.GeoJsonTooltip(fields=values_column, aliases=aliases, localize=True),
                popup_keep_highlighted=True,
                popup=folium.GeoJsonPopup(fields=values_column, aliases=aliases, localize=True),
                overlay=False,
                control=True,
                show=show
            )
            geojson.add_to(map_object)
            return geojson

        center = [data_layer1.unary_union.convex_hull.centroid.y, data_layer1.unary_union.convex_hull.centroid.x]

        # Generate the legends
        values_data1 = data_layer1[cols_values1[8]].dropna().values
        values_data1 = [round(value, 2) for value in values_data1]
        breaks_data1 = discretize(values_data1, num_class)
        colors_data1 = generate_color_gradient(num_class, 'YlOrBr')

        legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; z-index: 1000; font-size: 14px; background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 5px;">'
        
        legend_html += '<b>Indice de qualité attributaire pour le diag1</b><br>'
        for i in range(len(breaks_data1) - 1):
            legend_html += f'<i style="background:{colors_data1[i]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> [{breaks_data1[i]} ; {breaks_data1[i+1]}[<br>'
        legend_html += f'<i style="background:{colors_data1[-1]};width:20px;height:20px;float:left;margin-right:8px;opacity:0.7;"></i> >= {breaks_data1[-1]}<br>'
        # legend_html += '<br>'
         
        legend_html += '</div>'

        # Create a Folium map centered on a location
        m = folium.Map(location=center, zoom_start=11, control_scale=True)

        # Add GeoJSON layers
        add_geojson_layer(m, 'diagnostic 1', data_layer1, cols_values1, cols_aliases1, num_class, True)
        
        # Add different tile layers to the map
        folium.TileLayer('openstreetmap').add_to(m)
        
        # Add Layer Control to toggle layers
        folium.LayerControl(collapsed=False).add_to(m)

        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save the map to an HTML file
        map_path = 'map_with_geojson.html'
        m.save(map_path)
        
        # # Use pywebview to open the map in a new browser window
        # webview.create_window('Map Viewer', url=f'file://{os.path.abspath(map_path)}', width=1280, height=720, resizable=True)
        # webview.start()

        webbrowser.open(f'file://{os.path.abspath(map_path)}', new=2)