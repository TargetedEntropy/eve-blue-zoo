"""Preston ESI Client for Market Dumper"""

import preston
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MarketESIClient:
    """Preston-based ESI client for market data collection"""
    
    def __init__(self):
        # Initialize Preston for public data access
        self.client = preston.Preston(
            user_agent="Eve Blue Zoo Market Dumper/1.0",
            # No client_id/secret needed for public market data
        )
        logger.info("Preston ESI client initialized for market data")
    
    def get_market_orders(self, region_id: int, page: int = 1) -> Dict[str, Any]:
        """Get market orders for a region
        
        Args:
            region_id (int): EVE region ID
            page (int): Page number for pagination
            
        Returns:
            dict: Response with orders data and pagination info
        """
        endpoint = f"/markets/{region_id}/orders/"
        params = {
            "datasource": "tranquility",
            "order_type": "all", 
            "page": page
        }
        
        try:
            response = self.client.request("GET", endpoint, params=params)
            
            # Preston returns the data directly, but we need pagination info
            # For now, we'll use the direct response - pagination handled elsewhere
            return {
                "data": response,
                "page": page
            }
            
        except Exception as e:
            logger.error(f"Error fetching market orders for region {region_id}, page {page}: {e}")
            raise
    
    def get_region_info(self, region_id: int) -> Dict[str, Any]:
        """Get information about a region
        
        Args:
            region_id (int): EVE region ID
            
        Returns:
            dict: Region information
        """
        endpoint = f"/universe/regions/{region_id}/"
        
        try:
            return self.client.request("GET", endpoint)
        except Exception as e:
            logger.error(f"Error fetching region info for {region_id}: {e}")
            raise