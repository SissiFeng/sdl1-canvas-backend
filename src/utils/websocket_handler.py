"""
WebSocket data handler for real-time data visualization
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.utils.data_processing import DataHandler
from src.utils.websocket_server import WebSocketServer

class WebSocketDataHandler(DataHandler):
    """WebSocket data handler for real-time data visualization"""
    
    def __init__(self, websocket_server: WebSocketServer):
        """
        Initialize WebSocket data handler
        
        Parameters
        ----------
        websocket_server : WebSocketServer
            WebSocket server instance
        """
        self.websocket_server = websocket_server
        self.logger = logging.getLogger(__name__)
        self.current_technique = None
    
    async def handle_data(self, data: Any) -> None:
        """
        Process data and send to WebSocket clients
        
        Parameters
        ----------
        data : Any
            Data to process
        """
        try:
            # Get technique type
            technique_type = self.get_technique_type(data)
            
            # Extract data
            if hasattr(data, 'data') and hasattr(data.data, 'to_json'):
                json_data = data.data.to_json()
                
                # Check if technique has changed
                if technique_type != self.current_technique:
                    self.current_technique = technique_type
                    
                    # Send technique change notification
                    await self.websocket_server.broadcast({
                        'type': 'technique_change',
                        'technique': technique_type
                    })
                
                # Get plot data
                x_data, y_data = self._get_plot_data(json_data, technique_type)
                
                # Send data points
                if x_data and y_data:
                    for i in range(len(x_data)):
                        await self.websocket_server.broadcast({
                            'type': 'data_point',
                            'technique': technique_type,
                            'x': x_data[i],
                            'y': y_data[i]
                        })
                        
                    self.logger.debug(f"Sent {len(x_data)} data points to WebSocket clients")
        
        except Exception as e:
            self.logger.error(f"WebSocket data handling error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _get_plot_data(self, data: Dict[str, Any], technique_type: str) -> Tuple[List[float], List[float]]:
        """
        Get plot data based on technique type
        
        Parameters
        ----------
        data : Dict[str, Any]
            Data to process
        technique_type : str
            Technique type
            
        Returns
        -------
        Tuple[List[float], List[float]]
            X and Y data
        """
        if not data:
            return [], []
            
        # Ensure all data is list format
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                processed_data[key] = [value]
            elif isinstance(value, list):
                processed_data[key] = value
            else:
                try:
                    processed_data[key] = list(value)
                except:
                    processed_data[key] = [value]
        
        # Extract data based on technique type
        if technique_type in ['CV', 'MockCVTechnique']:
            return processed_data.get('Ewe', []), processed_data.get('I', [])
        elif technique_type in ['PEIS', 'MockPEISTechnique']:
            re_z = processed_data.get('Re(Z)', [])
            im_z = [-im for im in processed_data.get('Im(Z)', [])] if 'Im(Z)' in processed_data else []
            return re_z, im_z
        elif technique_type in ['OCV', 'CP', 'MockOCVTechnique', 'MockCPTechnique', 'MockResult']:
            return processed_data.get('time', []), processed_data.get('Ewe', [])
        elif technique_type == 'LP':
            return processed_data.get('Ewe', []), processed_data.get('I', [])
        else:
            # Try to find any numeric array that can be plotted
            for key1 in processed_data:
                if isinstance(processed_data[key1], list) and processed_data[key1]:
                    for key2 in processed_data:
                        if key1 != key2 and isinstance(processed_data[key2], list) and processed_data[key2]:
                            self.logger.info(f"Using general data: x={key1}, y={key2}")
                            return processed_data[key1], processed_data[key2]
            return [], []
    
    @staticmethod
    def get_technique_type(data: Any) -> str:
        """
        Get technique type from data
        
        Parameters
        ----------
        data : Any
            Data to process
            
        Returns
        -------
        str
            Technique type
        """
        if hasattr(data, 'data'):
            data_obj = data.data
            
            # Method 1: Get class name
            class_name = data_obj.__class__.__name__
            if class_name != 'object':
                return class_name
            
            # Method 2: Find type attribute
            if hasattr(data_obj, 'type'):
                return data_obj.type
            
            # Method 3: Find technique type attribute
            if hasattr(data_obj, 'technique_type'):
                return data_obj.technique_type
        
        return "Unknown"
