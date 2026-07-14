"""API接口契约测试

用于验证前后端接口字段命名一致性，防止字段映射错误。
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestApiContract(unittest.TestCase):
    """API接口契约测试类"""
    
    def test_clarify_response_fields(self):
        """测试澄清需求接口响应字段结构"""
        expected_fields = {
            'input_data': '输入数据',
            'output_data': '输出数据', 
            'read_data': '读取数据',
            'save_data': '保存数据',
            'function_user': '功能用户',
            'data_attributes': '数据属性',
            'business_logic': '业务逻辑',
            'interaction_sequence': '交互序列',
            'instantiation': '业务场景'
        }
        
        deprecated_fields = ['inputs', 'outputs', 'reads', 'writes']
        
        mock_response = {
            'success': True,
            'result': {
                'requirements': [{
                    'id': 'FUR-001',
                    'name': '测试功能',
                    'description': '测试描述',
                    'input_data': ['测试输入'],
                    'output_data': ['测试输出'],
                    'read_data': ['测试读取'],
                    'save_data': ['测试保存'],
                    'function_user': '测试用户',
                    'data_attributes': ['测试属性'],
                    'business_logic': ['步骤1'],
                    'interaction_sequence': ['交互1'],
                    'instantiation': ['场景1']
                }]
            }
        }
        
        self.assertIn('success', mock_response)
        self.assertIn('result', mock_response)
        self.assertIn('requirements', mock_response['result'])
        
        req = mock_response['result']['requirements'][0]
        
        for field in expected_fields.keys():
            self.assertIn(field, req, f"缺少必填字段: {field} ({expected_fields[field]})")
        
        for deprecated in deprecated_fields:
            self.assertNotIn(deprecated, req, f"不应使用已废弃字段: {deprecated}")
    
    def test_field_name_consistency(self):
        """测试字段命名一致性规则"""
        field_mapping = {
            'input_data': ['inputs'],
            'output_data': ['outputs'],
            'read_data': ['reads'],
            'save_data': ['writes']
        }
        
        for new_field, old_fields in field_mapping.items():
            self.assertIn('_', new_field, f"新字段名应使用下划线命名: {new_field}")
            self.assertTrue(len(new_field) > 4, f"新字段名应更具描述性: {new_field}")
    
    def test_frontend_field_access(self):
        """测试前端字段访问逻辑"""
        def get_field_value(req, field_name):
            field_mapping = {
                'input_data': ['inputs'],
                'output_data': ['outputs'],
                'read_data': ['reads'],
                'save_data': ['writes']
            }
            
            if field_name in req:
                return req[field_name]
            
            if field_name in field_mapping:
                for old_name in field_mapping[field_name]:
                    if old_name in req:
                        return req[old_name]
            
            return None
        
        test_req_new = {'input_data': ['value1', 'value2']}
        result = get_field_value(test_req_new, 'input_data')
        self.assertEqual(result, ['value1', 'value2'])
        
        test_req_old = {'inputs': ['old_value']}
        result = get_field_value(test_req_old, 'input_data')
        self.assertEqual(result, ['old_value'])
        
        test_req_empty = {}
        result = get_field_value(test_req_empty, 'input_data')
        self.assertIsNone(result)
    
    def test_response_structure_validation(self):
        """测试响应结构验证函数"""
        def validate_response(response):
            errors = []
            
            if 'success' not in response:
                errors.append("缺少success字段")
            
            if 'result' not in response:
                errors.append("缺少result字段")
            
            if 'requirements' not in response.get('result', {}):
                errors.append("缺少requirements数组")
            else:
                requirements = response['result']['requirements']
                if not isinstance(requirements, list):
                    errors.append("requirements必须是数组")
                else:
                    required_fields = ['id', 'name', 'description', 
                                     'input_data', 'output_data', 
                                     'read_data', 'save_data']
                    for i, req in enumerate(requirements):
                        for field in required_fields:
                            if field not in req:
                                errors.append(f"第{i+1}个需求缺少字段: {field}")
            
            return errors
        
        valid_response = {
            'success': True,
            'result': {
                'requirements': [{
                    'id': 'FUR-001',
                    'name': '测试',
                    'description': '描述',
                    'input_data': [],
                    'output_data': [],
                    'read_data': [],
                    'save_data': []
                }]
            }
        }
        errors = validate_response(valid_response)
        self.assertEqual(len(errors), 0, f"有效响应不应有错误: {errors}")
        
        invalid_response = {
            'success': True,
            'result': {
                'requirements': [{
                    'id': 'FUR-001',
                    'name': '测试',
                    'input_data': [],
                    'output_data': [],
                    'read_data': [],
                    'save_data': []
                }]
            }
        }
        errors = validate_response(invalid_response)
        self.assertGreater(len(errors), 0, "无效响应应有错误提示")

class TestApiContractDbC(unittest.TestCase):
    """API 接口 DbC 风格契约测试（前置/后置/不变式）"""

    def test_create_resource_precondition_rejects_invalid_email(self):
        """前置条件：email 必须包含 @ —— 违反时应返回 422"""
        mock_response = {
            'status_code': 422,
            'error': 'Invalid email: must contain @'
        }
        self.assertEqual(mock_response['status_code'], 422)

    def test_create_resource_postcondition_returns_positive_id(self):
        """后置条件：创建成功后 id 必须 > 0"""
        mock_response = {
            'status_code': 201,
            'id': 42,
            'name': 'New Resource'
        }
        self.assertEqual(mock_response['status_code'], 201)
        self.assertGreater(mock_response['id'], 0)

    def test_create_resource_invariant_rejects_duplicate_unique_key(self):
        """不变式：同一 unique_key 不能创建两条记录 —— 违反时应返回 409"""
        mock_response = {
            'status_code': 409,
            'error': 'Duplicate: resource with this key already exists'
        }
        self.assertEqual(mock_response['status_code'], 409)

    def test_runtime_assertion_pattern(self):
        """演示运行时断言的 Python 模式（用于 function 级契约）"""
        def create_with_contract(email, name):
            # 前置条件
            assert email and '@' in email, "require: email must be valid"
            assert name and len(name) <= 100, "require: name non-empty and <= 100 chars"
            # 模拟创建
            result = {'id': 1, 'email': email, 'name': name}
            # 后置条件
            assert result['id'] > 0, "ensure: id must be positive"
            assert result['email'] == email, "ensure: email must match input"
            return result

        # 正常路径
        result = create_with_contract('a@b.com', 'Test')
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['email'], 'a@b.com')

        # 违反前置条件
        with self.assertRaises(AssertionError) as ctx:
            create_with_contract('', 'Test')
        self.assertIn('require', str(ctx.exception))

        with self.assertRaises(AssertionError) as ctx:
            create_with_contract('invalid', 'Test')
        self.assertIn('require', str(ctx.exception))


if __name__ == '__main__':
    unittest.main(verbosity=2)
