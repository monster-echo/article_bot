# Article Bot

自动化文章发布机器人，支持微信公众号发布。

## 功能特性

- 自动获取待发布文章
- 智能生成标题
- 自动获取配图
- 支持微信公众号定时发布

## 环境要求

- Python 3.11+
- Docker (可选)

## 配置说明

需要在项目根目录创建 `.env` 文件，包含以下配置：

```bash
# AI 服务配置
OPENAI_BASE_URL=your_openai_base_url
MOONSHOT_API_KEY=your_moonshot_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=your_deepseek_base_url

# API 服务配置
AISTUDIOX_API_URL=your_aistudio_api_url

# 微信公众号配置
WEIXIN_APPID=your_weixin_appid
WEIXIN_APPSECRET=your_weixin_appsecret
```

## 部署方式

### Docker 部署

1. 构建镜像
```bash
docker build -t article-bot .
```

2. 运行容器
```bash
docker run -d \
  --name article-bot \
  --restart always \
  -v $(pwd)/.env:/app/.env \
  article-bot
```

### 手动部署

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行程序
```bash
python -m main
```

## GitHub Actions

项目已配置自动构建和发布 Docker 镜像的工作流程。需要在 GitHub 仓库设置中配置以下 Secrets：

- `DOCKERHUB_USERNAME`: Docker Hub 用户名
- `DOCKERHUB_PASSWORD`: Docker Hub 访问令牌

## 日志

日志文件位于 `logs` 目录下，按天进行轮转，保留最近 15 天的日志。

## 许可证

MIT License
