SYSTEM_PROMPT = """你是专业内容编辑，将原始内容转化为结构良好的文章。

原标题: {title}
原内容: {content}

**核心任务**:
• 非中文内容翻译成中文（*保留*：代码、技术术语、公司名、人名、产品名、专业术语、URL）
• 创建标题（≤20字符，吸引眼球）
• 提取3-5个关键词
• 分配1-3个分类标签
• Markdown格式

**内容处理**:
• 移除：营销元素、评论区、订阅请求、社媒推广、"欢迎留言"等后续内容
• 提取：第一个有效图片URL作封面、文中实质性源链接

**输出JSON**:
{{
  "title": "中文标题",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "tags": ["分类1", "分类2"],
  "content": "markdown格式内容",
  "ad_indicators": "广告特征说明或空",
  "cover_image": "图片URL或空",
  "source_links": ["URL1", "URL2"]
}}

*注意*：关键词反映核心概念，标签表示分类，source_links仅包含原内容URL。
"""

if __name__ == "__main__":
    # from langchain_ollama import ChatOllama
    from langchain_deepseek import ChatDeepSeek

    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0,
        max_tokens=4096,
        api_base_url="https://api.deepseek.com/v1",
    )

    response = llm.invoke(
        SYSTEM_PROMPT.format(
            title="""白宫开始使用Starlink改善Wi-Fi连接 白宫新闻秘书Karoline Leavitt表示，白宫正在努力“改善Wi-Fi连接”，并采用Starlink解决网络问题。据《纽约时报》报道，白...""",
            content="""<p><b>白宫开始使用Starlink改善Wi-Fi连接<br></b><br>白宫新闻秘书Karoline Leavitt表示，白宫正在努力“改善Wi-Fi连接”，并采用Starlink解决网络问题。据《纽约时报》报道，白宫官员将问题归咎于物业信号不稳定和Wi-Fi基础设施“过载”。<br><br>尽管Starlink终端（如Starlink Mini）可以通过Wi-Fi直接连接，但白宫并未采用这种方式，而是通过数英里外的政府数据中心传输Starlink服务。这一决定引发了利益冲突和伦理问题，尤其是考虑到SpaceX CEO埃隆·马斯克与政府的关系。<br><br>白宫官员称Starlink服务是“捐赠”的，但即便如此，Starlink的稳定性仍无法与有线互联网连接相媲美。<br><br><a href="https://www.theverge.com/news/631716/white-house-starlink-wi-fi-connectivity-musk" target="_blank" rel="noopener" onclick="return confirm('Open this link?\n\n'+this.href);">The Verge</a><br><br><span class="emoji">📮</span><a href="http://t.me/ZaiHuabot" target="_blank" rel="noopener" onclick="return confirm('Open this link?\n\n'+this.href);">投稿</a>  <span class="emoji">☘️</span><a href="http://t.me/zaihuanews" target="_blank" rel="noopener" onclick="return confirm('Open this link?\n\n'+this.href);">频道</a>  <span class="emoji">🌸</span><a href="http://t.me/zaihuachat" target="_blank" rel="noopener" onclick="return confirm('Open this link?\n\n'+this.href);">聊天</a></p>""",
        )
    )

    print(response)
