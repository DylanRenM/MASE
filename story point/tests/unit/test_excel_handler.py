"""Excel 模板生成与解析测试。"""

import os
import tempfile

import pytest
from openpyxl import load_workbook

from utils.excel_handler import generate_template, parse_upload


class TestGenerateTemplate:
    """generate_template 测试。"""

    def test_creates_file_with_correct_headers(self):
        """生成的文件包含正确的4列表头。"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            filepath = f.name

        try:
            generate_template(filepath)
            assert os.path.exists(filepath)

            wb = load_workbook(filepath)
            ws = wb.active
            assert ws.title == "基准故事"

            headers = [ws.cell(1, col).value for col in range(1, 6)]
            assert headers == ["ID", "故事标题", "故事描述", "验收标准", "故事点"]
        finally:
            os.unlink(filepath)

    def test_points_column_has_data_validation(self):
        """故事点列 (E) 有数据验证下拉框。"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            filepath = f.name

        try:
            generate_template(filepath)
            wb = load_workbook(filepath)
            ws = wb.active

            # openpyxl 的数据验证存在 ws.data_validations 中
            validations = list(ws.data_validations.dataValidation)
            assert len(validations) >= 1

            dv = validations[0]
            assert dv.type == "list"
            assert "E" in str(dv.sqref)  # 校验应用于 E 列
        finally:
            os.unlink(filepath)


class TestParseUpload:
    """parse_upload 测试。"""

    def test_parses_all_rows_correctly(self):
        """正确解析所有数据行。"""
        filepath = _create_test_excel([
            ("S1", "修改Logo", "替换公司Logo", "页面展示Logo", 1),
            ("S2", "邮箱校验", "前端校验邮箱格式", "输入合法邮箱通过", 2),
            ("S3", "导出Excel", "含查询接口", "导出1000条数据", 5),
        ])

        try:
            rows = parse_upload(filepath)
            assert len(rows) == 3
            assert rows[0]["id"] == "S1"
            assert rows[0]["title"] == "修改Logo"
            assert rows[0]["description"] == "替换公司Logo"
            assert rows[0]["points"] == 1
            assert rows[2]["points"] == 5
        finally:
            os.unlink(filepath)

    def test_empty_file_returns_empty_list(self):
        """空文件（仅表头）返回空列表。"""
        filepath = _create_test_excel([])

        try:
            rows = parse_upload(filepath)
            assert rows == []
        finally:
            os.unlink(filepath)

    def test_parses_float_points_as_int(self):
        """浮点型故事点应该被转为 int。"""
        filepath = _create_test_excel([
            ("S1", "test", "desc", "", 3),
        ])

        try:
            rows = parse_upload(filepath)
            assert isinstance(rows[0]["points"], int)
        finally:
            os.unlink(filepath)


# ── helpers ──────────────────────────────────────────

def _create_test_excel(rows: list[tuple[str, str, str, str, int]]) -> str:
    """创建测试用 Excel 文件并返回路径。"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "故事标题", "故事描述", "验收标准", "故事点"])
    for row in rows:
        ws.append(list(row))

    filepath = tempfile.mktemp(suffix=".xlsx")
    wb.save(filepath)
    return filepath
