# Exercise Planner (EP)

A web application that helps users keep track of calories burned through exercise, log their workout sessions, and monitor their weight loss progress every day.

## About the Project
Exercise Planner is a focused weight loss companion. Users register with their physical details, log workouts to track calories burned each day, and monitor their progress through an at-a-glance dashboard. A ranking page keeps motivation high by showing how users compare against each other.

**Core goal**: track calories burned through exercise, monitor weight changes, and stay consistent.

## Design and Use

The application is designed around a simple exercise tracking flow: users register or sign in, review their current status on the dashboard, create exercise sessions to add new data, then use history, ranking, and sharing pages to review progress and interact with other users. The layout keeps the main navigation visible across signed-in pages so users can move naturally from recording a workout to checking charts, comparing rankings, and sharing saved sessions.

## Quick Start

### 1. Clone the project

```powershell
git clone <repository-url>
cd CITS3403-Agile-Web-Development
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Set `SECRET_KEY` in your terminal before running the app. The app will not start without this environment variable.

Windows PowerShell:

```powershell
$env:SECRET_KEY="replace-this-with-a-long-random-secret-key"
```

macOS / Linux:

```bash
export SECRET_KEY="replace-this-with-a-long-random-secret-key"
```

Do not commit the real `.env` file to GitHub.

### 5. Initialise the database

```powershell
py -m flask --app app db upgrade
```

This applies the Flask-Migrate database migrations and creates the local SQLite database schema. The database file is stored in the Flask `instance/` folder, which is ignored by Git.

### 6. Run the app

```powershell
py app.py
```

Open the local website:

```text
http://127.0.0.1:5000/
```

If `py` does not work on your machine, use `python` or `python3` instead.

## Testing

The project includes automated unit/integration tests and Selenium browser tests.

Before testing, make sure dependencies are installed and `SECRET_KEY` is set in your terminal.

Windows PowerShell:

```powershell
$env:SECRET_KEY="test-secret-key"
```

macOS / Linux:

```bash
export SECRET_KEY="test-secret-key"
```

Run all automated tests:

```powershell
py -m pytest
```

Run only the unit and Flask route tests:

```powershell
py -m pytest tests/test_unit.py tests/test_flask_flows.py
```

Run only the Selenium browser test:

```powershell
py -m pytest tests/test_selenium.py
```

The tests use a separate SQLite database at `instance/test_exercise_planner.db`. This keeps test data away from the local development database at `instance/exercise_planner.db`.

The Selenium test starts a Flask test server automatically on a free local port, then opens the app in a headless browser and checks signup, logout, login, dashboard, ranking, and history navigation flow. If Chrome or a compatible Chrome WebDriver cannot be started on the machine, the Selenium test is skipped with a clear reason.

HTML and CSS were checked for valid structure during cleanup, including removing invalid nested interactive elements from the share page.

Run a quick Python syntax check when needed:

```powershell
py -m compileall app.py models.py data.py utils.py
```

Manual smoke test checklist:

- Open the login page and confirm it loads.
- Sign up with a new user.
- Log out and log back in.
- Add an exercise session.
- Check the dashboard charts and calorie goal.
- Check the ranking page filters.
- Check the history page and share a saved session with a friend.
- Update profile details and change password from the account page.

## First Use

1. Open `http://127.0.0.1:5000/`
2. Click **Sign Up** and create a new account
3. Use the dashboard and **Create Exercise** page to add workout sessions

Password rules:

- At least 12 characters
- At least one letter
- At least one special character from `!@#$%^&*`

## Pages & Features
### Main Page (Home)
- Instructions to use the web
- **Sign In** — username and password login with redirect to dashboard on success
- Link to Sign Up page for new users

### Sign Up Page

- Registration form collecting: username, email, password, confirm password, date of birth, sex, weight (kg), height (cm)
- Username has to be unique
- Email has to be unique
- Password validation: at least 12 characters, at least one letter, and at least one special character
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

- **Activity Location** map:
  - Uses Leaflet and OpenStreetMap
  - Click the map to save the activity location
  - Optional current-location button using the browser's geolocation feature

- **Logged session** list — shows each added exercise with duration, intensity, and kcal burned
- **Estimated calories** burned — running total shown prominently at the bottom
- **Save session** button — saves the completed session

### Ranking Page

- Displays users ranked by kg lost and calories burned
- Shows each user's total sessions

### History Page

- Displays the logged-in user's saved workout sessions
- Shows date, weight, calories burned, and notes
- Displays saved activity locations on an interactive map

### Profile Page

- Edit personal info: password, date of birth, sex, weight, height
- Save changes and Logout buttons
- Separate panel with Change password and Delete account actions

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | HTML, JavaScript |
| Templates | Jinja templates with base template inheritance |
| CSS Framework | Bootstrap |
| Charting | Chart.js |
| Mapping | Leaflet, OpenStreetMap |
| Design | Figma |
| Auth & Database | Flask-Login, Flask-SQLAlchemy, SQLite |

## Troubleshooting

### `ModuleNotFoundError`

Install the dependencies again:

```powershell
pip install -r requirements.txt
```

### `sqlite3.OperationalError: no such table: user`

Apply the database migrations:

```powershell
py -m flask --app app db upgrade
```

Then restart the app with:

```powershell
py app.py
```

### Page shows a Flask debugger error

Check the terminal where the app is running. The error usually points to a missing dependency, missing template, or database setup issue.
