#!/usr/bin/python
# -*- coding: utf-8 -*-

# A color analysis script to help you label your store's products with color data
# automagically. It will take either a single file or scour an entire folder for
# folders of images and do each one individually printing a summary of what it 
# thinks is the correct color value. A work in progress...
#
#    ~jaymz | @jaymzcampbell | jaymz.eu
#
#
# MIT Licesnsed for what its worth, copy: http://www.opensource.org/licenses/mit-license.php

import Image
import ImageFilter
import os
import glob
import sys
import colorsys
import re
from operator import itemgetter

# Pixels will be first compared to these values before being
# added to the data list of color information on the first pass
LBOUND = 0
UBOUND = 255

MIN_SATURATION = 30 # avoid washed out pixels influencing counts

# Base folder for the processFolder function, it'll iterate over here on subfolders
FOLDER = '/home/jaymz/documents/crooked-docs/data-export/store-migration/product-images/'

# Names based off: http://bluelobsterart.com/wordpress/wp-content/uploads/2009/03/rgb-color-wheel-lg.jpg
COLOR = ['RED', 'ORANGE', 'YELLOW',
    'LIME', 'GREEN', 'TURQUOISE',
    'CYAN', 'OCEAN', 'BLUE',
    'VIOLET', 'MAGENTA', 'RASPBERRY',
    ]
TONE = ['DARK', '', 'BRIGHT']

def processImage(i, name=None):
  """ Scales down the image, blurs it to ease the blending of the color values
  and reduce spikes from anomolies. It then samples pixels creating a list of
  colors. This list is then looped over to build counts which are placed into
  bins of 30° hue's seperated into three based on their value. Pixels less than
  a certain saturation are discarded. """
  
  i = i.resize((200,200))
  i = i.convert("RGB")
  i = i.filter(ImageFilter.BLUR)
  d = i.getdata()
  cnt = 0
  h = [] #holds the hsv info
  for p in d:
      cnt = cnt + 1
      if cnt == 4: #take every 4th pixel
        if p[0]>LBOUND and p[1]>LBOUND and p[2]>LBOUND and p[0]<UBOUND and p[1]<UBOUND and p[2]<UBOUND:
            if p[0] != p[1] != p[2]:
                r = float(p[0])/255
                g = float(p[1])/255
                b = float(p[2])/255
                h.append(colorsys.rgb_to_hsv(r,g,b))
        cnt = 0 #reset sample counter
  h.sort()
  bin_width = 30 # size of hue slices (degress)
  max_bin = 360

  darks = [0] * int(max_bin/bin_width)
  mids = [0] * int(max_bin/bin_width)
  lites = [0] * int(max_bin/bin_width)

  for p in h[::]:
      hue = p[0]*360
      sat = p[1]*100
      val = p[2]*100
      if sat >= MIN_SATURATION:
        bin_number = ((int(hue)+15)/bin_width)%(max_bin/bin_width)
        if val<33:
            darks[bin_number] += 1
        elif val>33 and val < 66:
            mids[bin_number] += 1
        else:
            lites[bin_number] += 1
        print "HUE BIN: %s VALUE : %d" % (int(hue)/bin_width, int(hue))

  c = 0
  data = zip(darks, mids, lites)
  
  for x in data:
      print '%s : %s %d°' % (COLOR[c], x, c*bin_width)
      c += 1

  max_idxs = (darks.index(max(darks)), mids.index(max(mids)), lites.index(max(lites)))
  max_counts = (darks[max_idxs[0]], mids[max_idxs[1]], lites[max_idxs[2]])
  print "\nMax→ Indexes: %s Values: %s" % (max_idxs, max_counts)
  
  tone = max_counts.index(max(max_counts))
  max_hbin = max_idxs[tone]
  print "Dominant Hue: %s %s" % (TONE[tone], COLOR[max_hbin])

# Helper functions follow along with __main__ def

def processFolder(folder):
    for image_folder in glob.glob(folder+'*'):
        folder_images = []
        for image in os.listdir(image_folder):
            if "jpg" in image and "._" not in image:
                folder_images.append(image)
        folder_images.sort()
        j = os.path.join(image_folder, folder_images[1])
        print "working: "+j
        i = Image.open(j)
        processImage(i, j)

def processFile(_file):
    i = Image.open(_file)
    processImage(i)

if __name__ == "__main__":
    try:
        if 'product-images' not in sys.argv[1]:
            processFile('product-images/'+sys.argv[1])
        else:
            processFile(sys.argv[1])
    except IndexError:
        processFolder(FOLDER)
        
    
        
