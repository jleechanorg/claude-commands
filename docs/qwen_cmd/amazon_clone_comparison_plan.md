# Amazon.com Clone Comparison Test Plan

**Objective**: Comprehensive comparison of /qwen vs Claude Sonnet for full-stack e-commerce development

## 📋 Test Overview

This ambitious test will evaluate both systems' capabilities across:
- **Architectural design** (complex system thinking)
- **Code generation speed** (volume and velocity)  
- **Code quality** (maintainability, security, performance)
- **Real-world complexity** (e-commerce features, integrations)

## 🎯 Test Specifications

### Core Components
1. **Frontend**: React/Next.js with TypeScript
2. **Backend**: Node.js/Express with REST APIs  
3. **Database**: PostgreSQL with proper schemas
4. **Features**: Product catalog, user auth, shopping cart, checkout, reviews

### Key Features to Implement
- Product catalog with search and filtering
- User authentication and profiles
- Shopping cart functionality
- Order processing and checkout
- Product reviews and ratings
- Admin dashboard
- Payment integration (mock)
- Responsive design

## 🚀 Execution Plan

### Phase 1: Architectural Specification (Claude - 15 minutes)
Create detailed technical specifications for both systems:

**Database Schema Requirements**:
- Users table (id, email, password_hash, profile_data)
- Products table (id, name, description, price, category, inventory)
- Categories table (id, name, parent_category)
- Orders table (id, user_id, status, total, shipping_address)
- Order_items table (order_id, product_id, quantity, price)
- Reviews table (id, product_id, user_id, rating, comment)
- Cart_items table (user_id, product_id, quantity)

**API Endpoint Specifications**:
```
Authentication:
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout

Products:
GET /api/products
GET /api/products/:id
GET /api/products/search?q=query&category=cat
GET /api/categories

Cart:
GET /api/cart
POST /api/cart/items
PUT /api/cart/items/:id
DELETE /api/cart/items/:id

Orders:
GET /api/orders
POST /api/orders
GET /api/orders/:id

Reviews:
GET /api/products/:id/reviews
POST /api/products/:id/reviews
```

**Frontend Component Hierarchy**:
```
App
├── Header
│   ├── SearchBar
│   ├── UserMenu
│   └── CartIcon
├── ProductCatalog
│   ├── CategoryFilter
│   ├── ProductGrid
│   └── ProductCard
├── ProductDetail
│   ├── ProductImages
│   ├── ProductInfo
│   ├── AddToCart
│   └── ReviewsList
├── ShoppingCart
│   ├── CartItems
│   └── CheckoutButton
├── Checkout
│   ├── ShippingForm
│   ├── PaymentForm
│   └── OrderSummary
└── UserDashboard
    ├── OrderHistory
    └── ProfileSettings
```

### Phase 2: Parallel Generation (Timed Comparison)

**Agent 1: /qwen Amazon Clone**
- Generate complete full-stack application
- Timer: Start to working prototype
- Focus: Speed and code volume

**Agent 2: Claude Sonnet Amazon Clone**  
- Generate identical specification implementation
- Timer: Start to working prototype  
- Focus: Direct comparison baseline

### Phase 3: Evaluation & Integration (Claude - 30 minutes)

**Comparison Metrics**:
- **Generation Time**: Total time to working code
- **Code Quality**: Architecture, security, maintainability  
- **Completeness**: Feature coverage vs specification
- **Integration**: How well components work together
- **Real-world Viability**: Production readiness assessment

## 📊 Expected Timeline
- **Phase 1** (Specs): 15 minutes
- **Phase 2** (Parallel Generation): 45-90 minutes  
- **Phase 3** (Evaluation): 30 minutes
- **Total**: ~2-2.5 hours for comprehensive comparison

## 🎯 Success Criteria
- Both systems generate working Amazon clone prototypes
- Fair timing comparison with identical specifications
- Quality assessment across multiple dimensions
- Functional features that demonstrate e-commerce capabilities

## ⚡ Performance Hypothesis
Based on previous testing: /qwen should generate code 1.88x faster than Sonnet, but this will test at much larger scale and complexity.

## 📝 Results Documentation
Results will be documented in:
- `amazon_clone_qwen_results.md` - /qwen implementation and metrics
- `amazon_clone_sonnet_results.md` - Claude Sonnet implementation and metrics  
- `amazon_clone_comparison_analysis.md` - Side-by-side analysis and conclusions

## 🚨 Test Constraints
- Must use identical specifications for both implementations
- Time measurement starts with first generation command
- Both implementations must be functional, not just compilable
- Focus on core e-commerce functionality over advanced features