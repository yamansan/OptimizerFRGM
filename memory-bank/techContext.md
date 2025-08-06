# Technical Context

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary programming language
- **Dash 2.17.0+**: Web framework for interactive applications
- **Dash Bootstrap Components 1.6.0+**: UI component library
- **pandas 2.2.0+**: Data manipulation and analysis
- **requests 2.31.0+**: HTTP library for API calls
- **SQLite**: Embedded database for local data storage

### UI/UX Technologies
- **Bootstrap**: CSS framework for responsive design
- **HTML/CSS**: Custom styling and layout
- **JavaScript**: Client-side interactivity (via Dash)
- **Dash DataTable**: Advanced table component with theming

### Integration Technologies
- **TT REST API**: Trading Technologies API for order/fill data
- **pywinauto 0.6.8+**: Windows automation for Pricing Monkey
- **pyperclip 1.8.2+**: Clipboard automation for price capture
- **JSON**: Data serialization for API responses and config

### Data & Storage
- **SQLite3**: Local database for historical data
- **CSV**: File format for data exchange and logging
- **Pickle**: Binary serialization for state persistence
- **JSON**: Token storage and configuration files

## Platform Constraints

### Operating System
- **Windows Required**: Pricing Monkey integration requires Windows OS
- **PowerShell**: Batch scripts use Windows PowerShell
- **File System**: Windows path conventions throughout codebase
- **Browser**: Default browser must be configured for Pricing Monkey URL

### Network Requirements
- **Internet Access**: Required for TT API and Pricing Monkey
- **HTTPS**: All API communications use secure connections
- **Port 8053**: Default web interface port (configurable)
- **Outbound Connections**: TT API endpoints must be accessible

### Hardware Requirements
- **Memory**: Minimum 4GB RAM for Dash application
- **Storage**: 1GB free space for data files and logs
- **CPU**: Multi-core recommended for background monitoring
- **Display**: Multi-monitor setup typical for trading workstations

## Development Environment

### IDE & Tools
- **VS Code/PyCharm**: Recommended IDEs with Python support
- **Git**: Version control (repository structure suggests Git usage)
- **Command Line**: PowerShell for Windows batch operations
- **Browser DevTools**: For web interface debugging

### Testing Approach
- **Mock Data**: `USE_MOCK_DATA` flag for development
- **Environment Isolation**: SIM environment for safe testing
- **Manual Testing**: No automated test framework currently
- **Debug Logging**: Extensive console output for troubleshooting

### Package Management
- **pip**: Python package manager
- **requirements.txt**: Dependency specification
- **Virtual Environment**: Recommended for isolation
- **Package Structure**: Custom lib/ directory for reusable components

## Key Configuration

### Environment Variables
- **ENVIRONMENT**: SIM, UAT, or LIVE (set in config.py)
- **API Keys**: TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET
- **Application**: APP_NAME, COMPANY_NAME for TT API identification
- **Tokens**: TOKEN_FILE base name, AUTO_REFRESH settings

### Critical Constants
- **Price Conversion**: `BP_DECIMAL_PRICE_CHANGE = 0.0625` (1/16)
- **P&L Calculation**: `DOLLARS_PER_BP = 62.5` (basis point value)
- **Price Increment**: `PRICE_INCREMENT_DECIMAL = 1/64` (tick size)
- **Polling**: `DEFAULT_POLL_INTERVAL = 60` seconds for monitors

### File Paths
- **Data Directory**: `data/` (input and output subdirectories)
- **Library**: `lib/` (components, trading modules)
- **Output**: `data/output/ladder/` (CSV files, SQLite databases)
- **Logs**: `data/output/ladder/logs/` (monitoring logs)

## Tool Tips & Best Practices

### Development Workflow
1. **Start with SIM Environment**: Always develop against SIM API
2. **Use Mock Data**: Enable `USE_MOCK_DATA = True` for offline development
3. **Check Console Output**: All major operations log to console
4. **Test Price Conversions**: Verify bond format calculations with test cases
5. **Monitor Background Processes**: Use batch scripts to check system status

### API Integration
- **Token Management**: Let TTTokenManager handle authentication
- **Rate Limiting**: Implement delays between API calls
- **Error Handling**: Always check API response status
- **Request IDs**: Use proper format for audit trails
- **Environment Awareness**: Verify API endpoint matches environment

### Performance Optimization
- **Cache API Responses**: Store market enums and user data
- **Batch Operations**: Group related API calls
- **Lazy Loading**: Fetch data only when needed
- **Database Indexing**: Use appropriate indexes for queries
- **Memory Management**: Clean up large DataFrames after use

### Debugging Strategies
- **Console Logging**: All modules provide detailed logging
- **Mock Data Testing**: Use known good data for troubleshooting
- **API Response Inspection**: Log full API responses for analysis
- **State File Analysis**: Examine pickle files for background monitor state
- **Network Debugging**: Use browser DevTools for web interface issues

### Security Considerations
- **Credential Storage**: Never commit API keys to version control
- **Environment Separation**: Use different credentials for each environment
- **Token Security**: Protect token files with appropriate permissions
- **API Limits**: Respect TT API rate limits and quotas
- **Data Privacy**: Ensure trading data stays within secure boundaries

### Common Pitfalls
- **Price Format Confusion**: Always convert between decimal and TT bond format
- **Environment Mismatch**: Verify credentials match selected environment
- **Windows Path Issues**: Use `os.path.join()` for cross-platform compatibility
- **Token Expiry**: Monitor token refresh logs for authentication issues
- **Browser Automation**: Pricing Monkey timing may need adjustment for slow systems 