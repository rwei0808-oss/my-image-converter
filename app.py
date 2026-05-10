import streamlit as st
from PIL import Image
import io
import tempfile
import os
import subprocess  # 新增：用来在后台悄悄调用 LibreOffice 引擎

# 处理 SVG 的库
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# 处理 PDF 的库
import fitz  

st.set_page_config(page_title="全能文件转换工具", page_icon="🗂️")
st.title("🗂️ 个人专属全能转换器")
st.write("支持图片处理、SVG转换、PDF提取，以及 **Word 转 PDF（永久免费，拒绝会员！）**")

# 1. 在支持列表中加入了 doc 和 docx
uploaded_file = st.file_uploader("请选择要处理的文件", type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "svg", "pdf", "doc", "docx"])

if uploaded_file is not None:
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        img = None 

        # ==========================================
        # 🌟 【全新功能】处理 Word (.doc / .docx) 转 PDF
        # ==========================================
        if file_extension in ['doc', 'docx']:
            st.info("📄 识别到 Word 文档，准备执行 PDF 转换...")
            
            # 因为转换 Word 比较耗时，给用户一个加载提示
            with st.spinner("⏳ 正在调用底层开源引擎排版中，请稍候（耗时取决于文档大小）..."):
                # 把用户上传的 Word 保存到临时文件夹
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_in:
                    tmp_in.write(uploaded_file.getvalue())
                    in_path = tmp_in.name
                
                # 设置导出的 PDF 路径
                out_dir = os.path.dirname(in_path)
                out_path = in_path.rsplit('.', 1)[0] + ".pdf"
                
                # 核心魔法：在后台运行 LibreOffice 命令进行转换
                subprocess.run(
                    ["libreoffice", "--headless", "--convert-to", "pdf", in_path, "--outdir", out_dir],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                
                # 检查是否成功生成了 PDF
                if os.path.exists(out_path):
                    with open(out_path, "rb") as f:
                        byte_pdf = f.read()
                    
                    st.success("🎉 Word 成功转换为 PDF！成功省下了一个 WPS 会员！")
                    
                    st.download_button(
                        label="⬇️ 点击下载 PDF 文件",
                        data=byte_pdf,
                        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}.pdf",
                        mime="application/pdf"
                    )
                    # 转换完把临时文件删掉，释放服务器空间
                    os.remove(out_path)
                else:
                    st.error("转换失败，请检查文档是否损坏或包含无法识别的宏。")
                os.remove(in_path)


        # ==========================================
        # 以下是之前写好的：PDF 提取、SVG 转换、图片压缩
        # ==========================================
        elif file_extension == 'pdf':
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            total_pages = len(doc)
            page_num = 0
            if total_pages > 1:
                st.info(f"📄 该 PDF 共有 {total_pages} 页")
                page_num = st.number_input(f"请输入要转为图片的页码 (1-{total_pages})", min_value=1, max_value=total_pages, value=1) - 1
            
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        elif file_extension == 'svg':
            with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as tmp_svg:
                tmp_svg.write(uploaded_file.getvalue())
                tmp_svg_path = tmp_svg.name
            
            drawing = svg2rlg(tmp_svg_path)
            img = renderPM.drawToPIL(drawing)
            os.remove(tmp_svg_path)

        else:
            img = Image.open(uploaded_file)
        
        # --- 图片展示与导出逻辑 ---
        if img is not None:
            st.image(img, caption="图片预览", width=400)

            col1, col2 = st.columns(2)
            with col1:
                target_format = st.selectbox("请选择导出格式", ["JPEG", "PNG", "WEBP", "BMP"])
            with col2:
                image_quality = st.slider("图片质量 (越小文件越小)", min_value=1, max_value=100, value=85, step=1)

            if st.button("开始处理图片"):
                buf = io.BytesIO()
                
                if target_format == "JPEG" and img.mode in ("RGBA", "P"):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    img = background
                
                img.save(buf, format=target_format, quality=image_quality, optimize=True)
                byte_im = buf.getvalue()

                file_size_kb = len(byte_im) / 1024
                st.success(f"🎉 图片处理成功！最终文件大小: {file_size_kb:.1f} KB")

                st.download_button(
                    label=f"⬇️ 点击下载 {target_format} 图片",
                    data=byte_im,
                    file_name=f"converted_image.{target_format.lower()}",
                    mime=f"image/{target_format.lower()}"
                )
                
    except Exception as e:
        st.error(f"抱歉，解析文件时遇到问题。错误信息: {e}")
