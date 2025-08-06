# Product Context

## Why This System Exists

### Trading Challenge
Professional traders using Trading Technologies platform need real-time visibility into their position risk and P&L projections across different price scenarios. Without this visibility, traders make decisions based on incomplete information about their risk exposure.

### Current Pain Points
- **Fragmented Information**: Order data, position data, and P&L calculations exist in separate systems
- **Manual Calculations**: Traders manually calculate risk scenarios and breakeven points
- **Delayed Updates**: Position information may not reflect the most current state
- **Complex Price Formats**: Bond prices use special TT format (e.g., "110'005") requiring conversion

### Business Value
- **Risk Management**: Real-time risk visibility prevents overexposure
- **Informed Decision Making**: P&L projections help traders evaluate scenarios
- **Efficiency**: Automated calculations reduce manual work and errors
- **Compliance**: Accurate position tracking supports regulatory reporting

## Target Users

### Primary User: Professional Traders
- **Role**: Execute trades on behalf of institutions
- **Needs**: Real-time position monitoring, risk assessment, P&L tracking
- **Environment**: High-pressure, fast-moving trading floors
- **Technical Level**: Familiar with trading platforms, not necessarily technical

### Secondary User: Risk Managers
- **Role**: Monitor and control trading risk exposure
- **Needs**: Aggregate position views, risk metrics, historical analysis
- **Environment**: Oversight and compliance focused
- **Technical Level**: Analytical, comfortable with data tools

## UX Goals

### Primary Goals
1. **Immediate Clarity**: Ladder view provides instant understanding of position and risk
2. **Real-time Awareness**: Clear indication of current vs. projected states
3. **Error Prevention**: Visual cues prevent misunderstanding of position or risk
4. **Rapid Decision Making**: Information presented to support quick trading decisions

### Design Principles
- **Density Over Simplicity**: Traders need comprehensive information in limited screen space
- **Color Coding**: Visual indicators for buy/sell, profit/loss, and risk levels
- **Hierarchy**: Most critical information (current position, spot price) prominently displayed
- **Responsiveness**: System feedback for all user actions (refresh, data loading)

### User Journey
1. **System Access**: Trader opens web interface on trading workstation
2. **Data Loading**: System fetches live orders and position data from TT API
3. **Spot Price Refresh**: Manual refresh gets current market price from Pricing Monkey
4. **Ladder Analysis**: Trader reviews position and P&L projections at each price level
5. **Risk Assessment**: Trader evaluates risk metrics and breakeven scenarios
6. **Decision Making**: Trader uses information to inform trading strategy

## Context of Use

### Environment
- **Windows Trading Workstations**: Primary deployment environment
- **Multiple Monitors**: Ladder view used alongside other trading applications
- **Network Connectivity**: Reliable internet required for API access
- **Time Sensitivity**: Market hours operation with real-time requirements

### Integration Points
- **TT Platform**: Source of order and fill data
- **Pricing Monkey**: External price feed for spot price information
- **Actant SOD**: Start of day position data for baseline calculations
- **Internal Systems**: Position monitoring and P&L tracking workflows

### Constraints
- **Market Hours**: Primary usage during active trading sessions
- **API Limits**: TT API rate limiting affects refresh frequency
- **Windows Dependency**: Pricing Monkey integration requires Windows OS
- **Manual Refresh**: Spot price updates require user interaction 