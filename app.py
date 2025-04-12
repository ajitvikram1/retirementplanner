import streamlit as st
import numpy as np

st.title("Custom Retirement Planner")

# --- Inputs ---
st.header("Investment Inputs")

current_age = st.number_input("Current age", value=30)
retirement_age = st.number_input("Early retirement age (can access weekday funds)", value=36)

# Dynamically calculate years of investing
default_years_investing = max(retirement_age - current_age, 0)
years_investing = st.number_input("Years of investing", value=default_years_investing, min_value=0)

final_age = st.number_input("Expected lifespan", value=90)
annual_return = st.number_input("Annual return (%)", value=7.0) / 100
investing_days_per_year = st.number_input("Weekdays invested per year", value=260)

initial_investment = st.number_input("Total initial investment ($)", value=300000)
initial_locked_fraction = st.slider("Fraction of initial investment locked until full retirement", 0.0, 1.0, 0.5)

monthly_investment = st.number_input("Monthly investment amount ($)", value=3000)
lock_monthly_investment = st.checkbox("Monthly investment locked until full retirement", value=True)

monthly_withdrawal = st.number_input("Target monthly withdrawal ($)", value=10000)

# --- Derived Values ---
total_investing_days = int(years_investing * investing_days_per_year)
r_daily = (1 + annual_return) ** (1/365) - 1
r_annual = annual_return

# --- Time Periods ---
years_until_retirement = retirement_age - current_age
years_until_full_retirement = final_age - current_age
years_between_retirements = final_age - retirement_age
years_post_lock = final_age - 60
years_pre_lock = 60 - retirement_age

# --- Step 1: How much you need at retirement age ---
withdrawals_pre_lock = monthly_withdrawal * 12
withdrawals_post_lock = withdrawals_pre_lock

def present_value(amount, rate, n_years):
    return amount * (1 - (1 + rate) ** -n_years) / rate

need_at_retirement = present_value(withdrawals_pre_lock, r_annual, years_pre_lock)
need_at_60 = present_value(withdrawals_post_lock, r_annual, years_post_lock)

# --- Step 2: FV of current unlocked investments ---
unlocked_initial = initial_investment * (1 - initial_locked_fraction)
fv_unlocked_initial = unlocked_initial * (1 + r_annual) ** years_until_retirement

# --- Step 3: FV of locked initial and monthly investments at 60 ---
locked_initial = initial_investment * initial_locked_fraction
fv_locked_initial = locked_initial * (1 + r_annual) ** (60 - current_age)

if lock_monthly_investment:
    monthly_fv_at_retirement = monthly_investment * (((1 + r_annual / 12) ** (years_investing * 12) - 1) / (r_annual / 12))
    fv_monthly_locked = monthly_fv_at_retirement * (1 + r_annual) ** (60 - retirement_age)
else:
    monthly_fv_at_retirement = monthly_investment * (((1 + r_annual / 12) ** (years_investing * 12) - 1) / (r_annual / 12))
    fv_monthly_locked = 0  # None of it locked

total_locked_fv = fv_locked_initial + fv_monthly_locked

# --- Step 4: Shortfall at 60 and discount it back ---
shortfall_at_60 = max(need_at_60 - total_locked_fv, 0)
shortfall_discounted_to_retirement = shortfall_at_60 / ((1 + r_annual) ** (60 - retirement_age))

# --- Step 5: Remaining amount needed from weekday investments ---
needed_from_weekdays = max(need_at_retirement - fv_unlocked_initial, 0)
total_needed_from_weekdays = needed_from_weekdays + shortfall_discounted_to_retirement

# --- Step 6: Solve for daily investment ---
denominator = ((1 + r_daily) ** total_investing_days - 1) / r_daily
weekday_investment = total_needed_from_weekdays / denominator

# --- Display Results ---
st.header("Results")
st.write(f"### Amount needed at age {retirement_age}: ${need_at_retirement:,.0f}")
st.write(f"Future value of unlocked initial investment: ${fv_unlocked_initial:,.0f}")
st.write(f"Initial weekday investment shortfall: ${needed_from_weekdays:,.0f}")
st.write(f"Shortfall from locked funds (at 60): ${shortfall_at_60:,.0f}")
st.write(f"Shortfall discounted to age {retirement_age}: ${shortfall_discounted_to_retirement:,.0f}")
st.success(f"Required investment per weekday: ${weekday_investment:,.2f}")

st.write("---")
st.write(f"### Locked investment future value at age 60: ${total_locked_fv:,.0f}")
st.write(f"Required at age 60 to fund to age {final_age}: ${need_at_60:,.0f}")
if shortfall_at_60 > 0:
    st.error(f"You will have a shortfall of ${shortfall_at_60:,.0f} at age 60.")
else:
    st.success(f"You will have a surplus of ${-shortfall_at_60:,.0f} at age 60.")