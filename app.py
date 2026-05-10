import streamlit as st
from PIL import Image
import io
import tempfile
import os

# 处理 SVG 的库
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# 新增：处理 PDF 的顶级库
import fitz  

st.set_page_config(page_title="全能文件转换工具", page_icon="🗂️")
st.title("🗂️ 全能图片与文档转换器")
st.write("支持常见图片、SVG矢量图 以及 PDF文档 相互转换。")

# 1. 增加了 "pdf" 格式的支持
uploaded_file = st.file_uploader("请选择要转换的文件", type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "svg", "pdf"])

if uploaded_file is not None:
    try:
        # 获取文件的后缀名
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        # 建立一个占位变量来存放最终读取到的图片
        img = None 

        # === 处理 PDF 逻辑 ===
        if file_extension == 'pdf':
            # 读取 PDF 文件到内存
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            total_pages = len(doc)
            
            # 如果有多页，自动出现页码选择器
            page_num = 0
            if total_pages > 1:
                st.info(f"📄 该 PDF 共有 {total_pages} 页")
                page_num = st.number_input(f"请输入要提取的页码 (1-{total_pages})", min_value=1, max_value=total_pages, value=1) - 1
            
            # 提取指定页，并设置为 300 DPI (高清画质)
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            
            # 把 PDF 页面转为处理图片用的 Image 对象
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
        
        # --- 下面的逻辑不变，负责展示和导出 ---
        if img is not None:
            st.image(img, caption="原图/当前页 预览", width=400)

            target_format = st.selectbox("请选择要导出的目标图片格式", ["PNG", "JPEG", "WEBP", "BMP"])

            if st.button("开始转换"):
                buf = io.BytesIO()
                
                # 兼容透明底转 JPG 的报错问题
                if target_format == "JPEG" and img.mode in ("RGBA", "P"):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    img = background
                
                img.save(buf, format=target_format)
                byte_im = buf.getvalue()

                st.success("🎉 转换成功！")

                st.download_button(
                    label=f"⬇️ 点击下载 {target_format} 图片",
                    data=byte_im,
                    file_name=f"converted_file.{target_format.lower()}",
                    mime=f"image/{target_format.lower()}"
                )
                
    except Exception as e:
        st.error(f"抱歉，解析文件时遇到问题。错误信息: {e}")
