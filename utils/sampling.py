# Standard Libs
import json
import os
import random

# Third-party Libs
import numpy as np
from openslide import OpenSlide

# Custom Libs
from annotation import LesionAnnotations


class PatchSampler:
    '''Sample patches from the given wsi'''

    def __init__(self, wsi_dir_in: str, masks_dir_in: str, annots_dir_in: str,
                 tumor_coords_dir_in: str, normal_coords_dir_in: str, patches_dir_out: str) -> None:
        '''Initialize the PatchSampler

        -Args
            wsi_dir_in:
            masks_dir_in:
            annots_dir_in:
            tumor_coords_dir_in:
            normal_coords_dir_in:
            patches_dir_out:

        - Returns
            None
        '''
        self.wsi_dir_in = wsi_dir_in
        self.masks_dir_in = masks_dir_in
        self.annots_dir_in = annots_dir_in
        self.tumor_coords_dir_in = tumor_coords_dir_in
        self.normal_coords_dir_in = normal_coords_dir_in
        self.patches_dir_out = patches_dir_out
        self.classes = ['tumor', 'normal']

        self.tumor_wsi_dir_in = os.path.join(self.wsi_dir_in, 'tumor')
        self.normal_wsi_dir_in = os.path.join(self.wsi_dir_in, 'normal')

        self.tumor_wsi_fnames = os.listdir(self.tumor_wsi_dir_in)
        self.normal_wsi_fnames = os.listdir(self.normal_wsi_dir_in)

    def sample_patches(self, num_patches: int, wsi_level: int = 0, patch_size: int = 300) -> None:

        os.makedirs(self.patches_dir_out, exist_ok=True)

        # Path to the .json file to save the list of sampled patches; (patient_id,coord_x,coord_y)
        patches_list_path = os.path.join(self.patches_dir_out, 'patches_list.json')
        if not os.path.exists(patches_list_path):
            patch_fnames = set()

            count = 0
            while count < num_patches:
                picked_class = random.choice(self.classes)
                if picked_class == 'tumor':
                    picked_wsi_fname = random.choice(self.tumor_wsi_fnames)
                    picked_patient_id = picked_wsi_fname.rstrip('.tif')
                    picked_wsi_path = os.path.join(self.tumor_wsi_dir_in, picked_wsi_fname)

                    picked_mask_fname = f'{picked_patient_id}.npy'
                    picked_mask_path = os.path.join(self.masks_dir_in, picked_mask_fname)

                    picked_annot_fname = f'{picked_patient_id}.json'
                    picked_annot_path = os.path.join(self.annots_dir_in, picked_annot_fname)

                    os.makedirs(self.tumor_coords_dir_in, exist_ok=True)

                    picked_coords_fname = f'{picked_patient_id}.json'
                    picked_coords_path = os.path.join(self.tumor_coords_dir_in, picked_coords_fname)
                    # Sample a tumor coordinate randomly
                    picked_coord = self.sample_tumor_coord(coords_path=picked_coords_path,
                                                            wsi_path=picked_wsi_path,
                                                            mask_path=picked_mask_path,
                                                            annot_path=picked_annot_path,
                                                            wsi_level=wsi_level)        
                elif picked_class == 'normal':
                    picked_wsi_fname = random.choice(self.normal_wsi_fnames)
                    picked_wsi_path = os.path.join(self.normal_wsi_dir_in, picked_wsi_fname)
                    picked_patient_id = picked_wsi_fname.rstrip('.tif')

                    picked_mask_fname = f'{picked_patient_id}.npy'
                    picked_mask_path = os.path.join(self.masks_dir_in, picked_mask_fname)

                    os.makedirs(self.normal_coords_dir_in, exist_ok=True)

                    picked_coords_fname = f'{picked_patient_id}.json'
                    picked_coords_path = os.path.join(self.normal_coords_dir_in, picked_coords_fname)
                    # Sample a normal coordinate randomly
                    picked_coord = self.sample_normal_coord(coords_path=picked_coords_path,
                                                            wsi_path=picked_wsi_path,
                                                            mask_path=picked_mask_path,
                                                            wsi_level=wsi_level)

                coord_x, coord_y = picked_coord
                patch_fname = f'{picked_patient_id},{coord_x},{coord_y}'
                if not patch_fname in patch_fnames:
                    patch_fnames.add(patch_fname)
                    count += 1
                    print(f'{count}-th patch {patch_fname} was added to list')
            # while-statement ended

            num_patch_fnames = len(patch_fnames)
            assert num_patch_fnames == num_patches
            patches_dict = dict()
            patches_dict['num_patches'] = num_patch_fnames
            patches_dict['patches'] = list(patch_fnames)
            with open(patches_list_path, 'w+', encoding='utf-8') as f:
                json.dump(patches_dict, f, indent=4)
        # Root if-statement ended

        # Just load patches list if it already exists
        with open(patches_list_path, 'r', encoding='utf-8') as f:
            patches_dict = json.load(f)

        patch_fnames = patches_dict['patches']
        for (i, fname) in enumerate(patch_fnames, 1):
            patch_fname = fname.strip('\n')
            patient_id, center_x, center_y = patch_fname.split(',')
            center_x = int(center_x)
            center_y = int(center_y)
            # Top left coordinate of patch
            start_x = center_x - (patch_size // 2)
            start_y = center_y - (patch_size // 2)

            if patient_id.startswith('tumor'):
                wsi_fname = f'{patient_id}.tif'
                wsi_path = os.path.join(self.tumor_wsi_dir_in, wsi_fname)
            else:
                wsi_fname = f'{patient_id}.tif'
                wsi_path = os.path.join(self.normal_wsi_dir_in, wsi_fname)

            slide = OpenSlide(wsi_path)
            patch = slide.read_region(location=(start_x, start_y),
                                    level=wsi_level,
                                    size=(patch_size, patch_size))
            patch = patch.convert('RGB')
            patch_path = os.path.join(self.patches_dir_out, f'{patch_fname}.png')
            patch.save(patch_path)

            print(f'{i}-th {patch_fname} is saved in {self.patches_dir_out}')

    def sample_tumor_coord(self, coords_path: str, wsi_path: str, mask_path: str,
                           annot_path: str, wsi_level: int = 0):
        '''Sample a center coordinate of a normal patch from
    
        - Args
            coords_path: Path to the pre-sampled tumor coordinates
            wsi_path: Path to the wsi
            mask_path: Path to the binary mask of wsi
            annot_path: Path to the annotations directory
            wsi_level: Level of the given wsi

        - Returns
            A center coordinate of tumor patch; tuple of int
        '''
        # If the cache of tumor coordinates(tumor_coords.json) does not exist
        if not os.path.exists(coords_path):
            slide = OpenSlide(wsi_path)
            slide_width, slide_height = slide.level_dimensions[wsi_level]

            roi_mask = np.load(mask_path)
            roi_mask_width, roi_mask_height = roi_mask.shape

            assert (slide_width // roi_mask_width) == (slide_height // roi_mask_height), \
                f'Dimension does not match: slide_width({slide_width})//mask_width({roi_mask_width}) != \
                    slide_height({slide_height})//mask_height({roi_mask_height})'

            resolution = slide_width // roi_mask_width

            roi_x_coords, roi_y_coords = np.where(roi_mask)
            roi_coords = zip(roi_x_coords, roi_y_coords)
            roi_coords = list(roi_coords)
            roi_coords = [self.scale_coord(coord, resolution) for coord in roi_coords]
            roi_coords = np.array(roi_coords)

            lesion_annots = LesionAnnotations(annot_path)
            tumor_coords = lesion_annots.filter_tumor_coords(coords_path, roi_coords, is_pos=True)
        # If the cache of tumor coordinates(tumor_coords.json) exists
        else:
            with open(coords_path, 'r', encoding='utf-8') as f:
                tumor_coords_dict = json.load(f)
                tumor_coords = tumor_coords_dict['tumor_coords']

        picked_tumor_coord = random.choice(tumor_coords)

        return picked_tumor_coord

    def sample_normal_coord(self, coords_path: str, wsi_path: str,
                            mask_path: str, wsi_level: int = 0) -> tuple:
        '''Sample a center coordinate of a normal patch from uniform distribution.

        - Args
            coords_path: Path to the pre-sampled normal coordinates
            mask_path: Path to the binary mask of wsi
            wsi_path: Path to the wsi

        - Returns
            A center coordinate of a normal patch; tuple of int
        '''
        # If the cache of normal coordinates(normal_coords.json) does not exist
        if not os.path.exists(coords_path):
            slide = OpenSlide(wsi_path)
            slide_width, slide_height = slide.level_dimensions[wsi_level]

            roi_mask = np.load(mask_path)
            roi_mask_width, roi_mask_height = roi_mask.shape

            assert (slide_width // roi_mask_width) == (slide_height // roi_mask_height), \
                f'Dimension does not match: slide_width({slide_width})//mask_width({roi_mask_width}) != \
                    slide_height({slide_height})//mask_height({roi_mask_height})'

            resolution = slide_width // roi_mask_width

            roi_x_coords, roi_y_coords = np.where(roi_mask)
            roi_x_coords = roi_x_coords.tolist()
            roi_y_coords = roi_y_coords.tolist()

            # Scale roi coordinates because the level of wsi and its mask can be different
            roi_coords = zip(roi_x_coords, roi_y_coords)
            roi_coords = list(roi_coords)
            roi_coords = [self.scale_coord(coord, resolution) for coord in roi_coords]
            num_roi_coords = len(roi_coords)

            roi_coords_dict = dict()
            roi_coords_dict['num_coords'] = num_roi_coords
            roi_coords_dict['normal_coords'] = roi_coords

            with open(coords_path, 'w+', encoding='utf-8') as f:
                json.dump(roi_coords_dict, f, indent=4)
        # If the cache of normal coordinates(normal_coords.json) exists
        else:
            with open(coords_path, 'r', encoding='utf-8') as f:
                roi_coords_dict = json.load(f)
                roi_coords = roi_coords_dict['normal_coords']

        # Select an roi coordinate randomly
        picked_roi_coord = random.choice(roi_coords)

        return picked_roi_coord

    def scale_coord(self, coord: tuple, resolution: int) -> tuple:
        '''Scale the given coordinates correspoding resolution.

        - Args
            coords: A tuple of coordinates to scale
            resolution: Resolution to scale coordinates
        '''
        coord_x, coord_y = coord
        scaled_coord_x = coord_x * resolution
        scaled_coord_y = coord_y * resolution

        return scaled_coord_x, scaled_coord_y


if __name__ == '__main__':
    ROOT_DIR = os.path.abspath('.')

    WSI_DIR = r'/ssd-ext/dataset'
    TRAIN_WSI_DIR = os.path.join(WSI_DIR, 'train')
    VALID_WSI_DIR = os.path.join(WSI_DIR, 'valid')

    MASKS_DIR = os.path.join(ROOT_DIR, 'results', 'masks')
    ANNOTS_DIR = os.path.join(ROOT_DIR, 'annots')
    TRAIN_ANNOTS_DIR = os.path.join(ANNOTS_DIR, 'train', 'json')

    PATCHES_DIR = os.path.join(ROOT_DIR, 'data')
    TRAIN_PATCHES_DIR = os.path.join(PATCHES_DIR, 'train')
    VALID_PATCHES_DIR = os.path.join(PATCHES_DIR, 'valid')

    CACHES_DIR = os.path.join(ROOT_DIR, 'caches')
    COORDS_DIR = os.path.join(CACHES_DIR, 'coordinates')
    TUMOR_COORDS_DIR = os.path.join(COORDS_DIR, 'tumor')
    NORMAL_COORDS_DIR = os.path.join(COORDS_DIR, 'normal')

    NUM_TRAIN_PATCHES = 10000
    NUM_VALID_PATCHES = 10000

    train_patch_sampler = PatchSampler(wsi_dir_in=TRAIN_WSI_DIR,
                                       masks_dir_in=MASKS_DIR,
                                       annots_dir_in=TRAIN_ANNOTS_DIR,
                                       tumor_coords_dir_in=TUMOR_COORDS_DIR,
                                       normal_coords_dir_in=NORMAL_COORDS_DIR,
                                       patches_dir_out=TRAIN_PATCHES_DIR)

    train_patch_sampler.sample_patches(num_patches=NUM_TRAIN_PATCHES)

    valid_patch_sampler = PatchSampler(wsi_dir_in=VALID_WSI_DIR,
                                       masks_dir_in=MASKS_DIR,
                                       annots_dir_in=TRAIN_ANNOTS_DIR,
                                       tumor_coords_dir_in=TUMOR_COORDS_DIR,
                                       normal_coords_dir_in=NORMAL_COORDS_DIR,
                                       patches_dir_out=VALID_PATCHES_DIR)
                                       
    valid_patch_sampler.sample_patches(num_patches=NUM_VALID_PATCHES)

