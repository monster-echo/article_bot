from bots.base import BotBase
import json
import re


class ProgrammingTipBot(BotBase):
    interval = 60 * 60  # 每小时执行一次
    file_prefix = "ProgrammingTip-Telegram-"
    output_folder = "programming_tips"
    output_prefix = "programming_tips"
    min_files_required = 3  # 技术资源可以少一些也能生成有价值的内容

    def extract_info_from_file(self, file_path):
        """从ProgrammingTip文件中提取信息"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 清理标题中的特殊字符
            title = article.get("title", "无标题")
            # 移除多余的 * 符号和其他特殊字符
            title = re.sub(r"\*+", "", title)
            title = title.replace("**", "").strip()

            # 提取作者信息
            author = article.get("author", "")

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 提取GitHub链接
            github_link = ""
            link_match = re.search(r'https://github\.com/[^\s"]+', description)
            if not link_match:
                link_match = re.search(r'https://github\.com/[^\s"]+', title)
            if link_match:
                github_link = link_match.group(0)

            # 格式化输出
            info = f"标题：{title.strip()}\n"
            if github_link:
                info += f"GitHub链接：{github_link}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取ProgrammingTip文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成编程技巧标题的提示词"""
        return f"""
        你现在是一个技术博客和编程教程公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于编程技巧、开发路线图或技术资源分享的吸引人标题。标题应当简洁专业，突出内容的技术价值和学习意义，吸引开发者和编程爱好者阅读。
        """

    def generate_article_prompt(self, articles_info):
        """生成编程技巧文章的提示词"""
        return f"""
        你现在是一个技术博客和编程教程公众号编辑，需要根据以下几篇文章的信息整合生成一篇编程资源分享公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于编程技巧、开发路线图和技术资源的分享文章，要求：
        1. 按技术领域或编程语言分类（如前端、后端、移动开发、数据科学等）
        2. 每个技术资源或编程技巧的介绍要简明扼要，突出其核心价值和应用场景
        3. 说明适合的开发者层次（如入门级、中级、高级）
        4. 重点介绍资源的技术亮点和学习价值
        5. 保留GitHub链接或其他资源链接
        6. 适当添加一些学习建议或个人经验分享
        7. 文末可以总结这些资源的共同价值或技术发展趋势
        
        生成一篇技术深度强、实用价值高的编程资源分享文章，帮助读者提升技术能力。
        """
