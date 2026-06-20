from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

from .database import engine, Base
from .config import settings
from .utils.response import handle_exception
from .schemas.schemas import ResponseModel

from .api.auth import router as auth_router
from .api.users import router as users_router
from .api.dishes import router as dishes_router
from .api.orders import router as orders_router
from .api.family import router as family_router
from .api.voice import router as voice_router
from .api.prediction import router as prediction_router
from .api.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")
    
    try:
        from .scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"定时任务启动失败: {e}")
    
    yield
    
    try:
        from .scheduler import stop_scheduler
        stop_scheduler()
    except:
        pass


app = FastAPI(
    title="社区老年食堂智能点餐系统",
    description="专为老年人设计的智能点餐系统，支持适老化界面、亲属代订、语音辅助和智能备餐预测",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(os.path.dirname(backend_dir), "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")
    templates = Jinja2Templates(directory=os.path.join(frontend_dir, "templates"))
    admin_templates = Jinja2Templates(directory=os.path.join(frontend_dir, "admin"))
else:
    templates = Jinja2Templates(directory="templates")
    admin_templates = Jinja2Templates(directory="admin")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return handle_exception(exc)


@app.get("/api/v1/health", response_model=ResponseModel, tags=["系统"])
async def health_check():
    return ResponseModel(
        code=200,
        message="ok",
        data={"status": "healthy", "version": "1.0.0"}
    )


api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(dishes_router, prefix=api_prefix)
app.include_router(orders_router, prefix=api_prefix)
app.include_router(family_router, prefix=api_prefix)
app.include_router(voice_router, prefix=api_prefix)
app.include_router(prediction_router, prefix=api_prefix)
app.include_router(admin_router, prefix=api_prefix)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/order", response_class=HTMLResponse, include_in_schema=False)
async def order_page(request: Request):
    return templates.TemplateResponse("order.html", {"request": request})


@app.get("/order/confirm", response_class=HTMLResponse, include_in_schema=False)
async def confirm_page(request: Request):
    return templates.TemplateResponse("confirm.html", {"request": request})


@app.get("/orders", response_class=HTMLResponse, include_in_schema=False)
async def orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})


@app.get("/family", response_class=HTMLResponse, include_in_schema=False)
async def family_page(request: Request):
    return templates.TemplateResponse("family.html", {"request": request})


@app.get("/family/order", response_class=HTMLResponse, include_in_schema=False)
async def family_order_page(request: Request):
    return templates.TemplateResponse("family_order.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_login_page(request: Request):
    return admin_templates.TemplateResponse("login.html", {"request": request})


@app.get("/admin/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard(request: Request):
    return admin_templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/admin/prediction", response_class=HTMLResponse, include_in_schema=False)
async def admin_prediction(request: Request):
    return admin_templates.TemplateResponse("prediction.html", {"request": request})


@app.get("/admin/dishes", response_class=HTMLResponse, include_in_schema=False)
async def admin_dishes(request: Request):
    return admin_templates.TemplateResponse("dishes.html", {"request": request})


@app.get("/admin/orders", response_class=HTMLResponse, include_in_schema=False)
async def admin_orders(request: Request):
    return admin_templates.TemplateResponse("orders.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
