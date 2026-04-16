from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, Knowledge
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, SerperDevTool
from tools import YouTubeTranscriptTool, AcademicConsistencyTool

load_dotenv()

@CrewBase
class VideoLocalizationCrew():
    """Система локализации учебного видеоконтента (Вариант 11)"""

    def __init__(self, inputs=None) -> None:
        self.llm = "gemini/gemini-2.5-flash-lite"
        self.inputs = inputs if inputs is not None else {}

    @agent
    def terminologist(self) -> Agent:
        return Agent(
            config=self.agents_config['terminologist'] if hasattr(self, 'agents_config') else {},
            role=self.inputs.get('role1'),
            goal=self.inputs.get('goal1'),
            backstory=self.inputs.get('back1'),
            tools=[FileReadTool(), YouTubeTranscriptTool()],
            llm=self.llm,
            verbose=True
        )

    @agent
    def clarification_agent(self) -> Agent:
        return Agent(
            role=self.inputs.get('role2', 'Редактор спорных терминов'),
            goal=self.inputs.get('goal2', 'Найти перевод для отсутствующих в глоссарии слов'),
            backstory=self.inputs.get('back2', 'Специалист по поиску терминологии...'),
            llm=self.llm,
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def translator(self) -> Agent:
        return Agent(
            role=self.inputs.get('role3', 'Лингвист-переводчик'),
            goal=self.inputs.get('goal3', 'Создать академическое резюме на русском'),
            backstory=self.inputs.get('back3', 'Мастер локализации образовательного контента...'),
            llm=self.llm,
            tools=[AcademicConsistencyTool()],
            allow_delegation=True,
            verbose=True
        )

    @task
    def analysis_task(self) -> Task:
        file_name = self.inputs.get('file_name', '')
        video_url = self.inputs.get('video_url', '')

        if video_url:
            description = (
                f"Вызови инструмент YouTubeTranscriptTool с аргументом video_url='{video_url}'. "
                "Это единственный источник данных — не жди другого ввода. "
                "После получения текста выдели 3-5 основных тем и 7-10 ключевых терминов на английском."
            )
        else:
            description = (
                f"Вызови инструмент FileReadTool с аргументом file_path='{file_name}'. "
                "Это единственный источник данных — не жди другого ввода. "
                "После получения текста выдели 3-5 основных тем и 7-10 ключевых терминов на английском."
            )

        return Task(
            description=description,
            expected_output="Структурированный план лекции и список извлеченных терминов.",
            agent=self.terminologist()
        )

    @task
    def clarification_task(self) -> Task:
        return Task(
            description=(
                "Проверь извлечённые термины по базе знаний (Knowledge). "
                "Если термин отсутствует в глоссарии или имеет несколько значений, "
                "найди наиболее подходящий вариант через поиск в интернете."
            ),
            expected_output="Таблица: [Термин] -> [Рекомендуемый перевод] -> [Обоснование].",
            agent=self.clarification_agent(),
            context=[self.analysis_task()]
        )

    @task
    def final_translation_task(self) -> Task:
        return Task(
            description=(
                "На основе полученного плана и проверенных терминов составь итоговое "
                "учебное резюме (summary) на русском языке в формате Markdown. "
                "Убедись, что все термины соответствуют академическому стилю."
            ),
            expected_output="Готовое учебное резюме в формате Markdown.",
            agent=self.translator(),
            context=[self.analysis_task(), self.clarification_task()],
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