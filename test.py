#!/usr/bin/env python

try:
  import dropcam
  d = dropcam.Dropcam()
  print("Logged into dropcam acct {0}".format(d))

  cams = d.cameras()
  print("Got cameras {0}".format(cams))

  cam = cams[5]

  cam.save_image('test.jpg')
  print("Saved image")

  events = cam.events()[:20]
  print("Got {0} events from camera {1}".format(len(events), cam))

  timelapse = cam.time_lapse()
  import os
  os.system("open timelapse.mp4")

  print("Tests Complete, no errors!")
except Exception as ex:
  print("Error while running tests: {0}".format(ex))
  import pdb; pdb.set_trace()
