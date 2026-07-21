# 编码规范

> MASE 2.0 Design L2 | Python 3.10+ / Flask 项目

## 1. 通用规范

- 遵循 PEP 8 编码规范
- 4 空格缩进，不用 Tab
- 行宽上限 100 字符
- 文件末尾保留一个空行
- 使用 UTF-8 编码

## 2. 命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 模块/文件 | 小写字母 + 下划线 | `excel_handler.py` |
| 函数 | 小写字母 + 下划线 | `round_to_fibonacci()` |
| 类 | 大驼峰 | `EmbeddingClient` |
| 常量 | 全大写 + 下划线 | `FIB_SCALES` |
| 私有函数/变量 | 前缀单下划线 | `_build_prompt()` |

## 3. 类型注解

- 所有公共函数必须有完整类型注解
- 使用 `list[dict]` 而非 `List[dict]`（Python 3.10+ 语法）

```python
def round_to_fibonacci(value: float) -> int:
    ...
```

## 4. 文档字符串

- 公共函数使用 docstring 描述前置/后置条件
- 使用 Google 风格（Args / Returns / Raises）

```python
def validate_baseline(rows: list[dict]) -> ValidationResult:
    """校验上传的基线故事数据。

    Args:
        rows: Excel 解析后的行列表，每行含 id/title/description/points。

    Returns:
        ValidationResult，valid=True 表示全部规则通过。

    Raises:
        不抛异常，所有错误通过 ValidationResult.errors 返回。
    """
```

## 5. 错误处理

- 不吞异常，不写 `except: pass`
- 业务错误返回结果对象（非抛异常）
- 基础设施错误（API、DB、IO）抛明确异常类型
- 异常类继承自项目基类 `StoryPointError`

## 6. 测试规范

- 文件名：`test_<module>.py`
- 函数名：`test_<行为>_<场景>`
- 测试文件镜像源码结构（`tests/unit/` 对应 `core/`）
- 不依赖外部服务（单元测试全 mock）
- 集成测试使用 SQLite `:memory:`

## 7. Import 顺序

```
1. 标准库
2. 第三方库
3. 项目内部模块

每组之间空一行，组内按字母排序。
```

## 8. 提交规范

- Conventional Commit: `type(scope): description`
- type: feat / fix / refactor / test / docs / chore
- scope: 模块名（如 fibonacci, validator, embedding）
- 每完成一个 TDD 微循环或每 20 次对话提交
