from bots.base import BotBase
import json
import re


class HackerNewsBot(BotBase):
    interval = 60 * 60  # 每小时执行一次
    file_prefix = "thehackernews-Telegram-"
    output_folder = "hackernews"
    output_prefix = "hackernews"
    min_files_required = 3  # 网络安全信息可以少一些也能生成有价值的内容

    def extract_info_from_file(self, file_path):
        """从thehackernews文件中提取信息，只保留标题和描述"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 清理标题和作者信息
            title = article.get("title", "无标题")
            # 移除可能的emoji和其他特殊字符
            title = re.sub(r"[🔸🔹🔻🔺⚠️]", "", title)

            # 提取作者信息
            author = article.get("author", "")

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 移除广告和营销链接
            description = re.sub(r"Sign up for.*?(?=\n|$)", "", description)
            description = re.sub(r"Join them.*?(?=\n|$)", "", description)

            # 移除多余的空行
            description = re.sub(r"\n\s*\n", "\n\n", description).strip()

            # 只返回标题和描述
            info = f"标题：{title.strip()}\n"
            if author:
                info += f"作者：{author}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取thehackernews文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成科技新闻标题的提示词"""
        return f"""
        你现在是一个科技资讯公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于科技领域的吸引人标题，标题应当引人注目且专业，能引起科技爱好者的兴趣。标题可以涵盖科技创新、数字产品、AI发展、编程技术、科技公司动态等各方面内容。
        """

    def generate_article_prompt(self, articles_info):
        """生成科技文章的提示词"""
        return f"""
        你现在是一个科技资讯公众号编辑，需要根据以下几篇文章的信息整合生成一篇综合性科技资讯公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于最新科技动态、创新趋势和技术发展的公众号文章，要求：
        1. 按科技领域分类（如AI、硬件、软件开发、互联网服务、科技公司动态等）
        2. 解释复杂的技术概念，使非专业读者也能理解
        3. 重点关注最新的技术突破和科技趋势
        4. 对重要科技事件提供详细分析和背景信息
        5. 包含实用的科技产品使用建议和观点评论
        6. 保留重要的技术细节和关键链接
        7. 文末总结当前科技发展态势并提供见解
        
        生成一篇既专业又实用的科技资讯文章，帮助读者了解和把握最新科技动态。
        """
