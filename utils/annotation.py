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
            coords: Numpy array containing coordinates;
                    [(x1,y1), (x2,y2), ... ,(xn,yn)] of shape (n, 2)

        - Returns
            None
        '''
        self.name = name
        self.coords = coords

    def coordinates(self) -> None:
        '''Returns annotation coordinates; vertices'''
        return self.coords

    def __repr__(self) -> str:
        return self.name

    def does_contain(self, points: list) -> Sequence[bool]:
        '''Check if the Annotation object contains the given coordinate.

        - Args
            points: A list of points to perform the test

        - Returns
            True if the given coorindate is inside the Annotation object,
            False otherwise
        '''
        return points_in_poly(points, self.coords)


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

        self.annots_dict = {
            'pos': self.pos_annots,
            'neg': self.neg_annots,
        }

    def filter_tumor_coords(self, save_path: str,
                            points: np.ndarray, is_pos: bool = True) -> np.ndarray:
        '''Filter tumor coords from the given points.

        - Args
            save_dir: Path to json file to save the tumor coordinates
            points: Roi points to check if each of them is a tumor
            is_pos: True if to filter positive tumor, False otherwise

        - Returns
            A numpy array which contains tumor coordinates; points inside annotations
        '''
        if is_pos:
            annots = self.pos_annots
        else:
            annots = self.neg_annots

        tumor_coords_dict = defaultdict(list)
        tumor_coords_dict['patient_id'] = self.patient_id
        tumor_coords_dict['num_coords'] = 0

        for annot in annots:
            tumor_coords_mask = annot.does_contain(points)
            tumor_coords = points[tumor_coords_mask]
            tumor_coords = tumor_coords.tolist()
            tumor_coords_dict['tumor_coords'].extend(tumor_coords)
            tumor_coords_dict['num_coords'] += len(tumor_coords)

        with open(save_path, 'w+', encoding='utf-8') as f:
            json.dump(tumor_coords_dict, f, indent=4)

        return tumor_coords_dict['tumor_coords']

    def does_contain(self, points: Sequence[tuple], is_pos: bool = True) -> bool:
        '''Check if the Annotation object contains the given coordinate.

        - Args
            points: A list of points to perform the test
            is_pos: True if to check positive tumor, False otherwise

        - Returns
            True if the given coorindate is inside the Annotation object,
            False otherwise
        '''
        num_points = len(points)

        coords_mask_dict = defaultdict(list)
        if num_points > 1:
            if is_pos:
                annots = self.pos_annots
            else:
                annots = self.neg_annots

            for annot in annots:
                coords_mask = annot.does_contain(points=points)
                coords_mask_dict[annot.name] = coords_mask

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
    def coords(self) -> dict:
        '''Return the entire coordinates of shape (num_annotations, 2)

        - Args
            is_pos: True if the target annotations are positive, False otherwise

        - Returns
            A dict containing every positive/negative coordinates of each annotation
        '''
        pos_coords = [annot.coords for annot in self.pos_annots]
        neg_coords = [annot.coords for annot in self.neg_annots]
        coords_dict = {
            'pos': pos_coords,
            'neg': neg_coords,
        }

        return coords_dict

    @property
    def annots(self) -> dict:
        '''Return the entire annotations.

        - Returns
            A dict contaning every positive/negative annotations
        '''
        return self.annots_dict


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
        if 'Annotation' not in annot_name:
            annot_name = f'Annotation{annot_name}'

        json_annot['neg'].append({
            'name': annot_name,
            'coords': coords,
        })

    with open(json_path_out, 'w', encoding='utf-8') as f:
        json.dump(json_annot, f, indent=1)


if __name__ == '__main__':
    ROOT_DIR = os.path.abspath('.')
    ANNOTS_DIR = os.path.join(ROOT_DIR, 'annots')
    TRAIN_ANNOTS_DIR = os.path.join(ANNOTS_DIR, 'train')
    TRAIN_XML_ANNOTS_DIR = os.path.join(TRAIN_ANNOTS_DIR, 'xml')
    TRAIN_JSON_ANNOTS_DIR = os.path.join(TRAIN_ANNOTS_DIR, 'json')

    TEST_ANNOTS_DIR = os.path.join(ANNOTS_DIR, 'test')
    TEST_XML_ANNOTS_DIR = os.path.join(TEST_ANNOTS_DIR, 'xml')
    TEST_JSON_ANNOTS_DIR = os.path.join(TEST_ANNOTS_DIR, 'json')

    # Convert training annotations
    os.makedirs(TRAIN_JSON_ANNOTS_DIR, exist_ok=True)
    train_json_annot_fnames = os.listdir(TRAIN_JSON_ANNOTS_DIR)

    train_xml_annot_fnames = os.listdir(TRAIN_XML_ANNOTS_DIR)
    train_xml_annot_fnames = [fname.strip('.xml') for fname in train_xml_annot_fnames]
    train_xml_annot_fnames = sorted(train_xml_annot_fnames)
    for fname in train_xml_annot_fnames:
        if f'{fname}.json' not in train_json_annot_fnames:
            xml_path = os.path.join(TRAIN_XML_ANNOTS_DIR, f'{fname}.xml')
            json_path = os.path.join(TRAIN_JSON_ANNOTS_DIR, f'{fname}.json')
            xml_to_json(xml_path_in=xml_path, json_path_out=json_path)
            print(f'Converted {fname}.xml to {fname}.json')

    # Convert test annotations
    os.makedirs(TEST_JSON_ANNOTS_DIR, exist_ok=True)
    test_json_annot_fnames = os.listdir(TEST_JSON_ANNOTS_DIR)

    test_xml_annot_fnames = os.listdir(TEST_XML_ANNOTS_DIR)
    test_xml_annot_fnames = [fname.strip('.xml') for fname in test_xml_annot_fnames]
    test_xml_annot_fnames = sorted(test_xml_annot_fnames)
    for fname in test_xml_annot_fnames:
        if f'{fname}.json' not in test_json_annot_fnames:
            xml_path = os.path.join(TEST_XML_ANNOTS_DIR, f'{fname}.xml')
            json_path = os.path.join(TEST_JSON_ANNOTS_DIR, f'{fname}.json')
            xml_to_json(xml_path_in=xml_path, json_path_out=json_path)
            print(f'Converted {fname}.xml to {fname}.json')
