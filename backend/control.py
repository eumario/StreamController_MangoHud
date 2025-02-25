# Copied from MangoHud/control/src/control/__init__.py (https://github.com/flightlessmango/MangoHud/blob/master/control/src/control/__init__.py)
import os
import socket
import sys
import select
from select import EPOLLIN, EPOLLPRI, EPOLLERR
import time
from collections import namedtuple
from loguru import logger as log
import argparse

TIMEOUT=1.0

VERSION_HEADER = bytearray('MangoHudControlVersion', 'utf-8')
DEVICE_NAME_HEADER = bytearray('DeviceName', 'utf-8')
MANGOHUD_VERSION_HEADER = bytearray('MangoHudVersion', 'utf-8')

DEFAULT_SERVER_ADDRESS = "\0mangohud"

class Connection:
    def __init__(self, path):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(path)
        except socket.error as msg:
            log.error(msg)
            raise msg

        self.sock = sock
        epoll = select.epoll()
        epoll.register(sock, EPOLLIN | EPOLLPRI | EPOLLERR)
        self.epoll = epoll

    def recv(self, timeout):
        '''
        timeout as float in seconds
        retuirns:
            - None on error or disconnection
            - bytes() (empty) on timeout
        '''

        events = self.epoll.poll(timeout)
        for ev in events:
            (fd, event) = ev
            if fd != self.sock.fileno():
                continue

            if event & EPOLLERR:
                return None

            msg = self.sock.recv(4096)

            if len(msg) == 0:
                return None

            return msg

        return bytes()

    def send(self, msg):
        self.sock.send(msg)

class MsgParser:
    MSGBEGIN = bytes(':', 'utf-8')[0]
    MSGEND = bytes(';', 'utf-8')[0]
    MSGSEP = bytes('=', 'utf-8')[0]

    def __init__(self, conn):
        self.cmdpos = 0
        self.parampos = 0
        self.bufferpos = 0
        self.reading_cmd = False
        self.reading_param = False
        self.buffer = None
        self.cmd = bytearray(4096)
        self.param = bytearray(4096)

        self.conn = conn

    def readCmd(self, ncmds, timeout=TIMEOUT):
        '''
        returns:
            - None on error or disconnection
            - bytes() (empty) on timeout
        '''

        parsed = []
        remaining = timeout

        while remaining > 0 and ncmds > 0:
            now = time.monotonic()

            if self.buffer == None:
                self.buffer = self.conn.recv(remaining)
                self.bufferpos = 0

            if self.buffer == None:
                return None

            for i in range(self.bufferpos, len(self.buffer)):
                c = self.buffer[i]
                if c == self.MSGBEGIN:
                    self.cmdpos = 0
                    self.parampos = 0
                    self.reading_cmd = True
                    self.reading_param = False
                elif c == self.MSGEND:
                    if not self.reading_cmd:
                        continue
                    self.reading_cmd = False
                    self.reading_param = False

                    cmd = self.cmd[0:self.cmdpos]
                    param = self.param[0:self.parampos]
                    self.reading_cmd = False
                    self.reading_param = False

                    parsed.append((cmd, param))
                    ncmds -= 1
                    if ncmds == 0:
                        break
                elif c == self.MSGSEP:
                    if self.reading_cmd:
                        self.reading_param = True
                else:
                    if self.reading_param:
                        self.param[self.parampos] = c
                        self.parampos += 1
                    elif self.reading_cmd:
                        self.cmd[self.cmdpos] = c
                        self.cmdpos += 1

            self.buffer = None

            elapsed = time.monotonic() - now
            remaining = max(0, remaining - elapsed)

        return parsed

def control(socket : str = DEFAULT_SERVER_ADDRESS, logging : bool = False, hud : bool = False):
    if socket != DEFAULT_SERVER_ADDRESS:
        address = f"\0{socket}"
    else:
        address = socket

    conn = Connection(address)
    msgparser = MsgParser(conn)

    version = None
    name = None
    mangohud_version = None

    msgs = msgparser.readCmd(3)

    for m in msgs:
        cmd, param = m
        if cmd == VERSION_HEADER:
            version = int(param)
        elif cmd == DEVICE_NAME_HEADER:
            name = param.decode("utf-8")
        elif cmd == MANGOHUD_VERSION_HEADER:
            mangohud_version = param.decode("utf-8")

    if logging:
        conn.send(bytearray("logging=1;", "utf-8"))
    elif hud:
        conn.send(bytearray(":hud;", "utf-8"))