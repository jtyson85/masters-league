"""
Export 2025 Draft Results and Final Rosters to Excel
Pulls auction values and acquisition details from ESPN
"""
from espn_api.football import League
import pandas as pd
from datetime import datetime

# === CONFIGURATION ===
LEAGUE_ID = 1463914
YEAR = 2025
ESPN_S2 = "AEA%2BS%2Fr6rJGuLxbk2o2F16%2BC4WgtLlgR529fQxg%2BYD%2B2gIipmA2CJiaNmvWf6Gm6tbjHcPKRJZgEb9cE7RgUZjGfttWiaXIQRxUUqWfjKQKZnQXJmbKyBCdm%2BVBjXrYCzXFP0kYjunOPJrHPV%2BUsbxWVKoxMzqpd72n%2BgsAd6RtjxMSEon8JHZK4%2BJF%2F47%2BYRp5dmCdn6P7Db%2FrfHbWiEBYj3ZHJ8ByV%2FfSpu%2FhjoO7aLWLY14Oefu%2BUI3yqf%2FGeKPyfT6rOseM2Xjd4%2F185Ia1YjD2BmilceEjNngZFKmhazA%3D%3D"  # Your espn_s2 cookie
SWID = "{C030DBC8-E7FF-4728-8BA6-20DBB091D3DF}"     # Your SWID

def get_league():
    """Connect to ESPN league."""
    if ESPN_S2 and SWID:
        return League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
    return League(league_id=LEAGUE_ID, year=YEAR)

def get_draft_results(league):
    """Get all draft picks with auction values."""
    print("\nFetching draft data...")
    draft_data = []
    
    try:
        draft_picks = league.draft
        for pick in draft_picks:
            draft_data.append({
                'player_name': pick.playerName,
                'team_id': pick.team.team_id,
                'team_name': pick.team.team_name,
                'bid_amount': pick.bid_amount,
                'pick_number': pick.pick_number
            })
        print(f"✓ Found {len(draft_data)} draft picks")
    except Exception as e:
        print(f"⚠ Could not fetch draft data: {e}")
        print("  Trying alternate method...")
        # Fallback: Sometimes draft data is in different structure
        try:
            if hasattr(league, 'settings') and hasattr(league.settings, 'draft'):
                for pick in league.settings.draft:
                    draft_data.append({
                        'player_name': pick.get('playerName', 'Unknown'),
                        'team_id': pick.get('teamId', 0),
                        'team_name': 'Unknown',
                        'bid_amount': pick.get('bidAmount', 0),
                        'pick_number': pick.get('overallPickNumber', 0)
                    })
        except:
            print("  ✗ Draft data not accessible")
    
    return draft_data

def get_final_rosters(league):
    """Get end of season rosters for all teams."""
    print("\nFetching final rosters (Week 17)...")
    rosters = []
    
    # Try to get rosters from the last week of the season
    try:
        # Week 17 is typically the last regular season week
        for team in league.teams:
            print(f"  Processing {team.team_name}...")
            
            # Get roster - try different week numbers to find final week
            roster = None
            for week in [17, 16, 15, 14]:
                try:
                    roster = team.roster(week=week)
                    if roster:
                        print(f"    Found roster at week {week}")
                        break
                except:
                    continue
            
            if not roster:
                print(f"    ⚠ Could not find roster, using current")
                roster = team.roster
            
            for player in roster:
                # Get player info
                player_name = player.name
                position = player.position if hasattr(player, 'position') else 'N/A'
                
                # Try to determine acquisition type
                acquisition = 'Unknown'
                if hasattr(player, 'acquisitionType'):
                    acquisition = player.acquisitionType
                elif hasattr(player, 'acquisition_type'):
                    acquisition = player.acquisition_type
                
                rosters.append({
                    'team_id': team.team_id,
                    'team_name': team.team_name,
                    'player_name': player_name,
                    'position': position,
                    'acquisition_type': acquisition
                })
        
        print(f"✓ Collected {len(rosters)} total roster slots")
    except Exception as e:
        print(f"✗ Error fetching rosters: {e}")
    
    return rosters

def merge_and_export(draft_data, roster_data):
    """Merge draft and roster data, then export to Excel."""
    print("\nMerging data and creating Excel file...")
    
    # Convert to DataFrames
    df_draft = pd.DataFrame(draft_data)
    df_roster = pd.DataFrame(roster_data)
    
    # Create lookup dictionary for draft values
    draft_lookup = {}
    if not df_draft.empty:
        for _, row in df_draft.iterrows():
            key = (row['team_id'], row['player_name'])
            draft_lookup[key] = row['bid_amount']
    
    # Build final dataset
    final_data = []
    for _, row in df_roster.iterrows():
        team_id = row['team_id']
        player_name = row['player_name']
        
        # Look up draft value
        draft_value = draft_lookup.get((team_id, player_name), None)
        
        # Determine acquisition method
        if draft_value is not None:
            acquisition = f"Draft (${draft_value})"
            draft_cost = draft_value
        else:
            acquisition = "Waiver/Trade/FA"
            draft_cost = 0
        
        final_data.append({
            'Team': row['team_name'],
            'Player': player_name,
            'Position': row['position'],
            '2025 Draft Cost': draft_cost,
            'Acquisition': acquisition,
            '2026 Keeper Cost': draft_cost + 5 if draft_cost > 0 else None
        })
    
    df_final = pd.DataFrame(final_data)
    
    # Sort by team, then by draft cost (highest first)
    df_final = df_final.sort_values(['Team', '2025 Draft Cost'], ascending=[True, False])
    
    # Export to Excel with multiple sheets
    filename = f"masters_league_2025_rosters_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # All rosters in one sheet
        df_final.to_excel(writer, sheet_name='All Rosters', index=False)
        
        # Create individual team sheets
        for team_name in df_final['Team'].unique():
            team_df = df_final[df_final['Team'] == team_name].copy()
            team_df = team_df.drop('Team', axis=1)
            
            # Calculate team summary
            total_spent = team_df['2025 Draft Cost'].sum()
            keeper_cost = team_df['2026 Keeper Cost'].dropna().sum()
            
            # Add summary row
            summary = pd.DataFrame([{
                'Player': '--- TEAM TOTAL ---',
                'Position': '',
                '2025 Draft Cost': total_spent,
                'Acquisition': '',
                '2026 Keeper Cost': keeper_cost
            }])
            
            team_df = pd.concat([team_df, summary], ignore_index=True)
            
            # Write to sheet (truncate team name if too long for Excel sheet name)
            sheet_name = team_name[:31] if len(team_name) > 31 else team_name
            team_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Draft results sheet
        if not df_draft.empty:
            df_draft_sorted = df_draft.sort_values('bid_amount', ascending=False)
            df_draft_sorted.to_excel(writer, sheet_name='Draft Results', index=False)
    
    print(f"✓ Excel file created: {filename}")
    print(f"\nFile contains:")
    print(f"  - All Rosters sheet (combined)")
    print(f"  - Individual team sheets ({len(df_final['Team'].unique())} teams)")
    print(f"  - Draft Results sheet")
    print(f"\nTotal players: {len(df_final)}")
    print(f"Total auction spend: ${df_final['2025 Draft Cost'].sum():.0f}")
    
    return filename

def main():
    print("=" * 70)
    print("MASTER'S LEAGUE 2025 ROSTER & DRAFT EXPORT")
    print("=" * 70)
    
    # Connect
    print("\n1. Connecting to ESPN...")
    try:
        league = get_league()
        print(f"   ✓ Connected to: {league.settings.name}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        print("\n   Update ESPN_S2 and SWID in the script!")
        return
    
    # Get draft data
    print("\n2. Fetching 2025 draft results...")
    draft_data = get_draft_results(league)
    
    # Get final rosters
    print("\n3. Fetching final rosters...")
    roster_data = get_final_rosters(league)
    
    if not roster_data:
        print("\n✗ No roster data found. Cannot continue.")
        return
    
    # Merge and export
    print("\n4. Creating Excel file...")
    filename = merge_and_export(draft_data, roster_data)
    
    print("\n" + "=" * 70)
    print("SUCCESS!")
    print("=" * 70)
    print(f"\nExcel file ready: {filename}")
    print("\nThis file includes:")
    print("  • All team rosters")
    print("  • 2025 auction costs")
    print("  • Calculated 2026 keeper costs (2025 cost + $5)")
    print("  • Acquisition method (Draft/Waiver/Trade/FA)")
    print("\nUse this to help teams select their keepers!")
    print("=" * 70)

if __name__ == "__main__":
    # Check for pandas
    try:
        import pandas
        import openpyxl
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pandas', 'openpyxl'])
        print("Packages installed! Please run the script again.")
        exit()
    
    main()