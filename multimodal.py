# multimodal.py - 多模态图像分析模块（多模态升级版）

import base64
from io import BytesIO
from PIL import Image
import streamlit as st
from instinct_mapping import InstinctTheoryAnalyzer, INSTINCT_TONGUE_MAPPING

analyzer = InstinctTheoryAnalyzer()


def preprocess_image(image_file):
    """图像预处理"""
    image = Image.open(image_file)
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    max_size = 1024
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image


def image_to_base64(image):
    """图片转base64"""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()


def analyze_image_with_qwen(image, prompt_text, api_key):
    """
    通用：使用通义千问VL分析图片
    """
    try:
        from dashscope import MultiModalConversation
        
        img_base64 = image_to_base64(image)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{img_base64}"},
                    {"text": prompt_text}
                ]
            }
        ]
        
        response = MultiModalConversation.call(
            model='qwen-vl-plus',
            messages=messages,
            api_key=api_key
        )
        
        result_text = response.output.choices[0].message.content
        return {"success": True, "result": result_text}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_tongue_with_qwen(image, api_key):
    """
    使用通义千问VL分析舌象
    """
    prompt = """你是一位资深中医专家，请仔细分析这张舌象图片。

请从以下维度描述（只输出关键词，便于程序解析）：

【舌质颜色】淡红/红/绛红/紫/淡白/淡紫
【舌苔情况】薄白/白腻/黄腻/黄燥/无苔/剥苔/厚腻
【舌体形态】正常/胖大/瘦薄/齿痕/裂纹/点刺
【舌下络脉】正常/曲张/紫暗

请用结构化格式输出，每个特征单独一行，格式为：特征名：特征值"""

    result = analyze_image_with_qwen(image, prompt, api_key)
    
    if not result["success"]:
        return result
    
    features = extract_tongue_features(result["result"])
    
    return {
        "success": True,
        "raw_result": result["result"],
        "features": features
    }


def analyze_body_with_qwen(image, api_key):
    """
    使用通义千问VL分析体象（体态/面色）
    """
    prompt = """你是一位资深中医专家，请仔细分析这张体态或面部照片。

请从以下维度描述（只输出关键词，便于程序解析）：

【面色】红润/苍白/萎黄/晦暗/潮红/青紫/正常
【精神状态】精神饱满/精神萎靡/烦躁不安/淡漠
【体态特征】肥胖/消瘦/匀称/水肿/正常
【面部特征】浮肿/干燥/油腻/有斑/正常

请用结构化格式输出，每个特征单独一行，格式为：特征名：特征值"""

    result = analyze_image_with_qwen(image, prompt, api_key)
    
    if not result["success"]:
        return result
    
    features = extract_body_features(result["result"])
    
    return {
        "success": True,
        "raw_result": result["result"],
        "features": features
    }


def extract_tongue_features(text):
    """从AI返回文本提取舌象特征"""
    features = []
    
    keyword_map = {
        # 舌质
        "红": "舌质红", "绛红": "舌质绛红", "紫": "舌质紫",
        "淡白": "舌质淡白", "淡紫": "舌质淡紫", "淡红": "舌质淡红",
        # 舌苔
        "薄白": "苔薄白", "白腻": "苔白腻", "黄腻": "苔黄腻",
        "黄燥": "苔黄燥", "无苔": "无苔", "剥苔": "剥苔",
        "厚腻": "苔厚腻",
        # 舌形
        "胖大": "胖大舌", "瘦薄": "瘦薄舌", "齿痕": "齿痕舌",
        "裂纹": "裂纹舌", "点刺": "点刺舌", "正常": "舌体正常"
    }
    
    sorted_keywords = sorted(keyword_map.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in text and keyword_map[keyword] not in features:
            features.append(keyword_map[keyword])
    
    return features


def extract_body_features(text):
    """从AI返回文本提取体象特征"""
    features = []
    
    keyword_map = {
        # 面色
        "红润": "面色红润", "苍白": "面色苍白", "萎黄": "面色萎黄",
        "晦暗": "面色晦暗", "潮红": "面色潮红", "青紫": "面色青紫",
        # 精神状态
        "精神饱满": "精神饱满", "精神萎靡": "精神萎靡",
        "烦躁不安": "烦躁不安", "淡漠": "精神淡漠",
        # 体态
        "肥胖": "体态肥胖", "消瘦": "体态消瘦", "水肿": "体态水肿",
        # 面部特征
        "浮肿": "面部浮肿", "干燥": "面部干燥", "油腻": "面部油腻",
    }
    
    sorted_keywords = sorted(keyword_map.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in text and keyword_map[keyword] not in features:
            features.append(keyword_map[keyword])
    
    # 如果没有匹配到特征，返回基础分析
    if not features:
        features = ["体象特征待进一步辨识"]
    
    return features


def analyze_inquiry(inquiry_info):
    """
    分析问诊信息（问象），生成中医诊断描述
    
    参数：
        inquiry_info: dict，包含睡眠、饮食、情绪、寒热、汗出、二便、体力、疼痛等
    
    返回：
        list: 问诊分析结果列表
    """
    if not inquiry_info:
        return []
    
    analysis = []
    
    # 格式化问诊信息
    inquiry_text = "；".join([f"{k}：{v}" for k, v in inquiry_info.items()])
    analysis.append(f"问诊信息采集：{inquiry_text}")
    
    # 睡眠分析
    sleep = inquiry_info.get("睡眠", "")
    if sleep in ["入睡困难", "多梦易醒", "彻夜不眠"]:
        analysis.append(f"睡眠不佳（{sleep}），可能涉及心肾不交或肝郁化火，与调节系统、神经系统相关")
    
    # 饮食分析
    diet = inquiry_info.get("饮食", "")
    if diet == "食欲不振":
        analysis.append(f"食欲不振，脾胃虚弱，与代谢系统、消化系统相关")
    elif diet == "多食易饥":
        analysis.append(f"多食易饥，胃火炽盛，与代谢系统相关")
    elif diet == "口苦口干":
        analysis.append(f"口苦口干，肝胆湿热，与分泌系统、代谢系统相关")
    
    # 情绪分析
    mood = inquiry_info.get("情绪", "")
    if mood == "焦虑烦躁":
        analysis.append(f"焦虑烦躁，肝郁化火，与调节系统、神经系统相关")
    elif mood == "抑郁低落":
        analysis.append(f"抑郁低落，肝气郁结，与调节系统相关")
    elif mood == "易怒激动":
        analysis.append(f"易怒激动，肝阳上亢，与调节系统、神经系统相关")
    
    # 寒热分析
    temp = inquiry_info.get("寒热", "")
    if temp == "畏寒怕冷":
        analysis.append(f"畏寒怕冷，阳虚寒盛，与调节系统、内分泌系统相关")
    elif temp == "发热怕热":
        analysis.append(f"发热怕热，阴虚火旺，与调节系统、分泌系统相关")
    elif temp == "寒热往来":
        analysis.append(f"寒热往来，邪在半表半里，与排异系统、调节系统相关")
    
    # 汗出分析
    sweat = inquiry_info.get("汗出", "")
    if sweat == "自汗":
        analysis.append(f"自汗，卫阳不固，与调节系统、排异系统相关")
    elif sweat == "盗汗":
        analysis.append(f"盗汗，阴虚内热，与调节系统、分泌系统相关")
    
    # 二便分析
    urine = inquiry_info.get("二便", "")
    if "大便干结" in urine:
        analysis.append(f"大便干结，肠燥津亏，与分泌系统、代谢系统相关")
    elif "大便溏薄" in urine:
        analysis.append(f"大便溏薄，脾虚湿盛，与代谢系统、调节系统相关")
    
    # 体力分析
    energy = inquiry_info.get("体力", "")
    if energy in ["容易疲劳", "四肢乏力", "气短懒言"]:
        analysis.append(f"体力不足（{energy}），气虚或脾虚，与代谢系统、循环系统相关")
    
    # 疼痛分析
    pain = inquiry_info.get("疼痛", "")
    if pain:
        analysis.append(f"疼痛部位：{pain}，气滞血瘀，与调节系统、神经系统相关")
    
    return analysis


def full_multimodal_analysis(tongue_image=None, body_image=None, symptoms=None, inquiry_info=None, api_key=None):
    """
    完整多模态分析流程 - 望（舌象+体象）+ 问（症状+问诊）
    
    参数：
        tongue_image: 舌象图片（PIL Image）
        body_image: 体象图片（PIL Image），可选
        symptoms: 症状列表，可选
        inquiry_info: 问诊信息字典，可选
        api_key: API密钥
    
    返回：
        dict: 结构化诊断数据
    """
    if not api_key:
        return {"success": False, "error": "未配置API Key"}
    
    if not tongue_image and not body_image:
        return {"success": False, "error": "请至少提供舌象或体象图片"}
    
    # ========== 1. 望诊分析 ==========
    
    # 1.1 舌象分析
    tongue_features = []
    tongue_raw = ""
    if tongue_image:
        img_result = analyze_tongue_with_qwen(tongue_image, api_key)
        if img_result["success"]:
            tongue_features = img_result["features"]
            tongue_raw = img_result["raw_result"]
        if not tongue_features:
            tongue_features = ["舌质红", "苔薄白"]  # 默认特征
    
    # 1.2 体象分析
    body_features = []
    body_raw = ""
    if body_image:
        body_result = analyze_body_with_qwen(body_image, api_key)
        if body_result["success"]:
            body_features = body_result["features"]
            body_raw = body_result["raw_result"]
    
    # ========== 2. 问诊分析（问象） ==========
    inquiry_analysis = analyze_inquiry(inquiry_info) if inquiry_info else []
    
    # ========== 3. 综合分析 ==========
    
    # 合并所有症状/特征用于本能论分析
    all_features = tongue_features + body_features
    all_symptoms = all_features + (symptoms or [])
    
    # 2. 本能论分析
    analysis = analyzer.analyze(all_features)
    
    # 3. 生成本能论报告
    report, _ = analyzer.generate_report(all_features, symptoms)
    
    # 4. 构建完整的返回数据结构
    return {
        "success": True,
        # 望诊结果
        "tongue_features": tongue_features,
        "body_features": body_features,
        "tongue_raw": tongue_raw,
        "body_raw": body_raw,
        # 问诊结果
        "inquiry_analysis": inquiry_analysis,
        "text_symptoms": symptoms or [],
        "all_symptoms": list(set(all_symptoms)),
        # 本能论分析
        "instinct_systems": analysis.get("instinct_systems", []),
        "disease_trends": analysis.get("disease_trends", []),
        "pathogenesis": analysis.get("pathogenesis", []),
        "treatment_principles": analysis.get("treatment_principles", []),
        "prescriptions": analysis.get("prescriptions", []),
        "report": report
    }
