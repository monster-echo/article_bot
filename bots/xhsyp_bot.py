from bots.base import BotBase
import json
import re


class XhsypBot(BotBase):
    interval = 60 * 60
    file_prefix = "xhsyp-Telegram-"
    output_folder = "xhsyp"
    output_prefix = "xhsyp"
    min_files_required = 3

    def extract_info_from_file(self, file_path):
        """从xhsyp文件中提取信息"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 提取标题和链接
            title = article.get("title", "无标题")
            link = article.get("link", "")

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 提取文章正文链接
            article_link = ""
            link_match = re.search(r'href="(https?://telegra\.ph/[^"]+)"', description)
            if link_match:
                article_link = link_match.group(1)

            # 格式化输出
            info = f"标题：{title.strip()}\n"
            info += f"链接：{link}\n"
            if article_link:
                info += f"文章链接：{article_link}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取xhsyp文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成文章标题的提示词"""
        return f"""
        你现在是一个资讯文章公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于时事新闻和社会热点的吸引人标题。标题应当简洁有力，能够准确传达文章的核心观点并引发读者的阅读兴趣。
        """

    def generate_article_prompt(self, articles_info):
        """生成文章的提示词"""
        return f"""
        你现在是一个资讯文章公众号编辑，需要根据以下几篇文章的信息整合生成一篇综合性公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于时事热点和社会话题的深度文章，要求：
        1. 按主题进行分类（如国际时事、社会热点、生活百态等）
        2. 对每个话题进行有深度的分析和解读
        3. 保持客观中立的叙述风格
        4. 提供多角度的思考和观点
        5. 关注社会现象背后的原因和影响
        6. 保留原文重要的观点和链接
        7. 文末可以进行总结和展望
        
        生成一篇有思想深度、有社会价值的优质文章。
        """
