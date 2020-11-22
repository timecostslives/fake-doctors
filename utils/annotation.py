# import copy
import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Sequence

import numpy as np
from skimage.measure import points_in_poly


class Annotation:
    '''Represents an annotation using a coordinates array of shape (n, 2).'''

    def __init__(self, name: str, coords: np.ndarray) -> None:
        '''Initialize a Annotation object.
        
        - Args
            name: Name of the Annotation object
            coords: Numpy array containing coordinates [(x1,y1), (x2,y2), ... ,(xn,yn)] of shape (n, 2)

        - Returns
            None
        '''
        self.name = name
        self.coords = coords

    @property
    def name(self) -> str:
        '''Getter of property *name*'''
        return self.name
    
    @property
    def coords(self) -> np.ndarray:
        '''Getter of property *coords*'''
        return self.coords

    @name.setter
    def name(self, name: str) -> None:
        self.name = name

    @coords.setter
    def coords(self, coords: np.ndarray) -> None:
        self.coords = coords

    def __repr__(self) -> str:
        return self.name

    def does_contain(self, points: list) -> Sequence[bool]: # Warn -> repair to coord: tuple
        '''Check if the Annotation object contains the given coordinate.
        
        - Args
            points: A list of points to perform the test

        - Returns
            True if the given coorindate is inside the Annotation object,
            False otherwise
        '''
        return points_in_poly(points, self.coords) # Warn -> repair to [coord] | points_in_poly(points, self.coords)[0]

    # @property
    # def coordinates(self) -> np.ndarray:
    #     '''Getter of '''
    #     return self.coords

    
class LesionAnnotations:
    '''Represents an annotation drawn on a whole slide image.'''

    def __init__(self, annot_path: str) -> None:
        '''Init LesionAnnotations.'''

        self.annot_path = annot_path
        self.annot_fname = Path(self.annot_path).name
        self.patient_id = self.annot_fname.rstrip('.json')

        with open(annot_path, 'r', encoding='utf-8') as f:
            lesion_annots = json.load(f)
        
        # Parse positive annotations
        self.pos_annots = []
        for annot in lesion_annots['pos']:
            annot_name = annot['name']
            coords = annot['coords'] # annot['vertices'], originally in ncrf code
            pos_annot = Annotation(name=annot_name, coords=coords)
            self.pos_annots.append(pos_annot)

        # Parse negative annotations
        self.neg_annots = []
        for annot in lesion_annots['neg']:
            annot_name = annot['name']
            coords = annot['coords']
            neg_annot = Annotation(name=annot_name, coords=coords)
            self.neg_annots.append(neg_annot)

    def filter_tumor_coords(self, save_path: str, points: np.ndarray, is_pos: bool = True) -> np.ndarray:
        '''Filter tumor coords from the given points.
        
        - Args
            save_dir: Path to json file to save the tumor coordinates
            points: Roi points to check if each of them is a tumor
            is_pos: True if to filter positive tumor, False otherwise

        - Returns
            A numpy array which contains tumor coordinates; points inside annotations
        '''
        # tumor_coords_mask = np.zeros_like(points, dtype=bool)
        
        if is_pos:
            annots = self.pos_annots
        else:
            annots = self.neg_annots

        tumor_coords_dict = defaultdict(list)
        tumor_coords_dict['patient_id'] = self.patient_id
        tumor_coords_dict['num_coords'] = 0
        # entire_tumor_coords = []
        for annot in annots:
            tumor_coords_mask = annot.does_contain(points)
            # print(f'tumor_coords_mask: {tumor_coords_mask}')
            tumor_coords = points[tumor_coords_mask]
            tumor_coords = tumor_coords.tolist()
            # print(f'tumor_coords: {tumor_coords}')
            tumor_coords_dict['tumor_coords'].extend(tumor_coords)
            tumor_coords_dict['num_coords'] += len(tumor_coords)
            # entire_tumor_coords.extend(tumor_coords)
            # print(f'entire_tumor_coords: {entire_tumor_coords}')        
            
        # save_path = os.path.join(save_dir, self.annot_fname)
        with open(save_path, 'w+', encoding='utf-8') as f:
            json.dump(tumor_coords_dict, f, indent=4)
            # for coord in entire_tumor_coords:
            #     x_coord, y_coord = coord
            #     f.write(f'{x_coord},{y_coord}\n')
            #     print(f'{x_coord}, {y_coord} were written in {save_path}')

            # for (i, point) in enumerate(points):
            #     print(f'Testing point: {point} {i}/{num_points}')
            #     for annot in annots:
            #         if annot.deos_contain(points=[point]):

            #             tumor_coords_mask[i] = True
            #         else:
            #             tumor_coords_mask[i] = False
            


        # return entire_tumor_coords
        return tumor_coords_dict['tumor_coords']

    def does_contain(self, points: Sequence[tuple], is_pos: bool = True) -> bool: # Warn: repair to coord: tuple
        '''Check if the Annotation object contains the given coordinate.
        
        - Args
            points: A list of points to perform the test
            is_pos: True if to check positive tumor, False otherwise

        - Returns
            True if the given coorindate is inside the Annotation object,
            False otherwise
        '''
        num_points = len(points)
        print(f'Number of points: {num_points}')
        # coords_mask = np.zeros_like(points, dtype=bool)
        coords_mask_dict = defaultdict(list)
        if num_points > 1:
            if is_pos:
                annots = self.pos_annots
            else:
                annots = self.neg_annots
            
            for annot in annots:
                coords_mask = annot.does_contain(points=points)
                coords_mask_dict[annot.name] = coords_mask
            # for (i, point) in enumerate(points):
            #     print(f'Testing point: {point} {i}/{num_points}')
            #     for annot in annots:
            #         if annot.does_contain(points=[point]):
            #             coords_mask[i] = True
            #         else:
            #             coords_mask[i] = False
            # return coords_mask
            return coords_mask_dict
           

        if is_pos:
            annots = self.pos_annots
        else:
            annots = self.neg_annots

        for annot in annots:
            if annot.does_contain(points=points): # Warn: repair to coord=coord
                return True
            
        return False

    def __repr__(self):
        return self.annot_fname

    @property
    def coordinates(self, is_pos: bool) -> list:
        '''Return the entire coordinates of shape (num_annotations, 2)

        - Args
            is_pos: True if the target annotations are positive, False otherwise

        - Returns
            A list containing every coordinates of each annotation
        '''
        if is_pos:
            pos_coords = [annot.coords for annot in self.pos_annots]
            return pos_coords
        else:
            neg_coords = [annot.coords for annot in self.neg_annots]
            return neg_coords

    @property
    def annotations(self, is_pos: bool) -> Sequence[list]:
        '''Return the entire annotations.

        - Args
            is_pos: True if the target annotations are positive, False otherwise

        - Returns
            A list contaning every positive/negative annotations
        '''
        if is_pos:
            return self.pos_annots
        else:
            return self.neg_annots



def xml_to_json(xml_path_in: str, json_path_out: str) -> None:
    '''Convert xml annotation to json
    
    - Args
        xml_in_path: Path to the input xml annotation file
        json_out_path: Path to save the output json annotation file

    - Returns
        None
    '''

    xml_annot = ET.parse(xml_path_in)
    xml_annot_root = xml_annot.getroot()
    
    tumor_annot_route = './Annotations/Annotation[@PartOfGroup="Tumor"]'
    tumor_annots = xml_annot_root.findall(tumor_annot_route)
    
    cls_0_annot_route = './Annotations/Annotation[@PartOfGroup="_0"]'
    cls_0_annots = xml_annot_root.findall(cls_0_annot_route)

    cls_1_annot_route = './Annotations/Annotation[@PartOfGroup="_1"]'
    cls_1_annots = xml_annot_root.findall(cls_1_annot_route)

    cls_2_annot_route = './Annotations/Annotation[@PartOfGroup="_2"]'
    cls_2_annots = xml_annot_root.findall(cls_2_annot_route)

    pos_annots = tumor_annots + cls_0_annots + cls_1_annots
    neg_annots = cls_2_annots

    json_annot = defaultdict(list)
    json_annot['pos'] = []
    json_annot['neg'] = []
    # Parse positive annotations
    for annot in pos_annots:
        coords = annot.findall('./Coordinates/Coordinate')
        x_coords = []
        y_coords = []
        for coord in coords:
            # Parse x coordinates
            x_coord = coord.get('X') # type(x_coord) == 'str'
            x_coord = float(x_coord) # type(x_coord) == 'float'
            x_coord = int(x_coord) # type(x_coord) == 'int'
            x_coords.append(x_coord)

            # Parse y coordinates
            y_coord = coord.get('Y') # type(x_coord) == 'str'
            y_coord = float(y_coord) # type(x_coord) == 'float'
            y_coord = int(y_coord) # type(x_coord) == 'int'
            y_coords.append(y_coord)
        
        # Concat x=[x1, x2, ...], y=[y1, y2, ...] to coords=[(x1,y1), (x2,y2), ...]
        coords = np.c_[x_coords, y_coords]
        coords = coords.tolist() # because np.ndarray is not json serializable
        annot_name = annot.attrib['Name']
        json_annot['pos'].append({
            'name': f'Annotation{annot_name}',
            'coords': coords,
        })
    
    # Parse negative annotations
    for annot in neg_annots:
        coords = annot.findall('./Coordinates/Coordinate')
        x_coords = []
        y_coords = []
        for coord in coords:
            # Parse x coordinates
            x_coord = coord.get('X') # type(x_coord) == 'str'
            x_coord = float(x_coord) # type(x_coord) == 'float'
            x_coord = int(x_coord) # type(x_coord) == 'int'
            x_coords.append(x_coord)

            # Parse y coordinates
            y_coord = coord.get('Y') # type(y_coord) == 'str'
            y_coord = float(y_coord) # type(y_coord) == 'float'
            y_coord = int(y_coord) # type(y_coord) == 'int'
            y_coords.append(y_coord)

        # Concat x=[x1, x2, ...], y=[y1, y2, ...] to coords=[(x1,y1), (x2,y2), ...]
        coords = np.c_[x_coords, y_coords]
        coords = coords.tolist() # because np.ndarray is not json serializable
        annot_name = annot.attrib['Name']
        # annot_name = f'Annotation{annot_name}' if 'Annotation' not in annot_name else annot_name
        if 'Annotation' not in annot_name:
            annot_name = f'Annotation{annot_name}'

        json_annot['neg'].append({
            # 'name': f'Annotation{annot_name}',
            'name': annot_name,
            'coords': coords,
        })

    with open(json_path_out, 'w', encoding='utf-8') as f:
        json.dump(json_annot, f, indent=1)


if __name__ == '__main__':
    ROOT_DIR = os.path.abspath('..')
    ANNOT_DIR = os.path.join(ROOT_DIR, 'annotations')
    XML_ANNOT_DIR = os.path.join(ANNOT_DIR, 'xml')
    JSON_ANNOT_DIR = os.path.join(ANNOT_DIR, 'json')

    xml_annot_fnames = os.listdir(XML_ANNOT_DIR)
    xml_annot_fnames = [fname.strip('.xml') for fname in xml_annot_fnames]
    for fname in xml_annot_fnames:
        xml_path = os.path.join(XML_ANNOT_DIR, f'{fname}.xml')
        json_path = os.path.join(JSON_ANNOT_DIR, f'{fname}.json')
        xml_to_json(xml_path_in=xml_path, json_path_out=json_path)