"""
ESPN Data Fetcher for Master's League
Run this script locally to update data.json with latest ESPN data
"""
from espn_api.football import League
import json
import os

# === CONFIGURATION - UPDATE THESE ===
LEAGUE_ID = 1463914
YEAR = 2025
ESPN_S2 = os.environ.get('ESPN_S2', 'AEA%2BS%2Fr6rJGuLxbk2o2F16%2BC4WgtLlgR529fQxg%2BYD%2B2gIipmA2CJiaNmvWf6Gm6tbjHcPKRJZgEb9cE7RgUZjGfttWiaXIQRxUUqWfjKQKZnQXJmbKyBCdm%2BVBjXrYCzXFP0kYjunOPJrHPV%2BUsbxWVKoxMzqpd72n%2BgsAd6RtjxMSEon8JHZK4%2BJF%2F47%2BYRp5dmCdn6P7Db%2FrfHbWiEBYj3ZHJ8ByV%2FfSpu%2FhjoO7aLWLY14Oefu%2BUI3yqf%2FGeKPyfT6rOseM2Xjd4%2F185Ia1YjD2BmilceEjNngZFKmhazA%3D%3D')  # Set as environment variable or paste here
SWID = os.environ.get('SWID', '{C030DBC8-E7FF-4728-8BA6-20DBB091D3DF}')        # Set as environment variable or paste here

REGULAR_SEASON_WEEKS = 13
PLAYOFF_WEEKS = [14, 15, 16, 17]

# Pre-defined second H2H schedule (from your Excel - 2nd matchup each week)
# ESPN IDs: Arbour=1, More=2, Gore=3, Bruton=4, Reynolds=5, Brown=6, Tyson=7, Tack=8, Jackson=9, Caldwell=10
SCHEDULE_H2H2 = {
    "1": [[1,8], [2,7], [3,6], [4,5], [9,10]],
    "2": [[1,6], [2,4], [3,5], [7,10], [8,9]],
    "3": [[1,3], [2,5], [4,10], [6,9], [7,8]],
    "4": [[1,5], [2,10], [3,9], [4,8], [6,7]],
    "5": [[1,9], [2,8], [3,7], [4,6], [5,10]],
    "6": [[1,7], [2,6], [3,4], [5,9], [8,10]],
    "7": [[1,4], [2,3], [5,8], [6,10], [7,9]],
    "8": [[1,2], [3,10], [4,9], [5,7], [6,8]],
    "9": [[1,10], [2,9], [3,8], [4,7], [5,6]],
    "10": [[1,8], [2,7], [3,6], [4,5], [9,10]],
    "11": [[1,6], [2,4], [3,5], [7,10], [8,9]],
    "12": [[1,3], [2,5], [4,10], [6,9], [7,8]],
    "13": [[1,5], [2,10], [3,9], [4,8], [6,7]],
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

def build_playoff_structure(standings, playoff_weeks_data):
    """Build playoff matchups based on seeding and results."""
    seeds = {i+1: s for i, s in enumerate(standings)}
    
    playoffs = {
        "seeds": {str(i+1): {"id": s['id'], "name": s['name'], "abbrev": s['abbrev']} for i, s in enumerate(standings)},
        "championship": {
            "semifinal1": {"team1Seed": 1, "team2Seed": 4, "week14Score": {}, "week15Score": {}, "winner": None},
            "semifinal2": {"team1Seed": 2, "team2Seed": 3, "week14Score": {}, "week15Score": {}, "winner": None},
            "final": {"team1Seed": None, "team2Seed": None, "week16Score": {}, "week17Score": {}, "winner": None}
        },
        "consolation": {
            "week14": {
                "match1": {"team1Seed": 7, "team2Seed": 10, "score": {}, "winner": None},
                "match2": {"team1Seed": 8, "team2Seed": 9, "score": {}, "winner": None},
                "bye5": 5, "bye6": 6
            },
            "week15": {"match1": {"team1Seed": 5, "team2Seed": None, "score": {}, "winner": None},
                       "match2": {"team1Seed": 6, "team2Seed": None, "score": {}, "winner": None}},
            "final": {"team1Seed": None, "team2Seed": None, "week16Score": {}, "week17Score": {}, "winner": None},
            "toiletBowl": {"team1Seed": None, "team2Seed": None, "week16Score": {}, "week17Score": {}, "loser": None}
        }
    }
    
    def get_score(week_data, seed):
        if not week_data or not week_data.get('scores'):
            return None
        team_id = str(seeds[seed]['id'])
        return week_data['scores'].get(team_id)
    
    # Process each playoff week
    week14 = next((w for w in playoff_weeks_data if w['week'] == 14), None)
    week15 = next((w for w in playoff_weeks_data if w['week'] == 15), None)
    week16 = next((w for w in playoff_weeks_data if w['week'] == 16), None)
    week17 = next((w for w in playoff_weeks_data if w['week'] == 17), None)
    
    # Week 14: Championship semis & consolation first round
    if week14:
        playoffs['championship']['semifinal1']['week14Score'] = {str(1): get_score(week14, 1), str(4): get_score(week14, 4)}
        playoffs['championship']['semifinal2']['week14Score'] = {str(2): get_score(week14, 2), str(3): get_score(week14, 3)}
        playoffs['consolation']['week14']['match1']['score'] = {str(7): get_score(week14, 7), str(10): get_score(week14, 10)}
        playoffs['consolation']['week14']['match2']['score'] = {str(8): get_score(week14, 8), str(9): get_score(week14, 9)}
        
        # Determine week 14 consolation winners
        s7, s10 = get_score(week14, 7), get_score(week14, 10)
        s8, s9 = get_score(week14, 8), get_score(week14, 9)
        if s7 is not None and s10 is not None:
            playoffs['consolation']['week14']['match1']['winner'] = 7 if s7 > s10 else 10
        if s8 is not None and s9 is not None:
            playoffs['consolation']['week14']['match2']['winner'] = 8 if s8 > s9 else 9
    
    # Week 15: Complete championship semis & consolation round 2
    if week15:
        playoffs['championship']['semifinal1']['week15Score'] = {str(1): get_score(week15, 1), str(4): get_score(week15, 4)}
        playoffs['championship']['semifinal2']['week15Score'] = {str(2): get_score(week15, 2), str(3): get_score(week15, 3)}
        
        # Determine championship semifinal winners (two-week total)
        w14_1 = playoffs['championship']['semifinal1']['week14Score']
        w15_1 = playoffs['championship']['semifinal1']['week15Score']
        if all(w14_1.get(str(s)) is not None and w15_1.get(str(s)) is not None for s in [1, 4]):
            total1 = w14_1[str(1)] + w15_1[str(1)]
            total4 = w14_1[str(4)] + w15_1[str(4)]
            playoffs['championship']['semifinal1']['winner'] = 1 if total1 > total4 else 4
        
        w14_2 = playoffs['championship']['semifinal2']['week14Score']
        w15_2 = playoffs['championship']['semifinal2']['week15Score']
        if all(w14_2.get(str(s)) is not None and w15_2.get(str(s)) is not None for s in [2, 3]):
            total2 = w14_2[str(2)] + w15_2[str(2)]
            total3 = w14_2[str(3)] + w15_2[str(3)]
            playoffs['championship']['semifinal2']['winner'] = 2 if total2 > total3 else 3
        
        # Set championship final matchup
        if playoffs['championship']['semifinal1']['winner'] and playoffs['championship']['semifinal2']['winner']:
            playoffs['championship']['final']['team1Seed'] = playoffs['championship']['semifinal1']['winner']
            playoffs['championship']['final']['team2Seed'] = playoffs['championship']['semifinal2']['winner']
        
        # Consolation week 15
        w14m1_winner = playoffs['consolation']['week14']['match1']['winner']
        w14m2_winner = playoffs['consolation']['week14']['match2']['winner']
        if w14m1_winner and w14m2_winner:
            lowest_winner = max(w14m1_winner, w14m2_winner)
            highest_winner = min(w14m1_winner, w14m2_winner)
            playoffs['consolation']['week15']['match1']['team2Seed'] = lowest_winner
            playoffs['consolation']['week15']['match2']['team2Seed'] = highest_winner
            playoffs['consolation']['week15']['match1']['score'] = {str(5): get_score(week15, 5), str(lowest_winner): get_score(week15, lowest_winner)}
            playoffs['consolation']['week15']['match2']['score'] = {str(6): get_score(week15, 6), str(highest_winner): get_score(week15, highest_winner)}
            
            s5 = get_score(week15, 5)
            s_low = get_score(week15, lowest_winner)
            s6 = get_score(week15, 6)
            s_high = get_score(week15, highest_winner)
            if s5 is not None and s_low is not None:
                playoffs['consolation']['week15']['match1']['winner'] = 5 if s5 > s_low else lowest_winner
            if s6 is not None and s_high is not None:
                playoffs['consolation']['week15']['match2']['winner'] = 6 if s6 > s_high else highest_winner
            
            m1_winner = playoffs['consolation']['week15']['match1']['winner']
            m2_winner = playoffs['consolation']['week15']['match2']['winner']
            if m1_winner and m2_winner:
                m1_loser = lowest_winner if m1_winner == 5 else 5
                m2_loser = highest_winner if m2_winner == 6 else 6
                playoffs['consolation']['final']['team1Seed'] = m1_winner
                playoffs['consolation']['final']['team2Seed'] = m2_winner
                playoffs['consolation']['toiletBowl']['team1Seed'] = m1_loser
                playoffs['consolation']['toiletBowl']['team2Seed'] = m2_loser
    
    # Weeks 16-17: Finals
    if week16:
        t1 = playoffs['championship']['final']['team1Seed']
        t2 = playoffs['championship']['final']['team2Seed']
        if t1 and t2:
            playoffs['championship']['final']['week16Score'] = {str(t1): get_score(week16, t1), str(t2): get_score(week16, t2)}
        ct1 = playoffs['consolation']['final']['team1Seed']
        ct2 = playoffs['consolation']['final']['team2Seed']
        if ct1 and ct2:
            playoffs['consolation']['final']['week16Score'] = {str(ct1): get_score(week16, ct1), str(ct2): get_score(week16, ct2)}
        tb1 = playoffs['consolation']['toiletBowl']['team1Seed']
        tb2 = playoffs['consolation']['toiletBowl']['team2Seed']
        if tb1 and tb2:
            playoffs['consolation']['toiletBowl']['week16Score'] = {str(tb1): get_score(week16, tb1), str(tb2): get_score(week16, tb2)}
    
    if week17:
        t1 = playoffs['championship']['final']['team1Seed']
        t2 = playoffs['championship']['final']['team2Seed']
        if t1 and t2:
            playoffs['championship']['final']['week17Score'] = {str(t1): get_score(week17, t1), str(t2): get_score(week17, t2)}
            w16 = playoffs['championship']['final']['week16Score']
            w17 = playoffs['championship']['final']['week17Score']
            if all(w16.get(str(s)) is not None and w17.get(str(s)) is not None for s in [t1, t2]):
                total1 = w16[str(t1)] + w17[str(t1)]
                total2 = w16[str(t2)] + w17[str(t2)]
                playoffs['championship']['final']['winner'] = t1 if total1 > total2 else t2
        
        ct1 = playoffs['consolation']['final']['team1Seed']
        ct2 = playoffs['consolation']['final']['team2Seed']
        if ct1 and ct2:
            playoffs['consolation']['final']['week17Score'] = {str(ct1): get_score(week17, ct1), str(ct2): get_score(week17, ct2)}
            w16 = playoffs['consolation']['final']['week16Score']
            w17 = playoffs['consolation']['final']['week17Score']
            if all(w16.get(str(s)) is not None and w17.get(str(s)) is not None for s in [ct1, ct2]):
                total1 = w16[str(ct1)] + w17[str(ct1)]
                total2 = w16[str(ct2)] + w17[str(ct2)]
                playoffs['consolation']['final']['winner'] = ct1 if total1 > total2 else ct2
        
        tb1 = playoffs['consolation']['toiletBowl']['team1Seed']
        tb2 = playoffs['consolation']['toiletBowl']['team2Seed']
        if tb1 and tb2:
            playoffs['consolation']['toiletBowl']['week17Score'] = {str(tb1): get_score(week17, tb1), str(tb2): get_score(week17, tb2)}
            w16 = playoffs['consolation']['toiletBowl']['week16Score']
            w17 = playoffs['consolation']['toiletBowl']['week17Score']
            if all(w16.get(str(s)) is not None and w17.get(str(s)) is not None for s in [tb1, tb2]):
                total1 = w16[str(tb1)] + w17[str(tb1)]
                total2 = w16[str(tb2)] + w17[str(tb2)]
                playoffs['consolation']['toiletBowl']['loser'] = tb1 if total1 < total2 else tb2
    
    return playoffs

def main():
    print("=" * 60)
    print("MASTER'S LEAGUE DATA UPDATER")
    print("=" * 60)
    
    # Connect to ESPN
    print("\n1. Connecting to ESPN...")
    try:
        league = get_league()
        print(f"   ✓ Connected to: {league.settings.name}")
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
    
    # Calculate standings
    print("\n4. Calculating standings...")
    standings = calculate_standings(teams, regular_season_weeks, SCHEDULE_H2H2)
    print(f"   ✓ Final Standings:")
    for i, s in enumerate(standings[:5], 1):
        print(f"      {i}. {s['name']} - {s['totalVP']} VP ({s['totalPts']:.1f} pts)")
    if len(standings) > 5:
        print(f"      ... {len(standings) - 5} more teams")
    
    # Get playoff data
    print(f"\n5. Fetching playoffs (weeks {PLAYOFF_WEEKS[0]}-{PLAYOFF_WEEKS[-1]})...")
    playoff_weeks = []
    for week in PLAYOFF_WEEKS:
        week_data = get_weekly_data(league, week)
        if week_data and any(score > 0 for score in week_data["scores"].values()):
            playoff_weeks.append(week_data)
            print(f"   ✓ Week {week}")
        else:
            print(f"   ⊘ Week {week}: No scores yet")
    
    # Build playoff structure
    playoffs = None
    if playoff_weeks:
        print("\n6. Building playoff structure...")
        playoffs = build_playoff_structure(standings, playoff_weeks)
        if playoffs['championship']['final']['winner']:
            champ_name = standings[playoffs['championship']['final']['winner'] - 1]['name']
            print(f"   🏆 CHAMPION: {champ_name}")
        else:
            print(f"   ⊙ Playoffs in progress...")
    
    # Build final data structure
    data = {
        "leagueName": "Master's League",
        "year": YEAR,
        "currentWeek": len(regular_season_weeks) + len(playoff_weeks),
        "teams": teams,
        "schedule": SCHEDULE_H2H2,
        "weeks": regular_season_weeks,
        "standings": standings,
        "playoffs": playoffs
    }
    
    # Write to file
    print("\n7. Writing data.json...")
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"   ✓ Saved: {len(regular_season_weeks)} regular season + {len(playoff_weeks)} playoff weeks")
    
    # Next steps
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Review data.json to verify everything looks correct")
    print("2. git add data.json")
    print('3. git commit -m "Update week X"')
    print("4. git push")
    print("\nYour dashboard will update automatically on GitHub Pages!")
    print("=" * 60)

if __name__ == "__main__":
    main()