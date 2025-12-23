"""
Dashboard Router
Provides analytics and statistics endpoints for the frontend dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app import models
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────
# RESPONSE MODELS
# ──────────────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_sales: float
    total_orders: int
    total_products: int
    low_stock_items: int
    
    class Config:
        # Allow response to use camelCase in JSON
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "totalSales": 1250.50,
                "totalOrders": 45,
                "totalProducts": 120,
                "lowStockItems": 5
            }
        }


class RevenueDataPoint(BaseModel):
    date: str
    revenue: float


class RevenueResponse(BaseModel):
    data: List[RevenueDataPoint]


class TopProduct(BaseModel):
    product_name: str
    quantity_sold: int
    revenue: float


class TopProductsResponse(BaseModel):
    products: List[TopProduct]


class RecentOrder(BaseModel):
    order_id: int
    total_amount: float
    payment_method: str
    created_at: str
    items_count: int


class RecentOrdersResponse(BaseModel):
    orders: List[RecentOrder]


# ──────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get overall dashboard statistics:
    - Total sales revenue
    - Total number of orders
    - Total products in inventory
    - Number of low stock items
    """
    # Calculate total sales (sum of all orders)
    total_sales = db.query(func.sum(models.Order.total_amount)).scalar() or 0.0
    
    # Count total orders
    total_orders = db.query(models.Order).count()
    
    # Count total products
    total_products = db.query(models.Product).count()
    
    # Count low stock items (stock_quantity < 10)
    low_stock_items = db.query(models.Product).filter(
        models.Product.stock_quantity < 10
    ).count()
    
    return StatsResponse(
        total_sales=round(total_sales, 2),
        total_orders=total_orders,
        total_products=total_products,
        low_stock_items=low_stock_items
    )


@router.get("/revenue", response_model=RevenueResponse)
def get_revenue_data(days: int = 7, db: Session = Depends(get_db)):
    """
    Get revenue data over the last N days (default 7).
    Returns daily revenue for chart visualization.
    
    Query params:
    - days: Number of days to look back (default: 7)
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query orders within date range
    orders = db.query(
        func.date(models.Order.created_at).label('date'),
        func.sum(models.Order.total_amount).label('revenue')
    ).filter(
        models.Order.created_at >= start_date,
        models.Order.created_at <= end_date
    ).group_by(
        func.date(models.Order.created_at)
    ).order_by('date').all()
    
    # Format response
    data_points = [
        RevenueDataPoint(
            date=str(order.date),
            revenue=round(order.revenue, 2)
        )
        for order in orders
    ]
    
    # Fill in missing dates with 0 revenue
    date_map = {dp.date: dp.revenue for dp in data_points}
    complete_data = []
    
    for i in range(days):
        check_date = (start_date + timedelta(days=i)).date()
        complete_data.append(
            RevenueDataPoint(
                date=str(check_date),
                revenue=date_map.get(str(check_date), 0.0)
            )
        )
    
    return RevenueResponse(data=complete_data)


@router.get("/top-products", response_model=TopProductsResponse)
def get_top_products(limit: int = 5, db: Session = Depends(get_db)):
    """
    Get top-selling products by quantity sold.
    
    Query params:
    - limit: Number of top products to return (default: 5)
    """
    # Query top products from order items
    top_products = db.query(
        models.OrderItem.product_name,
        func.sum(models.OrderItem.quantity).label('quantity_sold'),
        func.sum(models.OrderItem.quantity * models.OrderItem.unit_price).label('revenue')
    ).filter(
        models.OrderItem.item_type == "RETAIL"  # Only retail products
    ).group_by(
        models.OrderItem.product_name
    ).order_by(
        desc('quantity_sold')
    ).limit(limit).all()
    
    # Format response
    products = [
        TopProduct(
            product_name=product.product_name,
            quantity_sold=product.quantity_sold,
            revenue=round(product.revenue, 2)
        )
        for product in top_products
    ]
    
    return TopProductsResponse(products=products)


@router.get("/recent-orders", response_model=RecentOrdersResponse)
def get_recent_orders(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get most recent orders.
    
    Query params:
    - limit: Number of orders to return (default: 10)
    """
    # Query recent orders
    orders = db.query(models.Order).order_by(
        desc(models.Order.created_at)
    ).limit(limit).all()
    
    # Format response
    recent_orders = []
    for order in orders:
        # Count items in this order
        items_count = db.query(models.OrderItem).filter(
            models.OrderItem.order_id == order.id
        ).count()
        
        recent_orders.append(
            RecentOrder(
                order_id=order.id,
                total_amount=round(order.total_amount, 2),
                payment_method=order.payment_method,
                created_at=order.created_at.isoformat(),
                items_count=items_count
            )
        )
    
    return RecentOrdersResponse(orders=recent_orders)
