#!/usr/bin/env python3
"""
图片处理助手 - E-commerce API MCP Server

帮助用户将图片文件转换为Base64编码，用于MCP图片上传
"""

import base64
import mimetypes
import os
import sys
from pathlib import Path


def get_mime_type(file_path):
    """获取文件的MIME类型"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def encode_image_to_base64(image_path):
    """将图片文件编码为Base64"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        raise Exception(f"编码图片失败: {str(e)}")


def validate_image_file(file_path):
    """验证图片文件"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检查文件大小（限制为5MB）
    file_size = os.path.getsize(file_path)
    max_size = 5 * 1024 * 1024  # 5MB
    
    if file_size > max_size:
        raise ValueError(f"文件太大: {file_size / 1024 / 1024:.2f}MB，最大允许5MB")
    
    # 检查文件扩展名
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise ValueError(f"不支持的文件格式: {file_extension}，支持的格式: {', '.join(allowed_extensions)}")
    
    return True


def process_image(image_path):
    """处理单个图片文件"""
    try:
        # 验证文件
        validate_image_file(image_path)
        
        # 获取文件信息
        file_path = Path(image_path)
        filename = file_path.name
        mime_type = get_mime_type(image_path)
        file_size = os.path.getsize(image_path)
        
        # 编码为Base64
        base64_content = encode_image_to_base64(image_path)
        
        return {
            "filename": filename,
            "content": base64_content,
            "mime_type": mime_type,
            "original_size": file_size,
            "base64_size": len(base64_content)
        }
        
    except Exception as e:
        return {"error": str(e)}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🖼️  E-commerce API - 图片处理助手")
        print()
        print("用法:")
        print("  python image_helper.py <图片文件路径> [输出文件]")
        print()
        print("示例:")
        print("  python image_helper.py product.jpg")
        print("  python image_helper.py product.jpg base64_output.txt")
        print()
        print("支持的格式: .jpg, .jpeg, .png, .gif, .webp")
        print("最大文件大小: 5MB")
        return
    
    image_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🔄 处理图片: {image_path}")
    
    # 处理图片
    result = process_image(image_path)
    
    if "error" in result:
        print(f"❌ 处理失败: {result['error']}")
        return
    
    # 显示信息
    print(f"✅ 处理成功!")
    print(f"   文件名: {result['filename']}")
    print(f"   MIME类型: {result['mime_type']}")
    print(f"   原始大小: {result['original_size']} 字节")
    print(f"   Base64大小: {result['base64_size']} 字符")
    
    # 输出Base64内容
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            print(f"💾 Base64内容已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
    else:
        print()
        print("📋 Base64编码内容 (复制以下内容用于MCP上传):")
        print("=" * 50)
        print(result['content'][:100] + "..." if len(result['content']) > 100 else result['content'])
        print("=" * 50)
        
        # 生成MCP工具调用示例
        print()
        print("🛠️  MCP工具调用示例:")
        print("=" * 50)
        print(f"""使用upload_product_images工具上传图片:
- product_id: <产品ID>
- images: [
    {{
        "filename": "{result['filename']}",
        "content": "{result['content'][:50]}...",
        "mime_type": "{result['mime_type']}"
    }}
]""")
        print("=" * 50)


if __name__ == "__main__":
    main()