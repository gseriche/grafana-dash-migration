# Grafana Dashboard Migration Tool

Python script to migrate dashboards and folder structure from one Grafana instance to another.

## Features

- Migrates complete folder structure
- Preserves dashboard folder organization
- Maintains dashboard configurations
- Shows detailed migration progress
- Handles errors gracefully

## Requirements

- Python 3.6+
- `requests` library
- API access tokens for both Grafana instances

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables:
```bash
export SOURCE_TOKEN="your-source-grafana-token"
export TARGET_TOKEN="your-target-grafana-token"
```

Update the URLs in the script:
```python
SOURCE_URL = "http://old-grafana:3000"
TARGET_URL = "http://new-grafana:3000"
```

## Usage

Run the script:
```bash
python grafana_migrator.py
```

The script will:
1. Create the folder structure from source Grafana
2. Migrate dashboards to their respective folders
3. Show progress and any errors during migration

## Development

### Running Tests
```bash
pip install pytest
pytest test_grafana_migrator.py -v
```

### Code Style
Project uses flake8 with custom configuration:
```ini
# .flake8
[flake8]
extend-ignore = C901
```

To check code style:
```bash
flake8 .
```

## API Token Permissions

Required permissions for both source and target tokens:
- Folders: Read/Write
- Dashboards: Read/Write

## Error Handling

The script handles common errors:
- Network connectivity issues
- API authentication errors
- Missing folders
- Dashboard import failures

Each error is logged with the specific dashboard or folder affected.

## Contributing

Feel free to submit issues and enhancement requests.