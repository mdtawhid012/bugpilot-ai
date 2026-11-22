import asyncio
import socket

import uvicorn

from app.core.config import Settings


def _loopback_sockets(port: int) -> list[socket.socket]:
    sockets = []
    try:
        ipv4 = socket.create_server(("127.0.0.1", port), family=socket.AF_INET)
        sockets.append(ipv4)
        ipv6 = socket.create_server(("::1", port), family=socket.AF_INET6, dualstack_ipv6=False)
        sockets.append(ipv6)
        return sockets
    except Exception:
        for listener in sockets:
            listener.close()
        raise


def main() -> None:
    settings = Settings.from_environment()
    settings.validate()
    listeners = _loopback_sockets(settings.api_port)
    try:
        config = uvicorn.Config("app.main:app", host=None, port=settings.api_port)
        server = uvicorn.Server(config)
        asyncio.run(server.serve(sockets=listeners))
    finally:
        for listener in listeners:
            listener.close()


if __name__ == "__main__":
    main()