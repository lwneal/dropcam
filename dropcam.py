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

_CAMERAS_PATH = "https://www.dropcam.com/api/v1/cameras.get_visible"
_IMAGE_PATH = "https://nexusapi.dropcam.com/get_image"
_EVENT_PATH = "https://nexusapi.dropcam.com/get_cuepoint"

def apiv1_request(url, params):
    response = requests.get(url=url, params=params, cookies=login.get_cookiejar())
    return response.json()['items'][0]

def nexus_request(url, params):
    response = requests.get(url=url, params=params, cookies=login.get_cookiejar())
    return response.json()

def jpg_request(url, params):
    response = requests.get(url, params=params, cookies=login.get_cookiejar())
    return data.data()

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

class Event(object):
    def __init__(self, params):
        """
        :param params: Dictionary of dropcam event attributes.
        """
        self.__dict__.update(params)

    def __repr__(self):
        return "Cuepoint time {0}".format(self.time)

class Camera(object):
    def __init__(self, params):
        """
        :param params: Dictionary of dropcam camera attributes.
        """
        self.__dict__.update(params)

    def __repr__(self):
        return "Camera '{0}'".format(self.title)
    
    def events(self, start, end):
        """
        Returns a list of camera events for a given time period:

        :param start: start time in seconds since epoch
        :param end: end time in seconds since epoch
        """
        params = dict(uuid=self.uuid, start_time=start, end_time=end, human=False)
        data = nexus_request(_EVENT_PATH, params)
        return [Event(e) for e in data]

    def get_image(self, width=720, time=None):
        """
        Requests a camera image, returns response object.
        
        :param width: image width or X resolution
        :param time: time of image capture (in seconds from epoch)
        """
        params = dict(uuid=self.uuid, width=width)
        if time:
            params.update(time=time)
        return jpg_request(_IMAGE_PATH, params)

    def save_image(self, path, width=720, time=None):
        """
        Saves a camera image to disc. 

        :param path: file path to save image
        :param width: image width or X resolution
        :param time: time of image capture (in seconds from ecoch)
        """
        f = open(path, "wb")
        response = self.get_image(width, time)
        f.write(response)
        f.close()
