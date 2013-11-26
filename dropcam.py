#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2012-2013, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# - Neither the name of the software nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ---------------------------------------------------------------------------------------------
# docs and latest version available for download at
# http://github.com/rsgalloway/dropcam
# ---------------------------------------------------------------------------------------------

import os
import sys
import requests
import simplejson as json

import login

__doc__ = """
An unofficial Dropcam Python API.
"""

__author__ = "Ryan Galloway <ryan@rsgalloway.com>"

# Please use /api/v1/ requests sparingly
_CAMERAS_PATH = "https://www.dropcam.com/api/v1/cameras.get_visible"

# NexusAPI provides useful metadata for CVR-subscribed Dropcams
# NOTE: Always batch multi-image requests using get_images/get_event_clip
_IMAGE_PATH = "https://nexusapi.dropcam.com/get_image"
_IMAGES_PATH = "https://nexusapi.dropcam.com/get_images"
_CLIPS_PATH = "https://nexusapi.dropcam.com/get_event_clip"
_EVENT_PATH = "https://nexusapi.dropcam.com/get_cuepoint"

def apiv1_request(url, params):
    response = requests.get(url=url, params=params, cookies=login.get_cookiejar())
    if not response.ok:
        print("Request failed: {0}".format(response.content))
        return None
    response_dict = response.json()
    if response_dict['status'] != 0 or not response_dict['items']:
        print(response_dict)
        return None
    else:
        return response_dict['items'][0]

def nexus_json_request(url, params):
    response = requests.get(url=url, params=params, cookies=login.get_cookiejar())
    if not response.ok:
        print("Request failed: {0}".format(response.content))
        return None
    return response.json()

def nexus_data_request(url, params):
    response = requests.get(url, params=params, cookies=login.get_cookiejar())
    if not response.ok:
        print("Request failed: {0}".format(response.content))
        return None
    return response.content

class Dropcam(object):
    def __init__(self, username=None, password=None):
        login.get_cookiejar(username, password)
        params = dict(group_cameras=True)
        self.data = apiv1_request(_CAMERAS_PATH, params)

    def __repr__(self):
        return "Dropcam account: {0}".format(self.owned_cameras())

    def cameras(self):
        return [Camera(c) for c in self.data['owned'] + self.data['subscribed']]

    def owned_cameras(self):
        return [Camera(c) for c in self.data['owned']]

    def subscribed_cameras(self):
        return [Camera(c) for c in self.data['subscribed']]

class Category(object):
    """
    Motion events can be categorized by Dropcam's learning systems
    Categories might include 'humans', 'cars', etc.
    Effectiveness depends highly on lighting, environment, and placement
    """
    pass

class Event(object):
    """
    An object representing an interesting 'cuepoint' on the timeline
    Includes motions, sounds, 'Enhance' uses, and other novel events
    """
    def __init__(self, params, camera):
        """
        :param params: Dictionary of dropcam event attributes.
        """
        self.__dict__.update(params)
        self.camera = camera

    def __repr__(self):
        return "Cuepoint time {0}".format(self.time)

    def get_image(self, width=720):
        params = dict(uuid=self.camera.uuid, width=width, time=self.time)
        return nexus_data_request(_IMAGE_PATH, params)

    def get_clip(self, width=720, num_frames=5):
        params = dict(uuid=self.camera.uuid, 
            width=width, 
            cuepoint_id=self.id,
            num_frames=num_frames,
            weigh_frames=True,
            format="JPEG") # JPEG, SPRITE, H264, TAR
        return nexus_data_request(_CLIPS_PATH, params)

class Camera(object):
    def __init__(self, params):
        """
        :param params: Dictionary of dropcam camera attributes.
        """
        self.__dict__.update(params)

    def __repr__(self):
        return "Camera '{0}'".format(self.title)
    
    def events(self, start=None, end=None):
        """
        Returns a list of camera events for a given time period:

        :param start: start time in seconds since epoch
        :param end: end time in seconds since epoch
        """
        params = dict(uuid=self.uuid, start_time=start, end_time=end, human=False)
        data = nexus_json_request(_EVENT_PATH, params)
        return [Event(e, self) for e in data]

    def get_image(self, width=720, time=None):
        """
        Requests a camera image, returns response object.
        
        :param width: image width or X resolution
        :param time: time of image capture (in seconds from epoch)
        """
        params = dict(uuid=self.uuid, width=width)
        if time:
            params.update(time=time)
        return nexus_data_request(_IMAGE_PATH, params)

    def save_image(self, path, width=720, time=None):
        """
        Saves a camera image to disc. 

        :param path: file path to save image
        :param width: image width or X resolution
        :param time: time of image capture (in seconds from ecoch)
        """
        f = open(path, "wb")
        response = self.get_image(width, time)
        if response:
            f.write(response)
            f.close()
        else:
            print("Failed save_image: {0} is not available".format(self))

    def time_lapse(self, filename='timelapse', start_time=None, end_time=None, category=None, frames_per_event=9, max_events=25, frames_per_hour=4):
        """
        Example time-lapse generator
        Requires FFMPEG

        Makes a constant framerate time-lapse at frames_per_hour, which 'slows down'
        by adding frames at each new event it comes to
        """
        if os.system('ffmpeg -version') is not 0:
            print("FFMPEG is not installed! Install it:")
            if 'Darwin' in os.uname():
                print("\tbrew install ffmpeg")
            else:
                print("\thttp://www.ffmpeg.org/download.html")
            return None

        events = self.events()
        if start_time:
            events = [e for e in events if e.id >= start_time]
        if end_time:
            events = [e for e in events if e.id <= end_time]

        # Ignore sound-only events
        events = [e for e in events if 'me2' in e.type]

        #  Time-lapse a single category (eg. only detected humans)
        if category:
            events = [e for e in events if e.cuepoint_category_id == category]

        if max_events:
            events = events[:max_events]

        if start_time is None:
            start_time = float(events[0].time)

        if end_time is None:
            end_time = float(events[-1].time)

        duration = end_time - start_time
        seconds_between_frames = duration / (frames_per_hour * 60 * 60)
        frame_times = [start_time + n * seconds_between_frames for n in range(int(duration / seconds_between_frames))]

        if not events:
            print("Error generating time-lapse: no events available")
            return
        else:
            print("Generating time-lapse from {0} events and {1} still frames".format(len(events), len(frame_times)))


        f_out = open('{0}.mjpeg'.format(filename), 'w')
        while frame_times and events:
            if frame_times[0] < events[0].time:
                f = frame_times[0]
                frame_times = frame_times[1:]
                jpg_stream = self.get_image(time=f)
            else:
                e = events[0]
                events = events[1:]
                jpg_stream = events[0].get_clip(num_frames=frames_per_event)
            if jpg_stream:
                print("Writing {0} Bytes".format(len(jpg_stream)))
                f_out.write(jpg_stream)
            else:
                print("Skipping event {0}".format(e.id))
        f_out.close()

        res = os.system('ffmpeg -y -i {0}.mjpeg {0}.mp4'.format(filename))
        if res:
            print("Warning: ffmpeg returned error code generating .mp4 video")
        print("Time-Lapse Complete")
