# crm: Core CRM Connectors

## Overview
The `crm/` directory contains core connectors for various CRM and productivity services, providing a standardized interface for interacting with Google Workspace (Gmail, Calendar, Sheets, Drive) and other platforms. These connectors are designed to be used by the AI assistant components in `asistente/`.

## Directory Structure
- `crm/connectors/` - Individual service connectors (gmail.py, calendar.py, etc.)
- `crm/config.example.json` - Example configuration for connectors
- `crm/cli.py` - Command-line interface for testing connectors
- `crm/README.md` - This file

## Key Features
- **Standardized Interface**: All connectors return `ConnectorResult` with `.ok` (bool) and `.data` (dict)
- **Modular Design**: Each service has its own connector file with consistent method names
- **Credential Management**: Connectors accept tokens via parameters or environment variables
- **Error Handling**: Consistent error handling and logging across all connectors
- **Google Workspace Focus**: Primary focus on Gmail, Calendar, Sheets, Drive APIs

## Connector Interface
Each connector should implement:
- `__init__(self, token=None, **kwargs)` - Initialize with optional token
- `list_messages(self, query, max_results)` - (Gmail specific) List messages matching query
- `send_message(self, to, subject, body)` - (Gmail specific) Send an email
- `get_events(self, time_min, time_max)` - (Calendar specific) Get events in time range
- `create_event(self, summary, start, end)` - (Calendar specific) Create calendar event
- `get_spreadsheet_values(self, spreadsheet_id, range)` - (Sheets specific) Get values from range
- `update_spreadsheet_values(self, spreadsheet_id, range, values)` - (Sheets specific) Update values
- `create_folder(self, name)` - (Drive specific) Create folder
- `upload_file(self, filepath, folder_id=None)` - (Drive specific) Upload file

## Usage
Connectors are designed to be imported and used by assistant components:
```python
from crm.connectors.gmail import GmailConnector

gmail = GmailConnector(token=my_token)
result = gmail.list_messages(query="is:unread", max_results=10)
if result.ok:
    messages = result.data['messages']
```

## Safety
- Never hardcode tokens in connector code
- Tokens should be passed via secure means (environment variables, parameter injection)
- Connectors should validate inputs before making API calls
- Rate limiting should be respected per service