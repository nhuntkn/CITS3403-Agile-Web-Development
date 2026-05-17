# Exercise Planner (EP)

Exercise Planner helps users record workout sessions, estimate calories burned, track body weight changes, and monitor progress over time through dashboards, history, ranking and sharing features.

**Core goal**: track calories burned through exercise, monitor weight changes, and stay consistent.

## Design and Use

The application is designed around a simple exercise tracking flow: users register or sign in, review their current status on the dashboard, create exercise sessions to add new data, then use history, ranking, and sharing pages to review progress and interact with other users. The layout keeps the main navigation visible across signed-in pages so users can move naturally from recording a workout to checking charts, comparing rankings, and sharing saved sessions.

## Pages & Features

### Main Page (Home)

- Instructions to use the website
- **Sign In** — username and password login with redirect to dashboard on success
- Link to Sign Up page for new users
- Link to Forgot Password page to change password if forgotten

### Sign Up Page

- Registration form collecting: username, email, password, confirm password, date of birth, sex, weight (kg), height (cm)
- Username has to be unique
- Email has to be unique
- Password validation: at least 12 characters, at least one letter, and at least one special character
- Sends a verification email before completing account registration
- Redirects to dashboard after successful registration

### Dashboard

- Navigation bar: EP logo · Dashboard · Ranking · Profile · Create Exercise
- 4 metric cards: Start Weight, Current Weight, Current BMI, Total Changes
- Today's calorie goal — progress bar showing calories burned vs daily target
- Calories burned — this week — bar chart by day (Mon–Sun)
- Calories burned — this month — bar chart by date (1–30/31)
- Weekly summary button: generates a summary for the current week, starting from Monday

### Create Exercise Page

- Date picker, Weight input at the top
- Exercise details panel:
  - Exercise dropdown (Bodyweight Exercises, Cycling, Elliptical, Jogging/Running, Rowing Machine, Skip Rope, Treadmill walk, Weight Lifting)
  - Activity level dropdown 
  - Duration input (minutes)
  - Add Another Exercise button


- Notes panel: Free-text field

- Add Activity Location button:
  - Uses Leaflet and OpenStreetMap
  - Click the map to save the activity location
  - Optional current-location button using the browser's geolocation feature

- Logged session list — shows each added exercise with duration, intensity, and kcal burned
- Calculate Session Calories — Shows the estimated calories for selected exercise sessions with intensity and duration
- Add to Record button — saves the completed session to database

### Ranking Page

- Displays all users ranked by total calories burned
- Shows each user's total sessions
- Filters by All Time, Daily, Weekly, Monthly, Half yearly

### History Page

- Displays the logged-in user's saved workout sessions
- Shows date, weight, calories burned, location, notes
- Displays saved activity locations on an interactive map when the user clicks the  `Check Location` button
- Action button for users to Share or Delete the session

### Profile Page

- Displays the user's username, date of birth, gender, current weight, height, email, and profile image
- Edit personal info: password, date of birth, gender, start weight, current weight, height, daily calorie goal, and profile image
- Friend system panel allows users to search for users, send friend requests, monitor pending requests, and delete friends



## Group Members

| UWA ID   | Name                          | GitHub Username |
| -------- | ----------------------------- | --------------- |
| 24383874 | Jackson Liu                   | JacksonnnnL     |
| 24527515 | Tran Khanh Nhu (Janet) Nguyen | nhuntkn         |
| 24487703 | Ziheng Ericson Liu            | godprofessor    |
| 24854637 | Zhihan Yao                    | ZH-Yao088       |



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

Set `SECRET_KEY` before running the app. Email verification also requires `MAIL_USERNAME` and `MAIL_PASSWORD`. The app uses `SECRET_KEY` for sessions, login and CSRF protection.

Email verification requires valid `MAIL_USERNAME` and `MAIL_PASSWORD` values. For Gmail, `MAIL_PASSWORD` must be a Google App Password, not the normal Gmail account password. Without these email credentials, account registration that depends on email verification cannot complete.

A `.env.example` file is included in the repository to show the required environment variable names without exposing real secrets.

Windows PowerShell:

```powershell
$env:SECRET_KEY="replace-this-with-a-long-random-secret-key"
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="your-google-app-password"
```

macOS / Linux:

```bash
export SECRET_KEY="replace-this-with-a-long-random-secret-key"
export MAIL_USERNAME="your-email@gmail.com"
export MAIL_PASSWORD="your-google-app-password"
```

**Optional** AI summary setup: The app can run without an AI API key. If no API key is provided, the dashboard will show a fallback message instead of generating AI feedback. By default, the app uses OpenAI for the dashboard AI feedback feature.

Windows PowerShell:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_API_KEY="your-openai-api-key"
```

macOS/Linux:

```bash
export AI_PROVIDER="openai"
export OPENAI_API_KEY="your-openai-api-key"
```

Other supported providers are:

```bash
AI_PROVIDER="claude" with ANTHROPIC_API_KEY
AI_PROVIDER="gemini" with GEMINI_API_KEY
```

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



## First Use

1. Open `http://127.0.0.1:5000/`
2. Click **Sign Up** and create a new account
3. Use the dashboard and **Create Exercise** page to add workout sessions

Password rules:

- At least 12 characters
- At least one letter
- At least one special character from `!@#$%^&*`



## Running tests

The project includes automated unit/integration tests and Selenium browser tests. Before running tests, make sure the dependencies are installed and `SECRET_KEY` is set in your terminal.

Windows PowerShell:

```powershell
$env:SECRET_KEY="test-secret-key"
```

macOS / Linux:

```bash
export SECRET_KEY="test-secret-key"
```

Run all automated tests:

Windows:

```powershell
python -m pytest
```

macOS/Linux:

```bash
python3 -m pytest
```

Run only the unit and Flask route tests:

```bash
python -m pytest tests/test_unit.py tests/test_flask_flows.py
```

Run only the Selenium browser tests:

```bash
python -m pytest tests/test_selenium.py
```

The tests use a separate SQLite database at `instance/test_exercise_planner.db`. This keeps test data away from the local development database at `instance/exercise_planner.db`.

The Selenium tests start a Flask test server automatically on a free local port, then open the app in a headless browser and check signup, password validation, invalid login handling, exercise creation, history deletion, dashboard navigation, ranking navigation, and account user search. If Chrome or a compatible Chrome WebDriver cannot be started on the machine, the Selenium tests is skipped with a clear reason.

HTML and CSS were checked for valid structure during cleanup, including removing invalid nested interactive elements from the share page.

Run a quick Python syntax check when needed:

```powershell
python -m compileall .
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
