import streamlit as st
import os
from dotenv import load_dotenv
from app import VideoLocalizationCrew

load_dotenv()

st.set_page_config(page_title="Localization AI", layout="wide")
st.title("Ассистент локализации учебного видеоконтента")
st.header("Конфигурация агентов")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.subheader("Аналитик")
    role_1 = st.text_input("Role", "Терминологический аналитик", key="r1")
    goal_1 = st.text_area("Goal", "Извлечь структуру и термины из лекции", key="g1")
    back_1 = st.text_area("Backstory", "Эксперт в области лингвистики и ИТ", key="b1")

with col_b:
    st.subheader("Редактор")
    role_2 = st.text_input("Role", "Редактор терминов", key="r2")
    goal_2 = st.text_area("Goal", "Найти точный перевод для каждого термина", key="g2")
    back_2 = st.text_area("Backstory", "Специалист по поиску терминологии в интернете", key="b2")

with col_c:
    st.subheader("Переводчик")
    role_3 = st.text_input("Role", "Лингвист-переводчик", key="r3")
    goal_3 = st.text_area("Goal", "Создать академическое резюме на русском", key="g3")
    back_3 = st.text_area("Backstory", "Мастер академической локализации контента", key="b3")

st.divider()

st.header("Входные данные и База знаний")

col_in1, col_in2 = st.columns(2)

with col_in1:
    st.subheader("Источник лекции")
    source_type = st.radio("Выберите источник:", ["Файл (TXT/PDF)", "YouTube ссылка"])

    video_url = ""
    uploaded_file = None

    if source_type == "Файл (TXT/PDF)":
        uploaded_file = st.file_uploader("Загрузить транскрипт лекции", type=['txt', 'pdf'])
        if uploaded_file:
            st.success(f"Файл загружен: {uploaded_file.name}")
    else:
        video_url = st.text_input(
            "Вставьте ссылку на YouTube видео",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Видео должно иметь субтитры (auto-generated или ручные)"
        )
        if video_url.strip():
            st.success(f"Ссылка получена: {video_url.strip()[:60]}...")

with col_in2:
    st.subheader("Knowledge Source (Глоссарий)")
    knowledge_file = st.file_uploader(
        "Загрузить глоссарий терминов",
        type=['txt'],
        help="Текстовый файл с парами: Термин -> Перевод"
    )
    st.caption("Текущая база: `knowledge/glossary.txt`")

    if knowledge_file:
        os.makedirs("knowledge", exist_ok=True)
        with open("knowledge/glossary.txt", "wb") as f:
            f.write(knowledge_file.getbuffer())
        st.success("Глоссарий загружен и сохранён!")

    if os.path.exists("knowledge/glossary.txt"):
        with st.expander("Просмотр текущего глоссария"):
            with open("knowledge/glossary.txt", "r", encoding="utf-8") as f:
                st.code(f.read(), language="text")

st.divider()

st.header("Запуск и результат")

with st.container():
    run_button = st.button("ЗАПУСК", use_container_width=True, type="primary")


has_file = uploaded_file is not None
has_url = bool(video_url.strip())

if run_button:
    if not has_file and not has_url:
        st.error("Пожалуйста, укажите источник лекции: загрузите файл или введите YouTube ссылку.")
    elif not os.path.exists("knowledge/glossary.txt"):
        st.warning("Глоссарий не найден. Загрузите файл глоссария или убедитесь что `knowledge/glossary.txt` существует.")
    else:
        file_path = ""
        if has_file:
            os.makedirs("uploads", exist_ok=True)
            file_path = f"uploads/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        config_data = {
            'role1': role_1, 'goal1': goal_1, 'back1': back_1,
            'role2': role_2, 'goal2': goal_2, 'back2': back_2,
            'role3': role_3, 'goal3': goal_3, 'back3': back_3,
            'file_name': file_path,
            'video_url': video_url.strip()
        }

        if has_url:
            st.info(f"Режим: YouTube → {video_url.strip()[:60]}")
        else:
            st.info(f"Режим: Файл → {uploaded_file.name}")

        with st.status("Работа мультиагентной системы...", expanded=True) as status:
            st.write("Аналитик извлекает структуру и термины...")
            
            try:
                crew_instance = VideoLocalizationCrew(inputs=config_data)
                result = crew_instance.crew().kickoff(inputs=config_data)
                
                status.update(label="Локализация завершена", state="complete")
                
            except Exception as e:
                status.update(label="Ошибка выполнения", state="error")
                st.error(f"Ошибка: {str(e)}")
                st.stop()

        st.subheader("Итоговое резюме")
        st.markdown(result.raw)

        st.download_button(
            label="Скачать резюме (.md)",
            data=result.raw,
            file_name="localization_summary.md",
            mime="text/markdown"
        )

elif not run_button:
    st.info("Заполните поля выше и нажмите **ЗАПУСК**")