import sys
import os
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app.models.models import User, Dish, Order, OrderItem
from app.utils.auth import hash_password
from app.utils.helpers import generate_order_no, generate_pickup_code


def init_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("数据库表已重新创建")
    
    db = SessionLocal()
    
    try:
        admin = User(
            phone="13800000000",
            password_hash=hash_password("admin123"),
            name="系统管理员",
            role="admin"
        )
        db.add(admin)
        
        elderly_users = [
            {"phone": "13800000001", "name": "张大爷"},
            {"phone": "13800000002", "name": "李奶奶"},
            {"phone": "13800000003", "name": "王爷爷"},
            {"phone": "13800000004", "name": "赵奶奶"},
            {"phone": "13800000005", "name": "刘大爷"},
        ]
        
        for eu in elderly_users:
            user = User(
                phone=eu["phone"],
                name=eu["name"],
                role="elderly",
                birth_date=date(1950, 1, 1),
                address="阳光社区"
            )
            db.add(user)
        
        family_users = [
            {"phone": "13900000001", "name": "张小明"},
            {"phone": "13900000002", "name": "李小红"},
        ]
        
        for fu in family_users:
            user = User(
                phone=fu["phone"],
                name=fu["name"],
                role="family"
            )
            db.add(user)
        
        db.flush()
        
        breakfast_dishes = [
            {"name": "鲜肉包子", "price": Decimal("3.00"), "nutrition_info": {"calories": 250, "protein": 8}},
            {"name": "小米粥", "price": Decimal("2.00"), "nutrition_info": {"calories": 100, "protein": 2}},
            {"name": "茶叶蛋", "price": Decimal("1.50"), "nutrition_info": {"calories": 150, "protein": 12}},
            {"name": "豆浆", "price": Decimal("2.00"), "nutrition_info": {"calories": 80, "protein": 4}},
            {"name": "油条", "price": Decimal("2.00"), "nutrition_info": {"calories": 300, "protein": 5}},
            {"name": "咸菜", "price": Decimal("1.00"), "nutrition_info": {"calories": 30, "protein": 1}},
        ]
        
        lunch_dishes = [
            {"name": "红烧肉", "price": Decimal("18.00"), "nutrition_info": {"calories": 450, "protein": 25}, "suitable_for": ["普通"]},
            {"name": "鱼香肉丝", "price": Decimal("15.00"), "nutrition_info": {"calories": 350, "protein": 20}, "suitable_for": ["普通"]},
            {"name": "清炒时蔬", "price": Decimal("8.00"), "nutrition_info": {"calories": 100, "protein": 3}, "suitable_for": ["高血压", "糖尿病"]},
            {"name": "西红柿炒蛋", "price": Decimal("10.00"), "nutrition_info": {"calories": 200, "protein": 12}, "suitable_for": ["普通"]},
            {"name": "清蒸鱼", "price": Decimal("22.00"), "nutrition_info": {"calories": 280, "protein": 30}, "suitable_for": ["高血压", "糖尿病"]},
            {"name": "米饭", "price": Decimal("1.00"), "nutrition_info": {"calories": 130, "protein": 3}},
            {"name": "馒头", "price": Decimal("0.50"), "nutrition_info": {"calories": 110, "protein": 4}},
            {"name": "紫菜蛋花汤", "price": Decimal("3.00"), "nutrition_info": {"calories": 50, "protein": 3}},
        ]
        
        dinner_dishes = [
            {"name": "小米粥", "price": Decimal("2.00"), "nutrition_info": {"calories": 100, "protein": 2}},
            {"name": "包子", "price": Decimal("3.00"), "nutrition_info": {"calories": 250, "protein": 8}},
            {"name": "凉拌黄瓜", "price": Decimal("6.00"), "nutrition_info": {"calories": 50, "protein": 2}, "suitable_for": ["高血压", "糖尿病"]},
            {"name": "炒土豆丝", "price": Decimal("8.00"), "nutrition_info": {"calories": 180, "protein": 3}, "suitable_for": ["普通"]},
            {"name": "炖豆腐", "price": Decimal("10.00"), "nutrition_info": {"calories": 150, "protein": 15}, "suitable_for": ["高血压", "糖尿病"]},
            {"name": "玉米粥", "price": Decimal("2.00"), "nutrition_info": {"calories": 90, "protein": 3}},
        ]
        
        all_dishes = []
        for d in breakfast_dishes:
            all_dishes.append(Dish(**d, category="breakfast", status="on", stock=100))
        for d in lunch_dishes:
            all_dishes.append(Dish(**d, category="lunch", status="on", stock=100))
        for d in dinner_dishes:
            all_dishes.append(Dish(**d, category="dinner", status="on", stock=100))
        
        db.add_all(all_dishes)
        db.flush()
        
        print(f"已创建 {len(breakfast_dishes)} 道早餐菜品")
        print(f"已创建 {len(lunch_dishes)} 道午餐菜品")
        print(f"已创建 {len(dinner_dishes)} 道晚餐菜品")
        
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=90)
        
        import numpy as np
        from app.utils.helpers import is_weekend, is_holiday
        
        current = start_date
        order_count = 0
        
        while current <= end_date:
            base = 40
            if is_weekend(current):
                base += 15
            if is_holiday(current):
                base += 20
            
            day_of_year = current.timetuple().tm_yday
            seasonal = 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            base += int(seasonal)
            
            for period, factor in [("breakfast", 0.7), ("lunch", 1.0), ("dinner", 0.85)]:
                count = max(5, int(base * factor + np.random.normal(0, 5)))
                
                category = "breakfast" if period == "breakfast" else "lunch" if period == "lunch" else "dinner"
                dishes_in_category = [d for d in all_dishes if d.category == category]
                
                for i in range(count):
                    user_idx = np.random.randint(0, len(elderly_users))
                    user_id = user_idx + 2
                    
                    num_items = np.random.randint(1, 4)
                    selected_dishes = np.random.choice(dishes_in_category, size=min(num_items, len(dishes_in_category)), replace=False)
                    
                    total = Decimal(0)
                    items = []
                    
                    for dish in selected_dishes:
                        qty = np.random.randint(1, 3)
                        subtotal = dish.price * qty
                        total += subtotal
                        items.append({
                            "dish_id": dish.id,
                            "quantity": qty,
                            "unit_price": dish.price,
                            "subtotal": subtotal
                        })
                    
                    order_no = generate_order_no()
                    order = Order(
                        order_no=order_no,
                        user_id=user_id,
                        total_amount=total,
                        meal_period=period,
                        meal_date=current,
                        pickup_code=generate_pickup_code(),
                        status="completed"
                    )
                    db.add(order)
                    db.flush()
                    
                    for item in items:
                        order_item = OrderItem(
                            order_id=order.id,
                            dish_id=item["dish_id"],
                            quantity=item["quantity"],
                            unit_price=item["unit_price"],
                            subtotal=item["subtotal"]
                        )
                        db.add(order_item)
                    
                    order_count += 1
            
            current += timedelta(days=1)
        
        db.commit()
        print(f"已创建 {order_count} 条历史订单数据")
        print(f"数据时间范围: {start_date} 至 {end_date} (共90天)")
        
        print("\n=== 初始化完成 ===")
        print("\n测试账号:")
        print("  管理员: 13800000000 / admin123")
        print("  老人用户: 13800000001 ~ 13800000005 (验证码 123456)")
        print("  亲属用户: 13900000001 ~ 13900000002 (验证码 123456)")
        
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
