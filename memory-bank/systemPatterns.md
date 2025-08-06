# System Patterns

## Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Background     │    │   Data Layer    │
│   (Dash App)    │    │  Monitors       │    │   (SQLite)      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ - Ladder View   │    │ - Fill Monitor  │    │ - Position Data │
│ - P&L Display   │    │ - Position Mon. │    │ - SOD Fills     │
│ - Risk Metrics  │    │ - LIFO Monitor  │    │ - Audit Trail   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   TT API Layer  │
                    │                 │
                    │ - Token Manager │
                    │ - API Utils     │
                    │ - Config        │
                    └─────────────────┘
```

### Component Architecture
- **Separation of Concerns**: UI, business logic, and data access clearly separated
- **Modular Design**: Components, trading logic, and API integration in separate packages
- **Plugin Architecture**: Theme system allows customization of UI appearance

## Design Patterns

### 1. Token Manager Pattern
**Purpose**: Centralized authentication and token lifecycle management
**Implementation**:
- `TTTokenManager` class handles token acquisition, refresh, and storage
- Environment-specific token files (`tt_token_sim.json`, `tt_token_uat.json`)
- Automatic refresh with configurable buffer time (10 minutes default)
- Thread-safe token access for concurrent operations

### 2. Component Factory Pattern
**Purpose**: Consistent UI component creation with theme support
**Implementation**:
- `BaseComponent` abstract class defines common interface
- All UI components inherit from base class
- Theme injection through constructor
- Standardized `render()` method for Dash component generation

### 3. Data Processing Pipeline
**Purpose**: Consistent data transformation and formatting
**Implementation**:
- Price format conversion (decimal ↔ TT bond format)
- P&L calculation engine with configurable constants
- Data validation and error handling at each stage
- Caching for performance optimization

### 4. Monitor Pattern
**Purpose**: Background data collection and state management
**Implementation**:
- `FillMonitor` class for continuous API polling
- State persistence with pickle files for recovery
- Signal handling for graceful shutdown
- Configurable polling intervals and retry logic

### 5. Configuration Strategy Pattern
**Purpose**: Environment-aware configuration management
**Implementation**:
- Single config file with environment-specific sections
- Runtime environment selection (SIM, UAT, LIVE)
- API key management with environment isolation
- Feature flags for mock data and debugging

## Data Flow Patterns

### 1. Request-Response Flow
```
User Action → Dash Callback → TT API Call → Data Processing → UI Update
```
- User triggers refresh → `load_and_display_orders()` callback
- Token manager provides authentication → API request to TT
- Raw data processed (price conversion, P&L calculation)
- Formatted data returned to Dash DataTable component

### 2. Background Monitoring Flow
```
Scheduler → API Poll → Data Processing → File/DB Storage → State Update
```
- Continuous monitoring processes run independently
- Fill monitor polls TT API for new trades
- LIFO processor calculates realized P&L
- Results stored in CSV files and database
- State persisted for system recovery

### 3. Price Data Flow
```
Pricing Monkey → Browser Automation → Clipboard → Price Parser → Decimal Conversion
```
- Manual spot price refresh triggers browser automation
- Price copied from Pricing Monkey interface
- Parsed from "110-08.5" format to decimal
- Converted to TT bond format for display

## Error Handling Patterns

### 1. Graceful Degradation
- API failures show cached data with error indicators
- Missing data fields display as "N/A" rather than breaking UI
- Network issues trigger retry logic with exponential backoff
- Mock data mode for development and testing

### 2. State Recovery
- Background monitors persist state to recover from interruptions
- Token manager handles expired tokens automatically
- Database operations use transactions for consistency
- Audit trail maintains record of all operations

### 3. Validation Layers
- Input validation at API boundaries
- Data type checking before processing
- Range validation for price and quantity values
- Schema validation for configuration files

## Performance Patterns

### 1. Caching Strategy
- Market enum data cached to reduce API calls
- User information cached with TTL
- Instrument data cached for session duration
- Token reuse until expiry

### 2. Lazy Loading
- UI components rendered only when needed
- Data fetched on-demand for user actions
- Background processes start only when required
- Database connections opened per operation

### 3. Asynchronous Processing
- Background monitors run independently
- API calls don't block UI updates
- File I/O operations use buffered writes
- State persistence happens asynchronously

## Security Patterns

### 1. Credential Management
- API keys stored in configuration files (not hardcoded)
- Environment-specific credential separation
- Token files stored locally with restricted access
- No credentials logged or exposed in UI

### 2. API Security
- All API calls use HTTPS
- Bearer token authentication
- Request IDs for audit trails
- Rate limiting compliance

### 3. Data Protection
- Sensitive data not cached unnecessarily
- Log files exclude authentication details
- Database files use local file system
- No user data transmitted outside system boundaries 