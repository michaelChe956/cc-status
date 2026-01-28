#!/bin/bash
# PyPI 发布脚本
set -e

echo "🚀 开始准备发布 cc-statusline 到 PyPI..."

# 1. 清理旧构建
echo "🧹 清理旧构建文件..."
rm -rf dist/ build/ *.egg-info src/*.egg-info

# 2. 构建分发包
echo "📦 构建分发包..."
python -m build

# 3. 检查分发包
echo "🔍 检查分发包质量..."
twine check dist/*

echo ""
echo "✅ 构建和检查完成！"
echo ""
echo "📝 下一步操作："
echo "   1. 发布到 TestPyPI 测试:"
echo "      twine upload --repository testpypi dist/*"
echo ""
echo "   2. 从 TestPyPI 测试安装:"
echo "      uvx --index-url https://test.pypi.org/simple/ cc-statusline --version"
echo ""
echo "   3. 正式发布到 PyPI:"
echo "      twine upload dist/*"
echo ""
echo "   4. 验证安装:"
echo "      uvx cc-statusline --version"
echo ""
