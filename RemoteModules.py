import requests
from flask import request, Response

import cv2
import numpy as np

class RemoteModule:
    """ This class provides common interface functions for working with remote modules, hitting their API endpoints. Setup using config dicts. """

    def __init__(self, config):
        self.ip = config["ip"]
        self.port = config["port"]
        self.address = f"http://{self.ip}:{self.port}"

    def endpoint(self, endpoint):
        """ Returns full address from endpoint passed as '/a/b' or 'a/b' """
        if endpoint[0] != "/":
            endpoint = "/" + endpoint
        return self.address + endpoint

class Beamer(RemoteModule):
    """ Implementation of the beamer """

    def __init__(self, config):
        RemoteModule.__init__(self, config)

    def push_image(self, img):
        """ Method to post an image to the beamer module to be displayed on the beamer.

        :param img: image to be posted. Will get stretched to fullscreen on the beamer.
        :type img: cv2-image
        """
        _, buffer = cv2.imencode(".jpg", img)
        try:
            requests.post(self.endpoint("/v1/receiveimage"), data=buffer.tobytes(), headers={"content-type": "image/jpeg"})
        except Exception as e:
            print(e)

        #print(f"Posted image to the beamer-module at {url}.")
        return "Game beamer push image"

    def off(self):
        """ Method to display a black image on the beamer from the beamer module.
        """
        try:
            requests.get(self.endpoint("/v1/off"))
        except:
            pass
        return "Beamer displays a black image."

    def play_sound(self, sound):
        try:
            requests.post(self.endpoint("/v1/playsound"), json={"sound": sound})
        except:
            pass

class Camera(RemoteModule):
    """ Implementation of the Camera 
    
    Methods of this class are as specified UML diagrams.
    """

    def __init__(self, config):
        RemoteModule.__init__(self, config)

    def get_coords(self):
        """ Send request to camera module and receive the (uncorrected) coordinates """
        try:
            response = requests.get(self.endpoint("/v1/coords"))
            res = response.json()
        except Exception:
            res = {}
        return res
    
    def cache_image(self):
        """ Take image and cache for storing it later on with coordinates (on the camera module device) """
        requests.get(self.endpoint("/v1/cacheimage"))

    def save_cached_image_training(self, coordinates):
        """ Sends coordinates to the camera module and instructs it to save the last cached image (see cache_image()) with the coordinates transformed to YOLO label format """
        try:
            requests.get(self.endpoint("/v1/savepic"), json={"coords": coordinates, "action": "save-labels"}, headers={"content-type": "application/json"})
        except:
            pass

    def save_image(self):
        """ Only save the current image, dont do anything with coordinates """
        requests.get(self.endpoint("v1/savepic"))
