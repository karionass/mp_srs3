from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type


class YouTubeInput(BaseModel):
    video_url: str = Field(..., description="Полная ссылка на YouTube видео, например https://www.youtube.com/watch?v=XXXX")


class YouTubeTranscriptTool(BaseTool):
    name: str = "YouTube Transcript Downloader"
    description: str = (
        "Извлекает текст субтитров из YouTube видео по ссылке. "
        "Используй этот инструмент передав полную ссылку на видео."
    )
    args_schema: Type[BaseModel] = YouTubeInput

    def _run(self, video_url: str) -> str:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # Парсим video_id из разных форматов
            video_id = None
            if "v=" in video_url:
                video_id = video_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_url:
                video_id = video_url.split("youtu.be/")[1].split("?")[0]
            elif "shorts/" in video_url:
                video_id = video_url.split("shorts/")[1].split("?")[0]

            if not video_id:
                return f"Ошибка: не удалось извлечь ID видео из ссылки '{video_url}'"

            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Пробуем разные языки субтитров
            transcript = None
            for lang in [["ru"], ["en"], ["ru", "en"]]:
                try:
                    transcript = transcript_list.find_transcript(lang)
                    break
                except Exception:
                    pass

            if transcript is None:
                try:
                    # Берём первые доступные (автогенерированные)
                    for t in transcript_list:
                        transcript = t
                        break
                except Exception:
                    pass

            if transcript is None:
                return "Ошибка: субтитры для данного видео недоступны."

            # Новый API youtube-transcript-api >= 0.6 возвращает объект
            raw = transcript.fetch()
            # Поддержка как старого (list of dict), так и нового API (FetchedTranscript)
            if hasattr(raw, '__iter__') and not isinstance(raw, str):
                chunks = []
                for item in raw:
                    if isinstance(item, dict):
                        chunks.append(item.get("text", ""))
                    else:
                        chunks.append(str(getattr(item, "text", item)))
                text = " ".join(chunks)
            else:
                text = str(raw)

            return (
                f"Субтитры получены (язык: {transcript.language}).\n\n"
                f"Текст видео (первые 5000 символов):\n\n{text[:5000]}"
            )

        except ImportError:
            return "Ошибка: установите библиотеку: pip install youtube-transcript-api"
        except Exception as e:
            return f"Не удалось получить субтитры: {str(e)}"


class AcademicInput(BaseModel):
    text: str = Field(..., description="Текст для проверки на академический стиль")


class AcademicConsistencyTool(BaseTool):
    name: str = "Academic Consistency Checker"
    description: str = (
        "Проверяет текст на соответствие академическому стилю. "
        "Выявляет разговорные и неформальные выражения."
    )
    args_schema: Type[BaseModel] = AcademicInput

    def _run(self, text: str) -> str:
        forbidden = [
            "типа", "короче", "блин", "как бы", "stuff", "cool", "окей", "ну вот",
            "ваще", "прикольно", "клёво", "basically", "you know", "kind of", "gonna"
        ]
        found = [w for w in forbidden if w in text.lower()]
        if found:
            return (
                f"Найдены неакадемические выражения: {', '.join(found)}. "
                "Исправьте их на нейтральные академические формулировки."
            )
        return "Текст соответствует академическому стилю."