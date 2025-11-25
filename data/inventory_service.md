# Inventory Service

InventoryService manages product catalog and stock levels across all warehouses.

## Overview

InventoryService provides:
- Product catalog management
- Real-time stock tracking
- Warehouse management
- Stock reservation system
- Inventory forecasting

## Features

### Product Management
- Product CRUD operations
- SKU management
- Product categorization
- Variant management (size, color, etc.)
- Product attributes and metadata

### Stock Management
- Real-time stock levels
- Multi-warehouse support
- Stock reservation during checkout
- Automatic reorder alerts
- Stock adjustment tracking

### Warehouse Operations
- Multiple warehouse locations
- Stock transfer between warehouses
- Receiving and putaway
- Pick and pack operations

## Architecture

### Components

- **CatalogManager**: Product catalog operations
- **StockTracker**: Real-time inventory tracking
- **ReservationEngine**: Stock reservation for pending orders
- **ForecastingModule**: Inventory prediction and alerts

## Dependencies

InventoryService depends on:
- **DatabaseService** - Product and stock data
- **CacheService** - Real-time stock level caching

## Used By

Multiple services depend on InventoryService:
1. **ProjectAlpha** - Product catalog display, stock checks
2. **ProjectBeta** - Inventory management interface
3. **CheckoutService** - Stock validation during checkout
4. **OrderService** - Stock deduction on order completion
5. **SearchService** - Product search with availability

## Stock Reservation

When a customer adds items to cart:
1. InventoryService reserves stock temporarily
2. Reservation expires after 15 minutes
3. Stock is deducted upon order completion
4. Failed orders release reserved stock

## API Endpoints

- GET /products - List products
- GET /products/:id - Get product details
- POST /products - Create product (admin only)
- PUT /products/:id - Update product (admin only)
- GET /stock/:sku - Check stock level
- POST /stock/reserve - Reserve stock
- POST /stock/release - Release reservation
- POST /stock/adjust - Adjust stock level (admin only)

## Performance

- Stock level caching with 5-second TTL
- Optimistic locking for concurrent stock updates
- Read replicas for product catalog queries
- Event-driven stock updates

## Integration Notes

Services should:
- Check stock availability before order processing
- Reserve stock during checkout
- Release reservations on timeout or cancellation
- Subscribe to stock update events for real-time sync
