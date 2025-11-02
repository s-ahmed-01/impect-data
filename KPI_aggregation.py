import pandas as pd
import json
from pathlib import Path
from examples.functions.load_data import load_matches, load_match_events, load_match_scorings

def load_fullback_data(match_ids):
    fullback_data = []
    fullback_positions = ['RIGHT_WINGBACK_DEFENDER', 'LEFT_WINGBACK_DEFENDER']
    
    for match_id in match_ids:
        # Load lineup data
        with open(Path(f"data/lineups/lineups_{match_id}.json")) as f:
            lineup_data = json.load(f)
            
        # Load events and KPIs
        match_events = pd.read_json(f"data/events/events_{match_id}.json")
        match_kpis = pd.read_json(f"data/events_kpis/events_kpis_{match_id}.json")
        
        # Find fullbacks using specific position labels
        for team in lineup_data:
            team_id = team['teamId']
            fullbacks = [p for p in team['players'] if p['specificPosition'] in fullback_positions]
            
            for fullback in fullbacks:
                # Get player's KPIs
                player_kpis = match_kpis[match_kpis['playerId'] == fullback['id']]
                player_events = match_events[match_events['playerId'] == fullback['id']]
                
                fullback_data.append({
                    'match_id': match_id,
                    'team_id': team_id,
                    'player_id': fullback['id'],
                    'player_name': fullback['name'],
                    'position': fullback['specificPosition'],
                    'minutes_played': fullback.get('minutesPlayed', 0),
                    'events_count': len(player_events),
                    'kpis': player_kpis.to_dict('records')
                })
    
    return pd.DataFrame(fullback_data)

def calculate_fullback_metrics(df):
    """Calculate aggregated KPIs for fullbacks"""
    metrics = df.groupby(['player_id', 'player_name', 'position']).agg({
        'minutes_played': 'sum',
        'events_count': 'sum'
    }).reset_index()
    
    # Calculate per 90 minutes metrics
    metrics['events_per_90'] = metrics['events_count'] / (metrics['minutes_played'] / 90)
    
    return metrics

# Example usage
matches = load_matches()
match_ids = matches['id'].tolist()[:3]  # Start with 3 matches for testing

fullback_data = load_fullback_data(match_ids)
fullback_metrics = calculate_fullback_metrics(fullback_data)
print(fullback_metrics)