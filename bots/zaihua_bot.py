from bots.base import BotBase
import json
import re


class ZaihuaBot(BotBase):
    interval = 60 * 60
    file_prefix = "ZaihuaNews-Telegram-"
    output_folder = "ZaihuaNews"
    output_prefix = "ZaihuaNews"
    min_files_required = 3

    def extract_info_from_file(self, file_path):
        """从ZaihuaNews文件中提取信息"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                article = json.load(f)

            # 清理标题中的emoji等特殊字符
            title = article.get("title", "无标题")
            title = re.sub(r"🖼|↩️|🌐|⚡️", "", title)

            # 提取作者信息
            author = article.get("author", "")

            # 从描述中提取纯文本内容
            description = self.clean_html(article.get("description", ""))

            # 格式化输出
            info = f"标题：{title.strip()}\n"
            if author:
                info += f"作者：{author}\n"
            info += f"描述：{description}\n"

            return info
        except Exception as e:
            self.logger.error(f"提取ZaihuaNews文件信息时发生错误: {e}")
            return None

    def generate_title_prompt(self, article_content):
        """生成科技新闻标题的提示词"""
        return f"""
        你现在是一个科技新闻公众号编辑，需要根据以下内容生成一个吸引人的标题，要能增加点击量：
        
        文章内容: {article_content}
        
        请生成一个关于科技产品、数码硬件和软件更新的吸引人标题。标题应当简洁明了，突出产品的创新点或重要更新，能够吸引科技爱好者的兴趣。
        """

    def generate_article_prompt(self, articles_info):
        """生成科技新闻文章的提示词"""
        return f"""
        你现在是一个科技新闻公众号编辑，需要根据以下几篇文章的信息整合生成一篇科技动态公众号文章：
        
        文章集合: {articles_info}
        
        请生成一篇关于最新科技产品、硬件更新和软件发布的综合性文章，要求：
        1. 按产品类型分类（如手机、电脑、软件、AI等）
        2. 每个产品或更新介绍要简洁有力，突出其创新点和技术升级
        3. 对重要产品发布提供详细参数和性能分析
        4. 客观分析产品优缺点，提供专业评测观点
        5. 关注行业动态和发展趋势
        6. 保留重要的产品信息和发布细节
        7. 文末可以总结科技产品的发展方向和未来展望
        
        生成一篇信息量充足、专业性强的科技新闻文章。
        """
