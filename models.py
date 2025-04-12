# models.py
# 模型映射和管理模块

# 模型映射
MODEL_MAPPING = {
    "deepseek-r1-70b": "deepseek70b",
    "deepseek-r1-turbo": "deepseekr1turbo",
    "deepseek-r1-turbo-2": "deepseekr1turbo2",
    "deepseek-r1-turbo-3": "deepseekr1turbo3",
    "deepseek-ai/DeepSeek-R1-Turbo": "deepseekr1turbo",
    "deepseek-ai/DeepSeek-V3-Turbo": "deepseekv3turbo",
    "deepseek-v3-turbo": "deepseekv3turbo",
    "deepseek-v3-turbo2": "deepseekv3turbo2",
    "deepseek-v3-0324-3": "deepseekv303243",
    "deepseek-v3-0324-2": "deepseekv303242",
    "deepseek-v3-0324": "deepseekv30324",
    "deepseek-r1-search": "volcengine",
    "grok-3": "grok3",
    "grok-3-search": "grok3search",
    "grok-3-deepsearch": "grok3deepsearch",
    "grok-3-reasoning": "grok3reasoning",
    "qwen-32b": "qwen32b",
    "qwq-32b": "qwq32b"
}

# 可用模型列表，兼容OpenAI格式
AVAILABLE_MODELS = [
    {
        "id": model_id,
        "object": "model",
        "created": 1677650000 + idx,  # 使用递增时间戳
        "owned_by": "deepseek" if "deepseek" in model_id.lower() else 
                    "xai" if "grok" in model_id.lower() else 
                    "alibaba",
        "permission": [],
        "root": MODEL_MAPPING[model_id],
        "parent": None
    }
    for idx, model_id in enumerate(MODEL_MAPPING.keys())
]

# 默认模型
DEFAULT_MODEL = "deepseek70b"


def get_model_list():
    """获取所有可用模型列表，兼容OpenAI格式"""
    return {
        "object": "list",
        "data": AVAILABLE_MODELS
    }


def map_model_name(model_name):
    """将请求中的模型名称映射到内部使用的模型名称
    
    Args:
        model_name: 请求中指定的模型名称
        
    Returns:
        映射后的内部模型名称
    """
    if not model_name:
        return model_name
        
    return MODEL_MAPPING.get(model_name, model_name)