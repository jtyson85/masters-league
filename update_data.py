"""
ESPN Data Fetcher for Master's League 2026
Run this script weekly to update data.json with latest ESPN data
"""
from espn_api.football import League
import json
import os

# === CONFIGURATION - UPDATE THESE ===
LEAGUE_ID = 1463914
YEAR = 2026  # Updated for 2026 season
ESPN_S2 = os.environ.get('ESPN_S2', 'AEA%2BS%2Fr6rJGuLxbk2o2F16%2BC4WgtLlgR529fQxg%2BYD%2B2gIipmA2CJiaNmvWf6Gm6tbjHcPKRJZgEb9cE7RgUZjGfttWiaXIQRxUUqWfjKQKZnQXJmbKyBCdm%2BVBjXrYCzXFP0kYjunOPJrHPV%2BUsbxWVKoxMzqpd72n%2BgsAd6RtjxMSEon8JHZK4%2BJF%2F47%2BYRp5dmCdn6P7Db%2FrfHbWiEBYj3ZHJ8ByV%2FfSpu%2FhjoO7aLWLY14Oefu%2BUI3yqf%2FGeKPyfT6rOseM2Xjd4%2F185Ia1YjD2BmilceEjNngZFKmhazA%3D%3D')  # Set as environment variable or paste here
SWID = os.environ.get('SWID', '{C030DBC8-E7FF-4728-8BA6-20DBB091D3DF}')        # Set as environment variable or paste here

REGULAR_SEASON_WEEKS = 13

# 2026 Second H2H Schedule (Generated Schedule)
# ESPN IDs: Arbour=1, More=2, Gore=3, Bruton=4, Reynolds=5, Brown=6, Tyson=7, Tack=8, Jackson=9, Caldwell=10
SCHEDULE_H2H2 = {
  "1": [[1,2], [7,6], [3,10], [4,8], [9,5]],
  "2": [[1,6], [2,10], [7,8], [3,5], [4,9]],
  "3": [[1,10], [6,8], [2,5], [7,9], [3,4]],
  "4": [[1,8], [10,5], [6,9], [2,4], [7,3]],
  "5": [[1,5], [8,9], [10,4], [6,3], [2,7]],
  "6": [[1,9], [5,4], [8,3], [10,7], [6,2]],
  "7": [[1,4], [9,3], [5,7], [8,2], [10,6]],
  "8": [[1,3], [4,7], [9,2], [5,6], [8,10]],
  "9": [[1,7], [3,2], [4,6], [9,10], [5,8]],
  "10": [[1,2], [7,6], [3,10], [4,8], [9,5]],
  "11": [[1,6], [2,10], [7,8], [3,5], [4,9]],
  "12": [[1,10], [6,8], [2,5], [7,9], [3,4]],
  "13": [[1,8], [10,5], [6,9], [2,4], [7,3]]
}

def get_league():
    """Connect to ESPN league."""
    if ESPN_S2 and SWID:
        return League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
    return League(league_id=LEAGUE_ID, year=YEAR)

def get_teams(league):
    """Get all teams with their ESPN IDs."""
    teams = []
    for team in league.teams:
        owner_name = "Unknown"
        if hasattr(team, 'owners') and team.owners:
            owner_data = team.owners[0] if isinstance(team.owners, list) else team.owners
            if isinstance(owner_data, dict):
                first = owner_data.get('firstName', '')
                last = owner_data.get('lastName', '')
                owner_name = f"{first} {last}".strip() or owner_data.get('displayName', 'Unknown')
            else:
                owner_name = str(owner_data)
        elif hasattr(team, 'owner'):
            if isinstance(team.owner, dict):
                first = team.owner.get('firstName', '')
                last = team.owner.get('lastName', '')
                owner_name = f"{first} {last}".strip() or team.owner.get('displayName', 'Unknown')
            else:
                owner_name = str(team.owner)
        
        teams.append({
            "id": team.team_id,
            "name": team.team_name,
            "abbrev": team.team_abbrev,
            "owner": owner_name
        })
    return teams

def get_weekly_data(league, week):
    """Get scores and ESPN matchups for a specific week."""
    scores = {}
    espn_matchups = []
    
    try:
        box_scores = league.box_scores(week)
        for box in box_scores:
            home_id = box.home_team.team_id
            away_id = box.away_team.team_id
            scores[str(home_id)] = box.home_score
            scores[str(away_id)] = box.away_score
            espn_matchups.append([home_id, away_id])
    except Exception as e:
        print(f"    Error fetching week {week}: {e}")
        return None
    
    return {
        "week": week,
        "scores": scores,
        "espnMatchups": espn_matchups
    }

def calculate_standings(teams, weeks, schedule):
    """Calculate VP standings from regular season data."""
    standings = {}
    for t in teams:
        standings[t['id']] = {
            'id': t['id'],
            'name': t['name'],
            'abbrev': t['abbrev'],
            'owner': t['owner'],
            'totalVP': 0,
            'h2hVP': 0,
            'ptsVP': 0,
            'totalPts': 0,
            'wins': 0,
            'losses': 0,
            'ties': 0
        }
    
    for week in weeks:
        scores = week['scores']
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        def process_matchup(home, away):
            hs = float(scores.get(str(home), 0))
            as_ = float(scores.get(str(away), 0))
            if hs > as_:
                standings[home]['h2hVP'] += 2
                standings[home]['wins'] += 1
                standings[away]['losses'] += 1
            elif as_ > hs:
                standings[away]['h2hVP'] += 2
                standings[away]['wins'] += 1
                standings[home]['losses'] += 1
            else:
                standings[home]['h2hVP'] += 1
                standings[away]['h2hVP'] += 1
                standings[home]['ties'] += 1
                standings[away]['ties'] += 1
        
        # ESPN matchups
        for h, a in week['espnMatchups']:
            process_matchup(h, a)
        
        # Schedule matchups
        week_schedule = schedule.get(str(week['week']), [])
        for h, a in week_schedule:
            process_matchup(h, a)
        
        # Points VP: top 3 = 2 VP, 4-6 = 1 VP
        for rank, (team_id, score) in enumerate(sorted_scores):
            tid = int(team_id)
            standings[tid]['totalPts'] += float(score)
            if rank < 3:
                standings[tid]['ptsVP'] += 2
            elif rank < 6:
                standings[tid]['ptsVP'] += 1
    
    for s in standings.values():
        s['totalVP'] = s['h2hVP'] + s['ptsVP']
    
    return sorted(standings.values(), key=lambda x: (-x['totalVP'], -x['totalPts']))

def main():
    print("=" * 60)
    print("MASTER'S LEAGUE 2026 DATA UPDATER")
    print("=" * 60)
    
    # Connect to ESPN
    print("\n1. Connecting to ESPN...")
    try:
        league = get_league()
        print(f"   ✓ Connected to: {league.settings.name}")
        print(f"   ✓ Current Week: {league.current_week}")
    except Exception as e:
        print(f"   ✗ Failed to connect: {e}")
        print("\n   Make sure ESPN_S2 and SWID are set correctly!")
        return
    
    # Get teams
    print("\n2. Fetching teams...")
    teams = get_teams(league)
    print(f"   ✓ Found {len(teams)} teams:")
    for t in teams:
        print(f"      ID {t['id']}: {t['name']} ({t['abbrev']}) - {t['owner']}")
    
    # Get regular season data
    print(f"\n3. Fetching regular season (weeks 1-{REGULAR_SEASON_WEEKS})...")
    regular_season_weeks = []
    for week in range(1, REGULAR_SEASON_WEEKS + 1):
        week_data = get_weekly_data(league, week)
        if week_data and any(score > 0 for score in week_data["scores"].values()):
            regular_season_weeks.append(week_data)
            print(f"   ✓ Week {week}")
        else:
            print(f"   ⊘ Week {week}: No scores yet")
            break  # Stop at first empty week
    
    # Calculate standings
    if regular_season_weeks:
        print("\n4. Calculating standings...")
        standings = calculate_standings(teams, regular_season_weeks, SCHEDULE_H2H2)
        print(f"   ✓ Current Standings:")
        for i, s in enumerate(standings[:10], 1):
            print(f"      {i}. {s['name']} - {s['totalVP']} VP ({s['totalPts']:.1f} pts)")
    else:
        standings = []
        print("\n4. No games played yet - standings not calculated")
    
    # Build data structure
    data = {
        "leagueName": "Master's League",
        "year": YEAR,
        "currentWeek": len(regular_season_weeks),
        "teams": teams,
        "schedule": SCHEDULE_H2H2,
        "weeks": regular_season_weeks,
        "standings": standings if standings else []
    }
    
    # Write to file
    print("\n5. Writing data.json...")
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"   ✓ Saved: {len(regular_season_weeks)} weeks")
    
    # Next steps
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. git add data.json")
    print('2. git commit -m "2026 Season - Week X"')
    print("3. git push")
    print("\nDashboard updates automatically on GitHub Pages!")
    print("=" * 60)

if __name__ == "__main__":
    main()