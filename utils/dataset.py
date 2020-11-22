import json
import os
# import ntpath
from collections import defaultdict

import wget


ROOT_DIR = os.path.abspath('.')

CACHES_DIR = os.path.join(ROOT_DIR, 'caches')
WSI_URLS_DIR = os.path.join(CACHES_DIR, 'download_urls')

WSI_DIR = os.path.join(ROOT_DIR, 'wsi')
TRAIN_WSI_DIR = os.path.join(WSI_DIR, 'train')
# VALID_WSI_DIR = os.path.join(WSI_DIR, 'valid')
# TEST_WSI_DIR = os.path.join(WSI_DIR, 'test')

# Number of training wsi per class
# NUM_TRAIN_TUMOR_WSI = 88
# NUM_TRAIN_NORMAL_WSI = 159

# Number of validation wsi per class
# NUM_VALID_TUMOR_WSI = 127
# NUM_VALID_NORMAL_WSI = 32

# Number of test wsi
# NUM_TEST_WSI = 129


num_train_wsi_dict = {
    'tumor': 110,
    'normal': 160,
}

# Urls to download whole slide images for training and their annotations

# Name of .zip file which contains lesion annotations of wsis
BASE_URL = 'ftp://parrot.genomics.cn/gigadb/pub/10.5524/100001_101000/100439/CAMELYON16'

# annot_zfname = 'lesion_annotations.zip'
classes = ['tumor', 'normal']

if not os.path.exists(WSI_URLS_DIR):
    os.mkdir(WSI_URLS_DIR)
train_wsi_urls_path = os.path.join(WSI_URLS_DIR, 'train_wsi_urls.json')
# valid_wsi_urls_path = os.path.join(WSI_URLS_DIR, 'valid_wsi_urls.json')
# test_wsi_urls_path = os.path.join(WSI_URLS_DIR, 'test_wsi_urls.json')

train_wsi_urls = defaultdict(list)
# valid_wsi_urls = defaultdict(list)
# test_wsi_urls = defaultdict(list)
if not os.path.exists(train_wsi_urls_path):

# Make urls to download train wsis 
    train_wsi_urls_dict = defaultdict(list)
    for class_, num_wsi in num_train_wsi_dict.items():
        for i in range(1, num_wsi+1):
            if (class_ == 'normal') and ((i == 144) or (i == 86)):
                continue
            train_wsi_urls_dict[class_].append(f'{BASE_URL}/training/{class_}/{class_}_{i:03}.tif')

    with open(train_wsi_urls_path, 'w+', encoding='utf-8') as f:
        # train_wsi_urls_dict = json.load(f)
        json.dump(train_wsi_urls_dict, f, indent=4)


# Download wsi using wget
with open(train_wsi_urls_path, 'r', encoding='utf-8') as f:
    train_wsi_urls_dict = json.load(f)

from pprint import pprint
pprint(train_wsi_urls_dict)

os.makedirs(TRAIN_WSI_DIR, exist_ok=True)
for (class_, wsi_urls) in train_wsi_urls_dict.items():
    # Specify the classes' wsi directory
    wsi_dir_out = os.path.join(TRAIN_WSI_DIR, f'{class_}')
    # Download every wsi to the directory
    for url in wsi_urls:
        # slide_fname = ntpath.basename(url)
        # print(f'Start downloading {slide_fname} to {wsi_dir_out}')
        wget.download(url=url, out=wsi_dir_out)
        # print(f'Complete!')

# from pprint import pprint
# pprint(train_wsi_urls_dict)