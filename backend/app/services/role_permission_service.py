"""合约市场 9 方参与角色权限矩阵服务."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.system import User


# 9 方参与角色定义
PARTICIPANT_ROLES = {
    "creator": {"name": "创作者", "description": "内容/作品原创者"},
    "operator": {"name": "运营方", "description": "作品运营/推广代理"},
    "legal_rep": {"name": "法务代表", "description": "法律事务代理人"},
    "tax_agent": {"name": "税务代理", "description": "税务申报/合规代理"},
    "logistics": {"name": "物流方", "description": "实体商品配送"},
    "insurer": {"name": "保险方", "description": "版权/履约保险"},
    "trader": {"name": "采购方", "description": "商业授权采购者"},
    "payment_provider": {"name": "支付托管方", "description": "资金托管/结算"},
    "platform": {"name": "平台方", "description": "OriStudio 平台运营"},
}

# 角色权限矩阵：每个角色可执行的操作
ROLE_PERMISSIONS = {
    "creator": [
        "create_contract",
        "publish_contract",
        "manage_split_rules",
        "view_analytics",
        "receive_payment",
        "upload_work",
    ],
    "operator": [
        "view_listed_contracts",
        "submit_quote",
        "manage_marketing",
        "view_creator_data",
    ],
    "legal_rep": [
        "review_contract_terms",
        "advise_compliance",
        "handle_disputes",
        "manage_legal_docs",
    ],
    "tax_agent": [
        "calculate_taxes",
        "file_tax_reports",
        "manage_invoices",
        "view_earnings",
    ],
    "logistics": [
        "manage_shipments",
        "update_tracking",
        "handle_returns",
        "verify_delivery",
    ],
    "insurer": [
        "issue_policy",
        "assess_risk",
        "process_claims",
        "cancel_coverage",
    ],
    "trader": [
        "browse_contracts",
        "subscribe_contract",
        "negotiate_terms",
        "make_payment",
        "view_license",
    ],
    "payment_provider": [
        "hold_escrow",
        "release_payment",
        "process_refund",
        "view_transaction_history",
    ],
    "platform": [
        "approve_contracts",
        "manage_platform_fees",
        "mediate_disputes",
        "view_all_data",
        "manage_users",
    ],
}


class RolePermissionService:
    """合约市场 9 方参与角色权限服务."""

    @staticmethod
    def get_participant_roles() -> dict:
        """获取所有参与角色定义."""
        return PARTICIPANT_ROLES

    @staticmethod
    def get_role_permissions(role: str) -> list[str]:
        """获取指定角色的权限列表."""
        if role not in ROLE_PERMISSIONS:
            return []
        return ROLE_PERMISSIONS[role]

    @staticmethod
    def get_user_roles(user: User) -> list[str]:
        """获取用户的所有参与角色."""
        roles = user.participant_roles or []
        return roles

    @staticmethod
    def add_role(user: User, role: str) -> bool:
        """为用户添加参与角色."""
        if role not in PARTICIPANT_ROLES:
            return False
        if not user.participant_roles:
            user.participant_roles = []
        if role not in user.participant_roles:
            user.participant_roles.append(role)
        return True

    @staticmethod
    def remove_role(user: User, role: str) -> bool:
        """移除用户的参与角色."""
        if role not in PARTICIPANT_ROLES:
            return False
        if user.participant_roles and role in user.participant_roles:
            user.participant_roles.remove(role)
            return True
        return False

    @staticmethod
    def has_permission(user: User, permission: str) -> bool:
        """检查用户是否拥有指定权限."""
        roles = user.participant_roles or []
        for role in roles:
            role_perms = ROLE_PERMISSIONS.get(role, [])
            if permission in role_perms:
                return True
        return False

    @staticmethod
    def get_user_permissions(user: User) -> list[str]:
        """获取用户的所有权限（合并所有角色的权限）."""
        permissions = set()
        roles = user.participant_roles or []
        for role in roles:
            role_perms = ROLE_PERMISSIONS.get(role, [])
            permissions.update(role_perms)
        return sorted(permissions)

    @staticmethod
    def validate_role_assignment(user: User, role: str) -> tuple[bool, str]:
        """验证角色分配是否合法."""
        if role not in PARTICIPANT_ROLES:
            return False, f"无效角色: {role}"

        # creator 和 trader 不能同时存在
        if "creator" in role and "trader" in role:
            return False, "创作者和采购方角色互斥"

        # platform 需要特殊权限
        if role == "platform" and not user.is_platform_operator:
            return False, "平台角色需要运营权限"

        return True, "验证通过"

    @staticmethod
    def get_contract_participants(contract: object) -> list[dict]:
        """获取合约的所有参与方信息."""
        participants = []

        if contract.creator_id:
            participants.append({
                "role": "creator",
                "user_id": contract.creator_id,
                "name": contract.creator.username if contract.creator else "",
            })

        if contract.operator_id:
            participants.append({
                "role": "operator",
                "user_id": contract.operator_id,
                "name": contract.operator.username if contract.operator else "",
            })

        if contract.trader_id:
            participants.append({
                "role": "trader",
                "user_id": contract.trader_id,
                "name": contract.trader.username if contract.trader else "",
            })

        return participants
