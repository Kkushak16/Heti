"""
Local WebSocket & HTTP Event Server for Handless Mode.
Broadcasts gesture status, active hand landmarks, FPS, and gesture events to web clients (such as Ekam).
"""
import json
import asyncio
import threading
from typing import Set, Dict, Any

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    websockets = None
    HAS_WEBSOCKETS = False

class GestureEventServer:
    """Broadcasting server that connects Handless Gesture Engine with Web Frontends."""

    def __init__(self, port: int = 8765):
        self.port = port
        self.connected_clients: Set[Any] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        """Starts the WebSocket server in a background daemon thread."""
        if not HAS_WEBSOCKETS or self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def handler(websocket, path=None):
            self.connected_clients.add(websocket)
            try:
                async for message in websocket:
                    # Parse incoming commands from client (e.g. toggle handless mode)
                    try:
                        data = json.loads(message)
                        cmd = data.get("command")
                        if cmd == "ping":
                            await websocket.send(json.dumps({"status": "pong"}))
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                self.connected_clients.remove(websocket)

        async def main():
            async with websockets.serve(handler, "127.0.0.1", self.port):
                await asyncio.Future()  # run forever

        try:
            self.loop.run_until_complete(main())
        except Exception:
            pass

    def broadcast(self, data: Dict[str, Any]):
        """Broadcasts event payload to all connected frontend clients."""
        if not self.running or not self.connected_clients or not self.loop:
            return
        
        message = json.dumps(data)
        for ws in list(self.connected_clients):
            try:
                asyncio.run_coroutine_threadsafe(ws.send(message), self.loop)
            except Exception:
                pass

    def stop(self):
        self.running = False
