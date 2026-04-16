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
        return Task(
            description=f"Проанализируй файл {self.inputs.get('file_name')}. Выдели структуру и 5-7 терминов.",
            expected_output="План лекции и список извлеченных терминов.",
            agent=self.terminologist()
        )

    @task
    def clarification_task(self) -> Task:
        return Task(
            description="Проверь термины. Если их нет в Knowledge Base, найди их перевод в сети.",
            expected_output="Уточненный список терминов с переводами.",
            agent=self.clarification_agent(),
            context=[self.analysis_task()]
        )

    @task
    def final_translation_task(self) -> Task:
        return Task(
            description="Напиши итоговое резюме лекции на русском языке в формате Markdown.",
            expected_output="Готовое локализованное учебное резюме.",
            agent=self.translator(),
            context=[self.analysis_task(), self.clarification_task()],
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
            verbose=True
        )