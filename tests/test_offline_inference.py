import socket
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from seed_vc_local import block_network

class OfflineBoundary(unittest.TestCase):
    def test_internet_sockets_are_blocked_before_connecting(self):
        original_connect=socket.socket.connect
        original_create=socket.create_connection
        try:
            block_network()
            for family,address in [(socket.AF_INET,('127.0.0.1',9)),(socket.AF_INET6,('::1',9))]:
                with socket.socket(family,socket.SOCK_STREAM) as sock:
                    with self.assertRaisesRegex(RuntimeError,'Offline inference'):
                        sock.connect(address)
            with self.assertRaisesRegex(RuntimeError,'Offline inference'):
                socket.create_connection(('example.invalid',443))
        finally:
            socket.socket.connect=original_connect
            socket.create_connection=original_create

if __name__=='__main__':unittest.main()
