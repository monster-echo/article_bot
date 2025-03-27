from bots.base import BotBase
import json
import re


class MiaoBot(BotBase):
    interval = 60 * 60  # 每小时执行一次
    file_prefix = "miaoaaaaa-Telegram-"
    output_folder = "apps"
    output_prefix = "apps"
    min_files_required = 3

    def extract_info_from_file(self, file_path):
        """从miaoaaaaa文件中提取信息，只保留有用的内容"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 清理标题中的emoji等特殊字符
            title = article.get("title", "无标题")
            title = re.sub(r"🖼|🗣|🏷️|👉|🚬|🔥|⏺️|🎉|🎁|👍", "", title)

            # 提取作者信息
            author = article.get("author", "")

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 过滤掉广告内容
            if "烟业" in title or "烟业" in description:
                return None

            # 提取下载链接
            download_link = ""
            link_match = re.search(r"下载地址：?(https?://\S+)", description)
            if not link_match:
                link_match = re.search(r"链接：?(https?://\S+)", description)
            if link_match:
                download_link = link_match.group(1)

            # 提取标签
            tags = []
            tag_matches = re.findall(r"#(\w+)", description)
            if tag_matches:
                tags = tag_matches

            # 移除频道、投稿等信息
            description = re.sub(r"频道.*?(?=\n|$)", "", description)
            description = re.sub(r"群聊.*?(?=\n|$)", "", description)
            description = re.sub(r"投稿.*?(?=\n|$)", "", description)
            description = re.sub(r"合作.*?(?=\n|$)", "", description)

            # 移除多余的空行和空格
            description = re.sub(r"\n\s*\n", "\n\n", description).strip()

            # 格式化输出
            info = f"标题：{title.strip()}\n"
            if author:
                info += f"作者：{author}\n"
            if download_link:
                info += f"下载链接：{download_link}\n"
            if tags:
                info += f"标签：{', '.join(tags)}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取miaoaaaaa文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成应用推荐标题的提示词"""
        return f"""
        你现在是一个应用推荐公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于App推荐、实用软件工具的吸引人标题。标题应当简洁明了，突出软件的核心价值和特点，吸引用户下载尝试。
        """

    def generate_article_prompt(self, articles_info):
        """生成应用推荐文章的提示词"""
        return f"""
        你现在是一个应用推荐公众号编辑，需要根据以下几篇文章的信息整合生成一篇软件推荐公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于实用App和软件工具的推荐文章，要求：
        1. 按软件类型分类（如效率工具、生活应用、设计软件、开发工具等）
        2. 每个应用介绍要简洁明了，突出其核心功能和使用场景
        3. 说明适用平台（如iOS、Android、Windows、macOS等）
        4. 重点介绍应用的特色功能和优势
        5. 保留下载链接，方便读者获取
        6. 适当添加一些使用技巧或个人评价
        7. 文末可以总结这些应用的共同特点或推荐理由
        
        生成一篇实用性强、能帮助读者发现优质应用的文章。
        """
