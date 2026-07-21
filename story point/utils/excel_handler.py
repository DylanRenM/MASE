"""Excel 模板生成与上传解析。

使用 openpyxl 生成带数据验证的模板，解析用户上传的基线故事 Excel。
"""

import os
import tempfile
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

# 模板列名
BASELINE_HEADERS = ["ID", "故事标题", "故事描述", "验收标准", "故事点"]
BATCH_HEADERS = ["ID", "标题", "描述", "验收标准"]
BATCH_RESULT_HEADERS = ["ID", "标题", "描述", "验收标准", "估算点数", "置信下限", "置信上限", "估算依据", "风险提示"]


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
    ws.append(BASELINE_HEADERS)

    # 设置故事点列的数据验证（下拉框）——第5列(E)
    dv = DataValidation(type="list", formula1='"1,2,3,5,8,13"')
    dv.error = "请选择有效的故事点: 1, 2, 3, 5, 8, 13"
    dv.errorTitle = "无效的故事点"
    ws.add_data_validation(dv)
    dv.add("E2:E1000")

    wb.save(filepath)


def parse_upload(filepath: str) -> list[dict]:
    """解析上传的 Excel 文件。

    前置条件: filepath 指向有效的 .xlsx/.xls 文件。
    后置条件: 返回 list[dict]，每个 dict 含 id/title/description/acceptance_criteria/points。
    不变量: len(result) 等于数据行数（不含表头）。

    Args:
        filepath: Excel 文件路径。

    Returns:
        行列表，每行为 {"id": str, "title": str, "description": str, "acceptance_criteria": str, "points": int}。
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
        acceptance_criteria = str(row[3]) if len(row) > 3 and row[3] is not None else ""
        points_raw = row[4] if len(row) > 4 and row[4] is not None else 0

        rows.append({
            "id": sid.strip(),
            "title": title.strip(),
            "description": description.strip(),
            "acceptance_criteria": acceptance_criteria.strip(),
            "points": int(points_raw),
        })

    wb.close()
    return rows


# ── 批量估算 ──────────────────────────────────────

def generate_batch_template(filepath: str) -> None:
    """生成批量估算模板 Excel 文件。

    前置条件: filepath 父目录存在且可写。
    后置条件: 文件存在，含"待估算故事" sheet 和 A1:C1 表头。

    Args:
        filepath: 输出文件路径。
    """
    os.makedirs(Path(filepath).parent, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "待估算故事"
    ws.append(BATCH_HEADERS)

    # 表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4361EE", end_color="4361EE", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # 列宽
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 50
    ws.column_dimensions["D"].width = 50

    wb.save(filepath)


def parse_batch_upload(filepath: str) -> list[dict]:
    """解析批量估算上传的 Excel 文件。

    Args:
        filepath: Excel 文件路径。

    Returns:
        [{"id": str, "title": str, "description": str}, ...]
    """
    wb = load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(cell is None for cell in row):
            continue
        sid = str(row[0]).strip() if row[0] is not None else ""
        title = str(row[1]).strip() if row[1] is not None else ""
        desc = str(row[2]).strip() if row[2] is not None else ""
        ac = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""

        if not title:
            continue

        rows.append({"id": sid, "title": title, "description": desc, "acceptance_criteria": ac})

    wb.close()
    return rows


def generate_batch_result(results: list[dict]) -> str:
    """生成批量估算结果 Excel，返回临时文件路径。

    Args:
        results: [{"id":..., "title":..., "description":...,
                   "estimate":..., "confidence_min":..., "confidence_max":...,
                   "reasoning":..., "risk_notes":...}, ...]

    Returns:
        临时文件路径，调用方用完需删除。
    """
    fd, filepath = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)

    wb = Workbook()
    ws = wb.active
    ws.title = "估算结果"
    ws.append(BATCH_RESULT_HEADERS)

    # 表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4361EE", end_color="4361EE", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # 数据行
    for r in results:
        ws.append([
            r.get("id", ""),
            r.get("title", ""),
            r.get("description", ""),
            r.get("acceptance_criteria", ""),
            r.get("estimate", ""),
            r.get("confidence_min", ""),
            r.get("confidence_max", ""),
            r.get("reasoning", ""),
            r.get("risk_notes", ""),
        ])

    # 列宽
    widths = {"A": 18, "B": 28, "C": 50, "D": 50, "E": 12, "F": 10, "G": 10, "H": 45, "I": 40}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    wb.save(filepath)
    return filepath
