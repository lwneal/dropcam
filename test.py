#!/usr/bin/env python

try:
  import dropcam
  d = dropcam.Dropcam()
  cams = d.cameras()
  cams[5].save_image('test.jpg')
  print("Tests Complete")
except:
  import pdb; pdb.set_trace()
