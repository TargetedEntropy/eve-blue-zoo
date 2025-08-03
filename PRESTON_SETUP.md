# Preston ESI Setup Guide

Eve Online Blue Zoo now uses **Preston** instead of esipy for all ESI API interactions.

## Installation

Install Preston dependencies for each component:

```bash
# Flask Web Application
cd src/flask_app
pip install -r requirements.txt

# Task Manager  
cd ../task_manager
pip install -r requirements.txt

# Market Dumper
cd ../market_dumper  
pip install -r requirements.txt
```

## Configuration

Copy and configure environment files:

```bash
# Flask App
cp src/flask_app/env-sample src/flask_app/.env
# Edit .env with your EVE Online application credentials

# Task Manager
cp src/task_manager/env-sample src/task_manager/.env  
# Edit .env with database configuration

# Market Dumper
cp src/market_dumper/env-sample src/market_dumper/.env
# Edit .env with database configuration
```

### Required EVE Online SSO Configuration

In your `.env` files, configure:

```bash
ESI_CLIENT_ID=your_eve_application_client_id
ESI_SECRET_KEY=your_eve_application_secret_key  
ESI_CALLBACK=http://localhost:5000/sso/callback
ESI_USER_AGENT=Eve Blue Zoo/1.0 (your-email@domain.com)
```

## Architecture Changes

### Preston Integration Points

1. **Flask Authentication** (`src/flask_app/apps/authentication/esi.py`)
   - Preston-based ESI client with automatic token refresh
   - EVE SSO authentication flow
   - Character data retrieval

2. **Task Manager** (`src/task_manager/esi_client.py`)
   - Shared Preston client for background jobs
   - Skills, blueprints, contracts, mining ledger synchronization

3. **Market Dumper** (`src/market_dumper/esi_client.py`)  
   - Preston client for public market data collection

### Key Benefits

- **Better Performance**: Preston optimizes HTTP requests and connection pooling
- **Automatic Token Refresh**: Built-in token management 
- **Improved Error Handling**: Better retry logic and error recovery
- **Modern Architecture**: Clean separation of concerns

## Testing

Run the integration test to verify Preston setup:

```bash
python test_preston_integration.py
```

Expected output:
```
✓ Preston library imported successfully
✓ Flask ESI client (Preston-based) created successfully  
✓ Task Manager ESI client (Preston-based) imported successfully
✓ Market Dumper ESI client (Preston-based) created successfully
✓ Schema mapping tests passed
🎉 All tests passed! Preston integration is working correctly.
```

## Running the Application

### Flask Web Application
```bash
cd src/flask_app
export FLASK_APP=run.py
flask run --host=0.0.0.0 --port=5000
```

### Task Manager
```bash
cd src/task_manager
python task_main.py --tasks skills blueprints contracts
```

### Market Dumper
```bash
cd src/market_dumper
python main.py --download-orders
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Preston is installed in each component's environment
2. **Token Issues**: Verify EVE Online application credentials are correct
3. **Database Errors**: Check database configuration and connectivity

### Debug Mode

Enable detailed logging in Preston:
```bash
export PRESTON_LOG_LEVEL=DEBUG
```

## Migration Notes

- **No Data Migration Required**: Preston works with existing database schemas
- **Backward Compatibility**: API interfaces remain the same
- **ESI Schema Mapping**: esipy schema names automatically converted to Preston endpoints

The application now runs entirely on Preston with improved performance and reliability!