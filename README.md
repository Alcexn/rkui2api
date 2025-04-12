# rkui2api
### 此项目仅供学习交流
#### 这是我的第一个2api项目，如果觉得本项目对你有帮助的话可以点个star~
我的一些其他的网站
[洛樱云API](https://api.luoying.work/) [个人博客](https://blog.alcex.cn)

目前grok系列模型无法使用.其他正常，等平台恢复即可使用
### 支持模型
- deepseek-r1-70b
- deepseek-r1-turbo
- deepseek-ai/DeepSeek-R1-Turbo
- deepseek-ai/DeepSeek-V3-Turbo
- deepseek-v3-turbo
- deepseek-v3-0324
- deepseek-r1-search
- grok-3
- grok-3-search
- grok-3-deepsearch
- grok-3-reasoning
- qwen-32b
- qwq-32b

### 部署
####  环境变量

API_TOKEN：APIkey可自定义默认为sk-114514

#### 通过Docker部署
```
docker run --name rkui2api -d --restart always -p 3014:8080 -e API_TOKEN=sk-114514 -e TZ=Asia/Shanghai alcexn/rkui2api
```
#### 直接运行
请确保您已安装python环境
```
pip install --no-cache-dir -r requirements.txt
```
```
python main.py
```

#### api路由
GET /v1/models 列出所有模型（兼容OPENAI规范）
POST /v1/chat/completions/ 聊天接口（兼容OPENAI规范）


```
curl -X POST 'http://localhost:3014/v1/chat/completions' -H 'Content-Type: application/json' -H 'Authorization: Bearer sk-114514' -d '{
  "messages": [
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "model": "deepseek-r1-70b",
  "stream": false
}'
```
