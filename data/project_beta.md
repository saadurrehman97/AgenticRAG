# Project Beta

ProjectBeta is an internal administration dashboard for managing our e-commerce operations.

## Overview

ProjectBeta provides administrative tools for:
- User management and moderation
- Order management and fulfillment
- Inventory management
- Analytics and reporting
- System configuration

## Technology Stack

- Frontend: Vue.js + TypeScript
- Backend: Python + FastAPI
- Database: PostgreSQL
- Real-time updates: WebSockets

## Service Dependencies

ProjectBeta uses several backend services:

### Authentication & Authorization
- **AuthService** - Admin authentication with elevated permissions
- Requires ADMIN role for access

### Data Management
- **DatabaseService** - Direct database access for admin operations
- **InventoryService** - Inventory management
- **OrderService** - Order management

### Analytics
- **AnalyticsModule** - Business intelligence and reporting
- **AuditService** - Admin action logging

## Key Features

### User Administration
- View and manage user accounts
- Reset user passwords
- Ban/suspend users
- View user activity logs

### Order Management
- View all orders
- Process refunds
- Update order status
- Generate shipping labels

### Inventory Control
- Add/update products
- Manage stock levels
- Set pricing and discounts
- Product categorization

### Reporting
- Sales reports
- User analytics
- Inventory reports
- Performance metrics

## Security

ProjectBeta has enhanced security requirements:
- Multi-factor authentication via AuthService
- IP whitelisting
- Comprehensive audit logging
- Role-based access control (RBAC)
- Session timeout: 30 minutes

## Access Control

Only users with ADMIN role can access ProjectBeta. The AuthService verifies:
- Valid authentication token
- ADMIN role assignment
- Active session
- IP whitelist (optional)
