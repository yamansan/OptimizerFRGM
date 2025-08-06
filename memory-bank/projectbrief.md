# Project Brief

## Vision
Build a real-time trading ladder visualization system that integrates with Trading Technologies (TT) REST API to provide traders with live position monitoring, P&L projections, and risk analysis across price levels.

## Scope

### Core Features
- **Real-time Working Orders Display**: Live visualization of buy/sell orders at each price level
- **P&L Projections**: Calculate and display projected profit/loss at different price scenarios
- **Position Tracking**: Monitor accumulated positions including historical fills and working orders
- **Risk Analysis**: Calculate risk values and breakeven ratios for trading decisions
- **Spot Price Integration**: Fetch live spot prices via Pricing Monkey with manual refresh capability
- **Multi-environment Support**: SIM, UAT, and LIVE environment configurations

### Technical Scope
- **Web Interface**: Dash-based responsive UI with Bootstrap theming
- **API Integration**: TT REST API for orders, fills, and position data
- **Data Processing**: Bond price formatting, decimal conversions, LIFO P&L calculations
- **Background Monitoring**: Continuous fill monitoring and position tracking
- **Database Management**: SQLite for historical data storage and SOD (Start of Day) integration

### Out of Scope
- Order execution/placement functionality
- Real-time streaming (uses polling approach)
- Multi-asset support beyond ZN futures
- Mobile applications

## Quality Bars

### Performance
- **Response Time**: Web interface updates within 2 seconds of data refresh
- **API Reliability**: Handle TT API rate limits and implement retry logic
- **Data Accuracy**: Price conversions must be exact (no rounding errors in bond format)

### Reliability
- **Uptime**: Background monitoring processes should run continuously
- **Error Handling**: Graceful degradation when API is unavailable
- **Data Integrity**: Prevent duplicate fills and maintain consistent state

### Usability
- **Intuitive Display**: Color-coded ladder with clear buy/sell indication
- **Real-time Updates**: Manual refresh capability with loading indicators
- **Error Reporting**: Clear error messages for connection and data issues

### Security
- **Credential Management**: Secure API key storage and environment separation
- **Token Management**: Automatic token refresh before expiry
- **Environment Isolation**: Clear separation between SIM, UAT, and LIVE environments

## Success Criteria
- Traders can monitor live positions and P&L projections in real-time
- System accurately calculates risk metrics and breakeven points
- Integration with TT API provides reliable order and fill data
- Background monitoring maintains consistent position tracking
- Web interface provides intuitive ladder visualization with spot price context 