from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class YouTubeTranscriptTool(BaseTool):
    name: str = "YouTube Transcript Downloader"
    description: str = "Извлекает текст субтитров из видео YouTube по ссылке."

    def _run(self, video_url: str) -> str:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            if "v=" in video_url:
                video_id = video_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_url:
                video_id = video_url.split("youtu.be/")[1].split("?")[0]
            else:
                return "Ошибка: Некорректная ссылка YouTube."

            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_transcript(["ru", "en"])
            except Exception:
                transcript = transcript_list.find_manually_created_transcript(["en"])

            data = transcript.fetch()
            text = " ".join([item["text"] for item in data])
            return f"Текст видео (первые 4000 символов):\n\n{text[:4000]}"
        except ImportError:
            return "Ошибка: установите библиотеку: pip install youtube-transcript-api"
        except Exception as e:
            return f"Не удалось получить субтитры: {str(e)}"


class AcademicConsistencyTool(BaseTool):
    name: str = "Academic Consistency Checker"
    description: str = "Проверяет текст на соответствие академическому стилю."

    def _run(self, text: str) -> str:
        forbidden_words = ["типа", "короче", "блин", "как бы", "stuff", "cool", "окей", "ну вот"]
        found = [w for w in forbidden_words if w in text.lower()]
        if found:
            return f"Найдены неакадемические выражения: {', '.join(found)}. Исправьте их."
        return "Текст соответствует академическому стилю."