# Script to create CSV data file from Pascal VOC annotation files
# Based off code from GitHub user datitran: https://github.com/datitran/raccoon_dataset/blob/master/xml_to_csv.py

import os
import glob
import pandas as pd
import xml.etree.ElementTree as ET

def xml_to_csv(path):
    xml_list = []
    for xml_file in glob.glob(os.path.join(path, '*.xml')):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        for member in root.findall('object'):
            # Check if bounding box coordinates exist
            bbox = member.find('bndbox')
            if bbox is not None:
                xmin = int(bbox.find('xmin').text) if bbox.find('xmin') is not None else 0
                ymin = int(bbox.find('ymin').text) if bbox.find('ymin') is not None else 0
                xmax = int(bbox.find('xmax').text) if bbox.find('xmax') is not None else 0
                ymax = int(bbox.find('ymax').text) if bbox.find('ymax') is not None else 0
            else:
                xmin, ymin, xmax, ymax = 0, 0, 0, 0
            
            value = (root.find('filename').text,
                     int(root.find('size')[0].text),
                     int(root.find('size')[1].text),
                     member.find('name').text,  # Change from member[0].text to member.find('name').text
                     xmin,
                     ymin,
                     xmax,
                     ymax)
            xml_list.append(value)

    column_name = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']
    xml_df = pd.DataFrame(xml_list, columns=column_name)
    return xml_df

def main():
    for folder in ['train', 'validation']:
        image_path = os.path.join('/kaggle/working/images', folder)  # Adjust the path accordingly
        xml_df = xml_to_csv(image_path)
        xml_df.to_csv(f'/kaggle/working/images/{folder}_labels.csv', index=None)
        print(f'Successfully converted {folder} XML to CSV.')

main()


