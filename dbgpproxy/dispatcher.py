import getopt
import logging
import asyncore
import socket
from re import split
from xml.dom import minidom

__author__ = 'gkralik'

E_NO_ERROR = 0
E_PARSE_ERROR = 1
E_INVALID_OPTIONS = 3
E_UNIMPLEMENTED_COMMAND = 4


class RegistrationServer(asyncore.dispatcher):
    def __init__(self, idehost, ideport, dbghost, dbgport, proxy_manager):
        """
        Initialize the RegistrationServer.

        Creates the socket and listens for incoming connections.
        @param idehost: The host to listen on for IDE requests.
        @param ideport: The port to listen on for IDE requests.
        @param dbghost: The host that the DebugConnectionServer is listening on for requests from the debugging engine.
        @param dbgport: The port that the DebugConnectionServer is listening on for requests from the debugging engine.
        @param proxy_manager: The proxy manager instance.
        """
        asyncore.dispatcher.__init__(self)
        self._ideport = ideport
        self._idehost = idehost

        self._dbghost = dbghost
        self._dbgport = dbgport

        self._proxy_manager = proxy_manager

        self.logger = logging.getLogger('dbgpproxy.ide')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((idehost, ideport))

        self.logger.info('listening for registration requests on {}:{}...'.format(idehost, ideport))
        self.listen(5)

    def handle_accept(self):
        """
        Handle incoming IDE requests.

        Dispatches a RegistrationHandler.
        """
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.logger.debug('incoming registration connection from {}'.format(repr(addr)))
            handler = RegistrationHandler(self._proxy_manager, dbghost=self._dbghost, dbgport=self._dbgport, sock=sock)


class RegistrationHandler(asyncore.dispatcher_with_send):
    def __init__(self, proxy_manager, dbghost=None, dbgport=None, sock=None, map=None):
        """
        Initialize the RegistrationHandler.
        @param proxy_manager: The proxy manger instance.
        @param dbghost: The host that the DebugConnectionServer is listening on for requests from the debugging engine.
        @param dbgport: The port that the DebugConnectionServer is listening on for requests from the debugging engine.
        @param sock: The socket.
        @param map: Not used.
        """
        super().__init__(sock, map)

        self.logger = logging.getLogger('dbgpproxy.ide')
        self._proxy_manager = proxy_manager

        self._dbghost = dbghost
        self._dbgport = dbgport

    def send(self, data):
        """
        Send data.

        Uses the format from the DBGp specification (message length followed by a \0 character, then the message
        terminated with a \0 character).
        @param data:
        """
        l = len(data)
        data = '{0:d}\0{1:s}\0'.format(l, data)

        super().send(data.encode())

    @staticmethod
    def _parse_line(line):
        """
        Parse an IDE command line.
        @param line: The line.
        @return: A tuple consisting of the command, a list of arguments and the full line.
        """
        line = line.strip().rstrip('\0')
        if not line:
            return None, None, line

        command, args = split(' ', line, maxsplit=1)

        return command, args.split(), line

    def handle_read(self):
        """
        Handle proxyinit and proxystop commands sent by the IDE.

        No other commands are recognized and responded to with a proxyerror.
        """
        data = self.recv(1024)
        if data:
            command, args, line = self._parse_line(data.decode())

            if not command:
                self._error('proxyerror', 'Failed to parse command.', E_PARSE_ERROR)

            self.logger.debug('command = %s, args = %s' % (command, args))

            if command == 'proxyinit':
                self._handle_proxyinit(args)
            elif command == 'proxystop':
                self._handle_proxystop(args)
            else:
                self._error('proxyerror', 'Unknown command [{0:s}]'.format(command), E_UNIMPLEMENTED_COMMAND)

    def _handle_proxyinit(self, args):
        """
        Handle a proxyinit command sent by the IDE.

        Parses the args and adds the IDE to the proxy manager's server list. A proxyinit success message is sent
        afterwards.
        If anything fails, a proxyerror is sent to the IDE.
        @param args: A list of args to the proxyinit command.
        @return: void
        """
        self.logger.debug('got proxyinit command: %s' % (args,))

        idekey = port = multi = None
        opts, args = getopt.getopt(args, 'p:k:m:')

        for o, a in opts:
            if o == '-p':
                port = int(a)
            elif o == '-k':
                idekey = a
            elif o == '-m':
                multi = a

        if not idekey:
            self._error('proxyinit', 'No IDE key defined for proxy.', E_INVALID_OPTIONS)
            return

        if not port:
            self._error('proxyinit', 'No port defined for proxy.', E_INVALID_OPTIONS)
            return

        id = self._proxy_manager.add_server(idekey, self.addr[0], port, multi)
        if id:
            msg = '<?xml version="1.0" encoding="UTF-8"?>\n<proxyinit success="1" idekey="{0:s}" address="{1:s}" port="{2:d}"/>'.format(
                id, self._dbghost, self._dbgport)
            self.send(msg)
            return
        else:
            self._error('proxyinit', 'IDE Key already exists.', E_INVALID_OPTIONS)
            return

    def _handle_proxystop(self, args):
        """
        Handle a proxystop command sent by the IDE.

        Parses the args and removes the IDE from the proxy manager's server list. Sends a proxystop success message if
        everything ok.
        If a failure occurs, sends a proxyerror.
        @param args: List of args to the proxystop command.
        @return: void
        """
        self.logger.debug('got proxystop command: %s' % (args))

        opts, args = getopt.getopt(args, 'k:')
        idekey = None
        for o, a in opts:
            if o == '-k':
                idekey = a

        if not idekey:
            self._error('proxystop', 'No IDE key.', E_INVALID_OPTIONS)
            return

        id = self._proxy_manager.remove_server(idekey)
        msg = '<?xml version="1.0" encoding="UTF-8"?>\n<proxystop success="1" idekey="{0:s}"/>'.format(id)
        self.send(msg)
        return

    def _error(self, command, message, code=E_NO_ERROR):
        """
        Send a proxyerror and shutdown the dispatcher.
        @param command: The command that caused the error.
        @param message: The error message to send (UI usable by the IDE).
        @param code: The error code (defaults to E_NO_ERROR).
        """
        error = '<?xml version="1.0" encoding="UTF-8"?>\n<{0:s} success="0"><error id="{1:d}"><message>{2:s}</message></error></{0:s}>'.format(
            command, code, message)

        self.logger.error(message)
        self.send(error)
        self.close()


class ToIDEHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, debug_sock):
        """
        Initialize the ToIDEHandler.
        @param sock: The IDE socket.
        @param debug_sock: The debugger engine socket.
        """
        super().__init__(sock)
        self._debug_sock = debug_sock
        self.logger = logging.getLogger('dbgpproxy.dbg')

    def handle_read(self):
        """
        Handle data sent by the IDE and forward to the debugging engine.
        """
        data = self.recv(1024)
        if data:
            self.logger.debug('<-- {}'.format(data.decode()))
            self._debug_sock.send(data)

    def handle_close(self):
        """
        Handle socket close.
        """
        self.close()


class DebugConnectionServer(asyncore.dispatcher):
    def __init__(self, host, port, proxy_manager):
        """
        Initialize the DebugConnectionServer.

        Creates the socket and listens for requests from the debugger engine.
        @param host: The host to listen on.
        @param port: The port to listen on.
        @param proxy_manager: The proxy manager instance.
        """
        asyncore.dispatcher.__init__(self)

        self._host = host
        self._port = port
        self._proxy_manager = proxy_manager

        self.logger = logging.getLogger('dbgpproxy.dbg')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))

        self.logger.info('listening for debugger connections on {}:{}'.format(host, port))
        self.listen(5)

    def handle_accept(self):
        """
        Handle incoming requests from the debugger engine.

        Dispatches a DebugConnectionHandler.
        """
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.logger.debug('incoming debugger connection from {}'.format(repr(addr)))
            handler = DebugConnectionHandler(self._proxy_manager, sock=sock, dbghost=self._host, dbgport=self._port,
                                             enginehost=addr)


class DebugConnectionHandler(asyncore.dispatcher_with_send):
    def __init__(self, proxy_manager, dbghost=None, dbgport=None, enginehost=None, sock=None, map=None):
        """
        Initialize the DebugConnectionHandler.
        @param proxy_manager: The proxy manager instance.
        @param dbghost: The host that the DebugConnectionServer is listening on for requests.
        @param dbgport: The port that the DebugConnectionServer is listening on for requests.
        @param enginehost: The host the debugger engine is running on.
        @param sock: The socket.
        @param map: Not used.
        """
        super().__init__(sock, map)

        self._proxy_manager = proxy_manager
        self._initialized = False
        self._ide_socket = None
        self._ide_handler = None

        self._dbghost = dbghost
        self._dbgport = dbgport
        self._enginehost = enginehost

        self.logger = logging.getLogger('dbgpproxy.dbg')

    def handle_read(self):
        """
        Handle data sent by the debugger engine.

        If the connection has not been initialized, _handle_init_packet() is called.
        Else, data is just sent to the IDE handler.
        @return:
        """
        # initialize the debugger session
        if not self._initialized:
            self._handle_init_packet()
            return

        # now play man in the middle ;)
        data = self.recv(1024)
        if data:
            self.logger.debug('--> {}'.format(data.decode()))
            self._ide_handler.send(data)

    def _handle_init_packet(self):
        """
        Handle an init packet from the debugger engine.

        Gets the server (IDE) from the proxy manager instance based on the IDE key from the init packet and tries to
        connect to the IDE. Also sets the 'proxied' attribute of the init packet to the hostname of the debugger
        engine.
        On failure, a proxyerror is sent and the socket is closed.
        @return: void
        """
        self.logger.debug('handle init packet')
        data = self.recv(100)

        # look for first NUL byte
        eol = data.find(b'\x00')

        # extract message length
        try:
            msg_len = int(data[:eol])
        except ValueError:
            self.logger.error('invalid protocol')
            # TODO send error to debugging engine
            self.close()
            return

        # skip \x00
        data = data[eol + 1:]

        # calculate remaining data length
        remaining_size = msg_len - len(data) + 1

        # get remaining data for init packet
        while remaining_size > 0:
            new_data = self.recv(remaining_size)
            data = data + new_data
            remaining_size -= len(new_data)

        # skip \x00
        data = data[:msg_len]

        dom = minidom.parseString(data.decode())
        init_packet = dom.documentElement
        packet_type = init_packet.localName

        if packet_type != 'init':
            self.logger.error('expected init packet, got {}'.format(packet_type))
            # TODO send error to debugging engine
            self.close()
            return

        # get/set information from/in init packet
        idekey = init_packet.getAttribute('idekey')
        server = self._proxy_manager.get_server(idekey)
        if not server:
            self.logger.warn('no server with IDE key [{}], aborting request'.format(idekey))
            # TODO send error
            self.close()
            return

        init_packet.setAttribute('proxied', self._enginehost[0])

        if not self.connect_to_ide(server, init_packet):
            self.logger.warn(
                'unable to connect to server with IDE key [{}], aborting and removing server'.format(idekey))
            # TODO send error (proxyerror)
            self._proxy_manager.remove_server(idekey)
            self.close()
            return

        self._initialized = True

    def connect_to_ide(self, server, init_packet):
        """
        Connect to the IDE.

        On success, adds the 'hostname' attribute to the init packet, specifying the proxy hostname.
        @param server: The IDE address (list with hostname and port).
        @param init_packet: The init packet (minidom node)
        @return: True if connection succeeded, False otherwise.
        """
        server_addr = server[0]

        try:
            self.logger.debug('trying to connect to {}:{}'.format(server_addr[0], server_addr[1]))
            self._ide_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._ide_socket.connect((server_addr[0], server_addr[1]))
        except socket.error:
            self.logger.warn('unable to connect to {}:{}'.format(server_addr[0], server_addr[1]))
            return False

        if not init_packet.hasAttribute('hostname') or not init_packet.getAttribute('hostname'):
            init_packet.setAttribute('hostname', self._dbghost)

        # send the init packet to the server (IDE)
        response = '<?xml version="1.0" encoding="UTF-8"?>\n'
        response += init_packet.toxml()
        l = len(response)
        self.logger.debug('sending init to IDE {0:d}\0{1:s}\0'.format(l, response))
        self._ide_socket.send('{0:d}\0{1:s}\0'.format(l, response).encode())
        self._ide_handler = ToIDEHandler(self._ide_socket, self)

        return True

    def handle_close(self):
        """
        Handle closing of the socket.

        Also closes the IDE handler if it has been initialized.
        """
        if self._ide_handler is not None:
            self.logger.debug('closing IDE socket')
            self._ide_handler.close()
        self.close()
