import os
from flask import Flask, jsonify, request, abort
import requests
from functools import wraps

app = Flask(__name__)

# Token validation decorator
def token_required(f):
    @wraps(f)  # This preserves the original function's name and docstring
    def decorated(*args, **kwargs):
        token = None

        # Check if the token is passed in the headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1] if len(auth_header.split(" ")) == 2 else None

        # If no token is provided or it's invalid, return an error
        if not token or token != os.getenv('API_BEARER_TOKEN'):
            abort(401, description="Invalid or missing token")

        return f(*args, **kwargs)
    return decorated

class ESPNFantasyFootballClient:
    def __init__(self, league_id, season_id, scoring, espn_s2, swid):
        self.league_id = league_id
        self.season_id = season_id
        self.scoring = scoring
        self.espn_s2 = espn_s2
        self.swid = swid
        self.base_url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{self.season_id}/segments/0/leagues/{self.league_id}"

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cookie': f"espn_s2={self.espn_s2}; SWID={self.swid}",
        }

    def get_available_players(self):
        endpoint = f"{self.base_url}?view=kona_player_info"
        response = requests.get(endpoint, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def filter_players_by_position(self, players, position):
        position_map = {
            "QB": 1,
            "RB": 2,
            "WR": 3,
            "TE": 4,
            "K": 5,
            "DEF": 16
        }
        position_id = position_map.get(position.upper())
        if not position_id:
            return []

        return [
            {
                'name': player['player']['fullName'],
                'team': player['player']['proTeamId'],
                'rank': player['player']['draftRanksByRankType'][self.scoring]['rank'],
                'projected_points': player['player']['stats'][0]['appliedTotal']
            }
            for player in players['players']
            if player['status'] == "FREEAGENT" and player['player']['defaultPositionId'] == position_id
        ]

    def get_best_available_player(self):
        players = self.get_available_players()
        if not players or len(players) == 0:
            return None

        best_player = None
        for player in players['players']:
            if player['status'] == "FREEAGENT":
                if not best_player or player['player']['draftRanksByRankType'][self.scoring]['rank'] < best_player['player']['draftRanksByRankType'][self.scoring]['rank']:
                    best_player = player

        if best_player:
            return {
                'name': best_player['player']['fullName'],
                'position': best_player['player']['defaultPositionId'],
                'team': best_player['player']['proTeamId'],
                'rank': best_player['player']['draftRanksByRankType'][self.scoring]['rank'],
                'projected_points': best_player['player']['stats'][0]['appliedTotal']
            }
        return None

    def get_current_roster(self):
        endpoint = f"{self.base_url}?view=mRoster"
        response = requests.get(endpoint, headers=self.get_headers())
        if response.status_code == 200:
            roster = response.json()['teams'][0]['roster']['entries']
            return {
                "QB": [player['playerPoolEntry']['player']['fullName'] for player in roster if player['playerPoolEntry']['player']['defaultPositionId'] == 1],
                "RB": [player['playerPoolEntry']['player']['fullName'] for player in roster if player['playerPoolEntry']['player']['defaultPositionId'] == 2],
                "WR": [player['playerPoolEntry']['player']['fullName'] for player in roster if player['playerPoolEntry']['player']['defaultPositionId'] == 3],
                "TE": [player['playerPoolEntry']['player']['fullName'] for player in roster if player['playerPoolEntry']['player']['defaultPositionId'] == 4],
                "FLEX": [],  # This can be implemented if needed
                "K": [player['playerPoolEntry']['player']['fullName'] for player in roster if player['playerPoolEntry']['player']['defaultPositionId'] == 5],
                "DEF": [player['playerPoolEntry']['player']['fullName'] for player in roster if player['playerPoolEntry']['player']['defaultPositionId'] == 16]
            }
        else:
            return None

    def get_draft_summary(self):
        endpoint = f"{self.base_url}?view=mDraftDetail"
        response = requests.get(endpoint, headers=self.get_headers())
        if response.status_code == 200:
            draft_picks = response.json()['draftDetail']['picks']
            summary = {}
            for pick in draft_picks:
                team_name = pick['teamId']
                player_name = pick['playerId']
                if team_name not in summary:
                    summary[team_name] = []
                summary[team_name].append(player_name)
            return summary
        else:
            return None

    def get_team_info(self):
        endpoint = f"{self.base_url}?view=mTeam"
        response = requests.get(endpoint, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def parse_team_for_projection(self, team_info):
        teams = []
        members = {member['id']: f"{member.get('firstName', '')} {member.get('lastName', '')}".strip() for member in team_info.get('members', [])}
        
        for team in team_info['teams']:
            owner_id = team['primaryOwner']
            owner_name = members.get(owner_id, "Unknown Owner")
            team_data = {
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "owner_name": owner_name,
                "total_points": team.get("points"),  # Total points scored so far
                "projected_points": team.get("projectedPoints"),  # Projected points for future matchups
                "wins": team.get("record", {}).get("overall", {}).get("wins"),  # Number of wins
                "losses": team.get("record", {}).get("overall", {}).get("losses"),  # Number of losses
                "ties": team.get("record", {}).get("overall", {}).get("ties"),  # Number of ties
                "rank": team.get("playoffSeed"),  # Current rank or seed in the league
                "schedule_strength": team.get("scheduleStrength"),  # Strength of remaining schedule
            }
            teams.append(team_data)
        return teams

    def get_projected_winner(self):
        team_info = self.get_team_info()
        parsed_teams = self.parse_team_for_projection(team_info)
        
        # Logic to determine the projected winner based on the parsed data
        return max(
            parsed_teams,
            key=lambda t: (
                t['wins'] or 0,  # Handle NoneType for wins
                (t['projected_points'] or 0) - (t['schedule_strength'] or 0)  # Handle NoneType for projected_points and schedule_strength
            )
        )

def get_env_value(env_var: str)->str:
    env_value = os.getenv(env_var)
    if env_value is None:
        abort(500, description=f'Missing environment variable {env_var}')
    return env_value

league_id = get_env_value('LEAGUE_ID')
season_id = get_env_value('SEASON_ID')
espn_s2 = get_env_value('ESPN_S2')
swid = get_env_value('SWID')
scoring = get_env_value('SCORING')

client = ESPNFantasyFootballClient(league_id, season_id, scoring, espn_s2, swid)

@app.route('/get-available-players', methods=['GET'])
@token_required
def get_available_players():
    position = request.args.get('position', default="ALL", type=str)
    players = client.get_available_players()
    if players:
        filtered_players = client.filter_players_by_position(players, position)
        return jsonify({"status": "success", "players": filtered_players})
    return jsonify({"status": "error", "message": "Failed to retrieve players"}), 500

@app.route('/get-best-available-player', methods=['GET'])
@token_required
def get_best_available_player():
    best_player = client.get_best_available_player()
    if best_player:
        return jsonify({"status": "success", "player": best_player})
    return jsonify({"status": "error", "message": "Failed to retrieve best player"}), 500

@app.route('/suggest-next-pick', methods=['GET'])
@token_required
def suggest_next_pick():
    best_player = client.get_best_available_player()
    if best_player:
        return jsonify({"status": "success", "suggested_pick": best_player})
    return jsonify({"status": "error", "message": "Failed to retrieve suggested pick"}), 500

@app.route('/get-current-roster', methods=['GET'])
@token_required
def get_current_roster():
    roster = client.get_current_roster()
    if roster:
        return jsonify({"status": "success", "roster": roster})
    return jsonify({"status": "error", "message": "Failed to retrieve current roster"}), 500

@app.route('/get-draft-summary', methods=['GET'])
@token_required
def get_draft_summary():
    draft_summary = client.get_draft_summary()
    if draft_summary:
        return jsonify({"status": "success", "draft_summary": draft_summary})
    return jsonify({"status": "error", "message": "Failed to retrieve draft summary"}), 500

@app.route('/projected-winner', methods=['GET'])
@token_required
def projected_winner():
    winner = client.get_projected_winner()
    if winner:
        return jsonify({
            "status": "success",
            "projected_winner": {
                "team_id": winner['team_id'],
                "team_name": winner['team_name'],
                "owner_name": winner['owner_name'],
                "total_points": winner['total_points'],
                "projected_points": winner['projected_points'],
                "wins": winner['wins'],
                "losses": winner['losses'],
                "ties": winner['ties'],
                "rank": winner['rank'],
                "schedule_strength": winner['schedule_strength']
            }
        }), 200
    return jsonify({"status": "error", "message": "Failed to retrieve projected winner"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "success", "message": "API is running correctly"}), 200

@app.route('/swagger', methods=['GET'])
def swagger():
    """
    Serves the swagger.json file
    """
    return app.send_static_file('swagger.json')

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
