
import streamlit as st
import pandas as pd

GPA_SCALE = [(0, 0.3), (45, 0.7), (50, 1.0), (60, 2.0), (70, 3.0), (80, 4.0)]
CGPA_SCALE = [(0, 1.15), (45, 1.70), (50, 2.15), (60, 2.85), (70, 3.67), (80, 4.00)]

def lookup_gpa(mark): return next((gp for threshold, gp in reversed(GPA_SCALE) if mark >= threshold), 0.0)
def lookup_cgpa(mark): return next((gp for threshold, gp in reversed(CGPA_SCALE) if mark >= threshold), 0.0)

if 'unit_rows' not in st.session_state:
    st.session_state.unit_rows = 4

st.title("Monash WAM calculator")

with st.container():
    st.markdown("### Enter Your Unit Details")

# 2/3 width left‑aligned layout
layout_cols = st.columns([4, 2])

with layout_cols[0]:
    #header row: blank, Mark, Year Level
    header_cols = st.columns([1, 2, 2])
    with header_cols[0]:
        st.markdown(" ")  # blank for the Unit label column
    with header_cols[1]:
        st.markdown("**Mark (%)**")
    with header_cols[2]:
        st.markdown("**Year Level**")

    unit_data = []
    # data rows
    for i in range(st.session_state.unit_rows):
        row_cols = st.columns([1, 2, 2])
        with row_cols[0]:
            st.markdown(f"**Unit {i+1}**")
        with row_cols[1]:
            mark = st.number_input(
                "", min_value=0.0, max_value=100.0, step=1.0,
                key=f"mark_{i}", label_visibility="collapsed"
            )
        with row_cols[2]:
            level = st.selectbox(
                "", ["Year 1", "Year 2+"],
                key=f"level_{i}", label_visibility="collapsed"
            )
        st.markdown("")  # vertical spacing
        unit_data.append((mark, level))

def add_unit():
    st.session_state.unit_rows += 1

def remove_unit():
    if st.session_state.unit_rows > 1:
        st.session_state.unit_rows -= 1

col1, col2 = st.columns([1,5])

with col1:
    st.button("➕ Add Unit", on_click=add_unit)

with col2:
    st.button("➖ Remove Unit", on_click=remove_unit)


columns = ['Mark', 'Year Level of Unit']
df = pd.DataFrame(unit_data, columns=columns)
df['Credit Points'] = 6
df['Year Weight'] = df['Year Level of Unit'].apply(lambda y: 0.5 if y == "Year 1" else 1.0)
df['Weighted CP'] = df['Credit Points'] * df['Year Weight']
df['Weighted Mark'] = df['Mark'] * df['Weighted CP']

total_wcp = df['Weighted CP'].sum()
total_wm = df['Weighted Mark'].sum()
wam = total_wm / total_wcp if total_wcp > 0 else 0.0

if not df.empty:
    df['GPA Point'] = df['Mark'].apply(lookup_gpa)
    df['CGPA Point'] = df['Mark'].apply(lookup_cgpa)
    avg_gpa = df['GPA Point'].mean()
    cgpa = (df['CGPA Point'] * df['Credit Points']).sum() / df['Credit Points'].sum()
else:
    avg_gpa = 0.0
    cgpa = 0.0

if any(mark > 0 for mark, level in unit_data):
    st.divider()
    st.subheader("Your Current Results")
    st.write(f"**WAM:**  {wam:.3f}")
    st.write(f"**GPA:**  {avg_gpa:.3f}")
    st.write(f"**CGPA:** {cgpa:.3f}")
else:
    st.info("Enter details for at least one unit to see your WAM/GPA/CGPA.")

st.divider()
st.subheader("Your WAM Target")

target_wam = st.number_input("Desired overall WAM (%)", min_value=0.0, max_value=100.0, step=0.1)
units_left = st.number_input("Remaining units until graduation", min_value=0, max_value=32, step=1, format="%d")

CP_PER_UNIT = 6
YEAR_WEIGHT_FUTURE = 1.0

if st.button("Compute Required Average Mark"):
    if units_left == 0:
        st.error("You must have > 0 remaining units.")
    else:
        wcp_new = units_left * CP_PER_UNIT * YEAR_WEIGHT_FUTURE
        new_total_wcp = total_wcp + wcp_new
        required_mark = (target_wam * new_total_wcp - total_wm) / wcp_new

        if required_mark > 100:
            st.warning(
                f"To reach a WAM of {target_wam:.1f}%, you’d need an average of "
                f"**{required_mark:.2f}%** across your remaining {units_left} units :( )"
            )
        elif required_mark < 0:
            st.success("You’ve already secured the target WAM.")
        else:
            st.success(
                f"You need an average of **{required_mark:.2f}%** "
                f"on your remaining units to obtain your desired WAM."
            )

st.divider()
st.subheader("Your GPA/CGPA Target")


target_gpa = st.number_input("Final GPA Target", min_value=0.0, max_value=4.0, step=0.01, format="%.2f", key="target_gpa")

if target_gpa and units_left > 0:
    completed_units = df.shape[0]
    total_gpa_points_needed = target_gpa * (completed_units + units_left)
    current_gpa_points = df['GPA Point'].sum()
    required_avg_gpa = (total_gpa_points_needed - current_gpa_points) / units_left


    st.success(f"You need an average GPA of **{required_avg_gpa:.2f}** for your remaining {units_left} units to obtain your desired GPA.")
    if required_avg_gpa > 4.0:
        st.error("Target GPA is unattainable (would require GPA > 4.0).")
    elif required_avg_gpa < 0:
        st.success("You've already exceeded your GPA goal.")
elif units_left == 0:
    st.warning("No remaining units detected. You must have units left for calculation.")

target_cgpa = st.number_input("Final CGPA Target", min_value=0.0, max_value=4.0, step=0.01, format="%.2f", key="target_cgpa")

if target_cgpa and units_left > 0:
    completed_cp = df.shape[0] * CP_PER_UNIT
    remaining_cp = units_left * CP_PER_UNIT
    total_cgpa_points_needed = target_cgpa * (completed_cp + remaining_cp)
    current_cgpa_points = (df['CGPA Point'] * df['Credit Points']).sum()
    required_avg_cgpa = (total_cgpa_points_needed - current_cgpa_points) / remaining_cp

    st.success(f"You need an average CGPA of **{required_avg_cgpa:.2f}** for your remaining {units_left} units to obtain your desired CGPA.")
    if required_avg_cgpa > 4.0:
        st.error("Target CGPA is unattainable (would require CGPA > 4.0).")
    elif required_avg_cgpa < 0:
        st.success("You've already exceeded your CGPA goal.")
elif units_left == 0:
    st.warning("No remaining units detected. You must have units left for calculation.")


with st.expander("Show Table For Full Course"):
    #copy to avoid mutating main df
    df_display = df.copy()

    df_display.index = [f"Unit {i+1}" for i in range(len(df_display))]

    st.dataframe(
        df_display.style.format({
            'Mark':           '{:.1f}',
            'Credit Points':  '{:.0f}',
            'Year Weight':    '{:.1f}',
            'Weighted CP':    '{:.1f}',
            'Weighted Mark':  '{:.1f}',
            'GPA Point':      '{:.2f}',
            'CGPA Point':     '{:.2f}',
        }),
        use_container_width=True
    )


