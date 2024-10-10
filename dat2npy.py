import os
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt

from utils import *

argvs = sys.argv
file_path = argvs[1]
file_name = argvs[2]

if __name__ == '__main__':
    f = open(file_name,'r')
    data=[]
    for line in f:
        line = line[:-1].split(',')
        data.append(line)
    f.close()
    data=np.array(data, dtype=float)
    data=data.reshape([4000,4000])#.T
    file_name=file_path+'/map'
    Image(data,file_name)
    np.save(file_name, data)

    #data=cv2.GaussianBlur(data,(11,11),3)
    #file_name='./output/blur_map'
    #Image(data,file_name)
    #np.save(file_name, data)
