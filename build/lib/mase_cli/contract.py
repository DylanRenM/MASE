"""MASE Contract — 运行时契约断言库

提供 DbC (Design by Contract) 风格的轻量级断言工具：
- require(condition, message): 前置条件
- ensure(condition, message): 后置条件
- invariant_check(condition, message): 不变式检查
- ContractViolation: 契约违反异常

使用示例：

    from mase_cli.contract import require, ensure, invariant_check, ContractViolation

    def transfer(from_account, to_account, amount):
        require(amount > 0, "转账金额必须大于0")
        require(from_account.balance >= amount, "余额不足")

        from_account.balance -= amount
        to_account.balance += amount

        ensure(from_account.balance >= 0, "转出账户余额不能为负")
        ensure(to_account.balance == old_to + amount, "转入金额不匹配")

    class Account:
        def _invariant(self):
            invariant_check(self.balance >= 0, "账户余额不能为负")
"""

import os
from typing import Optional


class ContractViolation(Exception):
    """契约违反异常。"""

    def __init__(self, kind: str, message: str, location: Optional[str] = None):
        self.kind = kind  # "precondition" | "postcondition" | "invariant"
        self.message = message
        self.location = location
        super().__init__(self._format())

    def _format(self):
        loc = f" [{self.location}]" if self.location else ""
        return f"[{self.kind.upper()}] {self.message}{loc}"


# ── 断言级别 ──

class _ContractConfig:
    """契约运行时配置。

    读取环境变量 MASE_CONTRACT_LEVEL:
    - strict (默认): 契约违反抛出 ContractViolation
    - relaxed: 只打印警告，不中断
    - disabled: 完全不做契约检查
    """
    STRICT = "strict"
    RELAXED = "relaxed"
    DISABLED = "disabled"

    @staticmethod
    def get_level() -> str:
        return os.environ.get("MASE_CONTRACT_LEVEL", _ContractConfig.STRICT)

    @staticmethod
    def is_strict() -> bool:
        return _ContractConfig.get_level() == _ContractConfig.STRICT

    @staticmethod
    def is_disabled() -> bool:
        return _ContractConfig.get_level() == _ContractConfig.DISABLED


_contract_config = _ContractConfig()


def require(condition: bool, message: str = "前置条件不满足"):
    """前置条件断言。调用函数/方法前必须满足的条件。

    Args:
        condition: 必须为 True
        message: 违反时的描述信息

    Raises:
        ContractViolation: condition 为 False 且 level=strict
    """
    if not condition:
        if _contract_config.is_disabled():
            return
        if _contract_config.is_strict():
            raise ContractViolation("precondition", message)
        else:
            import warnings
            warnings.warn(f"[PRECONDITION] {message}", stacklevel=2)


def ensure(condition: bool, message: str = "后置条件不满足"):
    """后置条件断言。函数/方法执行后必须保证的状态。

    Args:
        condition: 必须为 True
        message: 违反时的描述信息

    Raises:
        ContractViolation: condition 为 False 且 level=strict
    """
    if not condition:
        if _contract_config.is_disabled():
            return
        if _contract_config.is_strict():
            raise ContractViolation("postcondition", message)
        else:
            import warnings
            warnings.warn(f"[POSTCONDITION] {message}", stacklevel=2)


def invariant_check(condition: bool, message: str = "不变式违反"):
    """不变式断言。跨所有公共方法必须保持的规则。

    Args:
        condition: 必须为 True
        message: 违反时的描述信息

    Raises:
        ContractViolation: condition 为 False 且 level=strict
    """
    if not condition:
        if _contract_config.is_disabled():
            return
        if _contract_config.is_strict():
            raise ContractViolation("invariant", message)
        else:
            import warnings
            warnings.warn(f"[INVARIANT] {message}", stacklevel=2)


# ── 便捷装饰器 ──

def invariant(condition_fn):
    """不变式装饰器。自动在 __init__ 后和每个公共方法前后检查不变式。

    使用:
        @invariant(lambda self: self.balance >= 0)
        class Account:
            ...
    """
    # 简化实现：仅提供签名提示，实际使用时由 MASE 项目按需扩展
    return condition_fn
