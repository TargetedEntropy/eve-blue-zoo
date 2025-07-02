# EVE Online Market Data Collector

A Python script that collects market data from EVE Online's ESI API and stores it in a database for analysis, with special focus on identifying long-duration blueprint orders.

## Features

- **Region Discovery**: Automatically identifies regions with NULL factionID from the database
- **Market Data Collection**: Downloads all market orders from specified regions via EVE's ESI API
- **Blueprint Analysis**: Identifies blueprint items with market orders lasting longer than 90 days
- **Pagination Support**: Handles multi-page API responses automatically
- **Database Integration**: Uses SQLAlchemy ORM for database operations
- **Environment Configuration**: Secure credential management via .env files
- **CLI Interface**: Separate executable steps via command-line flags
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Requirements

- Python 3.7+
- MySQL, PostgreSQL, or SQLite database
- Internet connection for API access

## Installation

1. Clone this repository or download the script

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. For MySQL support, also install:
```bash
pip install pymysql
```

For PostgreSQL support:
```bash
pip install psycopg2-binary
```

## Configuration

1. Create a `.env` file in the project directory:

```env
# For MySQL
DATABASE_DSN=mysql+pymysql://username:password@localhost:3306/database_name

# For PostgreSQL
# DATABASE_DSN=postgresql://username:password@localhost:5432/database_name

# For SQLite (for testing)
# DATABASE_DSN=sqlite:///eve_market.db
```

2. Ensure your database has the required tables. The script will create the `blueprint_long_duration_orders` table automatically, but you need to have:
   - `mapRegions` table with EVE Online region data
   - `industryActivityProducts` table with blueprint data

## Usage

The script provides several command-line options:

### Get Regions with NULL factionID
```bash
python eve_market_collector.py --get-regions
```
Lists all regions where factionID is NULL.

### Download Market Orders
```bash
python eve_market_collector.py --download-orders
```
Downloads all market orders for regions with NULL factionID from the EVE ESI API.

### Find Long-Duration Blueprint Orders
```bash
python eve_market_collector.py --find-blueprints
```
Identifies blueprint items that have market orders with duration > 90 days.

### Run All Operations
```bash
python eve_market_collector.py --all
```
Executes all operations in sequence: get regions → download orders → find blueprints.

### Help
```bash
python eve_market_collector.py --help
```
Shows all available command-line options.

## Database Schema

### Required Tables (must exist in your database)

#### mapRegions
- `regionID` (INTEGER, PRIMARY KEY)
- `regionName` (VARCHAR(100))
- `factionID` (INTEGER, nullable)
- Additional coordinate and property fields

#### industryActivityProducts
- `typeID` (INTEGER)
- `activityID` (INTEGER)
- `productTypeID` (INTEGER)
- `quantity` (INTEGER)

### Tables Created by Script

#### market_orders
- `order_id` (BIGINT, PRIMARY KEY)
- `duration` (INTEGER)
- `is_buy_order` (BOOLEAN)
- `issued` (DATETIME)
- `location_id` (BIGINT)
- `system_id` (INTEGER)
- `range` (VARCHAR(50))
- `type_id` (INTEGER)
- `min_volume` (INTEGER)
- `volume_remain` (INTEGER)
- `volume_total` (INTEGER)
- `price` (BIGINT) - Stored in cents to avoid float precision issues

#### blueprint_long_duration_orders
- `id` (INTEGER, PRIMARY KEY, AUTO INCREMENT)
- `type_id` (INTEGER, UNIQUE)
- `first_detected` (DATETIME)
- `last_updated` (DATETIME)
- `order_count` (INTEGER)

## API Information

The script uses EVE Online's ESI (EVE Swagger Interface) API:
- Base URL: `https://esi.evetech.net/latest`
- Endpoint: `/markets/{region_id}/orders/`
- Rate limiting is respected with built-in delays

## Data Flow

1. **Region Discovery**: Queries `mapRegions` for regions where `factionID IS NULL`
2. **Market Data Collection**: 
   - For each region, fetches all market orders via ESI API
   - Handles pagination automatically
   - Saves/updates orders in `market_orders` table
3. **Blueprint Analysis**:
   - Gets blueprint type IDs from `industryActivityProducts.productTypeID`
   - Finds market orders for these items with `duration > 90`
   - Saves unique type IDs to `blueprint_long_duration_orders`

## Important Notes

- **Price Storage**: Prices are stored as cents (multiplied by 100) to avoid floating-point precision issues
- **API Rate Limiting**: The script includes delays between API calls to respect ESI rate limits
- **Date Handling**: All timestamps are stored in UTC
- **Error Handling**: Failed API calls or database operations are logged but don't stop the entire process
- **Duplicate Prevention**: The script checks for existing records before inserting to prevent duplicates

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify your DATABASE_DSN in the .env file
   - Ensure the database server is running
   - Check username/password credentials

2. **API Errors**
   - Check your internet connection
   - Verify the ESI API is accessible
   - Some regions might return 404 if they don't have market data

3. **Missing Tables**
   - Ensure `mapRegions` and `industryActivityProducts` tables exist
   - These should be loaded from EVE's Static Data Export (SDE)

4. **Memory Issues**
   - For regions with many orders, consider increasing Python's memory limit
   - The script processes orders in batches to minimize memory usage

### Logging

The script provides detailed logging at the INFO level. To change the logging level, modify this line in the script:
```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```

Change `logging.INFO` to `logging.DEBUG` for more detailed output.

## EVE Online Static Data Export (SDE)

To populate the initial `mapRegions` and `industryActivityProducts` tables, you'll need to import data from EVE's SDE:
- Download from: https://developers.eveonline.com/resource/resources
- Import the relevant .sql files to your database

## License

This project is provided as-is for educational and personal use. Ensure you comply with EVE Online's Terms of Service and ESI API usage guidelines.

## Contributing

Feel free to submit issues or pull requests if you find bugs or have improvements to suggest.

## Acknowledgments

- CCP Games for providing the EVE Online ESI API
- The EVE Online developer community