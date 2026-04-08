# app.py - 本能论Web系统主程序

import streamlit as st
from PIL import Image

# 导入模块
from config import init_database, get_api_keys, INSTINCT_SYSTEMS
from database import init_database as init_db, create_user, get_all_users, delete_user, update_user_role
from auth import login, logout, is_logged_in, is_admin, get_current_user
from multimodal import full_multimodal_analysis, preprocess_image

# 初始化
init_db()

# 页面配置
st.set_page_config(
    page_title="中医本能论智能诊疗系统",
    page_icon="🏥",
    layout="wide"
)

# ========== 登录/注册页面 ==========
def show_login_register_page():
    """登录注册页面（同一界面）"""
    st.title("🏥 中医本能论智能诊疗系统")
    st.markdown("*基于《生命本能系统论》与多模态AI*")
    st.markdown("---")
    
    # 使用tabs在同一页面切换
    tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册新账号"])
    
    # ===== 登录 =====
    with tab_login:
        st.subheader("用户登录")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            login_username = st.text_input("用户名", key="login_user")
            login_password = st.text_input("密码", type="password", key="login_pass")
            
            if st.button("登录", type="primary", use_container_width=True):
                if login(login_username, login_password):
                    st.success(f"欢迎回来，{st.session_state['name']}！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
        
        with col2:
            st.info("""
            **默认管理员账号**
            - 用户名：`admin`
            - 密码：`admin123`
            
            首次使用请先注册
            """)
    
    # ===== 注册 =====
    with tab_register:
        st.subheader("新用户注册")
        
        reg_username = st.text_input("用户名*", key="reg_user", 
                                    help="建议使用字母+数字组合")
        reg_password = st.text_input("密码*", type="password", key="reg_pass",
                                    help="至少6位字符")
        reg_password2 = st.text_input("确认密码*", type="password", key="reg_pass2")
        reg_name = st.text_input("显示名称*", key="reg_name", 
                                help="例如：张三")
        reg_email = st.text_input("邮箱（选填）", key="reg_email")
        
        if st.button("立即注册", type="primary", use_container_width=True):
            # 验证
            if not all([reg_username, reg_password, reg_name]):
                st.error("请填写所有必填项（带*号）")
            elif reg_password != reg_password2:
                st.error("两次密码不一致")
            elif len(reg_password) < 6:
                st.error("密码长度至少6位")
            else:
                success, msg = create_user(reg_username, reg_password, reg_name, reg_email)
                if success:
                    st.success(f"✅ {msg}！请切换到登录页登录")
                else:
                    st.error(f"❌ {msg}")

# ========== 管理员页面 ==========
def show_admin_page():
    """管理员用户管理页面"""
    st.title("👤 用户管理（管理员）")
    st.markdown("---")
    
    # 显示当前管理员
    user = get_current_user()
    st.info(f"当前管理员：**{user['name']}**（{user['username']}）")
    
    # 获取所有用户
    users = get_all_users()
    
    st.subheader(f"注册用户列表（共 {len(users)} 人）")
    
    if users:
        # 表头
        cols = st.columns([0.5, 1.5, 1.5, 2, 1, 1.5, 1.5])
        headers = ["ID", "用户名", "显示名", "邮箱", "角色", "注册时间", "操作"]
        for col, header in zip(cols, headers):
            col.write(f"**{header}**")
        
        # 用户列表
        for user_data in users:
            user_id, username, name, email, role, created_at, last_login = user_data
            
            cols = st.columns([0.5, 1.5, 1.5, 2, 1, 1.5, 1.5])
            cols[0].write(user_id)
            cols[1].write(username)
            cols[2].write(name)
            cols[3].write(email or "-")
            cols[4].write("🔴 管理员" if role == "admin" else "🟢 用户")
            cols[5].write(created_at[:10] if created_at else "-")
            
            # 操作按钮
            with cols[6]:
                # 不能操作自己
                if username != user['username']:
                    col_del, col_role = st.columns(2)
                    with col_del:
                        if st.button("删除", key=f"del_{user_id}"):
                            delete_user(user_id)
                            st.success("已删除")
                            st.rerun()
                    with col_role:
                        new_role = "user" if role == "admin" else "admin"
                        btn_text = "降为用户" if role == "admin" else "升为管理员"
                        if st.button(btn_text, key=f"role_{user_id}"):
                            update_user_role(user_id, new_role)
                            st.success("已修改")
                            st.rerun()
                else:
                    st.caption("当前用户")
    else:
        st.info("暂无用户数据")
    
    st.markdown("---")
    if st.button("← 返回主界面", use_container_width=True):
        st.session_state['show_admin'] = False
        st.rerun()

# ========== 多模态本能论诊断页面 ==========
def show_multimodal_diagnosis():
    """多模态本能论诊断页面"""
    st.header("🔬 本能系统多模态诊断")
    st.markdown("*上传舌象图片，AI结合《生命本能系统论》进行智能分析*")
    st.markdown("---")
    
    # 获取API Key
    api_keys = get_api_keys()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 舌象采集")
        
        # 图片上传
        uploaded_file = st.file_uploader(
            "请上传清晰的舌象照片",
            type=['jpg', 'jpeg', 'png'],
            help="建议在自然光下拍摄，避免使用滤镜"
        )
        
        # 拍摄指南
        with st.expander("📖 拍摄指南"):
            st.markdown("""
            **拍摄要求：**
            1. 在自然光或白色光源下拍摄
            2. 舌头自然伸出，不要用力
            3. 包含舌尖、舌中、舌根
            4. 避免使用美颜/滤镜
            5. 图片清晰，光线均匀
            """)
        
        image = None
        if uploaded_file:
            image = preprocess_image(uploaded_file)
            st.image(image, caption="上传的舌象图片", use_column_width=True)
    
    with col2:
        st.subheader("📝 症状补充（选填）")
        
        # 常用症状选择
        common_symptoms = [
            "发热", "怕冷", "头疼", "咳嗽", 
            "胸闷", "气短", "心慌", "失眠",
            "腹疼", "便秘", "腹泻", "没食欲",
            "口渴", "口苦", "口干", "疲劳"
        ]
        
        selected_symptoms = st.multiselect("选择症状", common_symptoms)
        custom_symptoms = st.text_input("或手动输入：", placeholder="例如：头疼 口渴 失眠")
        
        # 合并症状
        all_text_symptoms = selected_symptoms + (custom_symptoms.split() if custom_symptoms else [])
        
        if all_text_symptoms:
            st.info(f"已选症状：{'、'.join(all_text_symptoms)}")
    
    # 分析按钮
    st.markdown("---")
    analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
    with analyze_col2:
        if st.button("🔍 开始本能系统分析", type="primary", use_container_width=True):
            if not uploaded_file:
                st.error("请先上传舌象图片")
            elif not api_keys.get("dashscope_key"):
                st.error("未配置通义千问API Key，请联系管理员")
            else:
                with st.spinner("🤖 AI正在分析舌象并映射本能系统..."):
                    result = full_multimodal_analysis(
                        image, 
                        all_text_symptoms or None,
                        api_keys["dashscope_key"]
                    )
                    
                    if result["success"]:
                        st.session_state['analysis_result'] = result
                        st.success("✅ 分析完成！")
                    else:
                        st.error(f"分析失败：{result.get('error', '未知错误')}")
    
    # 显示分析结果
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        st.markdown("---")
        st.subheader("🧬 本能系统诊断结果")
        
        # 三列布局显示
        col_res1, col_res2, col_res3 = st.columns(3)
        
        with col_res1:
            st.markdown("### 📊 识别的舌象特征")
            for feature in result["tongue_features"]:
                st.markdown(f"- ✅ {feature}")
        
        with col_res2:
            st.markdown("### 🧠 涉及的本能系统")
            for system in result["instinct_systems"]:
                with st.container():
                    st.markdown(f"**{system['name']}**")
                    st.caption(system['description'][:30] + "...")
        
        with col_res3:
            st.markdown("### 💊 推荐方剂")
            for p in result["prescriptions"][:5]:
                st.markdown(f"- {p}")
        
        # 详细报告
        with st.expander("📄 查看完整《生命本能系统论》诊断报告", expanded=True):
            st.markdown(result["report"])
        
        # 知识图谱验证
        st.markdown("---")
        st.subheader("🔗 知识图谱验证")
        st.info("将本能系统分析结果与Neo4j知识图谱进行交叉验证...")
        
        # 这里可以添加Neo4j查询代码
        # 根据result["all_symptoms"]查询疾病和方剂

# ========== 主页面（登录后）==========
def show_main_page():
    """主页面"""
    # 侧边栏
    user = get_current_user()
    st.sidebar.markdown(f"👤 **{user['name']}**")
    st.sidebar.caption(f"角色：{'管理员' if is_admin() else '普通用户'}")
    st.sidebar.markdown("---")
    
    # 管理员入口
    if is_admin():
        if st.sidebar.button("🔧 用户管理", use_container_width=True):
            st.session_state['show_admin'] = True
            st.rerun()
        st.sidebar.markdown("---")
    
    # 退出
    if st.sidebar.button("🚪 退出登录", use_container_width=True):
        logout()
        st.rerun()
    
    # 主菜单
    menu = st.sidebar.radio(
        "功能菜单",
        ["🏠 首页", "🔬 本能系统诊断", "💊 方剂查询", "💬 智能问答"]
    )
    
    if menu == "🏠 首页":
        st.title("🏥 中医本能论智能诊疗系统")
        st.markdown("*基于郭生白《生命本能系统论》构建*")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("本能系统", "10大系统")
        col2.metric("方剂", "60+")
        col3.metric("疾病", "30+")
        
        st.info("""
        ### 🎯 系统特色
        
        本系统基于**郭生白《生命本能系统论》**，融合多模态AI技术：
        
        1. **🔬 本能系统诊断** - 上传舌象，AI识别并映射到十大本能系统
        2. **💊 方剂推荐** - 根据本能系统状态推荐调理方剂
        3. **💬 智能问答** - 基于知识图谱的专业中医问答
        
        ### 📚 理论基础
        
        《生命本能系统论》认为人体生命活动由十大本能系统调控：
        - 排异本能系统
        - 自主调节系统
        - 自塑本能系统
        - 自我修复系统
        - 自我更新系统
        - 应变系统
        - 共生性本能系统
        - ...
        """)
    
    elif menu == "🔬 本能系统诊断":
        show_multimodal_diagnosis()
    
    elif menu == "💊 方剂查询":
        st.header("💊 方剂查询")
        st.info("功能开发中...")
    
    elif menu == "💬 智能问答":
        st.header("💬 智能问答")
        st.info("功能开发中...")

# ========== 主入口 ==========
def main():
    # 检查是否显示管理员页面
    if st.session_state.get('show_admin', False) and is_admin():
        show_admin_page()
    # 检查是否已登录
    elif not is_logged_in():
        show_login_register_page()
    else:
        show_main_page()

if __name__ == "__main__":
    main()
