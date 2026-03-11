from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Data storage (In production, use a database)
DATA_FILE = 'user_data.json'

def load_user_data():
    """Load user data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    """Save user data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class BMICalculator:
    @staticmethod
    def calculate_bmi(height_cm, weight_kg):
        """Calculate BMI from height and weight"""
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        return round(bmi, 2)
    
    @staticmethod
    def get_bmi_category(bmi):
        """Get BMI category"""
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal Weight"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
    
    @staticmethod
    def calculate_ideal_weight(height_cm):
        """Calculate ideal weight (BMI = 22)"""
        height_m = height_cm / 100
        ideal_weight = 22 * (height_m ** 2)
        return round(ideal_weight, 2)

class WorkoutPlanner:
    EXERCISE_BENEFITS = {
        'pushups': {'calories_per_rep': 0.3, 'difficulty': 'medium'},
        'squats': {'calories_per_rep': 0.5, 'difficulty': 'high'},
        'lunges': {'calories_per_rep': 0.4, 'difficulty': 'medium'},
        'plank': {'calories_per_rep': 1.0, 'difficulty': 'high'},
        'jumping-jacks': {'calories_per_rep': 0.2, 'difficulty': 'low'},
        'burpees': {'calories_per_rep': 1.5, 'difficulty': 'high'}
    }
    
    @staticmethod
    def generate_workout_plan(user_data):
        """Generate personalized workout plan based on BMI"""
        bmi = user_data['bmi']
        fitness_level = user_data['fitness_level']
        weight_to_lose = user_data['weight_to_lose']
        
        plan = {
            'level': fitness_level,
            'weekly_workouts': WorkoutPlanner.get_weekly_workouts(fitness_level, bmi),
            'exercises': WorkoutPlanner.get_recommended_exercises(fitness_level, weight_to_lose),
            'daily_target_calories': WorkoutPlanner.calculate_daily_target(weight_to_lose)
        }
        
        return plan
    
    @staticmethod
    def get_weekly_workouts(fitness_level, bmi):
        """Determine weekly workout frequency"""
        if fitness_level == 'beginner':
            return 3
        elif fitness_level == 'intermediate':
            return 4
        else:
            return 5
    
    @staticmethod
    def get_recommended_exercises(fitness_level, weight_to_lose):
        """Get recommended exercises based on fitness level"""
        exercises = {
            'beginner': {
                'pushups': {'sets': 2, 'reps': 5, 'rest': 60},
                'squats': {'sets': 2, 'reps': 10, 'rest': 60},
                'jumping-jacks': {'sets': 2, 'reps': 15, 'rest': 45}
            },
            'intermediate': {
                'pushups': {'sets': 3, 'reps': 12, 'rest': 45},
                'squats': {'sets': 3, 'reps': 15, 'rest': 45},
                'lunges': {'sets': 3, 'reps': 10, 'rest': 45},
                'plank': {'sets': 3, 'duration': 30, 'rest': 60}
            },
            'advanced': {
                'pushups': {'sets': 4, 'reps': 20, 'rest': 30},
                'squats': {'sets': 4, 'reps': 25, 'rest': 30},
                'lunges': {'sets': 4, 'reps': 15, 'rest': 30},
                'burpees': {'sets': 3, 'reps': 10, 'rest': 60},
                'plank': {'sets': 3, 'duration': 60, 'rest': 45}
            }
        }
        
        return exercises.get(fitness_level, exercises['beginner'])
    
    @staticmethod
    def calculate_daily_target(weight_to_lose):
        """Calculate daily calorie burn target"""
        # 0.5 kg per week = 3500 calories deficit
        weekly_target = (weight_to_lose / 12) * 3500
        daily_target = weekly_target / 7
        return round(daily_target, 0)
    
    @staticmethod
    def get_exercise_reps(exercise, weight, bmi, fitness_level):
        """Calculate recommended reps based on user metrics"""
        plan = WorkoutPlanner.generate_workout_plan({
            'bmi': bmi,
            'fitness_level': fitness_level,
            'weight_to_lose': 0
        })
        
        if exercise in plan['exercises']:
            return plan['exercises'][exercise]
        
        return {'sets': 1, 'reps': 10, 'rest': 60}

@app.route('/api/calculate-bmi', methods=['POST'])
def calculate_bmi():
    """Calculate BMI and return personalized plan"""
    try:
        data = request.json
        
        height = data.get('height')
        weight = data.get('weight')
        age = data.get('age')
        gender = data.get('gender')
        fitness_level = data.get('fitnessLevel')
        name = data.get('name')
        
        # Validate input
        if not all([height, weight, age, gender, fitness_level, name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Calculate BMI
        bmi = BMICalculator.calculate_bmi(height, weight)
        category = BMICalculator.get_bmi_category(bmi)
        ideal_weight = BMICalculator.calculate_ideal_weight(height)
        weight_to_lose = max(0, weight - ideal_weight)
        
        user_data = {
            'name': name,
            'age': age,
            'gender': gender,
            'height': height,
            'weight': weight,
            'bmi': bmi,
            'category': category,
            'fitness_level': fitness_level,
            'ideal_weight': ideal_weight,
            'weight_to_lose': weight_to_lose,
            'created_at': datetime.now().isoformat()
        }
        
        # Generate workout plan
        workout_plan = WorkoutPlanner.generate_workout_plan(user_data)
        user_data['workout_plan'] = workout_plan
        
        # Save user data
        all_users = load_user_data()
        all_users[name] = user_data
        save_user_data(all_users)
        
        return jsonify({
            'bmi': bmi,
            'category': category,
            'ideal_weight': ideal_weight,
            'weight_to_lose': weight_to_lose,
            'workout_plan': workout_plan
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-exercise-plan', methods=['POST'])
def get_exercise_plan():
    """Get personalized exercise plan for specific exercise"""
    try:
        data = request.json
        
        exercise = data.get('exercise')
        weight = data.get('weight')
        bmi = data.get('bmi')
        fitness_level = data.get('fitnessLevel')
        
        if not all([exercise, weight, bmi, fitness_level]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        reps_plan = WorkoutPlanner.get_exercise_reps(exercise, weight, bmi, fitness_level)
        
        return jsonify({
            'exercise': exercise,
            'plan': reps_plan,
            'tips': get_exercise_tips(exercise)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-workout', methods=['POST'])
def save_workout():
    """Save completed workout data"""
    try:
        data = request.json
        
        user_name = data.get('userName')
        exercise = data.get('exercise')
        sets_completed = data.get('sets')
        reps_completed = data.get('reps')
        duration = data.get('duration')
        
        all_users = load_user_data()
        
        if user_name not in all_users:
            return jsonify({'error': 'User not found'}), 404
        
        if 'workouts' not in all_users[user_name]:
            all_users[user_name]['workouts'] = []
        
        workout_data = {
            'exercise': exercise,
            'sets': sets_completed,
            'reps': reps_completed,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        all_users[user_name]['workouts'].append(workout_data)
        save_user_data(all_users)
        
        return jsonify({'success': True, 'message': 'Workout saved successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<user_name>', methods=['GET'])
def get_user_data(user_name):
    """Get user data and progress"""
    try:
        all_users = load_user_data()
        
        if user_name not in all_users:
            return jsonify({'error': 'User not found'}), 404
        
        user = all_users[user_name]
        workouts = user.get('workouts', [])
        
        stats = {
            'workouts_completed': len(workouts),
            'total_reps': sum(w.get('reps', 0) for w in workouts),
            'exercises_done': list(set(w.get('exercise') for w in workouts))
        }
        
        return jsonify({
            'user': user,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_exercise_tips(exercise):
    """Get form tips for exercises"""
    tips = {
        'pushups': [
            'Keep your body in a straight line',
            'Lower until chest nearly touches ground',
            'Push through your palms',
            'Keep elbows at 45 degrees'
        ],
        'squats': [
            'Keep chest up and shoulders back',
            'Lower hips back and down',
            'Keep knees over toes',
            'Go as deep as comfortable'
        ],
        'lunges': [
            'Step forward with one leg',
            'Lower hips until both knees are at 90 degrees',
            'Keep torso upright',
            'Return to starting position'
        ],
        'plank': [
            'Keep body in straight line from head to feet',
            'Engage core muscles',
            'Keep shoulders above wrists',
            'Breathe steadily'
        ],
        'jumping-jacks': [
            'Jump while spreading legs and raising arms',
            'Land softly on balls of feet',
            'Return to starting position',
            'Keep movement rhythmic'
        ],
        'burpees': [
            'Start standing, crouch down',
            'Jump feet back to plank position',
            'Do a pushup',
            'Jump feet forward and jump up'
        ]
    }
    
    return tips.get(exercise, [])

if __name__ == '__main__':
    app.run(debug=True, port=5000)