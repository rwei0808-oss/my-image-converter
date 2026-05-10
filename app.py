import streamlit as st
from PIL import Image
import io
import tempfile
import os

# 处理 SVG 的库
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# 处理 PDF 的库
import fitz  

st.set_page_config(page_title="全能文件转换工具", page_icon="🗂️")
st.title("🗂️ 全能图片与文档转换器")
st.write("支持常见图片、SVG矢量图 以及 PDF文档 相互转换与压缩。")

# 1. 支持上传的格式
uploaded_file = st.file_uploader("请选择要转换或压缩的文件", type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "svg", "pdf"])

if uploaded_file is not None:
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        img = None 

        # === 处理 PDF 逻辑 ===
        if file_extension == 'pdf':
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            total_pages = len(doc)
            page_num = 0
            if total_pages > 1:
                st.info(f"📄 该 PDF 共有 {total_pages} 页")
                page_num = st.number_input(f"请输入要提取的页码 (1-{total_pages})", min_value=1, max_value=total_pages, value=1) - 1
            
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # === 处理 SVG 逻辑 ===
        elif file_extension == 'svg':
            with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as tmp_svg:
                tmp_svg.write(uploaded_file.getvalue())
                tmp_svg_path = tmp_svg.name
            
            drawing = svg2rlg(tmp_svg_path)
            img = renderPM.drawToPIL(drawing)
            os.remove(tmp_svg_path)

        # === 处理普通图片逻辑 ===
        else:
            img = Image.open(uploaded_file)
        
        # --- 展示与导出逻辑 ---
        if img is not None:
            st.image(img, caption="原图/当前页 预览", width=400)

            # 使用左右两列让界面更紧凑美观
            col1, col2 = st.columns(2)
            with col1:
                # 默认把 JPEG 放在最前面，因为压缩通常用 JPEG 或 WEBP
                target_format = st.selectbox("请选择导出格式", ["JPEG", "PNG", "WEBP", "BMP"])
            with col2:
                # 【新增功能】：压缩质量滑块
                image_quality = st.slider("图片质量 (100为最高画质，越小文件越小)", min_value=1, max_value=100, value=85, step=1)

            if st.button("开始处理"):
                buf = io.BytesIO()
                
                # 兼容透明底转 JPG
                if target_format == "JPEG" and img.mode in ("RGBA", "P"):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    img = background
                
                # 【关键修改】：在这里加入了 quality 参数和 optimize 自动优化
                img.save(buf, format=target_format, quality=image_quality, optimize=True)
                byte_im = buf.getvalue()

                # 【新增功能】：计算压缩后的文件大小并显示
                file_size_kb = len(byte_im) / 1024
                st.success(f"🎉 处理成功！最终文件大小: {file_size_kb:.1f} KB")

                st.download_button(
                    label=f"⬇️ 点击下载 {target_format} 图片",
                    data=byte_im,
                    file_name=f"converted_file.{target_format.lower()}",
                    mime=f"image/{target_format.lower()}"
                )
                
    except Exception as e:
        st.error(f"抱歉，解析文件时遇到问题。错误信息: {e}")
