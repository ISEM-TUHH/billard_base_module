import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, render_template_string, request, send_from_directory
from flask_cors import CORS, cross_origin
import socket
#import urllib.request
import requests
import json
from functools import wraps
from dotenv import dotenv_values

class Module:
	""" Parent class to modules
	Defines a web interface for modules consisting of HTML website and REST API

	:param config: path to the modules configuration .json file. Default for each module should be config/config.json
	:type config: str | path like
	:param template_folder:
	:type template_folder: str, optional 
	"""
	def __init__(self, config="config/config.json", template_folder="", storage_folder="./storage"):
		with open(config, "r") as f:
			self.config = json.load(f)

		self.storage_dir = storage_folder
		#self.template_folder = template_folder
		self.secrets = dotenv_values(".env")

		self.id = self.config["id"]

		self.api = {"id": (lambda: self.id)}
		self.app = Flask(__name__, template_folder=template_folder) # template folder would otherwise be "/template/" for stuff like index.html
		cors = CORS(self.app) # allow all cross origin requests
		self.app.add_url_rule("/id", "id", lambda: jsonify({"id": self.id}))
		self.app.add_url_rule("/api-doc", "api-doc", lambda: jsonify({"api": self.api_flat}))
		
		self.app.add_url_rule("/download", "download", self.auth_only(self.downloadStorage))
		self.app.add_url_rule("/downloadfiles/<path:filename>", "downloadFiles", self.auth_only(self.downloadStorageFile))

		self.api_flat = ["/id", "/api-doc", "/download"] # list of all api endpoints as full strings
		self.available_modules = None # change via scan_network method, initialized as None to signal it hasn't scanned yet
		return

	def add_website(self, file):
		"""Add a path to a html website/file to be made available under https://xxx.xxx.xxx.xxx/index

		file: absolute path to html file (e.g. index.html)
		"""
		self.index = file

		# return the website
		with self.app.app_context():
			self.app.add_url_rule("/index", "index", lambda: render_template(file))
		return

	def add_api(self, method, path):
		""" add an api point to the service which returns JSON when called

		method: method of the class which should be called when this API is called. Must return a dict object, which gets parsed to JSON and returned on request.
		path: str like "v1/coords" under where the methods output is available. Call like "http://XXX.XXX.XXX.XXX/v1/coords"

		return: no return value
		"""
		self.api_flat.append(path)

		# traverse api paths to find where to put it, check if parenting paths already exist
		path_list = path.split("/")
		cur = {path_list[-1]: method}
		for p in path_list[0:-2:-1]: # reverse from the back and build up deep nested dict
			cur = {p: cur}

		self.api = self.api | cur # merge the two dictionaries

		# set as path on the server
		#self.app.add_url_rule("/" + path, path, lambda: jsonify(method()))
		self.app.add_url_rule("/" + path, path, method, methods=["GET", "POST"]) 
		self.app.add_url_rule("/" + path + ".doc", path + ".doc", lambda: method.__doc__, methods=["GET"])


	def add_all_api(self, api):
		"""Just define a nested dictionary with paths building on each nest, ending on a method. Calls Module.add_api(...) on each path/method.

		:param api: a dictionary like {"v1":{"coords": getCoords}, "v2":{"image": getImage}} gets made available under /v1/coords and /v2/image with the return of each method (getCoords and getImage) getting send as parsed json as a response.
		:type api: <dict<dict...<method>..>>
		"""
		self.recursive_add_all_api(api, "")

	def recursive_add_all_api(self, api, path0):
		for k in api.keys():
			nextPath0 = f"{path0}/{k}"
			nextElement = api[k]
			if type(nextElement) == dict:
				self.recursive_add_all_api(nextElement, nextPath0)
			else:
				self.add_api(nextElement, nextPath0)


	def modules_available(self, modules):
		"""Check if all modules needed are available

		:param modules: List of module ids/names. Always lowercase!
		:type modules: list(str)
		"""
		ava = self.available_modules.keys()
		missing = []
		for m in modules:
			if m not in ava:
				missing.append(m)
		
		if len(missing) != 0:
			print(f"The following modules where missing when checking available modules for a certain function: {', '.join(missing)}")
			return False

		return True

	def check_modules_up(self):
		"""Ping all the modules mentioned in config.json. Add modules that answered to 
		
		"""
		self.available_modules = {}
		modules = self.config["modules"]
		for m in modules:
			ip = m["ip"]
			port = m["port"]
			try:
				con = requests.get(f"http://{ip}:{port}/id").json()
				print(f"Found module: {con['id']} on {ip}/{port}")
				
				#print(con)
				self.available_modules[con["id"]] = ip
			except Exception:
				print(f"Did not find anything on {ip}")
				1+1		

	def getModuleConfig(self, name):
		""" Returns a config dictionary based on the modules name
		"""
		modules = self.config["modules"]
		return next((x for x in modules if x["name"] == name), None)

	#%% Files
	def auth_only(self, f):
		""" Wrapper function to protect internal websites using basic http auth. As these pages are only accessible from inside a very local/protected network, this is most likely unnecessary. The implementation is very simple and everything but best practice! """
		@wraps(f)
		def wrapped_view(**kwargs):

			auth = request.authorization
			if not auth or not (self.secrets["USER"] == auth.username and self.secrets["PASSWORD"] == auth.password):
				return ("Unauthorized", 401, {
					"WWW-Authenticate": 'Basic realm="Login Required"'
				})
			
			return f(**kwargs)

		wrapped_view.__doc__ = f.__doc__
		return wrapped_view

	def downloadStorage(self):
		""" Select a file from the storage folder (wrapped auth) """
		files = os.listdir(self.storage_dir)

		# dodge flasks template folder settings
		download_page = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_page.html")
		with open("download_page.html", "r") as page:
			return render_template_string(page.read(), files=files)
	
	def downloadStorageFile(self, filename):
		""" Actually download the file from the storeage dir (wrapped auth) """
		return send_from_directory(os.path.abspath(self.storage_dir), filename, as_attachment=True)


#%% Testing
if __name__=="__main__":
	#print(Module.__doc__)
	#print(Module.add_api.__doc__)
	mod = Module(template_folder="templates", config="config_test/config.json", storage_folder="storage_test")
	mod.add_api(lambda: "1234", "v1/coords")
	mod.add_api(lambda: "14", "v1/pic") 
	#print(mod.api["id"]())
	#print(mod.api)
	# to run the actual api server
	#mod.scan_network()
	mod.app.run()
