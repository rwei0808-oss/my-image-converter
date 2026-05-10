import streamlit as st
from PIL import Image
import io
import tempfile
import os

# 新增的库：专门用来把 SVG 矢量代码画成像素图片
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

# 设置网页标题
st.set_page_config(page_title="全格式图片转换工具", page_icon="🖼️")
st.title("🖼️ 极简图片格式转换工具")
st.write("支持常见图片及 SVG 格式互相转换。")

# 1. 增加了 "svg" 格式的支持
uploaded_file = st.file_uploader("请选择要转换的图片", type=["png", "jpg", "jpeg", "webp", "bmp", "gif", "svg"])

if uploaded_file is not None:
    try:
        # 判断用户上传的是不是 SVG 文件
        if uploaded_file.name.lower().endswith('.svg'):
            # SVG 需要读取真实文件，所以我们在电脑上建一个临时文件存放它
            with tempfile.NamedTemporaryFile(delete=False, suffix=".svg") as tmp_svg:
                tmp_svg.write(uploaded_file.getvalue())
                tmp_svg_path = tmp_svg.name
            
            # 第一步：把 SVG 读取为图形对象
            drawing = svg2rlg(tmp_svg_path)
            # 第二步：把图形对象渲染成 Pillow 可以看懂的像素图片 (魔法就在这一句！)
            img = renderPM.drawToPIL(drawing)
            
            # 用完后把临时文件删掉，保持电脑干净
            os.remove(tmp_svg_path)
        else:
            # 如果是普通图片，直接读取
            img = Image.open(uploaded_file)
        
        # 在网页上展示预览图
        st.image(img, caption="原图预览", width=300)

        # 2. 下拉菜单选择目标格式
        target_format = st.selectbox("请选择要转换成的目标格式", ["PNG", "JPEG", "WEBP", "BMP"])

        # 3. 转换逻辑
        if st.button("开始转换"):
            buf = io.BytesIO()
            
            # 特殊处理：如果带有透明背景的图片（如 SVG/PNG）要转成 JPEG
            if target_format == "JPEG" and img.mode in ("RGBA", "P"):
                # 创建一张和原图一样大的纯白色背景画布
                background = Image.new('RGB', img.size, (255, 255, 255))
                # 把原图贴在白底画布上 (避免透明部分变黑)
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3]) # 利用 Alpha 通道作为遮罩
                else:
                    background.paste(img)
                img = background
            
            # 将图片保存到内存中转站
            img.save(buf, format=target_format)
            byte_im = buf.getvalue()

            st.success("🎉 转换成功！请点击下方按钮下载。")

            # 4. 生成下载按钮
            st.download_button(
                label=f"⬇️ 下载 {target_format} 格式图片",
                data=byte_im,
                file_name=f"converted_image.{target_format.lower()}",
                mime=f"image/{target_format.lower()}"
            )
            
    except Exception as e:
        # 如果遇到无法解析的损坏文件，给出一个友好的错误提示
        st.error(f"抱歉，读取图片失败了。错误信息: {e}")