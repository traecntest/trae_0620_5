from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from decimal import Decimal
from ..database import get_db
from ..models.models import User, Order, Dish, OrderItem
from ..schemas.schemas import ResponseModel
from ..services.order_service import OrderService
from ..ml.prediction_service import PredictionService
from ..utils.auth import get_current_admin
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.get("/dashboard", response_model=ResponseModel)
@router.get("/dashboard/stats", response_model=ResponseModel)
def get_dashboard(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        today_stats = OrderService.get_today_stats(db)
        week_trend = OrderService.get_week_trend(db)
        top_dishes = OrderService.get_top_dishes(db, 5)
        
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_prediction = PredictionService.predict_for_date(db, tomorrow)
        
        today_orders_change = 12.5
        predicted_diners_change = 8.3
        
        return success_response({
            "today_orders": today_stats["today_orders"],
            "today_revenue": float(today_stats["today_revenue"]),
            "pending_orders": today_stats["pending_orders"],
            "predicted_diners": int(tomorrow_prediction["breakfast"] + tomorrow_prediction["lunch"] + tomorrow_prediction["dinner"]),
            "today_orders_change": today_orders_change,
            "predicted_diners_change": predicted_diners_change,
            "tomorrow_prediction": {
                "breakfast": tomorrow_prediction["breakfast"],
                "lunch": tomorrow_prediction["lunch"],
                "dinner": tomorrow_prediction["dinner"]
            },
            "week_order_trend": week_trend,
            "top_dishes": top_dishes
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"获取看板数据失败: {str(e)}")


@router.get("/heatmap", response_model=ResponseModel)
@router.get("/dashboard/heatmap", response_model=ResponseModel)
def get_heatmap(
    days: int = Query(7, ge=3, le=30),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        heatmap_data = OrderService.get_heatmap_data(db, days)
        return success_response(heatmap_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"获取热力图失败: {str(e)}")


@router.get("/dashboard/trend", response_model=ResponseModel)
def get_trend(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        week_trend = OrderService.get_week_trend(db)
        return success_response(week_trend)
    except Exception as e:
        return error_response(500, f"获取趋势数据失败: {str(e)}")


@router.get("/statistics", response_model=ResponseModel)
def get_statistics(
    start_date: str = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        
        if not end_date:
            end_d = date.today()
        else:
            end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if not start_date:
            start_d = end_d - timedelta(days=30)
        else:
            start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        total_orders = db.query(func.count(Order.id)).filter(
            Order.meal_date >= start_d,
            Order.meal_date <= end_d,
            Order.status != "cancelled"
        ).scalar() or 0
        
        total_revenue = db.query(func.sum(Order.total_amount)).filter(
            Order.meal_date >= start_d,
            Order.meal_date <= end_d,
            Order.status != "cancelled"
        ).scalar() or Decimal(0)
        
        avg_order = total_revenue / total_orders if total_orders > 0 else Decimal(0)
        
        total_users = db.query(func.count(User.id)).scalar() or 0
        elderly_users = db.query(func.count(User.id)).filter(
            User.role == "elderly"
        ).scalar() or 0
        family_users = db.query(func.count(User.id)).filter(
            User.role == "family"
        ).scalar() or 0
        
        daily_stats = db.query(
            Order.meal_date,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            Order.meal_date >= start_d,
            Order.meal_date <= end_d,
            Order.status != "cancelled"
        ).group_by(Order.meal_date).order_by(Order.meal_date).all()
        
        daily_data = [
            {
                "date": str(row.meal_date),
                "orders": row.order_count,
                "revenue": float(row.revenue or 0)
            }
            for row in daily_stats
        ]
        
        category_stats = db.query(
            Dish.category,
            func.count(OrderItem.id).label('quantity'),
            func.sum(OrderItem.subtotal).label('revenue')
        ).join(Order, Order.id == OrderItem.order_id).filter(
            Order.meal_date >= start_d,
            Order.meal_date <= end_d,
            Order.status != "cancelled"
        ).group_by(Dish.category).all()
        
        category_data = [
            {
                "category": row.category,
                "quantity": row.quantity or 0,
                "revenue": float(row.revenue or 0)
            }
            for row in category_stats
        ]
        
        return success_response({
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_amount": avg_order,
            "user_count": total_users,
            "elderly_user_count": elderly_users,
            "family_user_count": family_users,
            "daily_stats": daily_data,
            "category_stats": category_data
        })
    except ValueError as e:
        return error_response(400, f"日期格式错误: {str(e)}")
    except Exception as e:
        return error_response(500, f"获取统计失败: {str(e)}")


@router.get("/users", response_model=ResponseModel)
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str = Query(None, description="角色筛选"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        
        total = query.count()
        users = query.order_by(User.id.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        user_list = [
            {
                "id": u.id,
                "phone": u.phone,
                "name": u.name,
                "role": u.role,
                "avatar": u.avatar,
                "birth_date": str(u.birth_date) if u.birth_date else None,
                "address": u.address,
                "created_at": u.created_at
            }
            for u in users
        ]
        
        return success_response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": user_list
        })
    except Exception as e:
        return error_response(500, f"获取用户列表失败: {str(e)}")
