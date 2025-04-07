import requests
from translations.base import TranslationBase
from prompts.translation_prompt import SYSTEM_PROMPT
from config import AISTUDIOX_API_URL


class AIPostTranslation(TranslationBase):
    """
    AIPost translation class.
    """

    interval = 60 * 5  # 5 minutes

    get_posts_url = f"{AISTUDIOX_API_URL}/api/posts?page=1&pageSize=10&source=AI%20Post%20—%20Artificial%20Intelligence&tags=&status=draft"
    put_posts_url = f"{AISTUDIOX_API_URL}/api/posts"

    def run(self):
        response = requests.get(self.get_posts_url)
        response.raise_for_status()

        data = response.json()
        if not data["posts"]:
            self.logger.info("No new articles found.")
            return

        for post in data["posts"]:
            id = post["id"]
            content = post["content"]
            translatedText = self.llm.invoke(
                SYSTEM_PROMPT.format(content=content, language=self.language),
            ).content

            self.logger.info(f"Translated post {id}: {translatedText}")

            formData = {
                "id": id,
                "formattedContent": translatedText,
                "status": "PENDING",
            }
            response = requests.put(self.put_posts_url, json=formData)
            response.raise_for_status()
            self.logger.info(f"Post {id} updated successfully.")
