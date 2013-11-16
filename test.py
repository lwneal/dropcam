#!/usr/bin/env python

USERNAME="unofficial_api_test"
EMAIL="unofficial_api_test@dropcamhacks.com"
PASSWORD="testpassword123"

try:
  import dropcam
  d = dropcam.Dropcam(username=USERNAME, password=PASSWORD)
  print("Logged into dropcam acct {0}".format(d))

  cams = d.cameras()
  print("Got cameras: {0}".format(cams))

  cam = cams[0] # Richmond Zoo Cheetah Cam

  cam.save_image('test_cheetah.jpg')
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
