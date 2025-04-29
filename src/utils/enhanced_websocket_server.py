"""
Enhanced WebSocket server for real-time data visualization with React frontend
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional, Set
from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)

class EnhancedWebSocketServer:
    """Enhanced WebSocket server for real-time data visualization with React frontend"""
    
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
        
        # Store experiment data
        self.threads = []
        self.current_thread_id = 0
    
    def setup_routes(self):
        """Setup server routes"""
        # Add WebSocket route
        self.app.router.add_get('/ws', self.websocket_handler)
        
        # Add a default route to serve index.html
        self.app.router.add_get('/', self.index_handler)
        self.logger.info("Added route for index.html")
        
        # Add routes for static files
        if self.static_dir and os.path.exists(self.static_dir):
            # For React build directory
            if os.path.exists(os.path.join(self.static_dir, 'static')):
                self.app.router.add_static('/static', os.path.join(self.static_dir, 'static'))
            
            # For CSS and JS files
            if os.path.exists(os.path.join(self.static_dir, 'css')):
                self.app.router.add_get('/css/style.css', self.css_handler)
            
            if os.path.exists(os.path.join(self.static_dir, 'js')):
                self.app.router.add_get('/js/realtime_chart.js', self.js_handler)
            
            self.logger.info(f"Serving static files from {self.static_dir}")
    
    async def index_handler(self, request):
        """Handle requests to the root path"""
        # First try React build index.html
        if self.static_dir:
            react_index = os.path.join(self.static_dir, 'index.html')
            if os.path.exists(react_index):
                with open(react_index, 'r') as f:
                    html_content = f.read()
                return web.Response(text=html_content, content_type='text/html')
        
        # Fallback to original index.html
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
            
            # Send existing threads if any
            if self.threads:
                await ws.send_json({
                    'type': 'threads_update',
                    'threads': self.threads
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
                            
                            # Handle client messages
                            if data.get('type') == 'get_threads':
                                await ws.send_json({
                                    'type': 'threads_update',
                                    'threads': self.threads
                                })
                            elif data.get('type') == 'select_thread':
                                thread_id = data.get('thread_id')
                                # Find thread and send its data
                                for thread in self.threads:
                                    if thread['id'] == thread_id:
                                        await ws.send_json({
                                            'type': 'thread_selected',
                                            'thread': thread
                                        })
                                        break
                            else:
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
    
    async def broadcast_data_point(self, technique: str, x: float, y: float):
        """
        Broadcast a data point to all connected clients
        
        Parameters
        ----------
        technique : str
            Technique type
        x : float
            X value
        y : float
            Y value
        """
        # Create data point message
        data_point = {
            'type': 'data_point',
            'technique': technique,
            'x': x,
            'y': y
        }
        
        # Update threads
        self._update_threads(technique, x, y)
        
        # Broadcast data point
        await self.broadcast(data_point)
    
    def _update_threads(self, technique: str, x: float, y: float):
        """
        Update threads with new data point
        
        Parameters
        ----------
        technique : str
            Technique type
        x : float
            X value
        y : float
            Y value
        """
        # Check if we need to create a new thread
        if not self.threads or self.threads[-1]['technique'] != technique:
            self.current_thread_id += 1
            new_thread = {
                'id': self.current_thread_id,
                'title': f"{technique}-{self.current_thread_id}",
                'technique': technique,
                'timestamp': self._get_timestamp(),
                'data': {
                    'x': [x],
                    'y': [y]
                }
            }
            self.threads.append(new_thread)
        else:
            # Update existing thread
            self.threads[-1]['data']['x'].append(x)
            self.threads[-1]['data']['y'].append(y)
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
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
