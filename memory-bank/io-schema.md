# I/O Schema

## Environment Variables

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| TT_API_KEY | EnvVar | str | UUID format | "0549df41-77a8-6799-1a7d-b2f4656a7fd4" |
| TT_API_SECRET | EnvVar | str | UUID format | "12d0bbbb-9f1b-caff-e9d3-19212d8426c2" |
| TT_SIM_API_KEY | EnvVar | str | UUID format | "2b429b91-8d96-8aed-4338-3d3d5b73887a" |
| TT_SIM_API_SECRET | EnvVar | str | UUID format | "8d9f572e-292e-c7a0-c39d-383fbfb56b8b" |
| APP_NAME | EnvVar | str | alphanumeric | "UIKitXTT" |
| COMPANY_NAME | EnvVar | str | text | "Fibonacci Research" |
| ENVIRONMENT | EnvVar | str | "SIM", "UAT", "LIVE" | "SIM" |
| TOKEN_FILE | EnvVar | str | filename | "tt_token.json" |
| AUTO_REFRESH | EnvVar | bool | True, False | True |
| REFRESH_BUFFER_SECONDS | EnvVar | int | > 0 | 600 |

## Core Constants

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| BP_DECIMAL_PRICE_CHANGE | Constant | float | 0.0625 | P&L calculation basis |
| DOLLARS_PER_BP | Constant | float | 62.5 | Dollar value per basis point |
| PRICE_INCREMENT_DECIMAL | Constant | float | 1/64 (0.015625) | ZN futures tick size |
| TT_API_BASE_URL | Constant | str | URL | "https://ttrestapi.trade.tt" |
| DEFAULT_POLL_INTERVAL | Constant | int | seconds > 0 | 60 |
| DEFAULT_MAX_RETRIES | Constant | int | > 0 | 5 |
| PM_URL | Constant | str | URL | "https://pricingmonkey.com/b/e9172aaf-..." |
| PM_WAIT_FOR_BROWSER_OPEN | Constant | float | seconds > 0 | 3.0 |
| PM_WAIT_BETWEEN_ACTIONS | Constant | float | seconds > 0 | 0.5 |
| PM_WAIT_FOR_COPY | Constant | float | seconds > 0 | 1.0 |
| PM_KEY_PRESS_PAUSE | Constant | float | seconds > 0 | 0.1 |

## File Paths

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| MOCK_DATA_FILE | Constant | str | file path | "data/input/ladder/my_working_orders_response.json" |
| ACTANT_CSV_FILE | Constant | str | file path | "data/input/sod/SampleSOD.csv" |
| ACTANT_DB_FILEPATH | Constant | str | file path | "data/output/ladder/actant_data.db" |
| ACTANT_TABLE_NAME | Constant | str | table name | "actant_sod_fills" |
| OUTPUT_DIR | Constant | str | directory path | "data/output/ladder" |
| DATATABLE_ID | Constant | str | HTML ID | "scenario-ladder-table" |
| MESSAGE_DIV_ID | Constant | str | HTML ID | "scenario-ladder-message" |
| STORE_ID | Constant | str | HTML ID | "scenario-ladder-store" |

## API Inputs

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| token | Input | str | Bearer token | "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." |
| request_id | Input | str | GUID format | "UIKitXTT-FibonacciResearch--uuid4" |
| instrumentId | Input | str | numeric ID | "1375333834396392980" |
| marketId | Input | str | numeric ID | "1" |
| userId | Input | str | numeric ID | "12345" |
| accountId | Input | str | numeric ID | "67890" |
| timeStamp | Input | str | ISO datetime | "2025-07-03T19:27:24.326Z" |
| side | Input | int | 1 (buy), 2 (sell) | 1 |
| quantity | Input | float | > 0 | 10.0 |
| price | Input | float | > 0 | 111.796875 |

## API Outputs

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| working_orders | Output | list[dict] | order objects | [{instrumentId: "123", side: 1, qty: 10}] |
| filled_orders | Output | list[dict] | fill objects | [{timeStamp: "2025-07-03T...", price: 111.5}] |
| positions | Output | list[dict] | position objects | [{buyFillQty: 100, sellFillQty: 50, netPosition: 50}] |
| market_enums | Output | dict | enum mappings | {"markets": {"1": "CME", "2": "CBOT"}} |
| user_info | Output | dict | user data | {"alias": "Eric", "id": "12345"} |
| instrument_info | Output | dict | instrument data | {"alias": "ZN Sep25", "marketId": "1"} |
| token_response | Output | dict | token data | {"access_token": "...", "token_type": "Bearer"} |

## Data Structures

### TT Bond Price Format
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| tt_bond_price | Internal | str | "XXX'YYZ" format | "110'005" (110 + 1/64) |
| decimal_price | Internal | float | > 0 | 110.015625 |
| pm_price_format | Internal | str | "XXX-YY.ZZ" format | "110-08.5" |

### Position Stack (LIFO)
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| position_stack | Internal | list[tuple] | [(qty, price)] | [(10.0, 111.5), (-5.0, 111.75)] |
| realized_pnl | Internal | float | any | 312.5 |
| unrealized_pnl | Internal | float | any | -125.0 |

### Dash Component IDs
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| component_id | Internal | str | alphanumeric + dash | "scenario-ladder-table" |
| callback_input | Internal | str | "component_id.property" | "refresh-button.n_clicks" |
| callback_output | Internal | str | "component_id.property" | "table.data" |

## CSV File Formats

### Continuous Fills CSV
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| Date | Input | str | YYYY-MM-DD | "2025-07-03" |
| Time | Input | str | HH:MM:SS.fff | "19:27:24.326" |
| Exchange | Input | str | exchange code | "CME" |
| Contract | Input | str | contract name | "ZN Sep25" |
| Side | Input | int | 1, 2 | 1 |
| Quantity | Input | float | > 0 | 10.0 |
| Price | Input | float | > 0 | 111.796875 |
| CurrentUser | Input | str | username | "Eric" |
| OrderId | Input | str | order ID | "12345678" |

### SOD CSV (Actant)
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| ASSET | Input | str | asset code | "ZN" |
| PRODUCT_CODE | Input | str | product type | "FUTURE" |
| PRICE_TODAY | Input | str | TT bond format | "110'005" |
| QUANTITY | Input | float | any | 100.0 |
| LONG_SHORT | Input | str | "L", "S" | "L" |

### LIFO Streaming CSV
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| Timestamp | Output | str | ISO datetime | "2025-07-03 19:27:24.326" |
| TradeQty | Output | float | any | -10.0 |
| TradePx | Output | float | > 0 | 111.796875 |
| RealisedPnL | Output | float | any | 312.5 |
| StackSize | Output | int | >= 0 | 3 |

### Net Position Streaming CSV
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| SignedQuantity | Output | float | any | -10.0 |
| NetPosition | Output | float | any | 125.0 |
| [all original columns] | Output | various | from continuous fills | Date, Time, Price, etc. |

### Trade State Events CSV
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| Timestamp | Output | str | timestamp | "1751585242691599374" |
| Date | Output | str | YYYY-MM-DD | "2025-07-03" |
| Time | Output | str | HH:MM:SS.fff | "19:27:22.691" |
| Price | Output | float | > 0 | 111.21875 |
| TradeState | Output | int | 0 (start), 1 (end) | 0 |
| NetPosition | Output | float | any | -1745.0 |
| PreviousNetPosition | Output | float | any | -1018.0 |
| Description | Output | str | event description | "Trade started: 0 -> 10.0" |

## Database Schema

### Actant SOD Table
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| ASSET | Input | TEXT | asset codes | "ZN" |
| PRODUCT_CODE | Input | TEXT | product types | "FUTURE" |
| PRICE_TODAY | Input | TEXT | TT bond format | "110'005" |
| QUANTITY | Input | REAL | any | 100.0 |
| LONG_SHORT | Input | TEXT | "L", "S" | "L" |

## State Files

### Token Files
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| access_token | Internal | str | JWT token | "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." |
| token_type | Internal | str | "Bearer" | "Bearer" |
| expires_at | Internal | str | ISO datetime | "2025-07-03T20:27:24.326Z" |

### LIFO State (Pickle)
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| position_stack | Internal | list[tuple] | [(qty, price)] | [(10.0, 111.5), (-5.0, 111.75)] |
| last_processed_row | Internal | int | >= 0 | 42 |
| processed_transactions | Internal | set[str] | transaction IDs | {"2025-07-03_1_10.0_111.5_12345"} |

### Net Position State (Pickle)
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| last_processed_row | Internal | int | >= 0 | 87 |
| current_net_position | Internal | float | any | 125.0 |

### Trade State Monitor State (Pickle)
| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| last_processed_row | Internal | int | >= 0 | 87 |

## Error Codes

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| api_error_status | Internal | int | HTTP status codes | 401, 403, 429, 500 |
| error_message | Internal | str | error description | "Token expired" |
| retry_count | Internal | int | 0 to max_retries | 3 |
| backoff_seconds | Internal | float | > 0 | 2.5 |

## Configuration Flags

| Name | Kind | Type | Allowed Values | Example Usage |
|------|------|------|----------------|---------------|
| USE_MOCK_DATA | Internal | bool | True, False | False |
| DEBUG_MODE | Internal | bool | True, False | True |
| LOG_TO_FILE | Internal | bool | True, False | True |
| LOG_TO_CONSOLE | Internal | bool | True, False | True | 