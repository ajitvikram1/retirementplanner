import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="Retirement Planner", layout="centered")
st.title("Retirement Planner with Locked Funds")

# --- Inputs ---
st.header("User Inputs")

current_age = st.number_input("Current Age", value=30)
retirement_age = st.number_input("Early Retirement Age", value=36)
lifespan = st.number_input("Expected Lifespan", value=90)

annual_return = st.number_input("Annual Return (%)", value=7.0) / 100
monthly_return = (1 + annual_return) ** (1 / 12) - 1

initial_investment = st.number_input("Initial Investment ($)", value=300_000)
locked_fraction = st.slider("Fraction of Initial Investment Locked", 0.0, 1.0, 0.5)

monthly_locked = st.number_input("Monthly Locked Investment ($)", value=3000)
target_withdrawal = st.number_input("Target Monthly Withdrawal Before Age 60 ($)", value=10_000)

# --- Timeline ---
months_total = (lifespan - current_age) * 12
months_to_retirement = (retirement_age - current_age) * 12
months_to_60 = (60 - current_age) * 12
months_post_60 = (lifespan - 60) * 12
years_to_retirement = retirement_age - current_age

# --- Advanced Investment Editing ---
st.subheader("Monthly and Lump Sum Investment Strategy")

use_advanced = st.checkbox("Use Advanced Yearly Investment Editor", value=True)

if use_advanced:
    default_data = pd.DataFrame({
        "Year": [current_age + i for i in range(years_to_retirement)],
        "Monthly Unlocked Investment ($)": [10000] * years_to_retirement,
        "Annual Lump Sum Investment ($)": [40000] * years_to_retirement
    })
    edited_data = st.data_editor(default_data, use_container_width=True, num_rows="fixed")
    monthly_map = dict(zip(edited_data["Year"], edited_data["Monthly Unlocked Investment ($)"]))
    lump_sum_map = dict(zip(edited_data["Year"], edited_data["Annual Lump Sum Investment ($)"]))
else:
    monthly_unlocked = st.number_input("Monthly Unlocked Investment ($)", value=3000)
    lump_sum = st.number_input("Annual Lump Sum Investment ($)", value=40000)

# --- Initialization ---
unlocked_fund = []
locked_fund = []
total_fund = []

unlocked = initial_investment * (1 - locked_fraction)
locked = initial_investment * locked_fraction

unlocked_fund.append(unlocked)
locked_fund.append(locked)
total_fund.append(unlocked + locked)

# --- Simulation ---
for month in range(1, months_total + 1):
    age = current_age + month / 12
    year = int(np.floor(age))

    # Investment Phase
    if month <= months_to_retirement:
        if use_advanced:
            unlocked += monthly_map.get(year, 0)
            if month % 12 == 1:  # First month of each year
                unlocked += lump_sum_map.get(year, 0)
        else:
            unlocked += monthly_unlocked
            if month % 12 == 1:
                unlocked += lump_sum
        locked += monthly_locked

    # Apply growth
    unlocked *= (1 + monthly_return)
    locked *= (1 + monthly_return)

    # Withdrawal Phase
    if months_to_retirement < month <= months_to_60:
        if unlocked >= target_withdrawal:
            unlocked -= target_withdrawal
        else:
            unlocked = 0

    # Track balances
    unlocked_fund.append(unlocked)
    locked_fund.append(locked)
    total_fund.append(unlocked + locked)

# --- Analysis at Age 60 ---
unlocked_at_60 = unlocked_fund[months_to_60]
locked_at_60 = locked_fund[months_to_60]
combined_at_60 = unlocked_at_60 + locked_at_60

# Compute max sustainable withdrawal after age 60
if monthly_return > 0:
    withdrawal_post_60 = combined_at_60 * (monthly_return * (1 + monthly_return) ** months_post_60) / \
                         ((1 + monthly_return) ** months_post_60 - 1)
else:
    withdrawal_post_60 = combined_at_60 / months_post_60

# --- Display Results ---
st.header("Results")

# Before 60
if unlocked_fund[months_to_60] > 0:
    st.success(f"Unlocked fund at age 60 has a **surplus of ${unlocked_fund[months_to_60]:,.0f}**.")
else:
    st.error("Unlocked fund was **exhausted before age 60**.")

# After 60
st.markdown(f"### Maximum Sustainable Monthly Withdrawal After 60: **${withdrawal_post_60:,.0f}**")
st.markdown(f"Total available at 60: **${combined_at_60:,.0f}**")

# --- Plotting: Fund Balance Over Time ---
st.header("Portfolio Growth and Depletion")

months = np.arange(0, months_total + 1)
ages = current_age + months / 12

df_plot = pd.DataFrame({
    "Age": ages,
    "Unlocked Fund": unlocked_fund,
    "Locked Fund": locked_fund,
    "Total Fund": total_fund
})

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_plot["Age"], y=df_plot["Unlocked Fund"],
                         mode='lines', name='Unlocked Fund', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=df_plot["Age"], y=df_plot["Locked Fund"],
                         mode='lines', name='Locked Fund', line=dict(color='green')))
fig.add_trace(go.Scatter(x=df_plot["Age"], y=df_plot["Total Fund"],
                         mode='lines', name='Total Fund', line=dict(color='black', dash='dash')))

fig.add_vline(x=retirement_age, line=dict(color='orange', dash='dot'),
              annotation_text="Retirement Age", annotation_position="top left")
fig.add_vline(x=60, line=dict(color='gray', dash='dot'),
              annotation_text="Age 60", annotation_position="top right")

fig.update_layout(
    title="Fund Balance Over Time",
    xaxis_title="Age",
    yaxis_title="Fund Value ($)",
    hovermode="x unified",
    legend=dict(x=0, y=1),
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- Optional CSV Download ---
csv = df_plot.to_csv(index=False).encode('utf-8')
st.download_button("Download Fund Trajectory CSV", csv, "fund_projection.csv", "text/csv")

# --- Custom Withdrawal After 60 ---
st.subheader("Custom Post-60 Withdrawal Analysis")
custom_withdrawal_post_60 = st.number_input("Monthly Withdrawal After Age 60 ($)", value=10_000)

fund_post_60 = combined_at_60
fund_post_60_trajectory = []

for i in range(months_post_60):
    fund_post_60 *= (1 + monthly_return)
    fund_post_60 -= custom_withdrawal_post_60
    fund_post_60 = max(fund_post_60, 0)
    fund_post_60_trajectory.append(fund_post_60)

surplus_at_90 = fund_post_60_trajectory[-1]

if surplus_at_90 > 0:
    st.success(f"At age 90, you will have a **surplus of ${surplus_at_90:,.0f}**.")
else:
    st.error("You will **run out of money before age 90** with this post-60 withdrawal amount.")

# --- Plot: Custom Post-60 Withdrawal ---
ages_post_60 = np.arange(60, lifespan, 1 / 12)
df_post60 = pd.DataFrame({
    "Age": ages_post_60,
    "Fund Value": fund_post_60_trajectory
})

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df_post60["Age"], y=df_post60["Fund Value"],
                          mode='lines', name='Post-60 Fund Value', line=dict(color='purple')))

fig2.update_layout(
    title=f"Fund Value After Age 60 with ${custom_withdrawal_post_60:,.0f}/mo Withdrawal",
    xaxis_title="Age",
    yaxis_title="Fund Value ($)",
    template="plotly_white",
    hovermode="x unified"
)

st.plotly_chart(fig2, use_container_width=True)