import json
import os
from collections import defaultdict

import wget


class Camelyon16:
    '''Camelyon16 dataset downloader'''

    def __init__(self, urls_dir_in: str, wsi_dir_out: str) -> None:
        '''Initialize Camelyon16.
        
        - Args
            urls_dir_in: Path to the directory to cache the wsi download urls
            wsi_dir_out: Path to the directory to save the downloaded wsi

        - Returns
            None
        '''
        self.base_url = u'ftp://parrot.genomics.cn/gigadb/pub/10.5524/100001_101000/100439/CAMELYON16'
        self.urls_dir_in = urls_dir_in
        self.wsi_dir_out = wsi_dir_out

        self.train_wsi_dir = os.path.join(self.wsi_dir_out, 'train')
        self.valid_wsi_dir = os.path.join(self.wsi_dir_out, 'valid')
        self.test_wsi_dir = os.path.join(self.wsi_dir_out, 'test') 

        # Do not use normal_86.tif, normal_144.tif
        # self.train_wsi_range_dict = {
        #     'tumor': (1, 89),
        #     'normal': (1, 128),
        # }

        self.train_wsi_range_dict = {
            'tumor': (1, 112),
            'normal': (1, 161)
        }

        self.valid_wsi_range_dict = {
            'tumor': (89, 112),
            'normal': (128, 161),
        }

        # Do not use test_049.tif; the same as tumor_036.tif
        self.test_wsi_range = (1, 131)

    def download_trainset(self) -> None:
        '''Download Camelyon16 training dataset'''

        os.makedirs(self.urls_dir_in, exist_ok=True)
        
        # Path to the url cache file(train_wsi_urls.json) to downlod training wsi
        train_wsi_urls_path = os.path.join(self.urls_dir_in, 'train_wsi_urls.json')
        if not os.path.exists(train_wsi_urls_path):
            # Make urls to download train wsi
            train_wsi_urls_dict = defaultdict(list)
            for (class_, wsi_range) in self.train_wsi_range_dict.items():
                for i in range(*wsi_range):
                    # We do not use normal_86.tif, normal_144.tif
                    if (class_ == 'normal') and (i in (86, 144)):
                        continue

                    train_wsi_url = f'{self.base_url}/training/{class_}/{class_}_{i:03}.tif'
                    train_wsi_urls_dict[class_].append(train_wsi_url)
                # inner for-statement ended
            # outer for-statement ended
            with open(train_wsi_urls_path, 'w+', encoding='utf-8') as f:
                json.dump(train_wsi_urls_dict, f, indent=4)  
        # if-statement ended
        with open(train_wsi_urls_path, 'r', encoding='utf-8') as f:
            train_wsi_urls_dict = json.load(f)
        
        os.makedirs(self.train_wsi_dir, exist_ok=True)
        # Wsi file names in train wsi directory
        wsi_fnames = os.listdir(self.train_wsi_dir)
        for (class_, urls) in train_wsi_urls_dict.items():
            dirname = f'{class_}'
            # Path to the directory to save training wsi
            train_wsi_dir_out = os.path.join(self.train_wsi_dir, dirname)

            # Download every wsi to the directory
            for url in urls:
                wsi_fname = url.split('/')[-1]
                if wsi_fname not in wsi_fnames:
                    print(f'Start downloading {wsi_fname}')
                    wget.download(url=url, out=train_wsi_dir_out)
                    print('Completed!')

    def download_testset(self) -> None:
        '''Download Camelyon16 test dataset'''

        # Path to the url cache file(test_wsi_urls.jon) to download test wsi
        test_wsi_urls_path = os.path.join(self.urls_dir_in, 'test_wsi_urls.json')
        if not os.path.exists(test_wsi_urls_path):
            # Make urls to download test wsi
            test_wsi_urls_dict = defaultdict(list)
            for i in range(*self.test_wsi_range):
                # We do not use test_049.tif; the same as tumor_036.tif
                if i == 49:
                    continue

                test_wsi_url = f'{self.base_url}/testing/images/test_{i:03}.tif'
                test_wsi_urls_dict['images'].append(test_wsi_url)
            # for-statement ended
            with open(test_wsi_urls_path, 'w+', encoding='utf-8') as f:
                json.dump(test_wsi_urls_dict, f, indent=4)
        # outer if-statement ended
        

        with open(test_wsi_urls_path, 'r', encoding='utf-8') as f:
            test_wsi_urls_dict = json.load(f)

        os.makedirs(self.test_wsi_dir, exist_ok=True)
        # Wsi file names in train wsi directory
        wsi_fnames = os.listdir(self.test_wsi_dir)

        test_wsi_urls = test_wsi_urls_dict['images']
        for url in test_wsi_urls:
            wsi_fname = url.split('/')[-1]
            if wsi_fname not in wsi_fnames:
                print(f'Start downloading {wsi_fname}')
                wget.download(url=url, out=self.test_wsi_dir)
                print('Completed!')
        

if __name__ == '__main__':

    ROOT_DIR = os.path.abspath('.')
    CACHES_DIR = os.path.join(ROOT_DIR, 'caches')
    URLS_DIR = os.path.join(CACHES_DIR, 'download_urls')
    WSI_DIR = os.path.join(ROOT_DIR, 'wsi')

    downloader = Camelyon16(urls_dir_in=URLS_DIR,
                            wsi_dir_out=WSI_DIR)
    # downloader.download_trainset()
    downloader.download_testset()