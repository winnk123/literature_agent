#!/bin/bash
# ⚠️ 正式上线前使用：删除 UI 风格切换器的开发代码
# 使用方法：./remove-dev-ui-switcher.sh

echo "⚠️  准备删除 UI 风格切换器的开发代码..."
echo ""

# 备份文件
echo "📦 创建备份..."
cp index.html index.html.backup
cp app.js app.js.backup
cp styles.css styles.css.backup

echo "✅ 备份完成"
echo ""

# 删除 HTML 中的 UI 风格切换按钮和面板
echo "🗑️  删除 index.html 中的 UI 风格切换代码..."
# 删除按钮（3个）
sed -i '' '/<!-- ⚠️ 开发模式：UI风格切换器（正式上线前请删除） -->/,/<\/button>/d' index.html
# 删除面板
sed -i '' '/<!-- ⚠️ 开发模式：UI风格切换面板（正式上线前请删除） -->/,/<\/div>/d' index.html

echo "✅ index.html 清理完成"
echo ""

# 删除 JavaScript 中的 UI 风格切换器代码
echo "🗑️  删除 app.js 中的 UI 风格切换器代码..."
# 使用 Python 脚本更精确地删除（因为 sed 处理多行注释可能有问题）
python3 << 'EOF'
import re

with open('app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除 UI 风格切换器函数（从注释开始到函数结束）
pattern = r'  // ⚠️ 开发模式：UI风格切换器.*?  \}\(\)\);'
content = re.sub(pattern, '', content, flags=re.DOTALL)

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app.js 清理完成")
EOF

echo ""

# 删除 CSS 中的 UI 风格面板样式
echo "🗑️  删除 styles.css 中的 UI 风格面板样式..."
# 删除从注释开始到下一个主要样式块之前的所有内容
sed -i '' '/\/\* ⚠️ 开发模式：UI风格切换面板样式/,/^\.view { display: none/d' styles.css

echo "✅ styles.css 清理完成"
echo ""

echo "✨ 清理完成！"
echo ""
echo "📋 请检查以下内容："
echo "   1. 刷新浏览器测试功能是否正常"
echo "   2. 检查是否还有遗漏的开发代码"
echo "   3. 如果不需要硬朗风格，可以删除 styles-ui-hard.css"
echo ""
echo "💾 备份文件："
echo "   - index.html.backup"
echo "   - app.js.backup"
echo "   - styles.css.backup"

