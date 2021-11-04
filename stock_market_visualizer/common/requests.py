import requests
from socket import AF_INET

class ClientSessionGenerator:
	def __init__(self):
		self.__counter = 0
		self.__client = None

	def get(self):
		host_limit = 100
		if self.__counter == 0:
			self.__client = requests.session()
		self.__counter = (self.__counter + 1)%host_limit
		assert self.__client is not None
		return self.__client

def concat_port(url, port):
	return url + ":" + str(port)