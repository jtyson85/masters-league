"""
Master's League 2026 Dual Schedule Generator
Creates TWO complete schedules (Matchup 1 and Matchup 2) for all 13 weeks
"""
import json
import random

# ESPN Team IDs from your league
TEAMS = {
    1: "Arbour", 2: "More", 3: "Gore", 4: "Bruton", 5: "Reynolds",
    6: "Brown", 7: "Tyson", 8: "Tack", 9: "Jackson", 10: "Caldwell"
}

TEAM_IDS = list(TEAMS.keys())
WEEKS = 13

def generate_round_robin(teams, seed=None):
    """Generate a complete round-robin schedule where each team plays every other team once."""
    n = len(teams)
    schedule = []
    
    # Optionally shuffle for variety
    if seed:
        random.seed(seed)
        teams = teams.copy()
        random.shuffle(teams)
    
    # Circle method for round-robin
    if n % 2 == 1:
        teams = teams + [None]
        n += 1
    
    for round_num in range(n - 1):
        round_matchups = []
        for i in range(n // 2):
            t1 = teams[i]
            t2 = teams[n - 1 - i]
            if t1 is not None and t2 is not None:
                round_matchups.append([t1, t2])
        schedule.append(round_matchups)
        
        # Rotate (keep first team fixed)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    
    return schedule

def create_dual_schedules(team_ids, num_weeks=13):
    """
    Create two complete schedules for double-header format.
    Each schedule uses a different round-robin rotation.
    """
    # Generate first schedule (standard rotation)
    matchup1_schedule = generate_round_robin(team_ids.copy())
    
    # Generate second schedule (shuffled rotation for variety)
    matchup2_schedule = generate_round_robin(team_ids.copy(), seed=2026)
    
    # Package by week
    schedule_matchup1 = {}
    schedule_matchup2 = {}
    
    for week in range(1, num_weeks + 1):
        # Cycle through round-robin (9 weeks for 10 teams)
        rr_week = (week - 1) % len(matchup1_schedule)
        schedule_matchup1[str(week)] = matchup1_schedule[rr_week]
        schedule_matchup2[str(week)] = matchup2_schedule[rr_week]
    
    return schedule_matchup1, schedule_matchup2

def verify_schedules(sched1, sched2, team_ids):
    """Verify both schedules are valid."""
    print("\n=== SCHEDULE VERIFICATION ===\n")
    
    # Count total games per team
    games_per_team = {tid: 0 for tid in team_ids}
    opponent_count = {tid: {opp: 0 for opp in team_ids if opp != tid} for tid in team_ids}
    
    for week in range(1, 14):
        week_str = str(week)
        for home, away in sched1.get(week_str, []):
            games_per_team[home] += 1
            games_per_team[away] += 1
            opponent_count[home][away] += 1
            opponent_count[away][home] += 1
        for home, away in sched2.get(week_str, []):
            games_per_team[home] += 1
            games_per_team[away] += 1
            opponent_count[home][away] += 1
            opponent_count[away][home] += 1
    
    print(f"Games per team (should be {WEEKS * 2} = 26):")
    for tid in sorted(games_per_team.keys()):
        print(f"  Team {tid} ({TEAMS[tid]}): {games_per_team[tid]} games")
    
    print("\nOpponent matchup counts:")
    for tid in sorted(team_ids):
        opp_counts = [opponent_count[tid][opp] for opp in sorted(opponent_count[tid].keys())]
        min_games = min(opp_counts)
        max_games = max(opp_counts)
        print(f"  Team {tid} ({TEAMS[tid]}): plays each opponent {min_games}-{max_games} times")
    
    return True

def print_schedules(sched1, sched2):
    """Print human-readable schedules."""
    print("\n" + "=" * 80)
    print("2026 MASTER'S LEAGUE COMPLETE SCHEDULE")
    print("=" * 80)
    print("Each team plays TWO matchups every week\n")
    
    for week in range(1, WEEKS + 1):
        print(f"{'='*80}")
        print(f"WEEK {week}")
        print(f"{'='*80}")
        
        print("  MATCHUP 1:")
        for home, away in sched1[str(week)]:
            print(f"    {TEAMS[home]:20s} vs {TEAMS[away]:20s}")
        
        print("\n  MATCHUP 2:")
        for home, away in sched2[str(week)]:
            print(f"    {TEAMS[home]:20s} vs {TEAMS[away]:20s}")
        
        print()

def main():
    print("=" * 80)
    print("MASTER'S LEAGUE 2026 DUAL SCHEDULE GENERATOR")
    print("=" * 80)
    
    print(f"\nGenerating TWO schedules for {len(TEAM_IDS)} teams over {WEEKS} weeks...")
    print(f"Each team will play {WEEKS * 2} total games (2 per week)\n")
    
    # Generate both schedules
    matchup1, matchup2 = create_dual_schedules(TEAM_IDS, WEEKS)
    
    # Verify
    verify_schedules(matchup1, matchup2, TEAM_IDS)
    
    # Print readable version
    print_schedules(matchup1, matchup2)
    
    # Save to files
    print("\n" + "=" * 80)
    print("SAVING SCHEDULES")
    print("=" * 80)
    
    with open("schedule_matchup1_2026.json", "w") as f:
        json.dump(matchup1, f, indent=2)
    print("✓ Saved Matchup 1 to: schedule_matchup1_2026.json")
    
    with open("schedule_matchup2_2026.json", "w") as f:
        json.dump(matchup2, f, indent=2)
    print("✓ Saved Matchup 2 to: schedule_matchup2_2026.json")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Review the schedules above")
    print("2. Copy BOTH schedules into your update_data.py:")
    print("   - SCHEDULE_MATCHUP1 = <content of schedule_matchup1_2026.json>")
    print("   - SCHEDULE_MATCHUP2 = <content of schedule_matchup2_2026.json>")
    print("3. Update update_data.py to use both schedules")
    print("=" * 80)

if __name__ == "__main__":
    main()