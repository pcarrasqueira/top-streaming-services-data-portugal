# Developer Guide

This guide is for developers who want to contribute to or understand the codebase of the Top Streaming Services Data Portugal project.

## 🏗️ Project Architecture

### Overview
The project has been refactored from a monolithic script into a well-organized, object-oriented structure while maintaining complete backward compatibility.

### Core Components

#### 1. Configuration Management (`Config` class)
- **Purpose**: Centralized configuration management
- **Location**: `Config` class in `top_pt_stream_services.py`
- **Responsibilities**:
  - Environment variable loading
  - URL and endpoint management
  - Request timeout and retry configuration
  - Date calculations

```python
config = Config()
# Access configuration values
timeout = config.REQUEST_TIMEOUT
urls = config.urls['netflix']
```

#### 2. Main Business Logic (`StreamingServiceTracker` class)
- **Purpose**: Encapsulates all streaming service tracking functionality
- **Location**: `StreamingServiceTracker` class in `top_pt_stream_services.py`
- **Key Methods**:
  - `run()`: Main execution method
  - `_scrape_all_services()`: Scrapes data from all platforms
  - `_validate_trakt_setup()`: Validates authentication and lists
  - `_update_all_lists()`: Updates all Trakt lists

```python
tracker = StreamingServiceTracker()
result = tracker.run()  # Returns 0 on success, -1 on error
```

#### 3. Helper Functions
- **Web Scraping**: `scrape_top10()` - Extracts top content from FlixPatrol
- **API Communication**: `get_headers()`, `check_token()`, `update_list()`
- **Data Processing**: `create_type_trakt_list_payload()`, `search_title()`
- **Utilities**: `print_top_list()`, `retry_request` decorator

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+
- All dependencies from `requirements.txt` and `requirements-dev.txt`

### Installation
```bash
# Clone the repository
git clone https://github.com/pcarrasqueira/top-streaming-services-data-portugal.git
cd top-streaming-services-data-portugal

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Environment Setup
Copy `.env.example` to `.env` and fill in your Trakt API credentials:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## 🧪 Testing

### Running Tests
```bash
# Run basic refactoring tests
python test_refactoring.py

# Run code quality checks
flake8 top_pt_stream_services.py --max-line-length=120
black --check --line-length 120 top_pt_stream_services.py
bandit -r top_pt_stream_services.py
```

### Adding New Tests
To add tests for new functionality:

1. Create test functions in `test_refactoring.py`
2. Follow the existing pattern of simple assert statements
3. Test both success and failure cases where applicable

## 📝 Code Style Guidelines

### Formatting
- **Line Length**: Maximum 120 characters
- **Code Formatter**: Black with `--line-length 120`
- **Import Sorting**: isort with black profile
- **Type Hints**: Required for all public functions

### Naming Conventions
- **Classes**: PascalCase (e.g., `StreamingServiceTracker`)
- **Functions**: snake_case (e.g., `scrape_top10`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `REQUEST_TIMEOUT`)
- **Private Methods**: Leading underscore (e.g., `_scrape_all_services`)

### Code Quality
All code must pass:
- **flake8**: Style and syntax checking
- **black**: Code formatting
- **bandit**: Security scanning
- **isort**: Import organization

## 🔒 Security Considerations

### Request Timeouts
All HTTP requests must include timeout parameters to prevent hanging:

```python
response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
```

### Environment Variables
Sensitive data (API keys, tokens) must be stored in environment variables, never hardcoded:

```python
CLIENT_ID = os.getenv("CLIENT_ID")  # ✅ Good
CLIENT_ID = "your-key-here"         # ❌ Bad
```

### Error Handling
All external API calls and web scraping should include proper error handling:

```python
try:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    # Process response
except requests.exceptions.RequestException as e:
    logging.error(f"Request failed: {e}")
    return None
```

## 🚀 Adding New Streaming Services

To add support for a new streaming service:

1. **Update Configuration**:
   ```python
   # In Config.__init__()
   self.urls['new_service'] = "https://flixpatrol.com/top10/new-service/portugal/"
   ```

2. **Add List Data**:
   ```python
   # Add to StreamingServiceTracker._init_list_data()
   self.new_service_movies_list_data = {
       "name": "Top Portugal New Service Movies",
       "description": "Top movies on New Service Portugal",
       "privacy": "public",
       "display_numbers": True,
   }
   ```

3. **Update Scraping Logic**:
   ```python
   # In _scrape_all_services()
   'new_service_movies': scrape_top10(self.config.urls['new_service'], self.config.sections['movies'])
   ```

4. **Update List Management**:
   ```python
   # Add to streaming_services list in _update_all_lists()
   ("new_service", data['new_service_movies'], data['new_service_shows'], 
    new_service_movies_slug, new_service_shows_slug)
   ```

## 🔄 Backward Compatibility

The refactoring maintains 100% backward compatibility:

- **Original API**: `main()` function works exactly as before
- **Global Variables**: All original globals still exist and work
- **Execution**: `python top_pt_stream_services.py` works unchanged
- **GitHub Actions**: No changes needed to existing workflows

## 📊 Performance Considerations

### Request Optimization
- Requests include timeouts to prevent hanging
- Retry logic with exponential backoff for failed requests
- Minimal delay between requests to respect rate limits

### Memory Usage
- Data is processed in chunks rather than storing everything in memory
- Lists are cleared before updates to prevent memory leaks

### Error Recovery
- Graceful handling of network failures
- Automatic token refresh for authentication
- Continued execution even if some services fail

## 🐛 Debugging

### Logging Levels
Set environment variables to control output:

```bash
PRINT_LISTS=True  # Enable debug output for scraped data
```

### Common Issues

1. **Authentication Errors**: Check Trakt API credentials in `.env`
2. **Network Timeouts**: May indicate FlixPatrol structure changes
3. **Missing Content**: Usually means content couldn't be matched on Trakt

### Debug Mode
```bash
# Run with debug output
PRINT_LISTS=True python top_pt_stream_services.py
```

## 📈 Monitoring and Metrics

The project tracks:
- **Success Rates**: List update success/failure
- **API Response Times**: Through request timeouts
- **Error Patterns**: Via comprehensive logging
- **Code Quality**: Automated via CI/CD pipeline

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** the code style guidelines
4. **Add** tests for new functionality
5. **Ensure** all quality checks pass
6. **Submit** a pull request

### Pull Request Checklist
- [ ] All tests pass
- [ ] Code passes flake8, black, bandit checks
- [ ] Type hints added for new functions
- [ ] Documentation updated if needed
- [ ] Backward compatibility maintained