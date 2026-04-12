from crewai.tools import BaseTool
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeTranscriptTool(BaseTool):
    name: str = "YouTube Transcript Downloader"
    description: str = "Извлекает текст субтитров из видео YouTube по ссылке. На вход принимает полную ссылку."

    def _run(self, video_url: str) -> str:
        try:
            if "v=" in video_url:
                video_id = video_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_url:
                video_id = video_url.split("youtu.be/")[1].split("?")[0]
            else:
                return "Ошибка: Некорректная ссылка."
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_transcript(['ru', 'en'])
            except:
                transcript = transcript_list.find_manually_created_transcript(['en'])

            data = transcript.fetch()
            text = " ".join([item['text'] for item in data])
            return f"Текст видео (первые 3000 символов):\n\n{text[:3000]}"
        except Exception as e:
            return f"Не удалось получить субтитры: {str(e)}"

class AcademicConsistencyTool(BaseTool):
    name: str = "Academic Consistency Checker"
    description: str = "Проверяет текст на соответствие академическому стилю и отсутствие неформальной лексики."

    def _run(self, text: str) -> str:
        forbidden_words = ["типа", "короче", "блин", "как бы", "stuff", "cool"]
        found = [word for word in forbidden_words if word in text.lower()]
        
        if found:
            return f"Внимание: Текст содержит неакадемические выражения: {', '.join(found)}. Пожалуйста, исправьте их."
        return "Текст полностью соответствует академическому стилю."