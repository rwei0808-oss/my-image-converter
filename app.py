import streamlit as st
from PIL import Image
import io
import tempfile
import os
import subprocess

# 处理 SVG 的库
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# 处理 PDF 的库
import fitz  

st.set_page_config(page_title="全能办公神器", page_icon="🧰", layout="centered")

st.title("🧰 个人专属全能转换器")
st.write("请在下方选择你需要使用的工具：")

# ==========================================
# 🌟 核心布局：创建四个顶部选项卡
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🔄 图片格式转换", "🗜️ 图片极限压缩", "📄 Word 转 PDF", "🧩 多图长图拼接"])

# ==========================================
# 工具一：图片格式互换 (Tab 1)
# ==========================================
with tab1:
    st.subheader("支持常见图片、SVG及PDF提取")
    file_convert = st.file_uploader("请上传要转换的文件", type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "svg", "pdf"], key="upload_convert")
    
    if file_convert:
        try:
            ext = file_convert.name.lower().split('.')[-1]
            img = None
            
            if ext == 'pdf':
                doc = fitz.open(stream=file_convert.read(), filetype="pdf")
                if len(doc) > 1:
                    page_num = st.number_input("提取第几页？", min_value=1, max_value=len(doc), value=1, key="pdf_page") - 1
                else:
                    page_num = 0
                pix = doc.load_page(page_num).get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            elif ext == 'svg':
                with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as tmp_svg:
                    tmp_svg.write(file_convert.getvalue())
                    tmp_svg_path = tmp_svg.name
                img = renderPM.drawToPIL(svg2rlg(tmp_svg_path))
                os.remove(tmp_svg_path)
            else:
                img = Image.open(file_convert)

            if img:
                st.image(img, caption="预览", width=300)
                target_fmt = st.selectbox("导出格式", ["JPEG", "PNG", "WEBP", "BMP"], key="fmt_convert")
                
                if st.button("开始转换", key="btn_convert"):
                    buf = io.BytesIO()
                    if target_fmt == "JPEG" and img.mode in ("RGBA", "P"):
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        bg.paste(img, mask=img.split()[3]) if img.mode == 'RGBA' else bg.paste(img)
                        img = bg
                    
                    img.save(buf, format=target_fmt)
                    st.success("🎉 转换成功！")
                    st.download_button("⬇️ 下载转换后的图片", data=buf.getvalue(), file_name=f"converted.{target_fmt.lower()}", mime=f"image/{target_fmt.lower()}")
        except Exception as e:
            st.error(f"解析失败: {e}")

# ==========================================
# 工具二：图片极限压缩 (Tab 2)
# ==========================================
with tab2:
    st.subheader("在保持画质的前提下缩小文件体积")
    file_compress = st.file_uploader("请上传要压缩的图片", type=["png", "jpg", "jpeg", "webp", "bmp"], key="upload_compress")
    
    if file_compress:
        try:
            orig_size_kb = len(file_compress.getvalue()) / 1024
            st.info(f"📁 原始文件大小: **{orig_size_kb:.1f} KB**")
            
            img_c = Image.open(file_compress)
            st.image(img_c, caption="原图预览", width=300)
            
            quality = st.slider("压缩质量 (越小文件越小，推荐 60-80)", 1, 100, 75, key="slider_compress")
            
            if st.button("开始压缩", key="btn_compress"):
                buf_c = io.BytesIO()
                
                if img_c.mode in ("RGBA", "P"):
                    bg = Image.new('RGB', img_c.size, (255, 255, 255))
                    bg.paste(img_c, mask=img_c.split()[3]) if img_c.mode == 'RGBA' else bg.paste(img_c)
                    img_c = bg
                
                img_c.save(buf_c, format="JPEG", quality=quality, optimize=True)
                new_size_kb = len(buf_c.getvalue()) / 1024
                
                st.success(f"🎉 压缩完成！新文件大小: **{new_size_kb:.1f} KB** (缩小了 {((orig_size_kb - new_size_kb)/orig_size_kb*100):.1f}%)")
                st.download_button("⬇️ 下载压缩后的图片", data=buf_c.getvalue(), file_name="compressed.jpg", mime="image/jpeg")
        except Exception as e:
            st.error(f"处理失败: {e}")

# ==========================================
# 工具三：Word 转 PDF (Tab 3)
# ==========================================
with tab3:
    st.subheader("拒绝充值会员，免费本地引擎转换")
    file_word = st.file_uploader("请上传 Word 文档", type=["doc", "docx"], key="upload_word")
    
    if file_word:
        if st.button("🚀 开始生成 PDF", key="btn_word"):
            with st.spinner("⏳ 正在调用底层开源引擎排版中，请稍候..."):
                ext_w = file_word.name.lower().split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext_w}") as tmp_in:
                    tmp_in.write(file_word.getvalue())
                    in_path = tmp_in.name
                
                out_dir = os.path.dirname(in_path)
                out_path = in_path.rsplit('.', 1)[0] + ".pdf"
                
                subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", in_path, "--outdir", out_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if os.path.exists(out_path):
                    with open(out_path, "rb") as f:
                        st.success("🎉 Word 成功转换为 PDF！")
                        st.download_button("⬇️ 下载 PDF 文件", data=f.read(), file_name=f"{file_word.name.rsplit('.', 1)[0]}.pdf", mime="application/pdf")
                    os.remove(out_path)
                else:
                    st.error("转换失败，请检查文档是否损坏。")
                os.remove(in_path)

# ==========================================
# 🌟 【全新】工具四：多图拼接 (Tab 4)
# ==========================================
with tab4:
    st.subheader("将多张图片无缝拼成一张图")
    # 注意这里加入了 accept_multiple_files=True，允许一次选中多张图！
    uploaded_images = st.file_uploader("请选择多张图片 (按住 Ctrl 可多选)", type=["png", "jpg", "jpeg", "webp", "bmp"], accept_multiple_files=True, key="upload_merge")

    if uploaded_images:
        # 将上传的文件打包成字典，方便提取
        file_dict = {file.name: file for file in uploaded_images}
        
        st.info("💡 **调整顺序提示：** 下方的框内是你上传的图片。你可以把它们叉掉，然后**按照你期望的顺序重新点击选中**。先选的在上面/左边！")
        
        # 利用 multiselect 巧妙实现排序功能
        selected_order = st.multiselect("请确认拼接顺序：", options=list(file_dict.keys()), default=list(file_dict.keys()), key="merge_order")

        if selected_order:
            # 实时预览排列顺序
            cols = st.columns(min(len(selected_order), 5)) # 最多展示5列微缩图
            for i, fname in enumerate(selected_order):
                with cols[i % 5]:
                    st.image(Image.open(file_dict[fname]), caption=f"第 {i+1} 张", use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                merge_direction = st.radio("选择拼接方向：", ["⬇️ 垂直拼接 (长图)", "➡️ 水平拼接 (横图)"])
            with col2:
                target_fmt_merge = st.selectbox("导出格式", ["JPEG", "PNG"], key="fmt_merge")

            if st.button("🚀 开始拼接", key="btn_merge"):
                with st.spinner("正在绘制长图..."):
                    # 读取用户选好顺序的图片
                    images = [Image.open(file_dict[fname]) for fname in selected_order]

                    if "垂直" in merge_direction:
                        # 计算画布大小：最宽的宽度，高度的总和
                        max_width = max(img.size[0] for img in images)
                        total_height = sum(img.size[1] for img in images)
                        merged_img = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))

                        # 逐个贴上去
                        y_offset = 0
                        for img in images:
                            merged_img.paste(img, (0, y_offset))
                            y_offset += img.size[1]
                    else:
                        # 计算画布大小：宽度的总和，最高的高度
                        total_width = sum(img.size[0] for img in images)
                        max_height = max(img.size[1] for img in images)
                        merged_img = Image.new('RGB', (total_width, max_height), color=(255, 255, 255))

                        x_offset = 0
                        for img in images:
                            merged_img.paste(img, (x_offset, 0))
                            x_offset += img.size[0]

                    # 导出和下载
                    buf_m = io.BytesIO()
                    merged_img.save(buf_m, format=target_fmt_merge, quality=90)
                    
                    st.success("🎉 拼图成功！")
                    # 展示最终结果
                    st.image(merged_img, caption="拼接结果预览", use_container_width=True)
                    
                    st.download_button(
                        label="⬇️ 下载拼接好的图片", 
                        data=buf_m.getvalue(), 
                        file_name=f"merged_image.{target_fmt_merge.lower()}", 
                        mime=f"image/{target_fmt_merge.lower()}"
                    )
