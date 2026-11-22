import socket
import unittest

from app.server import _loopback_sockets


class LoopbackServerTests(unittest.TestCase):
    def test_server_sockets_bind_only_to_ipv4_and_ipv6_loopback(self) -> None:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        finally:
            probe.close()

        listeners = _loopback_sockets(port)
        try:
            self.assertEqual({listener.getsockname()[0] for listener in listeners}, {"127.0.0.1", "::1"})
            self.assertEqual({listener.getsockname()[1] for listener in listeners}, {port})
        finally:
            for listener in listeners:
                listener.close()