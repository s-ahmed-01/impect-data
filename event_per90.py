import pandas as pd
import json
from pathlib import Path
from examples.functions.load_data import load_matches

def analyze_fullback_events():
    """Analyze event types and locations for fullbacks across all matches"""
    
    fullback_events = []
    fullback_positions = ['RIGHT_WINGBACK_DEFENDER', 'LEFT_WINGBACK_DEFENDER']
    matches = load_matches()
    
    for match_id in matches['id'].tolist():
        # Load lineup data
        with open(Path(f"data/lineups/lineups_{match_id}.json")) as f:
            lineup_data = json.load(f)
        
        # Load match events
        events_df = pd.read_json(f"data/events/events_{match_id}.json")
        
        # Process both teams
        for squad in ['squadHome', 'squadAway']:
            team_data = lineup_data[squad]
            team_id = team_data['id']
            
            # Track fullback minutes using substitutions
            fullback_minutes = {}
            
            # Get starting fullbacks
            for pos in team_data['startingPositions']:
                if pos['position'] in fullback_positions:
                    fullback_minutes[pos['playerId']] = {
                        'start': 0,
                        'end': 90 * 60  # Default to full game
                    }
            
            # Update minutes based on substitutions
            for sub in team_data.get('substitutions', []):
                if sub['fromPosition'] in fullback_positions:
                    fullback_minutes[sub['playerId']]['end'] = sub['gameTime']['gameTimeInSec']
                if sub['toPosition'] in fullback_positions:
                    fullback_minutes[sub['playerId']] = {
                        'start': sub['gameTime']['gameTimeInSec'],
                        'end': 90 * 60
                    }
            
            # Get player names
            player_names = {p['id']: p.get('name', str(p['id'])) for p in team_data['players']}
            
            # Analyze events for each fullback
            for player_id, minutes in fullback_minutes.items():
                player_events = events_df[
                    (events_df['squadId'] == team_id) & 
                    (events_df['player'].apply(lambda x: x.get('id') if x else None) == player_id)
                ]
                
                # Group events by type and location
                for _, event in player_events.iterrows():
                    if event['start']:
                        fullback_events.append({
                            'match_id': match_id,
                            'team_id': team_id,
                            'player_id': player_id,
                            'player_name': player_names[player_id],
                            'minutes_played': (minutes['end'] - minutes['start']) / 60,
                            'event_type': event['actionType'],
                            'packing_zone': event['start'].get('packingZone'),
                            'pitch_position': event['start'].get('pitchPosition'),
                            'lane': event['start'].get('lane'),
                            'result': event.get('result'),
                            'gameTime': event['gameTime']['gameTimeInSec']
                        })
    
    # Convert to DataFrame
    df = pd.DataFrame(fullback_events)
    
    # Create summary by event type and location
    summary = df.groupby(
        ['player_name', 'event_type', 'packing_zone', 'pitch_position', 'lane']
    ).agg({
        'match_id': 'count',  # Count of events
        'minutes_played': 'first',  # Minutes played
        'result': lambda x: (x == 'SUCCESS').sum() / len(x) if len(x) > 0 else 0  # Success rate
    }).reset_index()
    
    # Calculate per 90 minutes rates
    summary['events_per_90'] = summary['match_id'] / (summary['minutes_played'] / 90)
    
    return summary

# Run analysis
summary = analyze_fullback_events()

# Display results grouped by player
for player in summary['player_name'].unique():
    print(f"\nEvents for {player}:")
    player_summary = summary[summary['player_name'] == player]
    print(player_summary.sort_values('events_per_90', ascending=False))