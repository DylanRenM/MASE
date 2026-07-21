"""Excel 模板生成与上传解析。

使用 openpyxl 生成带数据验证的模板，解析用户上传的基线故事 Excel。
"""

import os
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

# 模板列名
HEADERS = ["ID", "故事标题", "故事描述", "故事点"]


def generate_template(filepath: str) -> None:
    """生成基线故事模板 Excel 文件。

    前置条件: filepath 父目录存在且可写。
    后置条件: 文件存在，含"基准故事" sheet 和 A1:D1 表头。
    后置条件: D 列有数据验证下拉框 {1,2,3,5,8,13}。

    Args:
        filepath: 输出文件路径。
    """
    # 确保目录存在
    parent = Path(filepath).parent
    os.makedirs(parent, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "基准故事"
    ws.append(HEADERS)

    # 设置故事点列的数据验证（下拉框）
    dv = DataValidation(type="list", formula1='"1,2,3,5,8,13"')
    dv.error = "请选择有效的故事点: 1, 2, 3, 5, 8, 13"
    dv.errorTitle = "无效的故事点"
    ws.add_data_validation(dv)
    dv.add("D2:D1000")

    wb.save(filepath)


def parse_upload(filepath: str) -> list[dict]:
    """解析上传的 Excel 文件。

    前置条件: filepath 指向有效的 .xlsx/.xls 文件。
    后置条件: 返回 list[dict]，每个 dict 含 id/title/description/points。
    不变量: len(result) 等于数据行数（不含表头）。

    Args:
        filepath: Excel 文件路径。

    Returns:
        行列表，每行为 {"id": str, "title": str, "description": str, "points": int}。
    """
    wb = load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    rows: list[dict] = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if all(cell is None for cell in row):
            continue

        sid = str(row[0]) if row[0] is not None else ""
        title = str(row[1]) if row[1] is not None else ""
        description = str(row[2]) if row[2] is not None else ""
        points_raw = row[3] if row[3] is not None else 0

        rows.append({
            "id": sid.strip(),
            "title": title.strip(),
            "description": description.strip(),
            "points": int(points_raw),
        })

    wb.close()
    return rows
