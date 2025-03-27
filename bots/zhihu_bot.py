from bots.base import BotBase
import json
import re


class ZhihuBot(BotBase):
    interval = 60 * 60
    file_prefix = "zhihu_bazaar-Telegram-"
    output_folder = "zhihu"
    output_prefix = "zhihu_digest"
    min_files_required = 3

    def extract_info_from_file(self, file_path):
        """从zhihu_bazaar文件中提取信息"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 提取标题、链接
            title = article.get("title", "无标题")
            if " | 原文" in title:
                title = title.split(" | 原文")[0]
            link = article.get("link", "")

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 提取知乎原文链接
            original_link = ""
            link_match = re.search(
                r'href="(https?://www\.zhihu\.com/[^"]+)"', description
            )
            if link_match:
                original_link = link_match.group(1)

            # 提取Telegraph链接
            telegraph_link = ""
            telegraph_match = re.search(
                r'href="(https?://telegra\.ph/[^"]+)"', description
            )
            if telegraph_match:
                telegraph_link = telegraph_match.group(1)

            # 格式化输出
            info = f"标题：{title.strip()}\n"
            info += f"链接：{link}\n"
            if original_link:
                info += f"知乎链接：{original_link}\n"
            if telegraph_link:
                info += f"文章链接：{telegraph_link}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取zhihu_bazaar文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成知乎精选标题的提示词"""
        return f"""
        你现在是一个知识分享公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于深度思考和热门问答的吸引人标题。标题应当能够引发读者的思考和共鸣，突出内容的知识价值和思想深度。
        """

    def generate_article_prompt(self, articles_info):
        """生成知乎精选文章的提示词"""
        return f"""
        你现在是一个知识分享公众号编辑，需要根据以下几篇文章的信息整合生成一篇知乎精选公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于知乎热门问答和深度思考的综合文章，要求：
        1. 按主题进行分类（如生活哲学、职场经验、社会观察等）
        2. 保留原问题和优质回答的核心观点
        3. 对重要观点进行扩展和解读
        4. 保持思想的深度和知识的广度
        5. 提供多角度的思考和启示
        6. 保留原文中的精彩比喻和案例
        7. 文末可以进行总结和延伸思考
        
        生成一篇有思想深度、知识丰富的优质文章，帮助读者获取知识和启发思考。
        """
