import os
import argparse
import requests
from datetime import datetime
from typing import List, Set
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    BigInteger,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

Base = declarative_base()


# Define the models
class MapRegion(Base):
    __tablename__ = "mapRegions"

    # Primary key
    regionID = Column(Integer, primary_key=True, nullable=False)

    # Region information
    regionName = Column(String(100), nullable=True)

    # Coordinate information
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)

    # Bounding box coordinates
    xMin = Column(Float, nullable=True)
    xMax = Column(Float, nullable=True)
    yMin = Column(Float, nullable=True)
    yMax = Column(Float, nullable=True)
    zMin = Column(Float, nullable=True)
    zMax = Column(Float, nullable=True)

    # Additional properties
    factionID = Column(Integer, nullable=True)
    nebula = Column(Integer, nullable=True)
    radius = Column(Float, nullable=True)


class IndustryActivityProduct(Base):
    __tablename__ = "industryActivityProducts"

    # Columns matching the MySQL table structure
    # Note: No primary key defined in the original table
    typeID = Column(Integer, primary_key=True, nullable=True)
    activityID = Column(Integer, nullable=True)
    productTypeID = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)


class MarketOrder(Base):
    __tablename__ = "market_orders"

    # Primary key
    order_id = Column(BigInteger, primary_key=True, nullable=False)

    # Order details
    duration = Column(Integer, nullable=True)
    is_buy_order = Column(Boolean, nullable=False)
    issued = Column(DateTime, nullable=False)

    # Location information
    location_id = Column(BigInteger, nullable=False)
    system_id = Column(Integer, nullable=True)
    range = Column(String(50), nullable=True)  # e.g., "region", "station", "system"

    # Item and volume information
    type_id = Column(Integer, nullable=False)
    min_volume = Column(Integer, nullable=True)
    volume_remain = Column(Integer, nullable=False)
    volume_total = Column(Integer, nullable=False)

    # Price information
    price = Column(
        BigInteger, nullable=False
    )  # Using BigInteger for large price values


# New model for blueprint items with long durations
class BlueprintLongDurationOrder(Base):
    __tablename__ = "blueprint_long_duration_orders"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Item information
    type_id = Column(Integer, nullable=False, unique=True)  # ItemID from market orders

    # Additional metadata
    first_detected = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Optional: Store additional info about the blueprint
    order_count = Column(
        Integer, nullable=True
    )  # Number of orders found with duration > 90


class EVEMarketCollector:
    def __init__(self, database_dsn: str = None):
        """Initialize the EVE Market Collector with database connection."""
        if database_dsn is None:
            database_dsn = os.getenv("DATABASE_DSN")

        if not database_dsn:
            raise ValueError(
                "DATABASE_DSN not found in environment variables or provided as argument"
            )

        self.engine = create_engine(database_dsn)
        self.Session = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # ESI API base URL
        self.esi_base_url = "https://esi.evetech.net/latest"

    def get_null_faction_regions(self) -> List[int]:
        """Get list of region IDs where factionID is NULL."""
        with self.Session() as session:
            regions = (
                session.query(MapRegion.regionID)
                .filter(MapRegion.factionID.is_not(None))
                .all()
            )

            region_ids = [r[0] for r in regions]
            logger.info(f"Found {len(region_ids)} regions with NULL factionID")
            return region_ids

    def fetch_market_orders(self, region_id: int) -> List[dict]:
        """Fetch all market orders for a given region, handling pagination."""
        all_orders = []
        page = 1

        while True:
            url = f"{self.esi_base_url}/markets/{region_id}/orders/"
            params = {"datasource": "tranquility", "order_type": "all", "page": page}

            try:
                logger.info(
                    f"Fetching market orders for region {region_id}, page {page}"
                )
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 404:
                    logger.warning(f"Region {region_id} not found in ESI")
                    break

                response.raise_for_status()

                orders = response.json()
                if not orders:
                    break

                all_orders.extend(orders)

                # Check if there are more pages
                pages_header = response.headers.get("X-Pages", "1")
                total_pages = int(pages_header)

                if page >= total_pages:
                    break

                page += 1

                # Be nice to the API
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error fetching orders for region {region_id}, page {page}: {e}"
                )
                break

        logger.info(f"Fetched {len(all_orders)} total orders for region {region_id}")
        return all_orders

    def save_market_orders(self, orders: List[dict], region_id: int):
        """Save market orders to the database."""
        with self.Session() as session:
            saved_count = 0

            for order_data in orders:
                try:
                    # Check if order already exists
                    existing_order = (
                        session.query(MarketOrder)
                        .filter_by(order_id=order_data["order_id"])
                        .first()
                    )

                    if existing_order:
                        # Update existing order
                        existing_order.duration = order_data["duration"]
                        existing_order.is_buy_order = order_data["is_buy_order"]
                        existing_order.issued = datetime.fromisoformat(
                            order_data["issued"].replace("Z", "+00:00")
                        )
                        existing_order.location_id = order_data["location_id"]
                        existing_order.system_id = order_data.get("system_id")
                        existing_order.range = order_data.get("range")
                        existing_order.type_id = order_data["type_id"]
                        existing_order.min_volume = order_data.get("min_volume")
                        existing_order.volume_remain = order_data["volume_remain"]
                        existing_order.volume_total = order_data["volume_total"]
                        existing_order.price = int(
                            order_data["price"] * 100
                        )  # Store as cents to avoid float issues
                    else:
                        # Create new order
                        market_order = MarketOrder(
                            order_id=order_data["order_id"],
                            duration=order_data["duration"],
                            is_buy_order=order_data["is_buy_order"],
                            issued=datetime.fromisoformat(
                                order_data["issued"].replace("Z", "+00:00")
                            ),
                            location_id=order_data["location_id"],
                            system_id=order_data.get("system_id"),
                            range=order_data.get("range"),
                            type_id=order_data["type_id"],
                            min_volume=order_data.get("min_volume"),
                            volume_remain=order_data["volume_remain"],
                            volume_total=order_data["volume_total"],
                            price=int(
                                order_data["price"] * 100
                            ),  # Store as cents to avoid float issues
                        )
                        session.add(market_order)

                    saved_count += 1

                except Exception as e:
                    logger.error(
                        f"Error saving order {order_data.get('order_id')}: {e}"
                    )
                    continue

            try:
                session.commit()
                logger.info(
                    f"Saved/updated {saved_count} market orders for region {region_id}"
                )
            except SQLAlchemyError as e:
                logger.error(f"Database error while saving orders: {e}")
                session.rollback()

    def download_all_market_orders(self):
        """Download market orders for all regions with NULL factionID."""
        region_ids = self.get_null_faction_regions()

        for region_id in region_ids:
            logger.info(f"Processing region {region_id}")
            orders = self.fetch_market_orders(region_id)

            if orders:
                self.save_market_orders(orders, region_id)

            # Be nice to the API
            time.sleep(1)

    def get_blueprint_type_ids(self) -> Set[int]:
        """Get all blueprint type IDs from IndustryActivityProduct."""
        with self.Session() as session:
            # Get unique productTypeIDs that represent blueprints
            blueprint_ids = (
                session.query(IndustryActivityProduct.productTypeID)
                .filter(IndustryActivityProduct.productTypeID.isnot(None))
                .distinct()
                .all()
            )

            type_ids = {bid[0] for bid in blueprint_ids}
            logger.info(f"Found {len(type_ids)} unique blueprint type IDs")
            return type_ids

    def find_long_duration_blueprint_orders(self):
        """Find blueprint orders with duration > 90 days and save to new table."""
        blueprint_type_ids = self.get_blueprint_type_ids()

        with self.Session() as session:
            # Find market orders for blueprints with duration > 90 days
            long_duration_orders = (
                session.query(MarketOrder.type_id)
                .filter(
                    MarketOrder.type_id.in_(blueprint_type_ids),
                    MarketOrder.duration > 90,
                )
                .distinct()
                .all()
            )

            saved_count = 0

            for (type_id,) in long_duration_orders:
                # Check if already exists
                existing = (
                    session.query(BlueprintLongDurationOrder)
                    .filter_by(type_id=type_id)
                    .first()
                )

                if not existing:
                    # Count how many orders exist for this type
                    order_count = (
                        session.query(MarketOrder)
                        .filter(
                            MarketOrder.type_id == type_id, MarketOrder.duration > 90
                        )
                        .count()
                    )

                    # Create new record
                    blueprint_record = BlueprintLongDurationOrder(
                        type_id=type_id, order_count=order_count
                    )
                    session.add(blueprint_record)
                    saved_count += 1
                else:
                    # Update order count
                    order_count = (
                        session.query(MarketOrder)
                        .filter(
                            MarketOrder.type_id == type_id, MarketOrder.duration > 90
                        )
                        .count()
                    )
                    existing.order_count = order_count

            try:
                session.commit()
                logger.info(
                    f"Saved/updated {saved_count} blueprint type IDs with long duration orders"
                )
            except SQLAlchemyError as e:
                logger.error(f"Database error while saving blueprint records: {e}")
                session.rollback()


def main():
    parser = argparse.ArgumentParser(description="EVE Online Market Data Collector")
    parser.add_argument(
        "--get-regions",
        action="store_true",
        help="Get list of systems from MapRegion where factionID is NULL",
    )
    parser.add_argument(
        "--download-orders",
        action="store_true",
        help="Download market orders for all NULL faction regions",
    )
    parser.add_argument(
        "--find-blueprints",
        action="store_true",
        help="Find blueprint orders with duration > 90 days",
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all operations in sequence"
    )

    args = parser.parse_args()

    # Initialize collector
    collector = EVEMarketCollector()

    if args.get_regions or args.all:
        logger.info("Getting regions with NULL factionID...")
        region_ids = collector.get_null_faction_regions()
        for region_id in region_ids:
            logger.info(f"Region ID: {region_id}")

    if args.download_orders or args.all:
        logger.info("Downloading market orders...")
        collector.download_all_market_orders()

    if args.find_blueprints or args.all:
        logger.info("Finding blueprint orders with long durations...")
        collector.find_long_duration_blueprint_orders()

    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()
