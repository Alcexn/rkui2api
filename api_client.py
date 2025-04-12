# api_client.py
# API客户端模块，处理与目标API的通信

import httpx
import json
import asyncio
import random
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from random_user_agent.user_agent import UserAgent


def generate_random_user_agent():
    """生成随机的User-Agent字符串
    
    Returns:
        随机生成的User-Agent字符串
    """
    # 使用random-user-agent库生成随机User-Agent
    user_agent_rotator = UserAgent()
    return user_agent_rotator.get_random_user_agent()


async def call_api(payload, is_stream=False):
    """调用目标API并处理响应
    
    Args:
        payload: 请求负载
        is_stream: 是否为流式请求
        
    Returns:
        流式响应或完整内容
    """
    try:
        async with httpx.AsyncClient() as client:
            # 生成随机User-Agent
            user_agent = generate_random_user_agent()
            
            # 发送请求到目标API
            response = await client.post(
                "https://deepseek.rkui.cn/api/chat",
                json=payload,
                timeout=60.0,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "User-Agent": user_agent
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            # 检查响应内容是否为空
            if not response.content:
                raise HTTPException(status_code=502, detail="Empty response from API")
                
            # 处理流式响应
            if is_stream:
                return handle_stream_response(response)
            
            # 处理非流式响应
            return await handle_non_stream_response(response)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def handle_stream_response(response):
    """处理流式响应
    
    Args:
        response: API响应对象
        
    Returns:
        StreamingResponse对象
    """
    async def generate():
        buffer = ""
        chunk_count = 0  # 用于跟踪接收到的数据块数量
        
        print("\n===== 开始接收API响应数据 =====\n")
        
        # 使用aiter_text处理文本流，确保实时处理
        async for chunk in response.aiter_text():
            chunk_count += 1
            print(f"\n[接收数据块 #{chunk_count}] 原始数据: {chunk!r}\n")
            
            # 立即处理接收到的数据块
            buffer += chunk
            
            # 处理缓冲区中的每一行
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                
                # 处理完整的SSE行
                if line.startswith("data: "):
                    print(f"\n[SSE行] {line}")
                    
                    if line == "data: [DONE]":
                        print("\n===== 接收到完成标记 [DONE] =====\n")
                        # 直接转发[DONE]标记而不尝试解析
                        yield "data: [DONE]\n\n"
                        # 强制刷新缓冲区
                        await asyncio.sleep(0)
                        # 设置标志位表示已处理过[DONE]
                        done_processed = True
                        continue
                    
                    # 如果已经处理过[DONE]标记，则跳过后续所有[DONE]
                    if hasattr(generate, 'done_processed') and generate.done_processed:
                        print("[跳过重复的DONE标记]")
                        continue
                    
                    try:
                        # 检查是否存在双重data:前缀
                        content = line
                        if line.startswith("data: data:"):
                            print(f"[检测到双重data:前缀] 原始: {line}")
                            # 使用正则表达式精确匹配并去除多余的data:前缀
                            import re
                            content = re.sub(r'^data:\s*data:', 'data:', line)
                            print(f"[处理后] {content}")
                        
                        # 直接转发SSE行，不尝试解析JSON
                        # 确保行以data:开头并以\n\n结尾
                        formatted_response = f"{content}\n\n"
                        print(f"[直接转发SSE行] {formatted_response!r}")
                        # 立即发送数据，不等待整个响应完成
                        yield formatted_response
                        # 强制刷新缓冲区，确保数据立即发送
                        await asyncio.sleep(0)
                        # 添加额外的刷新，确保数据立即发送到客户端
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        print(f"\n[处理行时出错] 错误类型: {type(e).__name__}, 错误信息: {e}\n[问题数据] {line!r}")
                        continue
        
        print("\n===== API响应数据接收完毕 =====\n")
        if buffer:
            print(f"[剩余未处理的缓冲区数据] {buffer!r}")
    
    # 使用headers参数明确设置Content-Type，确保不包含charset=utf-8
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


async def handle_non_stream_response(response):
    """处理非流式响应
    
    Args:
        response: API响应对象
        
    Returns:
        提取的完整内容
    """
    full_content = ""
    buffer = ""
    print("\n===== 开始接收非流式API响应数据 =====\n")
    
    # 立即处理每个数据块，不等待整个响应完成
    async for chunk in response.aiter_text():
        print(f"\n[接收非流式数据块] 原始数据: {chunk!r}\n")
        
        # 立即处理接收到的数据块
        buffer += chunk
        
        # 处理缓冲区中的每一行
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            
            # 处理完整的SSE行
            if line.startswith("data: "):
                print(f"\n[非流式SSE行] {line}")
                
                if line == "data: [DONE]":
                    print("\n===== 接收到非流式完成标记 [DONE] =====\n")
                    # 强制刷新缓冲区
                    await asyncio.sleep(0)
                    continue
                
                try:
                    # 提取SSE行中的JSON数据
                    import re
                    json_str = re.sub(r'^data:\s*', '', line)  # 使用正则去掉data:前缀
                    
                    # 检查是否存在双重data:前缀
                    if json_str.startswith("data:"):
                        print(f"[检测到双重data:前缀] 原始: {json_str}")
                        json_str = re.sub(r'^data:\s*', '', json_str)  # 再次使用正则去掉data:前缀
                        print(f"[处理后原始] {json_str}")
                        
                        # 如果是[DONE]标记则跳过
                        if json_str.strip() == "[DONE]":
                            continue
                            
                        # 修复JSON格式：确保是有效的JSON字符串
                        # 检查是否缺少开头的花括号
                        if not json_str.strip().startswith("{"):
                            # 构建完整的JSON对象
                            json_str = '{' + json_str
                        
                        # 检查是否缺少结尾的花括号
                        if not json_str.strip().endswith("}"):
                            json_str = json_str + "}"
                            
                        print(f"[处理后最终] {json_str}")
                    
                    # 确保JSON字符串是有效的，处理可能的格式问题
                    json_str = json_str.strip()
                    if json_str.endswith("]"): # 处理特殊情况如 "DONE]"
                        if json_str == "DONE]":
                            print("[跳过无效JSON] DONE]")
                            continue
                        
                        # 处理不完整的JSON响应
                        if json_str.startswith("{") and not json_str.endswith("}"):
                            # 尝试补全JSON
                            json_str = json_str + "}"
                            print(f"[修复不完整JSON] 补全后: {json_str}")
                    
                    try:
                        # 尝试解析JSON
                        data = json.loads(json_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            full_content += content
                            # 强制刷新缓冲区
                            await asyncio.sleep(0)
                    except json.JSONDecodeError as json_err:
                        print(f"[JSON解析错误] {json_err} - 尝试修复并重新解析")
                        try:
                            # 尝试修复常见的JSON格式问题
                            # 移除可能导致问题的字符
                            json_str = json_str.strip()
                            # 如果字符串不是以{开头，尝试找到第一个{并从那里开始
                            if not json_str.startswith("{"):
                                start_idx = json_str.find("{")
                                if start_idx >= 0:
                                    json_str = json_str[start_idx:]
                            
                            # 尝试再次解析
                            data = json.loads(json_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                full_content += content
                                # 强制刷新缓冲区
                                await asyncio.sleep(0)
                        except json.JSONDecodeError:
                            print(f"[JSON修复失败] 无法解析JSON: {json_str} - 跳过此行")
                            continue
                except Exception as e:
                    print(f"\n[处理非流式行时出错] 错误类型: {type(e).__name__}, 错误信息: {e}\n[问题数据] {line!r}")
                    continue
    
    print("\n===== 非流式API响应数据接收完毕 =====\n")
    if buffer:
        print(f"[剩余未处理的缓冲区数据] {buffer!r}")        
    # 如果没有成功提取内容，尝试直接解析响应
    if not full_content:
        try:
            data = response.json()
            full_content = data.get("content", "")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON response from API: {response.text[:200]}"
            )
            
    return full_content
