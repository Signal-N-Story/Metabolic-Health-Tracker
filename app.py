import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import io

# --- CONFIG ---
st.set_page_config(page_title="Metabolic Health Tracker", layout="wide")

# --- EMBEDDED DATA ---
CSV_DATA = """Date,Time,User,State,Glucose (mg/dL),Ketones (mmol/L),Ratio,Weight (lbs),Body Fat %,Blood Pressure
12/09/25,4:40 PM,Theresa,Fed,109,0.2,545.0,,,
12/09/25,4:44 PM,TC,Fed,79,1.0,79.0,,,
12/10/25,6:04 AM,TC,Fasted,93,1.2,77.5,197,,120/80 (est 15.6%)
12/10/25,9:28 AM,TC,Fasted,86,0.8,107.5,,,
Week 45 Monday,6:30 AM,TC,Fasted,,,205,15.2%,
Week 45 Tuesday,6:30 AM,TC,Fasted,88,0.9,97.7,196.5,15.7%,(68 35 bpm)
Week 45 Wednesday,6:30 AM,TC,Fasted,84,0.9,93.3,191.6,15.4%,(71 9:46pm)
Week 45 Thursday,7:00 AM,TC,Fasted,85,,,191.6,14.8%,
Week 45 Friday,7:45 AM,TC,Fasted,88,,,192,14.8%,(100 5:45pm)
Week 45 Saturday,9:30 AM,TC,Fasted,117,,,,,
Week 46 Monday,7:00 AM,TC,Fasted,92,1.0,92.0,200.6,15.3%,
Week 46 Friday,4:45 PM,TC,Fed,105,,,194.0,14.4%,
12/03/25,10:30 AM,TC,Fasted,75,0.3,250.0,200.6,17.5%,
12/03/25,4:35 PM,TC,Fed,75,0.6,125.0,,,
12/03/25,10:00 PM,TC,Fed,89,1.1,80.9,,,"""

# --- INITIALIZE ---
if 'data' not in st.session_state:
    st.session_state.data = pd.read_csv(io.StringIO(CSV_DATA))

st.title("🩸 Metabolic Health Tracker")

# --- INPUT FORM ---
with st.sidebar:
    st.header("📝 Add Entry")
    with st.form("entry", clear_on_submit=True):
        user = st.text_input("User", value="TC")
        date = st.date_input("Date")
        time = st.time_input("Time")
        state = st.selectbox("State", ["Fasted", "Fed"])
        col1, col2 = st.columns(2)
        gluc = col1.number_input("Glucose", 0, value=90)
        ket = col2.number_input("Ketones", 0.0, value=0.0, step=0.1)
        wgt = st.number_input("Weight", 0.0, format="%.1f")
        bf = st.text_input("Body Fat %")
        bp = st.text_input("BP / Notes")
        if st.form_submit_button("Save"):
            ratio = round(gluc / ket, 1) if ket > 0 else 0
            new_row = {
                'Date': date.strftime("%m/%d/%y"), 
                'Time': time.strftime("%I:%M %p"), 
                'User': user, 'State': state, 
                'Glucose (mg/dL)': gluc if gluc>0 else None, 
                'Ketones (mmol/L)': ket if ket>0 else None, 
                'Ratio': ratio if ratio>0 else None, 
                'Weight (lbs)': wgt if wgt>0 else None, 
                'Body Fat %': bf, 'Blood Pressure': bp
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Saved!")

# --- DASHBOARD ---
if not st.session_state.data.empty:
    df = st.session_state.data
    users = list(df['User'].unique())
    sel_user = st.selectbox("Select User", users, index=users.index("TC") if "TC" in users else 0)
    udf = df[df['User'] == sel_user].copy()
    
    # KPI
    def get_last(col): 
        v = udf[col].dropna()
        return v.iloc[-1] if not v.empty else "-"
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Weight", f"{get_last('Weight (lbs)')}")
    c2.metric("Glucose", f"{get_last('Glucose (mg/dL)')}")
    c3.metric("Ketones", f"{get_last('Ketones (mmol/L)')}")
    c4.metric("Ratio", f"{get_last('Ratio')}")
    st.divider()
    
    # CHARTS
    t1, t2 = st.tabs(["Trends", "Data"])
    with t1:
        # Clean data for charting (drop rows without valid data for the specific chart)
        w_data = udf.dropna(subset=['Weight (lbs)'])
        r_data = udf.dropna(subset=['Ratio'])
        
        if not w_data.empty:
            st.plotly_chart(px.line(w_data, x='Date', y='Weight (lbs)', markers=True, title="Weight Trend"), use_container_width=True)
        if not r_data.empty:
            st.plotly_chart(px.bar(r_data, x='Date', y='Ratio', color='State', title="G/K Ratio"), use_container_width=True)
            
    with t2:
        st.dataframe(udf, use_container_width=True)
        st.download_button("Download CSV", udf.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv")
