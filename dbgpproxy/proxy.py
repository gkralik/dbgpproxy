import asyncore
import logging
from dbgpproxy.dispatcher import RegistrationServer, DebugConnectionServer

__author__ = 'gkralik'


class Proxy:
    def __init__(self, idehost=None, ideport=None, dbghost=None, dbgport=None):
        """
        Initialize the Proxy manager.

        Sets up the RegistrationServer and DebugConnectionServer instances.
        @param idehost: The host to listen on for IDE requests.
        @param ideport: The port to listen on for IDE requests.
        @param dbghost: The host to listen on for debugger engine requests.
        @param dbgport: The port to listen on for debugger engine requests.
        """
        self.logger = logging.getLogger('dbgpproxy')
        self._servers = {}

        self._registration_server = RegistrationServer(idehost, ideport, dbghost, dbgport, proxy_manager=self)
        self._debugger_connection_server = DebugConnectionServer(dbghost, dbgport, proxy_manager=self)

    @staticmethod
    def start():
        """
        Start the asyncore loop.
        """
        asyncore.loop()

    @staticmethod
    def stop():
        """
        Close all sockets handled by asyncore.
        """
        asyncore.close_all()

    def add_server(self, idekey, host, port, multi):
        """
        Add a server (IDE) to the list of known servers.
        @param idekey: The IDEKEY identifying the server.
        @param host: The host of the IDE process.
        @param port: The port of the IDE process.
        @param multi: Not used.
        @return: The IDEKEY or None if IDEKEY is already registered.
        """
        if idekey in self._servers:
            return None

        self.logger.debug('add_server: idekey = {}, host = {}, port = {}, multi = {}'.format(idekey, host, port, multi))

        self._servers[idekey] = [[host, port], multi]
        return idekey

    def remove_server(self, idekey):
        """
        Remove a server (IDE) from the list of known servers.
        @param idekey: The IDEKEY identifying the server.
        @return: The IDEKEY or None if the server is not registered.
        """
        if idekey in self._servers:
            self.logger.debug('remove_server: idekey = {}'.format(idekey))
            del self._servers[idekey]
            return idekey

        return None

    def get_server(self, idekey):
        """
        Get a server by its IDEKEY.
        @param idekey: The IDEKEY identifying the server.
        @return: The IDEKEY or None if the server is not registered.
        """
        if idekey in self._servers:
            return self._servers[idekey]

        return None
