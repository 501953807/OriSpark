"""网关模块."""

from app.gateway.base import (
    NotaryGateway, SearchGateway, PublishingGateway,
    NotaryResult, SearchResult,
)
from app.gateway.banquanjia import BanquanjiaGateway
from app.gateway.antchain import AntChainGateway
from app.gateway.zhixinchain import ZhixinChainGateway
from app.gateway.baidu_vision import BaiduVisionGateway, BaiduTextSearch
from app.gateway.google_vision import GoogleVisionGateway
from app.gateway.copyscape import CopyscapeGateway, GitHubCodeSearch
from app.gateway.ollama import OllamaGateway
from app.gateway.playwright_pub import PlaywrightPublisher
from app.gateway.printful import PrintfulGateway
from app.gateway.redbubble import RedbubbleGateway
from app.gateway.society6 import Society6Gateway
from app.gateway.gelato import GelatoGateway
from app.gateway.zazzle import ZazzleGateway
from app.gateway.spring import SpringGateway

__all__ = [
    "NotaryGateway", "SearchGateway", "PublishingGateway",
    "NotaryResult", "SearchResult",
    "BanquanjiaGateway", "AntChainGateway", "ZhixinChainGateway",
    "BaiduVisionGateway", "BaiduTextSearch",
    "GoogleVisionGateway",
    "CopyscapeGateway", "GitHubCodeSearch",
    "OllamaGateway",
    "PlaywrightPublisher",
    "PrintfulGateway",
    "RedbubbleGateway",
    "Society6Gateway",
    "GelatoGateway",
    "ZazzleGateway",
    "SpringGateway",
]
