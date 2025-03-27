from bots.base import BotBase
import json
import re


class NewlearnerBot(BotBase):
    interval = 60 * 60
    file_prefix = "NewlearnerChannel-Telegram-"
    output_folder = "NewlearnerChannel"
    output_prefix = "NewlearnerChannel"
    min_files_required = 3

    def extract_info_from_file(self, file_path):
        """从NewlearnerChannel文件中提取信息"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 清理标题中的emoji等特殊字符
            title = article.get("title", "无标题")
            title = re.sub(r"🖼|🪟|🔗|👉", "", title)

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 提取项目链接
            download_link = ""
            link_match = re.search(r"GitHub\s*\|\s*(https?://\S+)", title)
            if not link_match:
                link_match = re.search(r"Dowload\s*\|\s*(https?://\S+)", title)
            if not link_match:
                link_match = re.search(r"链接：?(https?://\S+)", description)
            if link_match:
                download_link = link_match.group(1)

            # 提取标签
            tags = []
            tag_matches = re.findall(r"#(\w+)", title)
            if tag_matches:
                tags = tag_matches

            # 格式化输出
            info = f"标题：{title.strip()}\n"
            if download_link:
                info += f"项目链接：{download_link}\n"
            if tags:
                info += f"标签：{', '.join(tags)}\n"
            if description:
                info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取NewlearnerChannel文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成项目推荐标题的提示词"""
        return f"""
        你现在是一个开发工具和项目推荐公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于开源项目、开发工具和应用推荐的吸引人标题。标题应当简洁明了，突出项目的技术亮点和实用价值。
        """

    def generate_article_prompt(self, articles_info):
        """生成项目推荐文章的提示词"""
        return f"""
        你现在是一个开发工具和项目推荐公众号编辑，需要根据以下几篇文章的信息整合生成一篇推荐公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于开源项目、开发工具和应用的推荐文章，要求：
        1. 按项目类型分类（如开发工具、实用应用、GitHub项目等）
        2. 每个项目介绍要简明扼要，突出其功能特点和技术亮点
        3. 说明适用场景和平台兼容性
        4. 重点介绍项目的创新点和实用价值
        5. 保留GitHub链接或下载链接
        6. 适当添加一些使用建议或技术点评
        7. 文末可以总结这些项目的共同特点或发展趋势
        
        生成一篇既有技术深度又有实用价值的项目推荐文章。
        """
