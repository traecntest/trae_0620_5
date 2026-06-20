from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
import logging

from .database import SessionLocal
from .ml.prediction_service import PredictionService

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.WARNING)

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def daily_prediction_task():
    db = SessionLocal()
    try:
        tomorrow = date.today() + timedelta(days=1)
        prediction = PredictionService.predict_for_date(db, tomorrow)
        
        print(f"[{date.today()}] 明日备餐预测完成:")
        print(f"  早餐: {prediction['breakfast']} 人")
        print(f"  午餐: {prediction['lunch']} 人")
        print(f"  晚餐: {prediction['dinner']} 人")
    except Exception as e:
        print(f"预测任务执行失败: {str(e)}")
    finally:
        db.close()


def weekly_model_retrain_task():
    db = SessionLocal()
    try:
        result = PredictionService.train_model(db, retrain=True)
        print(f"[{date.today()}] 模型重新训练完成:")
        if "metrics" in result:
            print(f"  MAE: {result['metrics']['mae']}")
            print(f"  RMSE: {result['metrics']['rmse']}")
            print(f"  MAPE: {result['metrics']['mape']}%")
    except Exception as e:
        print(f"模型训练任务执行失败: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        daily_prediction_task,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_prediction",
        replace_existing=True
    )
    
    scheduler.add_job(
        weekly_model_retrain_task,
        trigger=CronTrigger(day_of_week=0, hour=1, minute=0),
        id="weekly_retrain",
        replace_existing=True
    )
    
    scheduler.start()
    print("定时任务调度器已启动")
    print("  - 每日凌晨2:00: 生成次日备餐预测")
    print("  - 每周日凌晨1:00: 重新训练预测模型")


def stop_scheduler():
    scheduler.shutdown()
    print("定时任务调度器已停止")
