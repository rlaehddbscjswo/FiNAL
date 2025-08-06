import streamlit as st
from datetime import datetime, date, time, timedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm
import os

kcal_per_day_display = 0
st.sidebar.title('메뉴')
page = st.sidebar.radio("페이지 선택", ['홈', '수면 리듬 관리', '식단 조절'])

# --- 폰트 설정 함수 추가 ---
def load_local_font(font_filename="GmarketSansTTFBold.ttf", default_font="Malgun Gothic"):
    """
    Looks for a font file in the current working directory and applies it to matplotlib.
    If not found, it falls back to a default font.
    """
    font_path = os.path.join(os.getcwd(), font_filename)
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)

    else:
        plt.rc('font', family=default_font) # Fallback font
    plt.rcParams['axes.unicode_minus'] = False # Prevents issues with minus signs in Korean

# 폰트 적용
load_local_font()

# 페이지 레이아웃을 'centered'로 설정하여 전체 내용을 가운데 정렬합니다.
st.set_page_config(page_title="생활 관리 프로그램", layout="centered")

# 👇👇👇 세션 상태 초기화: 모든 페이지에서 사용할 핵심 변수들을 미리 정의합니다. 👇👇👇
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'input'
if 'sleep_mode_input' not in st.session_state:
    st.session_state.sleep_mode_input = '생체 리듬 생성'
if 'sleep_start_input' not in st.session_state:
    st.session_state.sleep_start_input = time(23, 0)
if 'wake_time_input' not in st.session_state:
    st.session_state.wake_time_input = time(7, 0)
if 'sleep_data_input' not in st.session_state:
    st.session_state.sleep_data_input = [(time(23, 0), time(7, 0)) for _ in range(3)]
if 'sleep_start_graph_input' not in st.session_state:
    st.session_state.sleep_start_graph_input = time(23, 0)
if 'wake_time_graph_input' not in st.session_state:
    st.session_state.wake_time_graph_input = time(7, 0)
if 'height_input' not in st.session_state:
    st.session_state.height_input = 170
if 'weight_input' not in st.session_state:
    st.session_state.weight_input = 65
if 'goal_weight_input' not in st.session_state:
    st.session_state.goal_weight_input = 60
if 'gender_input' not in st.session_state:
    st.session_state.gender_input = '남성'
if 'activity_input' not in st.session_state:
    st.session_state.activity_input = '보통'
if 'goal_date_input' not in st.session_state:
    st.session_state.goal_date_input = date.today() + timedelta(days=30)
# 👆👆👆 세션 상태 초기화 끝 👆👆👆


# REM 수면 그래프를 그리는 헬퍼 함수
def draw_rem_graph(sleep_start_dt, actual_sleep_duration_minutes, desired_wake_time_dt=None, show_desired_line=False):
    """
    REM 수면 주기 그래프를 그립니다.
    sleep_start_dt: 수면 시작 datetime 객체
    actual_sleep_duration_minutes: 실제 수면 시간 (분) - REM 곡선 생성에 사용
    desired_wake_time_dt: 원하는 깨는 시간 datetime 객체 (초록색 선으로 표시)
    show_desired_line: 원하는 깨는 시간을 초록색 선으로 표시할지 여부
    """
    fig, ax = plt.subplots(figsize=(10, 4))

    plot_x_max_minutes = actual_sleep_duration_minutes
    if show_desired_line and desired_wake_time_dt:
        temp_desired_wake_dt = desired_wake_time_dt
        if temp_desired_wake_dt < sleep_start_dt:
            temp_desired_wake_dt += timedelta(days=1)
        elapsed_minutes_to_desired_wake = (temp_desired_wake_dt - sleep_start_dt).total_seconds() / 60
        plot_x_max_minutes = max(actual_sleep_duration_minutes, elapsed_minutes_to_desired_wake) * 1.5
    
    plot_x_max_minutes = max(plot_x_max_minutes, 180) 

    x = np.linspace(0, plot_x_max_minutes, int(plot_x_max_minutes) * 2)
    y = np.zeros_like(x)

    rem_cycle_duration = 90
    rem_peak_duration = 20
    rem_start_offset = 60

    num_cycles_for_rem_curve = int(actual_sleep_duration_minutes / rem_cycle_duration)

    for i in range(num_cycles_for_rem_curve):
        rem_start_time = i * rem_cycle_duration + rem_start_offset
        rem_end_time = rem_start_time + rem_peak_duration * (1 + i * 0.1)

        rem_end_time_clipped = min(rem_end_time, actual_sleep_duration_minutes)

        for j, time_point in enumerate(x):
            if rem_start_time <= time_point <= rem_end_time_clipped:
                center = (rem_start_time + rem_end_time) / 2
                width = (rem_end_time - rem_start_time) / 2
                intensity = 1 - ((time_point - center) / width)**2
                y[j] = max(y[j], intensity * (0.5 + i * 0.1))

    ax.plot(x / 60, y, color='skyblue', linewidth=2)
    ax.fill_between(x / 60, y, color='skyblue', alpha=0.3)

    ax.set_title("REM 수면 주기 시뮬레이션")
    ax.set_xlabel("수면 경과 시간 (시간)")
    ax.set_ylabel("REM 수면 강도 (상대적)")
    ax.set_yticks([])
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_xlim(0, plot_x_max_minutes / 60)
    ax.set_ylim(0, 1.2)

    st.write("💡 **권장 깨는 시간 (90분 수면 주기에 맞춰):**")
    recommended_wake_times = []
    current_cycle_time_rec = sleep_start_dt
    current_cycle_time_rec += timedelta(minutes=rem_cycle_duration) 
    
    while (current_cycle_time_rec - sleep_start_dt).total_seconds() / 60 <= plot_x_max_minutes / 60:
        elapsed_hours_rec = (current_cycle_time_rec - sleep_start_dt).total_seconds() / 3600
        
        if 0 < elapsed_hours_rec <= plot_x_max_minutes / 60:
            ax.axvline(elapsed_hours_rec, color='red', linestyle='-', linewidth=2, label='권장 기상 시간')
            recommended_wake_times.append(current_cycle_time_rec.strftime("%H:%M"))
            ax.text(elapsed_hours_rec, 1.15, f'{current_cycle_time_rec.strftime("%H:%M")}', rotation=90, va='bottom', ha='center', fontsize=9, color='red', weight='bold')
        current_cycle_time_rec += timedelta(minutes=rem_cycle_duration)

    if recommended_wake_times:
        st.success(f"➡️ {', '.join(recommended_wake_times)}")
    else:
        st.info("현재 설정된 수면 시간 내에 90분 주기와 일치하는 권장 기상 시간이 없습니다.")

    if show_desired_line and desired_wake_time_dt:
        temp_desired_wake_dt = desired_wake_time_dt
        if temp_desired_wake_dt < sleep_start_dt:
            temp_desired_wake_dt += timedelta(days=1)
        
        elapsed_hours_desired = (temp_desired_wake_dt - sleep_start_dt).total_seconds() / 3600
        
        if 0 <= elapsed_hours_desired <= plot_x_max_minutes / 60:
            ax.axvline(elapsed_hours_desired, color='green', linestyle='--', linewidth=2, label='원하는 기상 시간')
            ax.text(elapsed_hours_desired, 1.05, f'{desired_wake_time_dt.strftime("%H:%M")}', rotation=90, va='bottom', ha='center', fontsize=9, color='green', weight='bold')

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper left')

    st.pyplot(fig)

if page == '홈':
    st.title("🧠 생활 관리 프로그램")
    st.write("왼쪽 사이드바에서 원하는 기능을 선택해주세요.")

# ───────────────────────────────
# 😴 섹션 1: 수면 리듬 관리
# ───────────────────────────────
if page == '수면 리듬 관리':
    st.title('😴 수면 리듬 관리')
    
    # "결과 보기" 버튼을 눌렀을 때만 결과 페이지를 표시합니다.
    if st.session_state.current_view == 'sleep_results':
        mode = st.session_state.sleep_mode_input
        st.subheader("결과")
        
        if mode == "생체 리듬 생성":
            sleep_start = st.session_state.sleep_start_input
            wake_time = st.session_state.wake_time_input
            st.success(f"🎯 목표 수면 시간: {sleep_start} ~ {wake_time}")
            st.write("- 수면 주기(90분 단위)에 따라 기상 시간을 조정하면 더 개운하게 일어날 수 있어요.")
            st.write("- 예: 23:00에 자면 → 05:30 / 07:00 / 08:30 기상 추천")

            sleep_start_dt = datetime.combine(date.today(), sleep_start)
            wake_time_dt = datetime.combine(date.today(), wake_time)

            if wake_time_dt < sleep_start_dt:
                wake_time_dt += timedelta(days=1)

            total_sleep_duration_minutes = (wake_time_dt - sleep_start_dt).total_seconds() / 60
            
            if total_sleep_duration_minutes > 0:
                draw_rem_graph(sleep_start_dt, total_sleep_duration_minutes, wake_time_dt, show_desired_line=True)
                st.info("REM 수면 강도(파란색 영역)는 실제 수면 시간까지만 표시되며, 그 이후에는 REM 활동이 없으므로 선이 0으로 이어집니다.")
            else:
                st.warning("수면 시작 시간이 기상 시간보다 늦을 수 없습니다. (총 수면 시간이 0분 이하)")

        elif mode == "생체 리듬 이어나가기":
            sleep_data = st.session_state.sleep_data_input
            total_minutes = 0
            total_start_minutes_from_midnight = 0
            num_valid_sleep_entries = 0

            for s, e in sleep_data:
                start_dt = datetime.combine(date.today(), s)
                end_dt = datetime.combine(date.today(), e)
                
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)

                diff = (end_dt - start_dt).total_seconds() / 60
                if diff > 0:
                    total_minutes += diff
                    total_start_minutes_from_midnight += s.hour * 60 + s.minute
                    num_valid_sleep_entries += 1
            
            if num_valid_sleep_entries > 0:
                avg_minutes = total_minutes / num_valid_sleep_entries
                hours = int(avg_minutes // 60)
                minutes = int(avg_minutes % 60)
                st.success(f"🕒 평균 수면 시간: {hours}시간 {minutes}분")

                avg_start_minutes_from_midnight = total_start_minutes_from_midnight / num_valid_sleep_entries
                avg_start_hour = int(avg_start_minutes_from_midnight // 60)
                avg_start_minute = int(avg_start_minutes_from_midnight % 60)
                avg_sleep_start_time = time(avg_start_hour, avg_start_minute)

                st.write("#### REM 수면 주기 그래프 (평균 수면 시간 기준)")
                st.info(f"이 그래프는 최근 3일간의 평균 수면 시작 시간({avg_sleep_start_time})과 평균 수면 시간을 기반으로 합니다.")
                
                assumed_sleep_start_dt = datetime.combine(date.today(), avg_sleep_start_time)
                avg_wake_time_dt = assumed_sleep_start_dt + timedelta(minutes=avg_minutes)
                
                draw_rem_graph(assumed_sleep_start_dt, avg_minutes, avg_wake_time_dt, show_desired_line=True)
                st.info("REM 수면 강도(파란색 영역)는 실제 수면 시간까지만 표시되며, 그 이후에는 REM 활동이 없으므로 선이 0으로 이어집니다.")
            else:
                st.warning("수면 데이터를 입력해주세요.")
        
        elif mode == "REM 수면 그래프 그리기":
            sleep_start_graph = st.session_state.sleep_start_graph_input
            wake_time_graph = st.session_state.wake_time_graph_input

            st.success(f"😴 설정된 수면 시간: {sleep_start_graph} ~ {wake_time_graph}")
            st.write("#### REM 수면 주기 그래프")

            sleep_start_dt = datetime.combine(date.today(), sleep_start_graph)
            wake_time_dt = datetime.combine(date.today(), wake_time_graph)

            if wake_time_dt < sleep_start_dt:
                wake_time_dt += timedelta(days=1)

            total_sleep_duration_minutes = (wake_time_dt - sleep_start_dt).total_seconds() / 60

            if total_sleep_duration_minutes > 0:
                draw_rem_graph(sleep_start_dt, total_sleep_duration_minutes, wake_time_dt, show_desired_line=True)
                st.info("REM 수면 강도(파란색 영역)는 실제 수면 시간까지만 표시되며, 그 이후에는 REM 활동이 없으므로 선이 0으로 이어집니다.")
            else:
                st.warning("수면 시작 시간이 기상 시간보다 늦을 수 없습니다. (총 수면 시간이 0분 이하)")


        if st.button("결과 닫기", key="close_sleep_results_btn"):
            st.session_state.current_view = 'input'
            st.rerun()

    else:
        # 수면 입력 화면
        mode = st.radio("수면 리듬 관리 방식 선택", ["생체 리듬 생성", "생체 리듬 이어나가기", "REM 수면 그래프 그리기"], key="sleep_mode_radio")
        st.session_state.sleep_mode_input = mode  # 라디오 버튼 선택값도 세션 상태에 저장

        if mode == "생체 리듬 생성":
            st.time_input("원하는 자는 시간", value=st.session_state.sleep_start_input, key="sleep_start_input")
            st.time_input("원하는 깨는 시간", value=st.session_state.wake_time_input, key="wake_time_input")
            
            if st.button("수면 리듬 결과 보기", key="show_sleep_results_btn"):
                st.session_state.current_view = 'sleep_results'
                st.rerun()

        elif mode == "생체 리듬 이어나가기":
            st.write("최근 3일간 수면 시간 입력:")
            sleep_data = []
            for i in range(3):
                st.markdown(f"**{i+1}일 전**")
                start = st.time_input(f"자는 시간 {i+1}", value=st.session_state.sleep_data_input[i][0], key=f"start_{i}")
                end = st.time_input(f"깨는 시간 {i+1}", value=st.session_state.sleep_data_input[i][1], key=f"end_{i}")
                sleep_data.append((start, end))
            
            if st.button("수면 리듬 결과 보기", key="show_sleep_results_btn_continue"):
                st.session_state.current_view = 'sleep_results'
                st.session_state.sleep_data_input = sleep_data
                st.rerun()

        elif mode == "REM 수면 그래프 그리기":
            st.time_input("자는 시간", value=st.session_state.sleep_start_graph_input, key="sleep_start_graph_input")
            st.time_input("깨는 시간", value=st.session_state.wake_time_graph_input, key="wake_time_graph_input")
            
            if st.button("REM 수면 그래프 그리기", key="show_rem_graph_btn"):
                st.session_state.current_view = 'sleep_results'
                st.rerun()

# ───────────────────────────────
# 🥗 섹션 2: 식단 조절
# ───────────────────────────────
if page == '식단 조절':
    st.title('🥗 식단 관리')
    
    # "결과 보기" 버튼을 눌렀을 때만 결과 페이지를 표시합니다.
    if st.session_state.current_view == 'diet_results':
        height = st.session_state.height_input
        weight = st.session_state.weight_input
        goal_weight = st.session_state.goal_weight_input
        gender = st.session_state.gender_input
        activity = st.session_state.activity_input
        goal_date = st.session_state.goal_date_input
        st.subheader("결과")
        days_left = (goal_date - date.today()).days
        weight_diff = weight - goal_weight
        
        date_adjustment_message = ""
        if days_left <= 0:
            days_left = 30
            goal_date = date.today() + timedelta(days=30)
            date_adjustment_message = "⚠️ 목표 달성 날짜가 오늘이거나 과거이므로, 계산을 위해 목표 날짜를 오늘로부터 30일 뒤로 임시 설정했습니다."

        if gender == "남성":
            bmr = 66 + (13.7 * weight) + (5 * height) - (6.8 * 20)
        else:
            bmr = 655 + (9.6 * weight) + (1.8 * height) - (4.7 * 20)

        activity_factor = {"낮음": 1.2, "보통": 1.55, "높음": 1.9}[activity]
        tdee = bmr * activity_factor
        
        daily_calorie_change_needed = (weight_diff * 7700) / days_left
        
        target_kcal = tdee - daily_calorie_change_needed

        min_healthy_kcal = 1200 if gender == "여성" else 1500

        if weight_diff < 0:
            if target_kcal < tdee + 200:
                original_days_left = (st.session_state.goal_date_input - date.today()).days
                adjusted_days_left = original_days_left
                while target_kcal < tdee + 200:
                    adjusted_days_left += 7
                    if adjusted_days_left <= 0:
                        adjusted_days_left = 7
                    daily_calorie_change_needed = (weight_diff * 7700) / adjusted_days_left
                    target_kcal = tdee - daily_calorie_change_needed
                    if adjusted_days_left > 365 * 5:
                        break
                if adjusted_days_left > original_days_left:
                    date_adjustment_message += f" 📈 건강한 체중 증량을 위해 목표 달성 날짜를 {adjusted_days_left - original_days_left}일 연장했습니다."
                days_left = adjusted_days_left
                kcal_per_day_display = -daily_calorie_change_needed
        
        else:
            if target_kcal < min_healthy_kcal:
                original_days_left = (st.session_state.goal_date_input - date.today()).days
                adjusted_days_left = original_days_left
                while target_kcal < min_healthy_kcal:
                    adjusted_days_left += 7
                    if adjusted_days_left <= 0:
                        adjusted_days_left = 7
                    daily_calorie_change_needed = (weight_diff * 7700) / adjusted_days_left
                    target_kcal = tdee - daily_calorie_change_needed
                    if adjusted_days_left > 365 * 5:
                        break
                if adjusted_days_left > original_days_left:
                    date_adjustment_message += f" 📉 건강한 체중 감량을 위해 목표 달성 날짜를 {adjusted_days_left - original_days_left}일 연장했습니다."
                days_left = adjusted_days_left
            kcal_per_day_display = daily_calorie_change_needed

        breakfast = target_kcal * 0.5
        lunch = target_kcal * 0.33
        dinner = target_kcal * 0.17

        st.subheader("📊 식단 결과 요약")
        if date_adjustment_message:
            st.warning(date_adjustment_message)
        st.write(f"✔️ 남은 일수: {days_left}일")
        
        if weight_diff < 0:
            st.write(f"✔️ 일일 증량 목표: {abs(kcal_per_day_display):.0f} kcal")
        else:
            st.write(f"✔️ 일일 감량 목표: {abs(kcal_per_day_display):.0f} kcal")
            
        st.write(f"✔️ 일일 섭취 권장량: {target_kcal:.0f} kcal")

        st.markdown(f"""
        - 🥣 아침: **{breakfast:.0f} kcal**
        - 🍱 점심: **{lunch:.0f} kcal**
        - 🌙 저녁: **{dinner:.0f} kcal**
        """)

        st.markdown("---")
        st.subheader("🗓️ 일별 식단 계획")

        if days_left > 0:
            daily_plan_data = []
            current_date = date.today()
            adjusted_goal_date_for_display = date.today() + timedelta(days=days_left)
            while current_date <= adjusted_goal_date_for_display:
                daily_plan_data.append({
                    "날짜": current_date.strftime("%Y-%m-%d"),
                    "총 권장 칼로리": f"{target_kcal:.0f} kcal",
                    "아침": f"{breakfast:.0f} kcal",
                    "점심": f"{lunch:.0f} kcal",
                    "저녁": f"{dinner:.0f} kcal"
                })
                current_date += timedelta(days=1)
            
            df_daily_plan = pd.DataFrame(daily_plan_data)
            st.dataframe(df_daily_plan, use_container_width=True)
        else:
            st.info("목표 달성 날짜가 설정되지 않았거나 과거이므로 일별 식단 계획을 표시할 수 없습니다.")
        if st.button("결과 닫기", key="close_diet_results_btn"):
            st.session_state.current_view = 'input'
            st.rerun()

    else:
        # 식단 입력 화면
        height = st.number_input("현재 키 (cm)", min_value=100, max_value=250, value=st.session_state.height_input, key="height_input")
        weight = st.number_input("현재 몸무게 (kg)", min_value=30, max_value=200, value=st.session_state.weight_input, key="weight_input")
        goal_weight = st.number_input("목표 몸무게 (kg)", min_value=30, max_value=200, value=st.session_state.goal_weight_input, key="goal_weight_input")
        gender = st.selectbox("성별", ["남성", "여성"], index=["남성", "여성"].index(st.session_state.gender_input), key="gender_input")
        activity = st.selectbox("활동량", ["낮음", "보통", "높음"], index=["낮음", "보통", "높음"].index(st.session_state.activity_input), key="activity_input")
        goal_date = st.date_input("목표 달성 날짜", value=st.session_state.goal_date_input, min_value=date.today(), key="goal_date_input")

        if st.button("식단 조절 결과 보기", key="show_diet_results_btn"):
            st.session_state.current_view = 'diet_results'
            st.rerun()