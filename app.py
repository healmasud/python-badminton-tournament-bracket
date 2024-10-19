from flask import Flask, render_template, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session handling

# Route to display the home page and input teams
@app.route('/')
def index():
    return render_template('index.html')

# Function to create a balanced schedule where each team plays exactly 2 matches
def create_schedule(teams):
    num_teams = len(teams)
    match_schedule = []
    team_matches = {team[1]: 0 for team in teams}  # Tracks the number of matches each team plays
    played_matches = set()  # Set to track played matches (team1, team2)

    while any(count < 2 for count in team_matches.values()):
        team1, team2 = random.sample(teams, 2)

        # Check if both teams can still play more matches (up to 2 matches each)
        if (team_matches[team1[1]] < 2 and 
            team_matches[team2[1]] < 2 and 
            (team1[1], team2[1]) not in played_matches and 
            (team2[1], team1[1]) not in played_matches):
                
            match_schedule.append((len(match_schedule) + 1, team1[1], team2[1]))
            team_matches[team1[1]] += 1
            team_matches[team2[1]] += 1
            played_matches.add((team1[1], team2[1]))  # Mark this match as played

    return match_schedule

# Route to handle team input and create round-robin matches
@app.route('/teams', methods=['POST'])
def set_teams():
    team_names = request.form.getlist('team')

    # Initialize teams and points
    teams = [(i + 1, team_names[i]) for i in range(len(team_names))]
    team_scores = {team[1]: {"points": 0, "score_diff": 0} for team in teams}

    # Create a balanced schedule of matches (each team plays exactly 2 matches)
    matches = create_schedule(teams)

    # Store the data in the session
    session['teams'] = teams
    session['matches'] = matches
    session['team_scores'] = team_scores

    return redirect(url_for('schedule'))

# Route to display the match schedule and input scores
@app.route('/schedule')
def schedule():
    matches = session.get('matches', [])
    return render_template('results.html', matches=matches)

# Route to handle match score input and update team points
@app.route('/results', methods=['POST'])
def submit_results():
    results = request.form.to_dict()
    matches = session.get('matches', [])
    team_scores = session.get('team_scores', {})

    for match in matches:
        # Get scores for each team in the match
        score_1 = int(results.get(f'score_{match[0]}_1', 0))
        score_2 = int(results.get(f'score_{match[0]}_2', 0))

        # Update team points and point differences
        if score_1 > score_2:
            team_scores[match[1]]["points"] += 2
        elif score_1 < score_2:
            team_scores[match[2]]["points"] += 2
        else:
            team_scores[match[1]]["points"] += 1
            team_scores[match[2]]["points"] += 1

        # Update score difference
        team_scores[match[1]]["score_diff"] += (score_1 - score_2)
        team_scores[match[2]]["score_diff"] += (score_2 - score_1)

    # Update the session with the new team scores
    session['team_scores'] = team_scores

    return redirect(url_for('ranking'))

# Route to display team rankings and semifinals
@app.route('/ranking')
def ranking():
    team_scores = session.get('team_scores', {})

    # Sort teams by points and resolve ties with point differences
    sorted_teams = sorted(team_scores.items(), key=lambda x: (x[1]["points"], x[1]["score_diff"]), reverse=True)

    # Determine semifinalists (top 4 teams)
    semifinalists = sorted_teams[:4]

    return render_template('ranking.html', rankings=sorted_teams, semifinalists=semifinalists)

# Route to clear session and restart the tournament
@app.route('/clear', methods=['POST'])
def clear():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
