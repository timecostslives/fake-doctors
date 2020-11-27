# Project Fake Doctors

**Simple Deep learning tools for Bio-informatics & Digital Pathology.**

- Due to the compatibility issue of the Openslide library, only installation in Ubuntu environment is now supported.
  We promise to support you on all platforms as soon as possible.
  
It is not a stable project yet, so there maybe some minor|majgor bugs.
We will provide a complete product in the near future, so we ask for your patience.

## Installation
```python3 -m pip install fake-doctors -U```

## Download Datasets

Now support only Camelyon16 whole slide image dataset(train/test).

- **Warning:** There is an issue related to the [wget](https://pypi.org/project/wget/) library, so debugging is in progress.
If it is confirmed that a problem with wget lib itself, we will migrate to a more stable library such as [requests](https://requests.readthedocs.io/en/master/).


**※ 800GB+ or free storage is required.**

In the near future, we will provide a lightweight benchmark dataset of dozens of gigabytes for computer vision research in the field of digital pathology.

```python
from fake_doctors.dataset import Camelyon16

downloader = Camelyon16(urls_dir_in=/path/to/cache/download/urls,
                        wsi_dir_out=/path/to/save/dataset,
                        annots_dir_out=/path/to/save/annotations)
                        
# Download training data
downloader.download_trainset()
# Split training/validation data
downloader.split_train_valid(ratio=0.2)

# Download test data
downloader.download_testset()
```

## Convert XML annotation to JSON

```python
from fake_doctors.annotation import xml_to_json

xml_to_json(xml_path_in=/path/to/xml/annotations,
            json_path_out=/path/to/save/json/annotations)
```

## Extract ROI from whole slide image(convert to binary mask)

```python
from fake_doctors.mask import generate_roi_mask

generate_roi_mask(wsi_path_in=/path/to/dataset,
                  mask_path_out=/path/to/save/mask)
```

## Filter tumor coordinates from whole slide image

```python
from fake_doctors.annotation import LesionAnnotations

lesion_annots = LesionAnnotations(annot_path=/path/to/annotation)
tumor_coords = lesion_annots.filter_tumor_coords(save_dir='/path/to/save/tumor/coords/list,
                                                 points=coordinates,
                                                 is_pos=True)
```

## Sample train/valid patch images

```python
from fake_doctors.sampling import 

num_train_patches = 2000000
num_valid_patches = 20000

train_patch_sampler = PatchSampler(wsi_dir_in=/path/to/dataset/dir
                                   masks_dir_in=/path/to/dataset/masks/dir,
                                   annots_dir_in=/path/to/annotations/dir,
                                   tumor_coords_dir_in=/path/to/tumor/coordinates/cache,
                                   normal_coords_dir_in=/path/to/normal/coordinates/cache,
                                   patches_dir_out=/path/to/save/sampled/patches)
                                   
valid_patch_sampler = PatchSampler(wsi_dir_in=/path/to/dataset/dir
                                   masks_dir_in=/path/to/dataset/masks/dir,
                                   annots_dir_in=/path/to/annotations/dir,
                                   tumor_coords_dir_in=/path/to/tumor/coordinates/cache,
                                   normal_coords_dir_in=/path/to/normal/coordinates/cache,
                                   patches_dir_out=/path/to/save/sampled/patches)
                                   
train_patch_sampler.sample_patches(num_patches=num_train_patches)
valid_patch_sampler.sample_patches(num_patches=num_valid_patches)
```

## Prototyping metastasis classifier model and training

- **Working in progress:**<br>
  The model used in our project is still being trained. 
  After the model has completely converged, it will be released as soon as the stability of the model is proven,
  because otherwise, it can confuse users or learners.
  Since transfer learning cannot be used and the computer power is insufficient, the model is expected to be released   in January 2021.
  
## Load checkpoints

- **Working in progress:**<br>
  The model used in our project is still being trained. 
  After the model has completely converged, it will be released as soon as the stability of the model is proven.
  Since transfer learning cannot be used and the computer power is insufficient, the model is expected to be released   in January 2021.


                                               






## 
