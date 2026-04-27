# Helper functions for the project
# This file stores reusable calculations used by the app

def calculate_calories(met_value, minutes, weight):
    calories = minutes * (met_value * 3.5 * weight) / 200
    return round(calories,2)