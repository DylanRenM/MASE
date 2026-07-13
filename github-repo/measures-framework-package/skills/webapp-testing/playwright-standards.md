# Playwright E2E 测试 - 元素定位规范

## 定位器优先级

从高到低，严格遵守：

1. **`page.getByRole()`** — 面向用户的语义定位
   - 适用于按钮、链接、标题、导航等 ARIA 角色
   - 例：`page.getByRole('button', { name: '登录' })`

2. **`page.getByLabel()`** — 表单标签定位
   - 适用于 input/select/textarea 等表单元素
   - 例：`page.getByLabel('用户名')`

3. **`page.getByPlaceholder()`** — 输入框占位符
   - 仅当前两类不适用时使用
   - 例：`page.getByPlaceholder('请输入需求描述')`

4. **`page.getByText()`** — 可见文本匹配
   - 适用于静态文本内容
   - 例：`page.getByText('COSMIC 度量结果')`

5. **`page.getByTestId()`** — data-testid 属性
   - 仅当前 4 类无法定位时使用
   - 需要先在 HTML 中添加 `data-testid` 属性
   - 例：`page.getByTestId('metric-result-table')`

## 禁止使用的定位方式

- ❌ CSS class 选择器：`page.locator('.btn-primary')`
- ❌ CSS id 选择器：`page.locator('#submit-btn')`
- ❌ XPath：`page.locator('//button[@class="submit"]')`
- ❌ 复杂 CSS 层级：`page.locator('.container > div:nth-child(2) > button')`

## 原因

- CSS class 是样式用的，频繁变动
- CSS id 可能被 JS 框架动态修改
- 语义定位器描述的是"用户看到了什么"，天然抗 UI 重构

## 补充 data-testid

当页面确实无法通过语义定位时，在 HTML 中添加 `data-testid`：

```html
<div data-testid="metric-result-table">
  <!-- 复杂动态渲染的内容 -->
</div>
```

添加 `data-testid` 的代码变更必须与对应的测试用例在同一 PR 中提交。
