    const exerciseData = {
      "Treadmill Walk": {
        "3.0 - 3.4 mph": 3.8,
        "3.5 - 3.9 mph": 4.8,
        "4.0 - 4.4 mph": 5.8,
        "4.5 - 4.9 mph": 6.8
      },
      "Jogging / Running": {
        "3.0 - 3.9 mph": 5.3,
        "4.0 - 4.9 mph": 6.5,
        "5.0 - 5.9 mph": 11.0
      },
      "Cycling": {
        "< 10 mph": 4.0,
        "10 - 11.9 mph": 6.8,
        "12 - 13.9 mph": 8.0,
        "14 - 15.9 mph": 10.0
      },
      "Elliptical": {
        "Moderate": 5.0,
        "Vigorous": 9.0
      },
      "Skip Rope": {
        "General": 11.0
      },
      "Weight Lifting": {
        "General": 3.5,
        "Squats / Deadlifts": 5.0,
        "Circuit / Supersets": 5.8,
        "Power Lifting / Bodybuilding": 6.0
      },
      "Rowing Machine": {
        "Moderate": 5.0,
        "General Vigorous": 7.3,
        "100 - 149 watts": 7.5,
        "150 - 199 watts": 11.0
      },
      "Bodyweight Exercise": {
        "General": 3.0,
        "High Intensity": 6.5
      }
    };

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
              <select class="form-select" onchange="updateLevels(${rowCount})" id="exercise${rowCount}">
                ${getExerciseOptions()}
              </select>
            </div>

            <div class="col-md-4">
              <label class="form-label">Activity Level</label>
              <select class="form-select" id="level${rowCount}">
                <option value="">Select activity level</option>
              </select>
            </div>

            <div class="col-md-3">
              <label class="form-label">Minutes</label>
              <input type="number" class="form-control" id="minutes${rowCount}" placeholder="0">
            </div>

            <div class="col-md-1 d-flex align-items-end">
              <button class="btn btn-outline-danger w-100" onclick="removeRow(${rowCount})" title="Remove">&times;</button>
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
          option.value = levels[level];
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

      // checks if weight exists and at lease one row is selected
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
        let met = Number(levelSelect.value);
        let minutes = Number(minutesInput.value);

        // only calculate if the row has valid inputs
        if (exercise !== "" && met && minutes > 0) {
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