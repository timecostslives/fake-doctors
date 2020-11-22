import logging
import ntpath
import os

import matplotlib.pyplot as plt
import numpy as np
import skimage.filters
from openslide import OpenSlide
from skimage.color import rgb2hsv


def generate_roi_mask(wsi_path_in: str, mask_path_out: str,
                      wsi_level: int=6, min_rgb: int=50) -> None:
    '''Generate binary mask to extract roi(tissue region) from whole slide image.

    - Args
        wsi_path_in:
        wsi_level:
        mask_path_out:
        min_rgb:

    - Returns
        None
    '''

    logging.basicConfig(level=logging.INFO)

    slide = OpenSlide(wsi_path_in)
    slide_width, slide_height = slide.level_dimensions[wsi_level] # (1) shape of (width, height)

    # Starting point to read(crop) image
    start_x, start_y = 0, 0 # top left coordinate of whole slide image

    image = slide.read_region(location=(start_x, start_y),
                              level=wsi_level,
                              size=(slide_width, slide_height))

    rgb_image = image.convert('RGB')
    rgb_image = np.transpose(rgb_image, axes=[1, 0, 2]) # shape of (height, width, channels); transpose of (1)

    hsv_image = rgb2hsv(rgb_image)

    r_channel = rgb_image[:, :, 0]
    g_channel = rgb_image[:, :, 1]
    b_channel = rgb_image[:, :, 2]
    h_channel = hsv_image[:, :, 1]

    r_threshold = skimage.filters.threshold_otsu(r_channel)
    g_threshold = skimage.filters.threshold_otsu(g_channel)
    b_threshold = skimage.filters.threshold_otsu(b_channel)
    h_threshold = skimage.filters.threshold_otsu(h_channel)

    r_channel_mask = r_channel > r_threshold
    g_channel_mask = g_channel > g_threshold
    b_channel_mask = b_channel > b_threshold

    rgb_tissue_mask = r_channel_mask & b_channel_mask & g_channel_mask
    rgb_tissue_mask = np.logical_not(rgb_tissue_mask)

    h_tissue_mask = h_channel > h_threshold

    min_r_mask = r_channel > min_rgb
    min_g_mask = g_channel > min_rgb
    min_b_mask = b_channel > min_rgb

    # ROI: Tissue reion in the slide
    roi_mask = h_tissue_mask & rgb_tissue_mask & min_r_mask & min_g_mask & min_b_mask

    np.save(mask_path_out, roi_mask)


def mask_to_image(mask_path_in: str, save_dir_out: str,
                  cmap: str = 'gray', format: str = 'png') -> None:
    '''Save the given mask(np.ndarray) to image.
    
    - Args
        mask_path_in:
        save_dir_out:
        cmap: 
        format:

    - Returns
        None
    '''
    if not os.path.exists(save_dir_out):
        os.mkdir(save_dir_out)

    mask = np.load(mask_path_in)
    mask = np.transpose(mask) # becuase openslide's shape is (width, height); numpy (height, width)
    mask_fname = ntpath.basename(mask_path_in)

    patient_id = mask_fname.rstrip('.npy')

    image_fname = f'{patient_id}.png'
    image_path = os.path.join(save_dir_out, image_fname) # path to save image
    plt.imsave(fname=image_path,
               arr=mask,
               cmap=cmap,
               format=format)

    print(f'Mask of {patient_id} was converted to image and saved to {image_path}')


if __name__ == '__main__':
    ROOT_DIR = os.path.abspath('.')
    DATA_DIR = '/ssd-ext/dataset'
    TRAIN_WSI_DIR = os.path.join(DATA_DIR, 'train')
    VALID_WSI_DIR = os.path.join(DATA_DIR, 'valid')
    MASKS_DIR = os.path.join(ROOT_DIR, 'results', 'masks')
    IMAGES_DIR = os.path.join(MASKS_DIR, 'images')

    os.makedirs(MASKS_DIR, exist_ok=True)

    # Generate training tumor slide masks
    train_tumor_wsi_dir = os.path.join(TRAIN_WSI_DIR, 'tumor')
    train_tumor_wsi_fnames = os.listdir(train_tumor_wsi_dir)
    train_tumor_wsi_fnames = sorted(train_tumor_wsi_fnames)
    for fname in train_tumor_wsi_fnames:
        wsi_path = os.path.join(train_tumor_wsi_dir, fname)

        patient_id = fname.rstrip('.tif')

        mask_fname = f'{patient_id}.npy'
        mask_fnames = os.listdir(MASKS_DIR)
        mask_path = os.path.join(MASKS_DIR, mask_fname)
        if mask_fname not in mask_fnames:
            generate_roi_mask(wsi_path_in=wsi_path,
                            mask_path_out=mask_path)
            print(f'Mask of {patient_id} was saved at {MASKS_DIR}')

    # Generate training normal slide masks
    train_normal_wsi_dir = os.path.join(TRAIN_WSI_DIR, 'normal')
    train_normal_wsi_fnames = os.listdir(train_normal_wsi_dir)
    train_normal_wsi_fnames = sorted(train_normal_wsi_fnames)
    for fname in train_normal_wsi_fnames:
        wsi_path = os.path.join(train_normal_wsi_dir, fname)

        patient_id = fname.rstrip('.tif')

        mask_fname = f'{patient_id}.npy'
        mask_fnames = os.listdir(MASKS_DIR)
        mask_path = os.path.join(MASKS_DIR, mask_fname)
        if mask_fname not in mask_fnames:
            generate_roi_mask(wsi_path_in=wsi_path,
                            mask_path_out=mask_path)
        print(f'Mask of {patient_id} was saved at {MASKS_DIR}')

    # Generate validation tumor slide masks
    valid_tumor_wsi_dir = os.path.join(VALID_WSI_DIR, 'tumor')
    valid_tumor_wsi_fnames = os.listdir(valid_tumor_wsi_dir)
    valid_tumor_wsi_fnames = sorted(valid_tumor_wsi_fnames)
    for fname in valid_tumor_wsi_fnames:
        wsi_path = os.path.join(valid_tumor_wsi_dir, fname)

        patient_id = fname.rstrip('.tif')

        mask_fname = f'{patient_id}.npy'
        mask_fnames = os.listdir(MASKS_DIR)
        mask_path = os.path.join(MASKS_DIR, mask_fname)
        if mask_fname not in mask_fnames:
            generate_roi_mask(wsi_path_in=wsi_path,
                            mask_path_out=mask_path)
            print(f'Mask of {patient_id} was saved at {MASKS_DIR}')

    # Generate validation normal slide masks
    valid_normal_wsi_dir = os.path.join(VALID_WSI_DIR, 'normal')
    valid_normal_wsi_fnames = os.listdir(valid_normal_wsi_dir)
    valid_normal_wsi_fnames = sorted(valid_normal_wsi_fnames)
    for fname in valid_normal_wsi_fnames:
        wsi_path = os.path.join(valid_normal_wsi_dir, fname)

        patient_id = fname.rstrip('.tif')

        mask_fname = f'{patient_id}.npy'
        mask_path = os.path.join(MASKS_DIR, mask_fname)
        generate_roi_mask(wsi_path_in=wsi_path,
                          mask_path_out=mask_path)
        print(f'Mask of {patient_id} was saved at {MASKS_DIR}')

    # Convert the masks to images and save them all
    mask_fnames = os.listdir(MASKS_DIR)
    mask_fnames = [fname for fname in mask_fnames if fname.endswith('.npy')]
    mask_fnames = sorted(mask_fnames)
    
    for fname in mask_fnames:
        mask_path = os.path.join(MASKS_DIR, fname)
        mask_to_image(mask_path_in=mask_path,
                      save_dir_out=IMAGES_DIR)