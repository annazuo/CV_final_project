import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import torchvision.transforms as T 
from numpy import asarray

from util import constants as C
from .transforms import get_transforms
from .array_transforms import resize_as_image, upscale, center_crop, scale_values

def class_labels_generator(string):
    # Create list of zeroes 
    label_vector = [0] * len(C.class_labels_list)
    for i in range(len(C.class_labels_list)):
        # Input a "1" if your label list contains that source
        if C.class_labels_list[i] in string:
            label_vector[i] = 1
        else:
            label_vector[i] = 0
    return label_vector

class ClassificationDataset(torch.utils.data.Dataset):
    def __init__(self, dataset_path, split, products_to_use,
                augmentation, image_size, crop_size, pretrained):
        self._df = pd.read_csv(dataset_path) # Careful of index_col here
        self._lat = self._df['Latitude'].tolist()
        self._lon = self._df['Longitude'].tolist()
        self._naip_path = [x + '/naip.png' for x in self._df['Image_Folder'].astype(str).tolist()]
        self._image_size = image_size
        self._crop_size = crop_size
        self._transforms = get_transforms(
            split=split,
            augmentation=augmentation,
            image_size=image_size,
            pretrained=pretrained
        )

        self.use_naip_rbg = True
        self.use_naip_nir = True
        
    def __len__(self):
        return len(self._labels)

    def __getitem__(self, index):
        lat = torch.tensor(np.float64(self._lat[index]))
        lon = torch.tensor(np.float64(self._lon[index]))
        label = torch.tensor(np.float64(self._labels[index]))

        image_band_segments = []
        if self.use_naip_rbg:
            im_frame = Image.open(self._naip_path[index])
            naip_image = asarray(im_frame) #np.array(im_frame.getdata())
            # naip_image = np.load(self._naip_path[index])
            naip_rgb = resize_as_image(naip_image[:, :, :3], self._image_size)
            if self._crop_size is not None:
                naip_rgb = center_crop(naip_rgb, self._crop_size)
            naip_rgb = resize_as_image(naip_rgb, C.TILESIZE)
            naip_rgb = scale_values(naip_rgb, C.NAIP_MIN, C.NAIP_MAX)
            image_band_segments.append(naip_rgb)
            
            if self.use_naip_nir:
                naip_nir = resize_as_image(naip_image[:, :, 3], self._image_size)
                if self._crop_size is not None:
                    naip_nir = center_crop(naip_nir, self._crop_size)
                naip_nir = resize_as_image(naip_nir, C.TILESIZE)
                naip_nir = scale_values(naip_nir, C.NAIP_MIN, C.NAIP_MAX)
                image_band_segments.append(np.expand_dims(naip_nir, axis=2))

        if len(image_band_segments) > 1:
            final_array = np.concatenate(image_band_segments, axis=2)
        else:
            final_array = image_band_segments[0]

        image = torch.tensor(np.transpose(final_array, (2, 0, 1))).float()
        return lat, lon, label, image

class MultiTaskClassificationDataset(ClassificationDataset):
    def __init__(self, dataset_path, split, products_to_use,
                augmentation, image_size, crop_size, pretrained):
        super().__init__(
            dataset_path=dataset_path,
            split=split,
            products_to_use=products_to_use,
            augmentation=augmentation,
            image_size=image_size,
            crop_size=crop_size,
            pretrained=pretrained
            )
        self._labels = self._df['Type'].apply(class_labels_generator).tolist() # Encode type column

class SingleTaskClassificationDataset(ClassificationDataset):
    def __init__(self, task, dataset_path, split,
                augmentation, image_size, pretrained):
        super().__init__(
            dataset_path=dataset_path,
            split=split,
            products_to_use='naip-rgb',
            augmentation=augmentation,
            image_size=image_size,
            crop_size=None,
            pretrained=pretrained
            )
        self._labels = self._df['Type'].apply(lambda string: 1 if task in string else 0).tolist()
