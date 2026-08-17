"""业务异常 — 服务层统一抛出，全局处理器统一响应."""


class BusinessException(Exception):
    """业务逻辑异常.

    统一字段: status_code / code / message
    """
    def __init__(
        self,
        message: str = "业务错误",
        status_code: int = 400,
        code: str | None = None,
        data: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.data = data

    def to_dict(self) -> dict:
        result = {"success": False, "message": self.message}
        if self.code:
            result["code"] = self.code
        if self.data:
            result["data"] = self.data
        return result
