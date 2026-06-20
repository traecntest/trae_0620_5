from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class ResponseModel(BaseModel):
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="提示信息")
    data: Any = Field(default=None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


class SendSmsRequest(BaseModel):
    phone: str = Field(..., description="手机号", pattern=r"^1[3-9]\d{9}$")


class LoginRequest(BaseModel):
    phone: str = Field(..., description="手机号", pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., description="验证码")
    role: str = Field(default="elderly", description="角色: elderly/family/admin")


class AdminLoginRequest(BaseModel):
    phone: str = Field(..., description="手机号", pattern=r"^1[3-9]\d{9}$")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    id: int
    phone: str
    name: str
    role: str
    avatar: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class DishBase(BaseModel):
    name: str
    category: str
    price: Decimal
    image: Optional[str] = None
    description: Optional[str] = None
    nutrition_info: Optional[Dict] = None
    suitable_for: Optional[List[str]] = None
    stock: int = 0
    status: str = "on"


class DishCreate(DishBase):
    pass


class DishUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = None
    image: Optional[str] = None
    description: Optional[str] = None
    nutrition_info: Optional[Dict] = None
    suitable_for: Optional[List[str]] = None
    stock: Optional[int] = None
    status: Optional[str] = None


class DishInfo(DishBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DishListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    list: List[DishInfo]


class OrderItemRequest(BaseModel):
    dish_id: int
    quantity: int = Field(..., ge=1)
    price: Decimal


class OrderSubmitRequest(BaseModel):
    meal_period: str = Field(..., pattern=r"^(breakfast|lunch|dinner)$")
    meal_date: str
    items: List[OrderItemRequest]
    remark: Optional[str] = None
    is_for_elderly: bool = False
    elderly_user_id: Optional[int] = None
    dining_type: str = Field(default="dinein", pattern=r"^(takeout|dinein)$")

    @field_validator("meal_date")
    def validate_meal_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("日期格式必须为YYYY-MM-DD")
        return v


class OrderItemInfo(BaseModel):
    id: int
    dish_id: int
    dish_name: Optional[str] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class OrderInfo(BaseModel):
    id: int
    order_no: str
    user_id: int
    elderly_user_id: Optional[int] = None
    elderly_name: Optional[str] = None
    total_amount: Decimal
    meal_period: str
    meal_date: date
    dining_type: str
    pickup_code: Optional[str] = None
    status: str
    remark: Optional[str] = None
    items: List[OrderItemInfo] = []
    created_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    list: List[OrderInfo]


class OrderSubmitResponse(BaseModel):
    order_id: str
    pickup_code: str
    total_amount: Decimal
    meal_period: str
    meal_date: str
    status: str
    pickup_time: str
    created_at: datetime


class FamilyBindRequest(BaseModel):
    elderly_phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    relation: str = Field(..., pattern=r"^(son|daughter|spouse|other)$")


class FamilyBindConfirmRequest(BaseModel):
    bind_id: int
    confirm: bool


class FamilyMemberInfo(BaseModel):
    bind_id: int
    user_id: int
    name: str
    phone: str
    relation: str
    status: str
    bound_at: Optional[datetime] = None


class FamilyMemberListResponse(BaseModel):
    members: List[FamilyMemberInfo]


class VoiceRecognizeResponse(BaseModel):
    text: str
    confidence: float


class PredictionData(BaseModel):
    breakfast: int
    lunch: int
    dinner: int


class PredictionItem(BaseModel):
    date: date
    prediction: PredictionData
    actual: Optional[PredictionData] = None
    accuracy: Optional[float] = None


class PredictionHistoryResponse(BaseModel):
    list: List[PredictionItem]
    total: int


class PredictionAccuracyResponse(BaseModel):
    avg_accuracy: float
    mae: float
    rmse: float
    mape: float
    data_points: int


class DashboardData(BaseModel):
    today_orders: int
    today_revenue: Decimal
    pending_orders: int
    tomorrow_prediction: PredictionData
    week_order_trend: List[Dict[str, Any]]
    top_dishes: List[Dict[str, Any]]


class HeatmapDataPoint(BaseModel):
    date: str
    period: str
    count: int


class HeatmapResponse(BaseModel):
    data: List[HeatmapDataPoint]
    date_range: List[str]
    periods: List[str]


class StatisticsResponse(BaseModel):
    total_orders: int
    total_revenue: Decimal
    avg_order_amount: Decimal
    user_count: int
    elderly_user_count: int
    family_user_count: int
    daily_stats: List[Dict[str, Any]]
    category_stats: List[Dict[str, Any]]
