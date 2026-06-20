from typing import Optional, Tuple, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from ..models.models import Order, OrderItem, Dish, User
from ..utils.helpers import generate_order_no, generate_pickup_code, get_pickup_time


class OrderService:
    @staticmethod
    def create_order(
        db: Session,
        user_id: int,
        meal_period: str,
        meal_date_str: str,
        items: list,
        remark: Optional[str] = None,
        elderly_user_id: Optional[int] = None,
        dining_type: str = "dinein"
    ) -> dict:
        meal_date = datetime.strptime(meal_date_str, "%Y-%m-%d").date()
        order_no = generate_order_no()
        pickup_code = generate_pickup_code()
        
        total_amount = Decimal(0)
        order_items = []
        
        for item in items:
            dish = db.query(Dish).filter(Dish.id == item["dish_id"]).first()
            if not dish:
                raise ValueError(f"菜品ID {item['dish_id']} 不存在")
            
            unit_price = dish.price
            quantity = item["quantity"]
            subtotal = unit_price * quantity
            total_amount += subtotal
            
            order_items.append(OrderItem(
                dish_id=item["dish_id"],
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            ))
        
        order = Order(
            order_no=order_no,
            user_id=user_id,
            elderly_user_id=elderly_user_id,
            total_amount=total_amount,
            meal_period=meal_period,
            meal_date=meal_date,
            dining_type=dining_type,
            pickup_code=pickup_code,
            status="pending",
            remark=remark,
            items=order_items
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return {
            "order_id": order_no,
            "pickup_code": pickup_code,
            "total_amount": total_amount,
            "meal_period": meal_period,
            "meal_date": meal_date_str,
            "status": "pending",
            "pickup_time": get_pickup_time(meal_period),
            "created_at": order.created_at
        }

    @staticmethod
    def get_order_list(
        db: Session,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        meal_date: Optional[str] = None,
        is_admin: bool = False
    ) -> Tuple[List[dict], int]:
        query = db.query(Order)
        
        if not is_admin and user_id:
            query = query.filter(
                (Order.user_id == user_id) | (Order.elderly_user_id == user_id)
            )
        
        if status:
            query = query.filter(Order.status == status)
        
        if meal_date:
            query = query.filter(Order.meal_date == meal_date)
        
        total = query.count()
        orders = query.order_by(Order.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        order_list = []
        for order in orders:
            elderly_name = None
            if order.elderly_user_id:
                elderly = db.query(User).filter(User.id == order.elderly_user_id).first()
                if elderly:
                    elderly_name = elderly.name
            
            items = []
            for item in order.items:
                dish = db.query(Dish).filter(Dish.id == item.dish_id).first()
                items.append({
                    "id": item.id,
                    "dish_id": item.dish_id,
                    "dish_name": dish.name if dish else None,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal
                })
            
            order_list.append({
                "id": order.id,
                "order_no": order.order_no,
                "user_id": order.user_id,
                "elderly_user_id": order.elderly_user_id,
                "elderly_name": elderly_name,
                "total_amount": order.total_amount,
                "meal_period": order.meal_period,
                "meal_date": order.meal_date,
                "dining_type": order.dining_type,
                "pickup_code": order.pickup_code,
                "status": order.status,
                "remark": order.remark,
                "items": items,
                "created_at": order.created_at
            })
        
        return order_list, total

    @staticmethod
    def get_order_detail(db: Session, order_id: int, user_id: int, is_admin: bool = False) -> Optional[dict]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        
        if not is_admin and order.user_id != user_id and order.elderly_user_id != user_id:
            return None
        
        elderly_name = None
        if order.elderly_user_id:
            elderly = db.query(User).filter(User.id == order.elderly_user_id).first()
            if elderly:
                elderly_name = elderly.name
        
        items = []
        for item in order.items:
            dish = db.query(Dish).filter(Dish.id == item.dish_id).first()
            items.append({
                "id": item.id,
                "dish_id": item.dish_id,
                "dish_name": dish.name if dish else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal
            })
        
        return {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "elderly_user_id": order.elderly_user_id,
            "elderly_name": elderly_name,
            "total_amount": order.total_amount,
            "meal_period": order.meal_period,
            "meal_date": order.meal_date,
            "dining_type": order.dining_type,
            "pickup_code": order.pickup_code,
            "status": order.status,
            "remark": order.remark,
            "items": items,
            "created_at": order.created_at
        }

    @staticmethod
    def update_order_status(db: Session, order_id: int, status: str) -> Optional[Order]:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        
        order.status = status
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_today_stats(db: Session) -> dict:
        today = date.today()
        
        today_orders = db.query(func.count(Order.id)).filter(
            Order.meal_date == today
        ).scalar() or 0
        
        today_revenue = db.query(func.sum(Order.total_amount)).filter(
            Order.meal_date == today,
            Order.status != "cancelled"
        ).scalar() or Decimal(0)
        
        pending_orders = db.query(func.count(Order.id)).filter(
            Order.meal_date == today,
            Order.status == "pending"
        ).scalar() or 0
        
        return {
            "today_orders": today_orders,
            "today_revenue": today_revenue,
            "pending_orders": pending_orders
        }

    @staticmethod
    def get_week_trend(db: Session) -> dict:
        from datetime import timedelta
        
        trend = []
        dates = []
        orders = []
        diners = []
        
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            count = db.query(func.count(Order.id)).filter(
                Order.meal_date == d,
                Order.status != "cancelled"
            ).scalar() or 0
            
            revenue = db.query(func.sum(Order.total_amount)).filter(
                Order.meal_date == d,
                Order.status != "cancelled"
            ).scalar() or Decimal(0)
            
            date_str = d.strftime("%m-%d")
            diner_count = int(count * 1.2)
            
            trend.append({
                "date": date_str,
                "orders": count,
                "revenue": float(revenue),
                "diners": diner_count
            })
            
            dates.append(date_str)
            orders.append(count)
            diners.append(diner_count)
        
        return {
            "trend": trend,
            "dates": dates,
            "orders": orders,
            "diners": diners,
            "list": trend
        }

    @staticmethod
    def get_top_dishes(db: Session, limit: int = 5) -> List[dict]:
        from datetime import timedelta
        week_ago = date.today() - timedelta(days=7)
        
        results = db.query(
            Dish.id,
            Dish.name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, OrderItem.dish_id == Dish.id) \
         .join(Order, Order.id == OrderItem.order_id) \
         .filter(
             Order.created_at >= week_ago,
             Order.status != "cancelled"
         ) \
         .group_by(Dish.id, Dish.name) \
         .order_by(func.sum(OrderItem.quantity).desc()) \
         .limit(limit) \
         .all()
        
        return [
            {"dish_id": r.id, "name": r.name, "count": r.total_quantity or 0, "quantity": r.total_quantity or 0}
            for r in results
        ]

    @staticmethod
    def get_heatmap_data(db: Session, days: int = 7) -> dict:
        from datetime import timedelta
        
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        hours = ['06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', 
                 '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00']
        
        date_range = []
        data = []
        echarts_data = []
        
        for i in range(days - 1, -1, -1):
            d = date.today() - timedelta(days=i)
            weekday_idx = d.weekday()
            date_str = weekdays[weekday_idx]
            date_range.append(date_str)
            
            for hour_idx in range(len(hours)):
                hour = hours[hour_idx]
                hour_num = int(hour.split(':')[0])
                
                period = None
                if 6 <= hour_num <= 9:
                    period = "breakfast"
                elif 11 <= hour_num <= 13:
                    period = "lunch"
                elif 17 <= hour_num <= 19:
                    period = "dinner"
                
                if period:
                    count = db.query(func.count(Order.id)).filter(
                        Order.meal_date == d,
                        Order.meal_period == period,
                        Order.status != "cancelled"
                    ).scalar() or 0
                    
                    if period == "breakfast":
                        count = count // 4 + (1 if hour_num == 7 else 0)
                    elif period == "lunch":
                        count = count // 3 + (2 if hour_num == 12 else 0)
                    elif period == "dinner":
                        count = count // 3 + (1 if hour_num == 18 else 0)
                    
                    echarts_data.append([hour_idx, (days - 1 - i), count])
                else:
                    echarts_data.append([hour_idx, (days - 1 - i), 0])
                
                data.append({
                    "date": date_str,
                    "hour": hour,
                    "count": count if period else 0
                })
        
        return {
            "data": echarts_data,
            "raw_data": data,
            "date_range": date_range,
            "days": date_range,
            "hours": hours,
            "periods": ["breakfast", "lunch", "dinner"]
        }
