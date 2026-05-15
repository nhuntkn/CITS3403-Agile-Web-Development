const exerciseData = JSON.parse(document.getElementById("exercise-data").textContent);

let rowCount = 0;

function getExerciseOptions(){
  let options = '<option value="">Select exercise</option>';
  for (let exercise in exerciseData) {
    options += '<option value="' + exercise + '">' + exercise + '</option>';
  }
  return options;
}

// adds a new exercise row to the page
function addExerciseRow() {
  rowCount++;

  let html = `
    <div class="exercise-row-box" id="row${rowCount}">
      <div class="row g-3 align-items-end">
        <div class="col-md-4">
          <label class="form-label">Exercise</label>
          <select class="form-select" name="exercise[]" onchange="updateLevels(${rowCount})" id="exercise${rowCount}" required>
            ${getExerciseOptions()}
          </select>
        </div>

        <div class="col-md-4">
          <label class="form-label">Activity Level</label>
          <select class="form-select" name="level[]" id="level${rowCount}" required>
            <option value="">Select activity level</option>
          </select>
        </div>

        <div class="col-md-3">
          <label class="form-label">Minutes</label>
          <input type="number" class="form-control" name="minutes[]" id="minutes${rowCount}" placeholder="0" min="1" max="300" step="1" required>
        </div>

        <div class="col-md-1 d-flex align-items-end">
          <button type="button" class="btn btn-outline-danger w-100" onclick="removeRow(${rowCount})" title="Remove">&times;</button>
        </div>
      </div>
    </div>
  `;

  document.getElementById("exerciseContainer").insertAdjacentHTML("beforeend", html);
}

// updates the activity level options based on selected exercise
function updateLevels(rowId) {
  let exercise = document.getElementById("exercise" + rowId).value;
  let levelSelect = document.getElementById("level" + rowId);

  levelSelect.innerHTML = '<option value="">Select activity level</option>';

  if (exercise !== "" && exerciseData[exercise]) {
    let levels = exerciseData[exercise];

    for (let level in levels) {
      let option = document.createElement("option");
      option.value = level;
      option.textContent = level;
      levelSelect.appendChild(option);
    }
  }
}

// removes one exercise row
function removeRow(rowId) {
  let row = document.getElementById("row" + rowId);
  if (row) {
    row.remove();
  }
}

// calculates the total calories for all exercise rows
function calculateCalories() {
  let weight = Number(document.getElementById("weight").value);
  let result = document.getElementById("result");
  let totalCalories = 0;
  let rows = document.querySelectorAll(".exercise-row-box");

  // checks if weight exists and at least one row is selected
  if (!weight || rows.length === 0) {
    result.innerHTML = "Please enter weight and add at least one exercise.";
    return;
  }

  // for loop to calculate calories for each exercise row and sum them up
  for (let i = 0; i < rows.length; i++) {
    let exerciseSelect = rows[i].querySelector('select[id^="exercise"]');
    let levelSelect = rows[i].querySelector('select[id^="level"]');
    let minutesInput = rows[i].querySelector('input[id^="minutes"]');

    let exercise = exerciseSelect.value;
    let level = levelSelect.value;
    let minutes = Number(minutesInput.value);

    // only calculate if the row has valid inputs
    if (exercise !== "" && level !== "" && minutes > 0) {
      let met = exerciseData[exercise][level];
      let calories = minutes * (met * 3.5 * weight) / 200;
      totalCalories += calories;
    }
  }

  // display result
  if (totalCalories > 0) {
    result.innerHTML = "Estimated total calories burnt: " + Math.round(totalCalories) + " kcal";
  } else {
    result.innerHTML = "Please complete at least one valid exercise row.";
  }
}

// add one exercise row by default when page loads
addExerciseRow();

const sessionDateInput = document.getElementById("sessionDate");
if (sessionDateInput) {
    const d = new Date();
    const localToday = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    sessionDateInput.max = localToday;
}