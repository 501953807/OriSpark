"""供应链 Pydantic 模型."""

from typing import Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class EtsyConnectRequest(BaseModel):
    """Etsy OAuth 连接请求."""
    authorization_code: str
    shop_id: Optional[str] = None


class EtsyShopResponse(BaseModel):
    """Etsy 店铺响应."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    shop_name: str
    shop_id: str
    is_active: bool
    token_expires_at: Optional[datetime] = None
    connected_at: Optional[datetime] = None
    created_at: datetime


class EtsyListingCreate(BaseModel):
    """Etsy 商品发布请求."""
    title: str
    price: float
    quantity: int = 1
    description: Optional[str] = None
    currency: str = "USD"
    tags: Optional[list[str]] = None
    materials: Optional[list[str]] = None
    category_id: Optional[str] = None
    shipping_profile_id: Optional[str] = None
    processing_time_days: Optional[int] = None
    ships_from_country: str = "CN"
    shipping_cost: Optional[float] = None
    free_shipping: bool = False
    variations: Optional[list[dict]] = None
    images: Optional[list[str]] = None
    product_id: Optional[str] = None  # link to local physical_product


class EtsyListingUpdate(BaseModel):
    """Etsy 商品更新请求 (部分更新)."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    tags: Optional[list[str]] = None
    materials: Optional[list[str]] = None
    status: Optional[str] = None
    shipping_cost: Optional[float] = None
    free_shipping: Optional[bool] = None
    variations: Optional[list[dict]] = None


class EtsyListingResponse(BaseModel):
    """Etsy 商品响应."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    product_id: Optional[str] = None
    etsy_listing_id: str
    etsy_shop_id: str
    title: str
    description: Optional[str] = None
    price: float
    currency: str
    quantity: int
    tags: Optional[list] = None
    materials: Optional[list] = None
    status: str
    etsy_status: str
    views_count: int
    favorites_count: int
    sales_count: int
    revenue: float
    created_at: datetime
    updated_at: datetime


class EtsyOrderResponse(BaseModel):
    """Etsy 订单响应."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    listing_id: str
    etsy_order_id: str
    buyer_name: Optional[str] = None
    buyer_country: Optional[str] = None
    order_total: float
    shipping_cost: Optional[float] = None
    tax: Optional[float] = None
    order_date: datetime
    shipping_deadline: Optional[datetime] = None
    status: str
    tracking_number: Optional[str] = None
    created_at: datetime


class EtsyDashboardResponse(BaseModel):
    """Etsy 仪表盘响应."""
    total_sales: int = 0
    total_views: int = 0
    total_favorites: int = 0
    total_revenue: float = 0.0
    active_listings: int = 0
    revenue_by_month: list[dict] = []
    orders_by_status: dict[str, int] = {}
    top_listings: list[dict] = []


class SupplyPartnerCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    type: str = "manufacturer"
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    categories: Optional[list[str]] = None
    product_categories: Optional[list[str]] = None
    material_capabilities: Optional[list[str]] = None
    moq_per_category: Optional[dict] = None
    typical_lead_time_days: Optional[int] = None
    price_range: Optional[list] = None
    moq: Optional[int] = None
    rating: int = 0
    tags: Optional[list[str]] = None
    notes: Optional[str] = None


class SupplyOrderCreate(BaseModel):
    """Order creation input."""
    partner_id: Optional[str] = None
    campaign_id: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    order_type: str = "custom_mfg"
    quantity: int = 1
    specifications: Optional[str] = None
    design_file_path: Optional[str] = None
    unit_price: float = 0
    total_amount: float = 0
    deposit_percent: float = 30
    deposit_paid: float = 0
    shipping_cost: float = 0
    status: str = "draft"
    expected_date: Optional[date] = None
    sample_requested: int = 0
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Order status update input."""
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    actual_date: Optional[date] = None
    notes: Optional[str] = None


class OrderSampleAction(BaseModel):
    """Order sample action input."""
    action: str = "request"


class RevenueCreate(BaseModel):
    """Revenue recording input."""
    product_id: Optional[str] = None
    platform: Optional[str] = None
    amount: float = 0
    currency: str = "CNY"
    date: Optional[date] = None
    order_count: int = 1
    source: str = "manual"
    refund_amount: float = 0
    platform_fee: float = 0
    net_revenue: float = 0
    notes: Optional[str] = None

    @property
    def resolved_date(self) -> date:
        return self.date or date.today()


class ReminderCreate(BaseModel):
    """Reminder creation input."""
    type: str = "order"
    related_id: str = ""
    title: Optional[str] = None
    remind_at: Optional[datetime] = None


class PublishToPodRequest(BaseModel):
    """Publish to POD platform input."""
    platform: str = ""
    product_data: dict = {}
    action: str = "publish"


class FundingGoalRequest(BaseModel):
    """Funding goal calculation input."""
    tiers: list[dict] = []
    manufacturing_cost: float = 0
    shipping_cost: float = 0
    platform_fee_pct: float = 8.0
    buffer_pct: float = 15.0
    currency: str = "CNY"


class FactoryPriceCompareRequest(BaseModel):
    """Factory price comparison input."""
    product_category: str = ""
    quantity: int = 1
    specifications: dict = {}
    partner_ids: list[str] = []


class PrintfulMockupRequest(BaseModel):
    """Printful mockup generation input."""
    product_id: Optional[str] = None
    design_file_id: Optional[str] = None
    colors: list[str] = ["white"]


class ProductMockupRequest(BaseModel):
    """AI product mockup generation input."""
    category_id: str = ""
    prompt: Optional[str] = None
    style: str = "realistic"


class DigitalProductValidateRequest(BaseModel):
    """Digital product validation input."""
    product_type: str = ""
    target_platform: str = ""
    file_formats: list[str] = []
    file_count: int = 0
    file_size_mb: float = 0
    has_preview: bool = False


class MonetizationAdvisorRequest(BaseModel):
    """AI monetization advisor input."""
    work_title: str = ""
    work_type: str = ""
    creator_type: str = ""
    current_paths: list[str] = []


class ListingCreate(BaseModel):
    """Listing (product) creation input."""
    work_id: Optional[str] = None
    product_template_id: Optional[str] = None
    title: str = "未命名商品"
    description: Optional[str] = None
    price: float = 0
    cost: float = 0
    currency: str = "CNY"
    monetization_path: Optional[str] = None
    variant_sku: Optional[str] = None
    variant_name: Optional[str] = None
    spec_validation: Optional[bool] = None
    mockup_image_path: Optional[str] = None
    design_file_path: Optional[str] = None
    status: str = "draft"


class ListingUpdate(BaseModel):
    """Listing partial update."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    monetization_path: Optional[str] = None
    variant_sku: Optional[str] = None
    variant_name: Optional[str] = None
    mockup_image_path: Optional[str] = None
    status: Optional[str] = None
    spec_validation: Optional[bool] = None


class DesignCompatRequest(BaseModel):
    """Design compatibility check input."""
    dpi: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    color_mode: Optional[str] = None
    file_format: Optional[str] = None
    has_transparency: Optional[bool] = None
    exclude_category_id: Optional[str] = None
    limit: int = 20


class RemediationRequest(BaseModel):
    """Remediation suggestion input."""
    category_id: str
    dpi: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    color_mode: Optional[str] = None
    file_format: Optional[str] = None
    has_transparency: Optional[bool] = None


# ============================================================================
# Design spec validation
# ============================================================================

class SpecValidateRequest(BaseModel):
    """Design spec validation input."""
    category_id: str
    dpi: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    color_mode: Optional[str] = None
    file_format: Optional[str] = None
    has_transparency: Optional[bool] = None


class SpecValidateBatchRequest(BaseModel):
    """Design spec batch validation input."""
    category_ids: list[str]
    dpi: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    color_mode: Optional[str] = None
    file_format: Optional[str] = None
    has_transparency: Optional[bool] = None


# ============================================================================
# Products (flat legacy products)
# ============================================================================

class ProductCreate(BaseModel):
    """Legacy product creation input."""
    work_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: float = 0
    cost: float = 0
    currency: str = "CNY"
    category: Optional[str] = None
    monetization_path: Optional[str] = None
    material_category: Optional[str] = None
    platform: Optional[str] = None
    specifications: Optional[str] = None
    design_variant_path: Optional[str] = None
    mockup_image_path: Optional[str] = None
    images: Optional[list] = None
    platform_status: str = "draft"
    status: str = "active"


class ProductUpdate(BaseModel):
    """Product partial update."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    category: Optional[str] = None
    monetization_path: Optional[str] = None
    material_category: Optional[str] = None
    platform: Optional[str] = None
    specifications: Optional[str] = None
    design_variant_path: Optional[str] = None
    mockup_image_path: Optional[str] = None
    images: Optional[list] = None
    platform_status: Optional[str] = None
    platform_product_id: Optional[str] = None
    platform_product_url: Optional[str] = None
    status: Optional[str] = None


# ============================================================================
# Monetization channel
# ============================================================================

class ChannelCreate(BaseModel):
    """Monetization channel creation."""
    name: Optional[str] = None
    channel_type: Optional[str] = None
    platform: Optional[str] = None
    platform_store_id: Optional[str] = None
    platform_store_url: Optional[str] = None
    credentials: Optional[dict] = None
    status: str = "active"


# ============================================================================
# Campaigns
# ============================================================================

class CampaignCreate(BaseModel):
    """Campaign creation input."""
    title: Optional[str] = None
    description: Optional[str] = None
    platform: Optional[str] = None
    platform_campaign_id: Optional[str] = None
    platform_url: Optional[str] = None
    goal_amount: float = 0
    currency: str = "CNY"
    raised_amount: float = 0
    backer_count: int = 0
    reward_tiers: list = []
    launch_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    related_product_ids: Optional[list[str]] = None
    related_work_ids: Optional[list[str]] = None
    status: str = "draft"


class CampaignUpdate(BaseModel):
    """Campaign partial update."""
    title: Optional[str] = None
    description: Optional[str] = None
    raised_amount: Optional[float] = None
    backer_count: Optional[int] = None
    status: Optional[str] = None
    actual_delivery_date: Optional[datetime] = None
    platform_url: Optional[str] = None


# ============================================================================
# IP Licensing
# ============================================================================

class LicenseCreate(BaseModel):
    """License creation input."""
    work_id: Optional[str] = None
    license_type: Optional[str] = None
    platform: Optional[str] = None
    allowed_uses: Optional[list[str]] = None
    restrictions: Optional[list[str]] = None
    price: float = 0
    currency: str = "CNY"
    platform_listing_id: Optional[str] = None
    platform_listing_url: Optional[str] = None
    status: str = "active"
