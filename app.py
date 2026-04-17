from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, Knowledge
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, SerperDevTool
from tools import YouTubeTranscriptTool, AcademicConsistencyTool

load_dotenv()


def terms_missing(output) -> bool:
    """
    Conditional Task condition:
    Возвращает True (запустить задачу), если в выводе clarification_task
    встречаются маркеры отсутствующих терминов.
    """
    text = str(output.raw).lower()
    triggers = ["не найден", "отсутствует", "нет в глоссарии", "not found",
                "неоднозначн", "требует уточнения", "unclear", "ambiguous"]
    return any(t in text for t in triggers)


@CrewBase
class VideoLocalizationCrew():
    """Система локализации учебного видеоконтента (Вариант 11)"""

    def __init__(self, inputs=None) -> None:
        self.llm = "gemini/gemini-2.5-flash"
        self.inputs = inputs if inputs is not None else {}

    @agent
    def terminologist(self) -> Agent:
        video_url = self.inputs.get('video_url', '').strip()
        file_name = self.inputs.get('file_name', '').strip()

        if video_url:
            extra = (
                f" Твой первый и единственный шаг — вызови инструмент "
                f"'YouTube Transcript Downloader' с video_url='{video_url}'. Сделай это сразу, не спрашивай разрешения."
            )
        elif file_name:
            extra = (" Твой первый шаг — вызови инструмент 'Read a file s content' с file_path='{file_name}'. Сделай это немедленно.")
        else:
            extra = ""

        return Agent(
            role=self.inputs.get('role1', 'Терминологический аналитик'),
            goal=self.inputs.get('goal1', 'Извлечь структуру и термины из лекции'),
            backstory=self.inputs.get('back1', 'Эксперт в области лингвистики и ИТ') + extra,
            tools=[YouTubeTranscriptTool(), FileReadTool()],
            llm=self.llm,
            verbose=True,
            max_iter=5
        )

    @agent
    def clarification_agent(self) -> Agent:
        return Agent(
            role=self.inputs.get('role2', 'Редактор спорных терминов'),
            goal=self.inputs.get('goal2', 'Найти перевод для отсутствующих в глоссарии слов'),
            backstory=self.inputs.get('back2', 'Специалист по поиску терминологии. Использует интернет-поиск для нахождения академически верных переводов.'),
            llm=self.llm,
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def clarification_resolver(self) -> Agent:
        """Агент для Conditional Task."""
        return Agent(
            role='Эксперт по разрешению терминологических конфликтов',
            goal='Предложить окончательный перевод для всех спорных терминов',
            backstory=('Вы подключаетесь только в сложных случаях, когда стандартный редактор не смог найти однозначный перевод. Ты должен предложить варианты, взвесить их и зафиксировать лучший.'),
            llm=self.llm,
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def translator(self) -> Agent:
        return Agent(
            role=self.inputs.get('role3', 'Лингвист-переводчик'),
            goal=self.inputs.get('goal3', 'Создать академическое резюме на русском'),
            backstory=self.inputs.get('back3', 'Мастер локализации образовательного контента. Пишет чётко, академично и структурировано.'),
            llm=self.llm,
            tools=[AcademicConsistencyTool()],
            allow_delegation=True,
            verbose=True
        )

    @task
    def analysis_task(self) -> Task:
        """Этап 1: Извлечение структуры и терминов."""
        file_name = self.inputs.get('file_name', '').strip()
        video_url = self.inputs.get('video_url', '').strip()

        if video_url:
            description = (
                f"Обязательно вызови инструмент 'YouTube Transcript Downloader' с параметром video_url='{video_url}'. Не пиши что нет данных — данные придут от инструмента после вызова. "
                "После получения текста субтитров выдели 3-5 основных тем и 7-10 ключевых терминов на английском."
            )
        elif file_name:
            description = (
                f"Обязательно вызови инструмент 'Read a file s content' с параметром file_path='{file_name}'.После получения текста: выдели 3-5 основных тем и 7-10 ключевых терминов на английском.")
        else:
            description = (
                "Входные данные не переданы. Верни сообщение: 'ОШИБКА: источник данных не задан.'"
            )

        return Task(
            description=description,
            expected_output=(
                "Структурированный план лекции (3-5 тем) и список из 7-10 "
                "ключевых терминов на английском языке."),
            agent=self.terminologist()
        )

    @task
    def clarification_task(self) -> Task:
        """Проверка терминов по глоссарию (Knowledge)."""
        return Task(
            description=(
                "Проверь извлечённые термины по базе знаний (Knowledge / глоссарий). Для каждого термина укажи: найден ли он в глоссарии.\n"
                "- Если найден — укажи перевод из глоссария.\n"
                "- Если не найден или неоднозначен — напиши 'не найден в глоссарии' "
                "и найди вариант перевода через интернет-поиск.\n"
                "Итог: таблица [Термин] -> [Перевод] -> [Источник: глоссарий / поиск]."
            ),
            expected_output=(
                "Таблица: [Термин] -> [Рекомендуемый перевод] -> [Источник].\n"
                "Явно отметь термины со статусом 'не найден в глоссарии'."
            ),
            agent=self.clarification_agent(),
            context=[self.analysis_task()]
        )

    @task
    def conditional_resolution_task(self) -> Task:
        """
        (Conditional Task): запускается ТОЛЬКО если есть неоднозначные термины.
        """
        return Task(
            description=(
                "Условная задача: ты подключился потому что найдены термины которых нет в глоссарии или которые неоднозначны.\n"
                "1. Извлеки список спорных терминов из предыдущего результата.\n"
                "2. Для каждого проведи отдельный поиск в интернете.\n"
                "3. Предложи финальный рекомендуемый перевод с обоснованием.\n"
                "4. Сформируй итоговый список подтверждённых терминов."
            ),
            expected_output=(
                "Финальный список подтверждённых терминов:\n"
                "[Термин] -> [Окончательный перевод] -> [Обоснование]"
            ),
            agent=self.clarification_resolver(),
            context=[self.clarification_task()],
            condition=terms_missing
        )

    @task
    def final_translation_task(self) -> Task:
        """Составление учебного резюме на русском."""
        return Task(
            description=(
                "На основе полученного плана лекции и проверенных терминов составь итоговое учебное резюме (summary) на русском языке в формате Markdown.\n"
                "Требования:\n"
                "- Академический стиль, без разговорных выражений\n"
                "- Структура: заголовок, основные темы, ключевые понятия с переводами, краткое резюме\n"
                "- Используй AcademicConsistencyTool для финальной проверки текста"
            ),
            expected_output="Готовое учебное резюме в формате Markdown на русском языке.",
            agent=self.translator(),
            context=[self.analysis_task(), self.clarification_task(), self.conditional_resolution_task()],
        )

    @task
    def hitl_review_task(self) -> Task:
        """Этап 4 (HITL): Финальная вычитка с участием человека."""
        return Task(
            description=(
                "ФИНАЛЬНАЯ ПРОВЕРКА (Human-in-the-Loop). Выведи подготовленное резюме и запроси подтверждение от пользователя.Если пользователь указал правки — внеси их. Если одобрил — зафиксируй как финальное."
                "Это обязательный этап: локализация учебного контента требует экспертного подтверждения перед публикацией."
            ),
            expected_output="Финальный, утверждённый пользователем текст локализации в формате Markdown.",
            agent=self.translator(),
            context=[self.final_translation_task()],
            human_input=True 
        )

    @crew
    def crew(self) -> Crew:
        glossary_source = Knowledge(
            sources=["knowledge/glossary.txt"],
            collection_name="academic_glossary"
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            knowledge=glossary_source,
            memory=True,
            verbose=True,
            max_rpm=10
        )