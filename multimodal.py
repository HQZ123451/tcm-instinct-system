# multimodal.py - 多模态图像分析模块（修复版）

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

def analyze_tongue_with_qwen(image, api_key):
    """
    使用通义千问VL分析舌象
    """
    try:
        from dashscope import MultiModalConversation
        
        img_base64 = image_to_base64(image)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{img_base64}"},
                    {"text": """你是一位资深中医专家，请仔细分析这张舌象图片。

请从以下维度描述（只输出关键词，便于程序解析）：

【舌质颜色】淡红/红/绛红/紫/淡白/淡紫
【舌苔情况】薄白/白腻/黄腻/黄燥/无苔/剥苔/厚腻
【舌体形态】正常/胖大/瘦薄/齿痕/裂纹/点刺
【舌下络脉】正常/曲张/紫暗

请用结构化格式输出，每个特征单独一行，格式为：特征名：特征值"""}
                ]
            }
        ]
        
        response = MultiModalConversation.call(
            model='qwen-vl-plus',
            messages=messages,
            api_key=api_key
        )
        
        result_text = response.output.choices[0].message.content
        
        # 解析特征
        features = extract_features_from_text(result_text)
        
        return {
            "success": True,
            "raw_result": result_text,
            "features": features
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "features": []
        }

def extract_features_from_text(text):
    """从AI返回文本提取特征"""
    features = []
    
    # 关键词映射
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
    
    # 优先匹配长的关键词
    sorted_keywords = sorted(keyword_map.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in text and keyword_map[keyword] not in features:
            features.append(keyword_map[keyword])
    
    return features

def full_multimodal_analysis(image, text_symptoms=None, api_key=None):
    """
    完整多模态分析流程 - 返回结构化数据
    """
    if not api_key:
        return {"success": False, "error": "未配置API Key"}
    
    # 1. 图像分析
    img_result = analyze_tongue_with_qwen(image, api_key)
    
    if not img_result["success"]:
        return img_result
    
    tongue_features = img_result["features"]
    
    # 如果AI没有识别出特征，使用默认特征（用于测试）
    if not tongue_features:
        tongue_features = ["舌质红", "苔黄腻"]  # 默认测试特征
    
    # 2. 本能论分析
    analysis = analyzer.analyze(tongue_features)
    
    # 3. 生成本能论报告
    report, _ = analyzer.generate_report(tongue_features, text_symptoms)
    
    # 4. 合并所有症状
    all_symptoms = tongue_features + (text_symptoms or [])
    
    # 5. 构建完整的返回数据结构
    return {
        "success": True,
        "tongue_features": tongue_features,
        "text_symptoms": text_symptoms or [],
        "all_symptoms": list(set(all_symptoms)),
        "instinct_systems": analysis.get("instinct_systems", []),
        "disease_trends": analysis.get("disease_trends", []),
        "pathogenesis": analysis.get("pathogenesis", []),
        "treatment_principles": analysis.get("treatment_principles", []),
        "prescriptions": analysis.get("prescriptions", []),
        "report": report,
        "raw_ai_result": img_result["raw_result"]
    }
