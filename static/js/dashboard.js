const dashboardData = JSON.parse(document.getElementById("dashboard-data").textContent);
const { sessions, startWeight, userHeight, currentWeight, calorieGoal, aiFeedbackUrl } = dashboardData;

const sorted = [...sessions].sort((a, b) => a.date.localeCompare(b.date));

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

if (startWeight !== null) {
    setText("startWeight", startWeight.toFixed(1));
}

if (currentWeight !== null) {
    setText("currentWeight", currentWeight.toFixed(1));
    if (startWeight !== null) {
        const change = currentWeight - startWeight;
        setText("totalChanges", (change >= 0 ? "+" : "") + change.toFixed(1));
    }
    if (userHeight) {
        const heightM = userHeight / 100;
        const bmi = currentWeight / (heightM * heightM);
        setText("currentBMI", bmi.toFixed(1));

        let category = "";
        if (bmi < 18.5) category = "Underweight";
        else if (bmi < 25) category = "Normal";
        else if (bmi < 30) category = "Overweight";
        else category = "Obese";
        setText("bmiCategory", category);
    }
}

const alerts = [];

if (currentWeight !== null && userHeight) {
    const heightM = userHeight / 100;
    const bmi = currentWeight / (heightM * heightM);
    if (bmi < 18.5) {
        alerts.push({ cls: "warning", msg: `BMI Alert: Your BMI is ${bmi.toFixed(1)} (Underweight). Consider consulting a healthcare professional.` });
    } else if (bmi >= 30) {
        alerts.push({ cls: "danger", msg: `BMI Alert: Your BMI is ${bmi.toFixed(1)} (Obese). Consider consulting a healthcare professional.` });
    } else if (bmi >= 25) {
        alerts.push({ cls: "warning", msg: `BMI Alert: Your BMI is ${bmi.toFixed(1)} (Overweight). Consider consulting a healthcare professional.` });
    }
}

if (sorted.length >= 2 && currentWeight !== null) {
    const now = new Date();
    const cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const cutoffStr = `${cutoff.getFullYear()}-${String(cutoff.getMonth() + 1).padStart(2, "0")}-${String(cutoff.getDate()).padStart(2, "0")}`;
    const older = sorted.filter(s => s.date <= cutoffStr);
    if (older.length > 0) {
        const refWeight = older[older.length - 1].current_weight;
        const change = currentWeight - refWeight;
        if (Math.abs(change) > 1) {
            alerts.push({ cls: "warning", msg: `Weight Alert: You have ${change < 0 ? "lost" : "gained"} ${Math.abs(change).toFixed(1)} kg in the last 7 days.` });
        }
    }
}

const today = (() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
})();
const todayKcal = sessions
    .filter(s => s.date === today)
    .reduce((sum, s) => sum + s.total_calories, 0);

const safeCalorieGoal = Math.max(Number(calorieGoal) || 0, 1);
const pct = Math.min(100, (todayKcal / safeCalorieGoal) * 100);
setText("goalCount", `${Math.round(Math.min(todayKcal, safeCalorieGoal))} / ${safeCalorieGoal} goal`);
const bar = document.getElementById("calorieBar");
bar.style.width = `${pct}%`;
bar.setAttribute("aria-valuenow", String(Math.round(pct)));

if (todayKcal >= safeCalorieGoal) {
    if (typeof confetti === "function") {
        confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
    }
    alerts.push({ cls: "success", msg: `Goal reached! You've burned ${Math.round(todayKcal)} kcal today - you hit your daily goal!` });
}

const alertBox = document.getElementById("alertBox");
alerts.forEach(alert => {
    const div = document.createElement("div");
    div.className = `alert alert-${alert.cls} alert-dismissible fade show`;
    div.setAttribute("role", "alert");
    div.append(document.createTextNode(alert.msg));

    const close = document.createElement("button");
    close.type = "button";
    close.className = "btn-close";
    close.setAttribute("data-bs-dismiss", "alert");
    close.setAttribute("aria-label", "Close");
    div.appendChild(close);
    alertBox.appendChild(div);
});

let weeklyOffset = 0;
let weeklyChart = null;

function dateKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function updateWeeklyChart(offset) {
    weeklyOffset = offset;

    const weekDays = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i + (weeklyOffset * 7));
        weekDays.push(dateKey(d));
    }

    const weekLabels = weekDays.map(d => {
        const dt = new Date(`${d}T00:00:00`);
        return dt.toLocaleDateString("en-AU", { weekday: "short", day: "numeric" });
    });

    const weekData = weekDays.map(d =>
        sessions.filter(s => s.date === d).reduce((sum, s) => sum + s.total_calories, 0)
    );

    const titleEl = document.getElementById("weeklyTitle");
    if (weeklyOffset === 0) {
        titleEl.textContent = "Calories burned - the last 7 days";
    } else {
        const startDt = new Date(`${weekDays[0]}T00:00:00`);
        const endDt = new Date(`${weekDays[6]}T00:00:00`);
        const fmt = { month: "short", day: "numeric" };
        titleEl.textContent = `Calories burned - ${startDt.toLocaleDateString("en-AU", fmt)} to ${endDt.toLocaleDateString("en-AU", fmt)}`;
    }

    document.getElementById("weeklyNext").disabled = weeklyOffset >= 0;

    if (weeklyChart) {
        weeklyChart.data.labels = weekLabels;
        weeklyChart.data.datasets[0].data = weekData;
        weeklyChart.update();
    } else {
        weeklyChart = new Chart(document.getElementById("weeklyChart"), {
            type: "bar",
            data: {
                labels: weekLabels,
                datasets: [{ label: "Calories", data: weekData, backgroundColor: "#7793ae", borderRadius: 4 }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#ccc" }, grid: { color: "rgba(255,255,255,0.1)" } },
                    y: { ticks: { color: "#ccc" }, grid: { color: "rgba(255,255,255,0.1)" }, beginAtZero: true }
                }
            }
        });
    }
}

document.getElementById("weeklyPrev").addEventListener("click", () => updateWeeklyChart(weeklyOffset - 1));
document.getElementById("weeklyNext").addEventListener("click", () => updateWeeklyChart(weeklyOffset + 1));

let monthlyOffset = 0;
let monthlyChart = null;

function updateMonthlyChart(offset) {
    monthlyOffset = offset;

    const now = new Date();
    const targetDate = new Date(now.getFullYear(), now.getMonth() + monthlyOffset, 1);
    const year = targetDate.getFullYear();
    const month = targetDate.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const monthDays = Array.from({ length: daysInMonth }, (_, i) => {
        const day = String(i + 1).padStart(2, "0");
        const mon = String(month + 1).padStart(2, "0");
        return `${year}-${mon}-${day}`;
    });

    const monthData = monthDays.map(d =>
        sessions.filter(s => s.date === d).reduce((sum, s) => sum + s.total_calories, 0)
    );

    const monthName = targetDate.toLocaleDateString("en-AU", { month: "long", year: "numeric" });
    const titleEl = document.getElementById("monthlyTitle");
    titleEl.textContent = monthlyOffset === 0
        ? `Calories burned - this month (${monthName})`
        : `Calories burned - ${monthName}`;

    document.getElementById("monthlyNext").disabled = monthlyOffset >= 0;

    if (monthlyChart) {
        monthlyChart.data.labels = Array.from({ length: daysInMonth }, (_, i) => i + 1);
        monthlyChart.data.datasets[0].data = monthData;
        monthlyChart.update();
    } else {
        monthlyChart = new Chart(document.getElementById("monthlyChart"), {
            type: "bar",
            data: {
                labels: Array.from({ length: daysInMonth }, (_, i) => i + 1),
                datasets: [{ label: "Calories", data: monthData, backgroundColor: "#7793ae", borderRadius: 4 }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#ccc" }, grid: { color: "rgba(255,255,255,0.1)" } },
                    y: { ticks: { color: "#ccc" }, grid: { color: "rgba(255,255,255,0.1)" }, beginAtZero: true }
                }
            }
        });
    }
}

document.getElementById("monthlyPrev").addEventListener("click", () => updateMonthlyChart(monthlyOffset - 1));
document.getElementById("monthlyNext").addEventListener("click", () => updateMonthlyChart(monthlyOffset + 1));

updateWeeklyChart(0);
updateMonthlyChart(0);

const aiFeedbackBtn = document.getElementById("generateAiFeedbackBtn");
const aiFeedbackBox = document.getElementById("aiFeedbackBox");
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

if (aiFeedbackBtn && aiFeedbackBox) {
    aiFeedbackBtn.addEventListener("click", async () => {
        aiFeedbackBtn.disabled = true;
        aiFeedbackBtn.textContent = "Generating...";
        aiFeedbackBox.textContent = "Generating weekly feedback. Please wait...";

        try {
            const response = await fetch(aiFeedbackUrl, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken }
            });

            const data = await response.json();

            if (!response.ok) {
                aiFeedbackBox.textContent = data.error || "AI feedback could not be generated.";
                aiFeedbackBtn.textContent = "Generate Weekly AI Feedback";
                aiFeedbackBtn.disabled = false;
                return;
            }

            aiFeedbackBox.textContent = data.feedback;
            aiFeedbackBtn.textContent = data.cached ? "Feedback already generated today" : "Generated";
            aiFeedbackBtn.disabled = true;
        } catch (error) {
            aiFeedbackBox.textContent = "AI feedback request failed. Please try again.";
            aiFeedbackBtn.textContent = "Generate Weekly AI Feedback";
            aiFeedbackBtn.disabled = false;
        }
    });
}
