import numpy as np
import torch
import glob

from pathlib import Path
from torch.utils.data import Dataset, DataLoader, Subset
from PIL import Image

from config import *

#load data from a folder
class DatasetLoader(Dataset):
    def __init__(self, gray_dir, gt_dir, pytorch=True, img_res = 384):
        super().__init__()
        
        # Loop through the files in red folder and combine, into a dictionary, the other bands
        self.files = [self.combine_files(f, gt_dir) for f in gray_dir.iterdir() if not f.is_dir()]
        self.pytorch = pytorch
        self.res= img_res
        
    def combine_files(self, gray_file: Path, gt_dir):
        
        files = {'gray': gray_file, 
                 'gt': gt_dir/gray_file.name.replace('gray', 'gt')}

        return files
                                       
    def __len__(self):
        #legth of all files to be loaded
        return len(self.files)
     
    def open_as_array(self, idx, invert=False):
        #open ultrasound data
        raw_PIL = Image.open(self.files[idx]['gray']).resize((self.res, self.res))
        raw_us = np.stack([np.array(raw_PIL),], axis=2)

        if invert:
            raw_us = raw_us.transpose((2,0,1))
    
        # normalize
        return (raw_us / np.iinfo(raw_us.dtype).max)
    

    def open_mask(self, idx, add_dims=False):
        #open mask file
        raw_mask = np.array(Image.open(self.files[idx]['gt']).resize((self.res, self.res)))

        # raw_mask = np.where(raw_mask> 100, 1, 0)
        
        return np.expand_dims(raw_mask, 0) if add_dims else raw_mask
    
    def __getitem__(self, idx):
        #get the image and mask as arrays
        x = torch.tensor(self.open_as_array(idx, invert=self.pytorch), dtype=torch.float32)
        y = torch.tensor(self.open_mask(idx, add_dims=False), dtype=torch.torch.int64)

        return x, y
    
    def get_as_pil(self, idx):
        #get an image for visualization
        arr = 256*self.open_as_array(idx)
        
        return Image.fromarray(arr.astype(np.uint8), 'RGB')

def split_dataset(data, train_percentage):

    if type(train_percentage) == tuple:
        train_idx = range(train_percentage[0])
        valid_idx = range(train_idx[-1] + 1, train_percentage[0] + train_percentage[1])
        test_idx = range(valid_idx[-1] + 1, sum(train_percentage))

        train_data = Subset(data, train_idx)
        valid_data = Subset(data, valid_idx)
        test_data = Subset(data, test_idx)

        return train_data, valid_data, test_data
        
    else:
        train_idx = range(int(len(data)*train_percentage))
        valid_idx = range(train_idx[-1] + 1, len(data))

        train_data = Subset(data, train_idx)
        valid_data = Subset(data, valid_idx)

        return train_data, valid_data
    
    

def make_train_dataloaders(dataset, train_percentage):
    # torch.random.seed(1)

    bs = BATCH_SIZE
    img_res = RESOLUTION
    bs = 12

    gt = Path.joinpath(BASE_PATH, dataset, 'train_gt')
    gray = Path.joinpath(BASE_PATH, dataset, 'train_gray')

    data = DatasetLoader(gray, gt)

    if type(train_percentage) == tuple:
        #Split dataset into training and validation
        # train_data, valid_data, test_data = torch.utils.data.random_split(data, (250,100,100))
        train_data, valid_data, test_data = split_dataset(data, train_percentage)

        train_load = DataLoader(train_data, batch_size = bs, shuffle = True)
        valid_load = DataLoader(valid_data, batch_size = bs, shuffle = True)
        test_load = DataLoader(test_data, batch_size= len(test_data), shuffle = True)

        return train_load, valid_load, test_load

    elif type(train_percentage) == float and 0 <= train_percentage <= 1:

        train_data, valid_data = split_dataset(data, train_percentage)

        train_load = DataLoader(train_data, batch_size = bs, shuffle = True)
        valid_load = DataLoader(valid_data, batch_size = bs, shuffle = True)

        return train_load, valid_load
    else:
        raise (f"Training percentage = {train_percentage}, must be between 0 and 1")

    # elif len(data_splits) == 3:
    #     #Split dataset into train, validation and test
    #     train_data, val_data, test_data = torch.utils.data.random_split(data, data_splits)

    #     train_load = DataLoader(train_data, batch_size = bs, shuffle = True, num_workers=1)
    #     valid_load = DataLoader(val_data, batch_size = bs, shuffle = True, num_workers=1)
    #     test_load  = DataLoader(test_data, batch_size = bs, shuffle = True, num_workers=1)

        # return train_load, valid_load, test_load

    return DataLoader(data, batch_size = bs, shuffle = True)

def make_test_dataloader(dataset):
    bs = BATCH_SIZE
    img_res = RESOLUTION
    # bs = 12

    gt = Path.joinpath(BASE_PATH, dataset, 'test_gt')
    gray = Path.joinpath(BASE_PATH, dataset, 'test_gray')

    data = DatasetLoader(gray, gt, img_res = img_res)

    test_load  = DataLoader(test_data, shuffle = True, num_workers=0)

    return test_load