# app.py - 本能论Web系统主程序（集成知识图谱可视化）

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
    update_last_login,
    verify_login
)
from auth import login, logout, is_logged_in, is_admin, get_current_user
from multimodal import full_multimodal_analysis, preprocess_image
from config import get_api_keys

# 导入知识图谱可视化所需库
from pyvis.network import Network
import pandas as pd

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
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("本能系统", "10大系统")
    col2.metric("方剂", "60+")
    col3.metric("疾病", "30+")
    col4.metric("知识节点", "500+")
    
    st.info("""
    ### 🎯 系统特色
    1. **🔬 本能系统诊断** - 上传舌象，AI识别并映射到十大本能系统
    2. **💊 方剂推荐** - 根据本能系统状态推荐调理方剂
    3. **💬 智能问答** - 基于知识图谱的专业中医问答
    4. **🕸️ 知识图谱可视化** - 交互式探索知识图谱结构
    """)


# ========== 知识图谱可视化页面 ==========
def show_graph_visualization():
    """知识图谱可视化页面 - 展示Neo4j知识图谱的交互式可视化效果"""
    st.header("🕸️ 知识图谱可视化")
    st.markdown("*探索《生命本能系统论》知识图谱的结构与关联*")
    st.markdown("---")
    
    # 获取数据库连接
    try:
        driver = get_neo4j_driver()
    except Exception as e:
        st.error(f"数据库连接失败：{e}")
        return
    
    # 获取图谱统计信息
    try:
        with driver.session() as session:
            # 总节点数
            node_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            # 总关系数
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
            # 各类型节点数量
            node_types = list(session.run("""
                MATCH (n) 
                RETURN labels(n)[0] AS node_type, count(n) AS count 
                ORDER BY count DESC
            """))
            # 各类型关系数量
            rel_types = list(session.run("""
                MATCH ()-[r]->() 
                RETURN type(r) AS rel_type, count(r) AS count 
                ORDER BY count DESC
            """))
    except Exception as e:
        st.error(f"获取统计信息失败：{e}")
        node_count = rel_count = 0
        node_types = rel_types = []
    
    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总节点数", node_count)
    with col2:
        st.metric("总关系数", rel_count)
    with col3:
        st.metric("节点类型", len(node_types))
    with col4:
        st.metric("关系类型", len(rel_types))
    
    st.markdown("---")
    
    # 创建左右布局
    left_col, right_col = st.columns([1, 3])
    
    with left_col:
        st.markdown("### 🔍 筛选条件")
        
        # 节点类型筛选
        st.markdown("**节点类型**")
        node_type_options = ['本能系统', '疾病', '症状', '方剂', '药物', '治法', '外因', '理论概念']
        selected_node_types = []
        for node_type in node_type_options:
            if st.checkbox(node_type, value=True, key=f"node_{node_type}"):
                selected_node_types.append(node_type)
        
        # 关系类型筛选
        st.markdown("**关系类型**")
        rel_type_options = ['包含', '导致', '临床表现', '属于', '治疗', '组成']
        selected_rel_types = []
        for rel_type in rel_type_options:
            if st.checkbox(rel_type, value=True, key=f"rel_{rel_type}"):
                selected_rel_types.append(rel_type)
        
        # 显示数量限制
        max_nodes = st.slider("最大显示节点数", 10, 300, 100, 10)
        
        # 物理引擎开关
        physics_enabled = st.toggle("启用物理引擎", value=True, 
                                    help="关闭后可手动固定节点位置")
        
        # 刷新按钮
        refresh = st.button("🔄 刷新图谱", type="primary", use_container_width=True)
        
        # 图例说明
        st.markdown("---")
        st.markdown("### 📌 图例说明")
        
        # 节点颜色图例
        color_map = {
            '本能系统': '#FF6B6B',
            '疾病': '#FFA502',
            '症状': '#FFD700',
            '方剂': '#2ED573',
            '药物': '#1E90FF',
            '治法': '#A55EEA',
            '外因': '#FF9F43',
            '理论概念': '#74B9FF'
        }
        
        st.markdown("**节点类型**")
        for node_type, color in color_map.items():
            st.markdown(
                f"<span style='display:inline-block;width:12px;height:12px;"
                f"background-color:{color};border-radius:50%;margin-right:8px;'></span>{node_type}",
                unsafe_allow_html=True
            )
        
        # 关系颜色图例
        edge_color_map = {
            '包含': '#3498DB',
            '导致': '#E74C3C',
            '临床表现': '#F39C12',
            '属于': '#9B59B6',
            '治疗': '#27AE60',
            '组成': '#1ABC9C'
        }
        
        st.markdown("**关系类型**")
        for rel_type, color in edge_color_map.items():
            st.markdown(
                f"<span style='display:inline-block;width:20px;height:3px;"
                f"background-color:{color};margin-right:8px;vertical-align:middle;'></span>{rel_type}",
                unsafe_allow_html=True
            )
    
    with right_col:
        st.markdown("### 🕸️ 知识图谱可视化")
        
        # 查询数据
        try:
            with driver.session() as session:
                # 构建节点查询
                label_filter = ""
                if selected_node_types:
                    label_conditions = [f"'{label}' IN labels(n)" for label in selected_node_types]
                    label_filter = "WHERE " + " OR ".join(label_conditions)
                
                node_query = f"""
                    MATCH (n)
                    {label_filter}
                    RETURN id(n) AS id, labels(n) AS labels, n.name AS name, n
                    LIMIT {max_nodes}
                """
                nodes_data = list(session.run(node_query))
                node_ids = [node['id'] for node in nodes_data]
                
                # 查询关系
                edges_data = []
                if node_ids:
                    rel_filter = ""
                    if selected_rel_types:
                        rel_conditions = [f"type(r) = '{rel_type}'" for rel_type in selected_rel_types]
                        rel_filter = "AND (" + " OR ".join(rel_conditions) + ")"
                    
                    rel_query = f"""
                        MATCH (a)-[r]->(b)
                        WHERE id(a) IN {node_ids} AND id(b) IN {node_ids}
                        {rel_filter}
                        RETURN id(a) AS source, id(b) AS target, type(r) AS type, r
                    """
                    edges_data = list(session.run(rel_query))
        except Exception as e:
            st.error(f"查询图谱数据失败：{e}")
            nodes_data = []
            edges_data = []
        
        if len(nodes_data) == 0:
            st.info("未找到符合条件的节点，请调整筛选条件")
        else:
            # 创建Pyvis网络图
            net = Network(
                height="600px",
                width="100%",
                bgcolor="#ffffff",
                font_color="#1A202C",
                heading=""
            )
            
            # 配置物理引擎
            if physics_enabled:
                net.set_options("""
                {
                    "physics": {
                        "enabled": true,
                        "barnesHut": {
                            "gravitationalConstant": -2000,
                            "centralGravity": 0.3,
                            "springLength": 95,
                            "springConstant": 0.04,
                            "damping": 0.09,
                            "avoidOverlap": 0.1
                        },
                        "stabilization": {
                            "enabled": true,
                            "iterations": 1000
                        }
                    },
                    "interaction": {
                        "hover": true,
                        "tooltipDelay": 200,
                        "hideEdgesOnDrag": false,
                        "navigationButtons": true,
                        "keyboard": true
                    },
                    "manipulation": {
                        "enabled": true
                    }
                }
                """)
            else:
                net.set_options("""
                {
                    "physics": {"enabled": false},
                    "interaction": {
                        "hover": true,
                        "tooltipDelay": 200,
                        "navigationButtons": true,
                        "keyboard": true
                    }
                }
                """)
            
            # 添加节点
            for node in nodes_data:
                node_id = node['id']
                labels = node['labels']
                name = node.get('name', f"Node_{node_id}")
                label_type = labels[0] if labels else 'Unknown'
                color = color_map.get(label_type, '#95A5A6')
                
                # 构建节点标题
                title = f"类型: {label_type}<br>名称: {name}"
                if 'description' in node['n']:
                    desc = node['n']['description']
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    title += f"<br>描述: {desc}"
                
                net.add_node(
                    node_id,
                    label=name,
                    title=title,
                    color=color,
                    size=25 if label_type == '本能系统' else 20,
                    font={'size': 14, 'color': '#1A202C'}
                )
            
            # 添加边
            for edge in edges_data:
                source = edge['source']
                target = edge['target']
                rel_type = edge['type']
                color = edge_color_map.get(rel_type, '#95A5A6')
                
                net.add_edge(
                    source,
                    target,
                    label=rel_type,
                    title=f"关系: {rel_type}",
                    color=color,
                    width=2,
                    arrows={'to': {'enabled': True, 'scaleFactor': 0.5}}
                )
            
            # 保存并显示
            net.save_graph("temp_graph.html")
            with open("temp_graph.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            
            st.components.v1.html(html_content, height=650)
            st.caption(f"显示 {len(nodes_data)} 个节点，{len(edges_data)} 条关系")
    
    # 节点详情查询
    st.markdown("---")
    st.markdown("### 🔎 节点详情查询")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        search_name = st.text_input("输入节点名称", placeholder="例如：排异系统")
        search_button = st.button("查询", type="primary")
    
    with col2:
        if search_button and search_name:
            try:
                with driver.session() as session:
                    # 查询节点信息
                    node_info = session.run("""
                        MATCH (n {name: $name})
                        RETURN n, labels(n) AS labels
                    """, name=search_name).single()
                    
                    if node_info:
                        node = node_info['n']
                        labels = node_info['labels']
                        
                        st.markdown(f"**节点名称**: {node['name']}")
                        st.markdown(f"**节点类型**: {', '.join(labels)}")
                        
                        # 显示属性
                        props = {k: v for k, v in node.items() if k != 'name'}
                        if props:
                            st.markdown("**属性信息**:")
                            st.json(props)
                        
                        # 查询相关关系
                        relationships = list(session.run("""
                            MATCH (n {name: $name})-[r]-(m)
                            RETURN type(r) AS rel_type, 
                                   m.name AS related_name, 
                                   labels(m) AS related_labels,
                                   startNode(r).name = $name AS is_outgoing
                        """, name=search_name))
                        
                        if relationships:
                            st.markdown("**关联关系**:")
                            rel_df = pd.DataFrame(relationships)
                            rel_df['方向'] = rel_df['is_outgoing'].apply(lambda x: '→' if x else '←')
                            rel_df['关联节点'] = rel_df['related_name'] + ' (' + rel_df['related_labels'].apply(lambda x: x[0] if x else 'Unknown') + ')'
                            st.dataframe(
                                rel_df[['rel_type', '方向', '关联节点']].rename(columns={'rel_type': '关系类型'}),
                                use_container_width=True
                            )
                    else:
                        st.warning(f"未找到名称为 '{search_name}' 的节点")
                        
            except Exception as e:
                st.error(f"查询失败: {e}")


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
        
        # 5. 推荐方剂（从Neo4j查询组成）
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
    
    # 添加知识图谱可视化菜单选项
    menu = st.sidebar.radio("功能菜单", [
        "🏠 首页", 
        "🔬 本能系统诊断", 
        "💊 方剂推荐", 
        "💬 智能问答",
        "🕸️ 知识图谱可视化"
    ])
    
    if menu == "🏠 首页":
        show_home_page()
    elif menu == "🔬 本能系统诊断":
        show_multimodal_diagnosis()
    elif menu == "💊 方剂推荐":
        show_prescription_recommendation()
    elif menu == "💬 智能问答":
        show_qa_module()
    elif menu == "🕸️ 知识图谱可视化":
        show_graph_visualization()


if __name__ == "__main__":
    main()
