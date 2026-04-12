import streamlit as st
import os
from dotenv import load_dotenv
from crew import VideoLocalizationCrew

load_dotenv()

st.set_page_config(page_title="Localization AI", layout="wide")
st.title("Ассистент локализации учебного контента")

st.header("Конфигурация агентов и задач")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("Аналитик")
    role_1 = st.text_input("Role", "Терминологический аналитик", key="r1")
    goal_1 = st.text_area("Goal", "Извлечь структуру и термины из {file_name}", key="g1")
    back_1 = st.text_area("Backstory", "Эксперт в лингвистике и ИТ...", key="b1")

with col_b:
    st.subheader("Редактор")
    role_2 = st.text_input("Role", "Редактор спорных терминов", key="r2")
    goal_2 = st.text_area("Goal", "Найти перевод для новых слов", key="g2")
    back_2 = st.text_area("Backstory", "Специалист по поиску терминологии...", key="b2")

with col_c:
    st.subheader("Переводчик")
    role_3 = st.text_input("Role", "Лингвист-переводчик", key="r3")
    goal_3 = st.text_area("Goal", "Создать summary на русском", key="g3")
    back_3 = st.text_area("Backstory", "Мастер академической локализации...", key="b3")

st.divider()

st.header("Входные данные и База знаний")
col_in1, col_in2 = st.columns(2)

with col_in1:
    source_type = st.radio("Источник лекции:", ["Файл", "YouTube ссылка"])
    
    video_url = ""
    uploaded_file = None
    
    if source_type == "Файл":
        uploaded_file = st.file_uploader("Загрузить TXT/PDF", type=['txt', 'pdf'])
    else:
        video_url = st.text_input("Вставьте ссылку (например, https://www.youtube.com/watch?v=...)")

with col_in2:
    st.subheader("Knowledge Source")
    knowledge_file = st.file_uploader("Загрузить глоссарий (База знаний)", type=['txt'])
    st.caption("Текущая база: `knowledge/glossary.txt`")

st.divider()

st.header("Выполнение и результат")

if st.button("ЗАПУСК", use_container_width=True):
    if uploaded_file or video_url:
        config_data = {
            'role1': role_1, 'goal1': goal_1, 'back1': back_1,
            'role2': role_2, 'goal2': goal_2, 'back2': back_2,
            'role3': role_3, 'goal3': goal_3, 'back3': back_3,
            'file_name': uploaded_file.name if uploaded_file else "YouTube Video",
            'video_url': video_url
        }

        with st.status("Работа агентов...", expanded=True) as status:
            crew_instance = VideoLocalizationCrew(inputs=config_data)
            result = crew_instance.crew().kickoff(inputs=config_data)
            status.update(label="Локализация завершена!", state="complete")

        st.subheader("Итоговое резюме:")
        st.markdown(result.raw)
    else:
        st.error("Пожалуйста, введите данные во второй зоне (файл или ссылку)!")