# app.py - 本能论Web系统主程序

import streamlit as st
from PIL import Image

# 正确导入所有需要的函数
from database import (
    init_database as init_db,
    create_user,
    get_all_users,
    delete_user,
    update_user_role,
    get_neo4j_driver,
    update_last_login
)
from auth import login, logout, is_logged_in, is_admin, get_current_user
from multimodal import full_multimodal_analysis, preprocess_image
from config import get_api_keys

# 初始化
init_db()

# 页面配置
st.set_page_config(page_title="中医本能论智能诊疗系统", page_icon="🏥", layout="wide")


# ========== 登录/注册页面 ==========
def show_login_register_page():
    st.title("🏥 中医本能论智能诊疗系统")
    st.markdown("*基于《生命本能系统论》与多模态AI*")
    st.markdown("---")
    
    tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册新账号"])
    
    with tab_login:
        st.subheader("用户登录")
        col1, col2 = st.columns([2, 1])
        with col1:
            login_username = st.text_input("用户名", key="login_user")
            login_password = st.text_input("密码", type="password", key="login_pass")
            
            if st.button("登录", type="primary", use_container_width=True):
                success, user_info = verify_login(login_username, login_password)
                if success and user_info:
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = user_info['id']
                    st.session_state['username'] = user_info['username']
                    st.session_state['name'] = user_info['name']
                    st.session_state['email'] = user_info['email']
                    st.session_state['role'] = user_info['role']
                    update_last_login(user_info['id'])
                    st.success(f"欢迎回来，{user_info['name']}！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
        
        with col2:
            st.info("**默认管理员账号**\n- 用户名：`admin`\n- 密码：`admin123`")
    
    with tab_register:
        st.subheader("新用户注册")
        reg_username = st.text_input("用户名*", key="reg_user")
        reg_password = st.text_input("密码*", type="password", key="reg_pass")
        reg_password2 = st.text_input("确认密码*", type="password", key="reg_pass2")
        reg_name = st.text_input("显示名称*", key="reg_name")
        reg_email = st.text_input("邮箱（选填）", key="reg_email")
        
        if st.button("立即注册", type="primary", use_container_width=True):
            if not all([reg_username, reg_password, reg_name]):
                st.error("请填写所有必填项")
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
    st.title("👤 用户管理（管理员）")
    st.markdown("---")
    
    user = get_current_user()
    st.info(f"当前管理员：**{user['name']}**（{user['username']}）")
    
    users = get_all_users()
    st.subheader(f"注册用户列表（共 {len(users)} 人）")
    
    if users:
        cols = st.columns([0.5, 1.5, 1.5, 2, 1, 1.5, 1.5])
        headers = ["ID", "用户名", "显示名", "邮箱", "角色", "注册时间", "操作"]
        for col, header in zip(cols, headers):
            col.write(f"**{header}**")
        
        for user_data in users:
            user_id, username, name, email, role, created_at, last_login = user_data
            cols = st.columns([0.5, 1.5, 1.5, 2, 1, 1.5, 1.5])
            cols[0].write(user_id)
            cols[1].write(username)
            cols[2].write(name)
            cols[3].write(email or "-")
            cols[4].write("🔴 管理员" if role == "admin" else "🟢 用户")
            cols[5].write(created_at[:10] if created_at else "-")
            
            with cols[6]:
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
    
    st.markdown("---")
    if st.button("← 返回主界面", use_container_width=True):
        st.session_state['show_admin'] = False
        st.rerun()


# ========== 首页 ==========
def show_home_page():
    st.title("🏥 中医本能论智能诊疗系统")
    st.markdown("*基于郭生白《生命本能系统论》构建*")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("本能系统", "10大系统")
    col2.metric("方剂", "60+")
    col3.metric("疾病", "30+")
    
    st.info("""
    ### 🎯 系统特色
    1. **🔬 本能系统诊断** - 上传舌象，AI识别并映射到十大本能系统
    2. **💊 方剂推荐** - 根据本能系统状态推荐调理方剂
    3. **💬 智能问答** - 基于知识图谱的专业中医问答
    """)


# ========== 多模态诊断（显示方剂组成）==========
def show_multimodal_diagnosis():
    st.header("🔬 本能系统多模态诊断")
    st.markdown("*上传舌象图片，AI结合《生命本能系统论》进行智能分析*")
    st.markdown("---")
    
    api_keys = get_api_keys()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 舌象采集")
        uploaded_file = st.file_uploader("请上传清晰的舌象照片", type=['jpg', 'jpeg', 'png'])
        
        with st.expander("📖 拍摄指南"):
            st.markdown("**拍摄要求：**\n1. 在自然光下拍摄\n2. 舌头自然伸出\n3. 避免使用美颜/滤镜")
        
        image = None
        if uploaded_file:
            image = preprocess_image(uploaded_file)
            st.image(image, caption="上传的舌象图片", use_column_width=True)
    
    with col2:
        st.subheader("📝 症状补充（选填）")
        common_symptoms = ["发热", "怕冷", "头疼", "咳嗽", "胸闷", "气短", "心慌", "失眠",
                          "腹疼", "便秘", "腹泻", "没食欲", "口渴", "口苦", "口干", "疲劳"]
        selected_symptoms = st.multiselect("选择症状", common_symptoms)
        custom_symptoms = st.text_input("或手动输入：", placeholder="例如：头疼 口渴 失眠")
        all_text_symptoms = selected_symptoms + (custom_symptoms.split() if custom_symptoms else [])
        if all_text_symptoms:
            st.info(f"已选症状：{'、'.join(all_text_symptoms)}")
    
    st.markdown("---")
    analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
    with analyze_col2:
        if st.button("🔍 开始本能系统分析", type="primary", use_container_width=True):
            if not uploaded_file:
                st.error("请先上传舌象图片")
            elif not api_keys.get("dashscope_key"):
                st.error("未配置通义千问API Key")
            else:
                with st.spinner("🤖 AI正在分析..."):
                    result = full_multimodal_analysis(image, all_text_symptoms or None, api_keys["dashscope_key"])
                    if result["success"]:
                        st.session_state['analysis_result'] = result
                        st.success("✅ 分析完成！")
                    else:
                        st.error(f"分析失败：{result.get('error', '未知错误')}")
    
    # 显示分析结果
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        st.markdown("---")
        st.header("📋 《生命本能系统论》诊断分析报告")
        
        # 1. 舌象特征
        st.subheader("一、望舌诊察")
        if result.get("tongue_features"):
            for feature in result["tongue_features"]:
                st.markdown(f"- ✅ {feature}")
        else:
            st.warning("未识别到舌象特征")
        
        # 2. 本能系统分析
        st.subheader("二、本能系统分析")
        if result.get("instinct_systems"):
            for i, system in enumerate(result["instinct_systems"], 1):
                st.markdown(f"**{i}. {system['name']}**")
                st.caption(f"病机：{system.get('description', '暂无')}")
                st.info(f"病势：{system.get('trend', '未知')}")
        
        # 3. 病势判断
        st.subheader("三、病势综合判断")
        if result.get("disease_trends"):
            for trend in result["disease_trends"]:
                if "外源" in trend:
                    st.error(f"🔴 {trend}")
                else:
                    st.warning(f"🟡 {trend}")
        
        # 4. 治则治法
        st.subheader("四、治则治法")
        if result.get("treatment_principles"):
            for principle in set(result["treatment_principles"]):
                st.success(f"💡 {principle}")
        
        # 5. 推荐方剂（从Neo4j查询组成）- 这是关键修复部分
        st.subheader("五、推荐方剂")
        if result.get("prescriptions"):
            unique_prescriptions = list(dict.fromkeys(result["prescriptions"]))[:8]
            
            try:
                driver = get_neo4j_driver()
                with driver.session() as session:
                    for p_name in unique_prescriptions:
                        query = """
                        MATCH (f:方剂 {name: $name})
                        OPTIONAL MATCH (f)-[:组成]->(m:药物)
                        OPTIONAL MATCH (f)-[:属于]->(t:治法)
                        RETURN f.name AS 方剂, t.name AS 治法, 
                               collect(DISTINCT m.name) AS 药物组成
                        """
                        db_result = session.run(query, name=p_name)
                        record = db_result.single()
                        
                        if record and record["方剂"]:
                            with st.expander(f"💊 {record['方剂']}", expanded=True):
                                if record['治法']:
                                    st.markdown(f"**治法：**{record['治法']}")
                                if record['药物组成']:
                                    st.markdown("**药物组成：**")
                                    for drug in record['药物组成']:
                                        st.markdown(f"- {drug}")
                                else:
                                    st.caption("暂无组成信息")
                        else:
                            st.markdown(f"- 💊 {p_name}")
            except Exception as e:
                st.warning(f"查询方剂详情失败：{e}")
                for p_name in unique_prescriptions:
                    st.markdown(f"- 💊 {p_name}")
        
        # 6. 调护建议
        st.subheader("六、调护建议")
        st.markdown("""
        1. **饮食调护**：外源性疾病宜清淡，内源性疾病宜辨证施食
        2. **起居调护**：保证充足睡眠
        3. **情志调护**：保持平和心态
        4. **运动调护**：适度运动，避免过劳
        """)


# ========== 方剂推荐 ==========
def show_prescription_recommendation():
    st.header("💊 智能方剂推荐")
    st.markdown("*输入症状，系统结合知识图谱和AI进行智能推荐*")
    st.markdown("---")
    
    try:
        driver = get_neo4j_driver()
    except Exception as e:
        st.error(f"数据库连接失败：{e}")
        return
    
    try:
        from zhipuai import ZhipuAI
        api_key = st.secrets.get("API_KEY", "")
        zhipu_client = ZhipuAI(api_key=api_key) if api_key else None
    except:
        zhipu_client = None
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 症状输入")
        
        try:
            with driver.session() as session:
                result = session.run("MATCH (s:症状) RETURN s.name AS name ORDER BY s.name")
                all_symptoms = [r["name"] for r in result]
        except:
            all_symptoms = []
        
        selected_symptoms = st.multiselect("选择症状（可多选）", all_symptoms)
        custom_input = st.text_input("或手动输入：", placeholder="例如：发烧 咳嗽 头疼")
        all_input_symptoms = selected_symptoms + (custom_input.replace("，", " ").split() if custom_input else [])
        
        if all_input_symptoms:
            st.info(f"**已选症状：**{'、'.join(all_input_symptoms)}")
        
        if st.button("🔍 智能推荐方剂", type="primary", use_container_width=True):
            if not all_input_symptoms:
                st.error("请至少输入一个症状")
            else:
                with st.spinner("🧠 正在分析..."):
                    st.session_state['prescription_symptoms'] = all_input_symptoms
                    st.rerun()
    
    with col2:
        if 'prescription_symptoms' in st.session_state:
            symptoms = st.session_state['prescription_symptoms']
            st.subheader("📊 分析结果")
            
            # 查询疾病
            diseases = []
            try:
                with driver.session() as session:
                    query = """
                    MATCH (d:疾病)-[:临床表现]->(s:症状)
                    WHERE s.name IN $symptoms
                    WITH d, count(s) AS 匹配症状数, collect(s.name) AS 匹配的症状
                    ORDER BY 匹配症状数 DESC
                    RETURN d.name AS 疾病, d.分类 AS 分类, 匹配症状数, 匹配的症状
                    LIMIT 5
                    """
                    diseases = list(session.run(query, symptoms=symptoms))
            except Exception as e:
                st.error(f"查询失败：{e}")
            
            all_prescriptions = []
            
            if diseases:
                st.markdown("### 🏥 可能的疾病")
                for i, d in enumerate(diseases, 1):
                    st.markdown(f"**【{i}】{d['疾病']}** ({d['分类']})")
                    st.caption(f"匹配{d['匹配症状数']}个症状")
                    
                    # 查询方剂
                    try:
                        with driver.session() as session:
                            p_query = """
                            MATCH (f:方剂)-[:治疗]->(d:疾病 {name: $disease})
                            OPTIONAL MATCH (f)-[:组成]->(m:药物)
                            OPTIONAL MATCH (f)-[:属于]->(t:治法)
                            RETURN f.name AS 方剂, t.name AS 治法, 
                                   collect(DISTINCT m.name) AS 药物组成
                            """
                            prescriptions = list(session.run(p_query, disease=d['疾病']))
                            for p in prescriptions:
                                all_prescriptions.append({
                                    "疾病": d['疾病'],
                                    "方剂": p['方剂'],
                                    "治法": p['治法'],
                                    "组成": p['药物组成']
                                })
                    except Exception as e:
                        st.error(f"查询方剂失败：{e}")
                    
                    st.divider()
            
            # 显示方剂详情
            if all_prescriptions:
                st.markdown("### 💊 方剂详情")
                shown = set()
                for p in all_prescriptions:
                    if p['方剂'] not in shown:
                        shown.add(p['方剂'])
                        with st.expander(f"{p['方剂']}（治疗{p['疾病']}）"):
                            st.markdown(f"**治法：**{p['治法'] or '暂无'}")
                            if p['组成']:
                                st.markdown("**药物组成：**")
                                for drug in p['组成']:
                                    st.markdown(f"- {drug}")
                            else:
                                st.caption("暂无组成信息")


# ========== 智能问答 ==========
def show_qa_module():
    st.header("💬 智能问答")
    st.markdown("*基于《生命本能系统论》知识图谱的AI问答系统*")
    st.markdown("---")
    
    try:
        driver = get_neo4j_driver()
    except Exception as e:
        st.error(f"数据库连接失败：{e}")
        return
    
    try:
        from zhipuai import ZhipuAI
        api_key = st.secrets.get("API_KEY", "")
        zhipu_client = ZhipuAI(api_key=api_key) if api_key else None
    except:
        st.error("智谱AI未配置")
        return
    
    question = st.text_area("请输入您的问题：", placeholder="例如：发烧怕冷是什么问题？", height=100)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 提问", type="primary", use_container_width=True):
            if not question:
                st.error("请输入问题")
            else:
                with st.spinner("🤖 正在检索知识图谱..."):
                    # 提取关键词
                    keywords = []
                    keyword_list = ["发热", "怕冷", "头疼", "咳嗽", "麻黄汤", "桂枝汤", "高血压", "糖尿病"]
                    for kw in keyword_list:
                        if kw in question:
                            keywords.append(kw)
                    
                    # 检索知识图谱
                    context = ""
                    try:
                        with driver.session() as session:
                            for kw in keywords:
                                # 查疾病
                                result = session.run("""
                                    MATCH (d:疾病) WHERE d.name CONTAINS $kw
                                    OPTIONAL MATCH (f:方剂)-[:治疗]->(d)
                                    RETURN d.name AS 疾病, collect(f.name) AS 方剂
                                    LIMIT 2
                                """, kw=kw)
                                for r in result:
                                    context += f"疾病：{r['疾病']}，治疗方剂：{', '.join(r['方剂'][:3])}\n"
                    except Exception as e:
                        context = "检索失败"
                    
                    # RAG生成回答
                    try:
                        prompt = f"""你是基于《生命本能系统论》的中医专家。
                        
用户问题：{question}

知识图谱检索结果：
{context}

请根据以上信息回答，结合本能系统论理论。"""
                        
                        response = zhipu_client.chat.completions.create(
                            model="glm-4-flash",
                            messages=[
                                {"role": "system", "content": "你是精通《生命本能系统论》的中医专家"},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        
                        st.success("回答：")
                        st.write(response.choices[0].message.content)
                        
                    except Exception as e:
                        st.error(f"AI生成失败：{e}")


# ========== 主入口 ==========
def main():
    if st.session_state.get('show_admin', False) and is_admin():
        show_admin_page()
    elif not is_logged_in():
        show_login_register_page()
    else:
        show_main_page()


def show_main_page():
    user = get_current_user()
    st.sidebar.markdown(f"👤 **{user['name']}**")
    st.sidebar.caption(f"角色：{'管理员' if is_admin() else '普通用户'}")
    st.sidebar.markdown("---")
    
    if is_admin():
        if st.sidebar.button("🔧 用户管理", use_container_width=True):
            st.session_state['show_admin'] = True
            st.rerun()
        st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 退出登录", use_container_width=True):
        logout()
        st.rerun()
    
    menu = st.sidebar.radio("功能菜单", ["🏠 首页", "🔬 本能系统诊断", "💊 方剂推荐", "💬 智能问答"])
    
    if menu == "🏠 首页":
        show_home_page()
    elif menu == "🔬 本能系统诊断":
        show_multimodal_diagnosis()
    elif menu == "💊 方剂推荐":
        show_prescription_recommendation()
    elif menu == "💬 智能问答":
        show_qa_module()


if __name__ == "__main__":
    main()
