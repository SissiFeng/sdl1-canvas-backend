"""
Proxy server to connect WebSocket backend with React frontend
"""

import sys
import os
import asyncio
import logging
import argparse
from aiohttp import web, ClientSession, WSMessage, WSMsgType, ClientWebSocketResponse
from typing import Dict, Set, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ProxyServer:
    """Proxy server to connect WebSocket backend with React frontend"""

    def __init__(self, ws_backend_url: str, react_frontend_url: str, 
                 host: str = "0.0.0.0", port: int = 3001):
        """
        Initialize proxy server

        Parameters
        ----------
        ws_backend_url : str
            URL of the WebSocket backend server (e.g., "ws://localhost:8765/ws")
        react_frontend_url : str
            URL of the React frontend development server (e.g., "http://localhost:3000")
        host : str
            Host to bind server to
        port : int
            Port to bind server to
        """
        self.ws_backend_url = ws_backend_url
        self.react_frontend_url = react_frontend_url
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.clients: Set[web.WebSocketResponse] = set()
        self.backend_ws: Optional[ClientWebSocketResponse] = None
        self.runner = None
        self.site = None
        self.session = None

    def setup_routes(self):
        """Setup server routes"""
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/{path:.*}', self.proxy_handler)
        self.app.router.add_post('/{path:.*}', self.proxy_handler)
        self.app.router.add_put('/{path:.*}', self.proxy_handler)
        self.app.router.add_delete('/{path:.*}', self.proxy_handler)

    async def proxy_handler(self, request):
        """Proxy HTTP requests to React frontend"""
        client_path = request.match_info.get('path', '')
        target_url = f"{self.react_frontend_url}/{client_path}"
        
        logger.info(f"Proxying request to {target_url}")
        
        async with ClientSession() as session:
            method = request.method
            data = await request.read()
            headers = {k: v for k, v in request.headers.items() 
                      if k.lower() not in ('host', 'content-length')}
            
            async with session.request(method, target_url, headers=headers, data=data) as resp:
                content = await resp.read()
                headers = {k: v for k, v in resp.headers.items() 
                          if k.lower() not in ('transfer-encoding', 'content-encoding', 'content-length')}
                
                return web.Response(body=content, status=resp.status, headers=headers)

    async def websocket_handler(self, request):
        """Handle WebSocket connections from clients and proxy to backend"""
        ws_client = web.WebSocketResponse()
        await ws_client.prepare(request)
        
        # Add client to set
        self.clients.add(ws_client)
        client_id = id(ws_client)
        logger.info(f"Client {client_id} connected, total clients: {len(self.clients)}")
        
        # Connect to backend WebSocket if not already connected
        if not self.backend_ws or self.backend_ws.closed:
            await self.connect_to_backend()
        
        try:
            # Forward messages from client to backend
            async for msg in ws_client:
                if msg.type == WSMsgType.TEXT:
                    if self.backend_ws and not self.backend_ws.closed:
                        await self.backend_ws.send_str(msg.data)
                    else:
                        logger.warning("Backend WebSocket is not connected")
                        await self.connect_to_backend()
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket client error: {ws_client.exception()}")
        finally:
            # 修复：安全地移除客户端，避免 KeyError
            if ws_client in self.clients:
                self.clients.remove(ws_client)
            logger.info(f"Client {client_id} disconnected, remaining clients: {len(self.clients)}")
        
        return ws_client

    async def connect_to_backend(self):
        """Connect to backend WebSocket server"""
        try:
            logger.info(f"Connecting to backend WebSocket at {self.ws_backend_url}")
            if self.session is None:
                self.session = ClientSession()
            self.backend_ws = await self.session.ws_connect(self.ws_backend_url)
            logger.info(f"Connected to backend WebSocket at {self.ws_backend_url}")
            
            # Start task to forward messages from backend to all clients
            asyncio.create_task(self.forward_backend_messages())
        except Exception as e:
            logger.error(f"Failed to connect to backend WebSocket: {str(e)}")
            self.backend_ws = None

    async def forward_backend_messages(self):
        """Forward messages from backend to all clients"""
        if not self.backend_ws:
            return
        
        try:
            async for msg in self.backend_ws:
                if msg.type == WSMsgType.TEXT:
                    # Broadcast message to all clients
                    disconnected_clients = set()
                    for client in self.clients:
                        try:
                            if not client.closed:
                                await client.send_str(msg.data)
                            else:
                                disconnected_clients.add(client)
                        except Exception as e:
                            logger.error(f"Error forwarding message to client: {str(e)}")
                            disconnected_clients.add(client)
                    
                    # Remove disconnected clients
                    for client in disconnected_clients:
                        if client in self.clients:
                            self.clients.remove(client)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket backend error: {self.backend_ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"Error in backend message forwarding: {str(e)}")
        finally:
            logger.warning("Backend WebSocket connection closed")
            self.backend_ws = None
            
            # Try to reconnect after delay
            await asyncio.sleep(2)
            if len(self.clients) > 0:
                await self.connect_to_backend()

    async def start(self):
        """Start proxy server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"Proxy server started at http://{self.host}:{self.port}")

    async def stop(self):
        """Stop proxy server"""
        if self.backend_ws:
            await self.backend_ws.close()
        
        if self.session:
            await self.session.close()
        
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Proxy server stopped")

async def run_proxy_server(args):
    """Run proxy server"""
    try:
        server = ProxyServer(
            ws_backend_url=args.ws_backend_url,
            react_frontend_url=args.react_frontend_url,
            host=args.host,
            port=args.port
        )
        
        await server.start()
        
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error running proxy server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if 'server' in locals():
            await server.stop()
        logger.info("Server stopped")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Proxy server for WebSocket and React")
    
    parser.add_argument("--host", default="0.0.0.0", 
                        help="Host to bind server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=3003, 
                        help="Port to bind server to (default: 3003)")
    parser.add_argument("--ws-backend-url", default="ws://localhost:8765/ws", 
                        help="URL of the WebSocket backend server (default: ws://localhost:8765/ws)")
    parser.add_argument("--react-frontend-url", default="http://localhost:3002", 
                        help="URL of the React frontend server (default: http://localhost:3002)")
    
    return parser.parse_args()

async def main():
    """Main function"""
    args = parse_arguments()
    await run_proxy_server(args)

if __name__ == "__main__":
    asyncio.run(main()) 
