# Exercise Planner (EP)

A web application that helps users keep track of calories burned through exercise, log their workout sessions, and monitor their weight loss progress every day.

## About the Project
Exercise Planner is a focused weight loss companion. Users register with their physical details, log workouts to track calories burned each day, and monitor their progress through an at-a-glance dashboard. A ranking page keeps motivation high by showing how users compare against each other.

**Core goal**: track calories burned through exercise, monitor weight changes, and stay consistent.

## Pages & Features
### Main Page (Home)

- **BMI Calculator** — enter weight (kg) and height (cm), click Calculate to see result
- **Sign In** — username and password login with redirect to dashboard on success
- Link to Sign Up page for new users

### Sign Up Page

- Registration form collecting: username, password, confirm password, date of birth, sex, weight (kg), height (cm)
- Username has to be unique
- Password validation: 6–20 characters, at least one uppercase letter and one number
- Redirects to dashboard after successful registration

### Dashboard

- Navigation bar: EP logo · Dashboard · Ranking · Profile · Create Exercise
- 4 metric cards: **Start Weight, Current Weight, Current BMI, Total Changes**
- **Today's calorie goal** — progress bar showing calories burned vs daily target
- **Calories burned — this week** — bar chart by day (Mon–Sun)
- **Calories burned — this month** — bar chart by date (1–30/31)

### Create Exercise Page

- **Date picker** at the top
- **Exercise details** panel:
  - Exercise dropdown (Running, Cycling, Jump rope, Squat, Deadlift, Bench Press, Push-ups, Burpees, Rowing, Elliptical)
  - Duration input (minutes)
  - Intensity dropdown (Light, Moderate, High, Very High)
  - Add button — appends exercise to the session log below


- **Notes** panel:

Free-text field ("How today feel?")
Weight today (kg) input


- **Logged session** list — shows each added exercise with duration, intensity, and kcal burned
- **Estimated calories** burned — running total shown prominently at the bottom
- **Save session** button — saves the completed session

### Ranking Page

- Displays users ranked by kg lost/ calories burned and current streak
- Toggle between weekly, monthly, and all-time views
- Badges awarded for milestones: first workout, 7-day streak, 10 workouts, top 3kg lost, 30-day log

### Profile Page

- Edit personal info: username, password, email, date of birth, sex, weight, height
- Save changes and Logout buttons
- Separate panel with Change password and Delete account actions

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | HTML, JavaScript |
| CSS Framework | Bootstrap |
| Charting | Chart.js |
| Design | Figma |
| Auth & Database |  |   
