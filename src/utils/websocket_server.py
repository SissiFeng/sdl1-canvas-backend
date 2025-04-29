"""
WebSocket server for real-time data visualization
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, Set
from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)

class WebSocketServer:
    """WebSocket server for real-time data visualization"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765, static_dir: Optional[str] = None):
        """
        Initialize WebSocket server

        Parameters
        ----------
        host : str
            Host to bind server to
        port : int
            Port to bind server to
        static_dir : Optional[str]
            Directory containing static files to serve
        """
        self.host = host
        self.port = port
        self.static_dir = static_dir
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.app = web.Application()
        self.setup_routes()
        self.clients: Set[web.WebSocketResponse] = set()
        self.runner = None
        self.site = None

    def setup_routes(self):
        """Setup server routes"""
        self.app.router.add_get('/ws', self.websocket_handler)

        # Add static file handling if static_dir is provided
        if self.static_dir and os.path.exists(self.static_dir):
            # Add a default route to serve index.html
            self.app.router.add_get('/', self.index_handler)
            self.logger.info("Added route for index.html")

            # Add routes for CSS and JS files
            self.app.router.add_get('/css/style.css', self.css_handler)
            self.app.router.add_get('/js/realtime_chart.js', self.js_handler)
            self.logger.info(f"Serving static files from {self.static_dir}")

    async def index_handler(self, request):
        """Handle requests to the root path"""
        if self.static_dir and os.path.exists(os.path.join(self.static_dir, 'index.html')):
            with open(os.path.join(self.static_dir, 'index.html'), 'r') as f:
                html_content = f.read()
            return web.Response(text=html_content, content_type='text/html')
        else:
            return web.Response(text="WebSocket server is running. Connect to /ws for data stream.")

    async def css_handler(self, request):
        """Handle CSS file requests"""
        css_path = os.path.join(self.static_dir, 'css', 'style.css')
        if os.path.exists(css_path):
            with open(css_path, 'r') as f:
                css_content = f.read()
            return web.Response(text=css_content, content_type='text/css')
        else:
            return web.Response(status=404)

    async def js_handler(self, request):
        """Handle JavaScript file requests"""
        js_path = os.path.join(self.static_dir, 'js', 'realtime_chart.js')
        if os.path.exists(js_path):
            with open(js_path, 'r') as f:
                js_content = f.read()
            return web.Response(text=js_content, content_type='application/javascript')
        else:
            return web.Response(status=404)

    async def websocket_handler(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Add client to set
        self.clients.add(ws)
        client_id = id(ws)
        self.logger.info(f"Client {client_id} connected, total clients: {len(self.clients)}")

        try:
            # Send initial message
            await ws.send_json({
                'type': 'connection_established',
                'message': 'Connected to Biologic data stream'
            })

            # Handle incoming messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data == 'close':
                        await ws.close()
                    else:
                        try:
                            data = json.loads(msg.data)
                            self.logger.debug(f"Received message from client {client_id}: {data}")

                            # Handle client messages here if needed
                            await ws.send_json({
                                'type': 'acknowledgement',
                                'message': 'Message received'
                            })
                        except json.JSONDecodeError:
                            self.logger.warning(f"Received invalid JSON from client {client_id}")
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket connection closed with exception: {ws.exception()}")
        finally:
            # Remove client from set
            self.clients.remove(ws)
            self.logger.info(f"Client {client_id} disconnected, remaining clients: {len(self.clients)}")

        return ws

    async def broadcast(self, data: Dict[str, Any]):
        """
        Broadcast data to all connected clients

        Parameters
        ----------
        data : Dict[str, Any]
            Data to broadcast
        """
        if not self.clients:
            return

        # Convert data to JSON string
        message = json.dumps(data)

        # Send to all clients
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send_str(message)
            except Exception as e:
                self.logger.error(f"Error sending data to client: {str(e)}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.remove(client)

    async def start(self):
        """Start WebSocket server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        self.logger.info(f"WebSocket server started at http://{self.host}:{self.port}")

    async def stop(self):
        """Stop WebSocket server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        self.logger.info("WebSocket server stopped")
