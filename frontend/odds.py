"""
Odds integration module for PrizePicks Correlation ML frontend.

Provides methods to:
- Fetch live odds from multiple sportsbooks
- Cache and update odds
- Convert between different odds formats
- Provide fallback mock data for demo purposes
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests


class OddsProvider:
    """Base class for odds providers."""
    
    def __init__(self, name: str):
        self.name = name
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    def get_odds(self, player: str, market: str) -> Optional[Dict]:
        """Fetch odds for a player in a market."""
        raise NotImplementedError
    
    def is_cached_fresh(self, key: str) -> bool:
        """Check if cached data is still fresh."""
        if key not in self.cache:
            return False
        timestamp, _ = self.cache[key]
        age = (datetime.now() - timestamp).total_seconds()
        return age < self.cache_ttl


class MockOddsProvider(OddsProvider):
    """Mock odds provider for demo/testing purposes."""
    
    # Sample data for popular players
    MOCK_ODDS_DATA = {
        'patrick_mahomes': {
            'passing_yards': {
                'DraftKings': {'over': -110, 'under': -110, 'line': 300.5},
                'FanDuel': {'over': -105, 'under': -115, 'line': 299.5},
                'BetMGM': {'over': -110, 'under': -110, 'line': 301.0},
                'PointsBet': {'over': -110, 'under': -110, 'line': 300.0},
            }
        },
        'travis_kelce': {
            'receiving_yards': {
                'DraftKings': {'over': -110, 'under': -110, 'line': 75.5},
                'FanDuel': {'over': -105, 'under': -115, 'line': 74.5},
                'BetMGM': {'over': -110, 'under': -110, 'line': 76.0},
                'PointsBet': {'over': -110, 'under': -110, 'line': 75.0},
            }
        },
        'isaiah_pacheco': {
            'rushing_yards': {
                'DraftKings': {'over': -110, 'under': -110, 'line': 65.5},
                'FanDuel': {'over': -105, 'under': -115, 'line': 64.5},
                'BetMGM': {'over': -110, 'under': -110, 'line': 66.0},
                'PointsBet': {'over': -110, 'under': -110, 'line': 65.0},
            }
        },
    }
    
    def __init__(self):
        super().__init__('MockOddsProvider')
    
    def get_odds(self, player: str, market: str) -> Optional[Dict]:
        """Return mock odds for demo purposes."""
        player_key = player.lower().replace(' ', '_')
        
        if player_key in self.MOCK_ODDS_DATA:
            if market in self.MOCK_ODDS_DATA[player_key]:
                sportsbook_odds = self.MOCK_ODDS_DATA[player_key][market]
                return {
                    'player': player,
                    'market': market,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'mock',
                    'sportsbooks': sportsbook_odds,
                }
        
        # Return generic fallback odds
        return {
            'player': player,
            'market': market,
            'timestamp': datetime.now().isoformat(),
            'source': 'mock_fallback',
            'sportsbooks': {
                'DraftKings': {'over': -110, 'under': -110, 'line': 50.0},
                'FanDuel': {'over': -105, 'under': -115, 'line': 50.0},
                'BetMGM': {'over': -110, 'under': -110, 'line': 50.0},
                'PointsBet': {'over': -110, 'under': -110, 'line': 50.0},
            },
        }


class TheOddsAPIProvider(OddsProvider):
    """Integration with The Odds API (theoddapi.com)."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__('TheOddsAPI')
        self.api_key = api_key or 'demo'  # Use demo key by default
        self.base_url = 'https://api.the-odds-api.com/v4'
    
    def get_odds(self, player: str, market: str) -> Optional[Dict]:
        """
        Fetch live odds from The Odds API.
        
        Note: Requires API key from https://the-odds-api.com
        Free tier limited to 500 requests/month.
        """
        # For demo: use mock provider instead
        # In production: uncomment below and provide API key
        
        # Example implementation (would need real API key):
        # try:
        #     sport = self._map_market_to_sport(market)
        #     url = f"{self.base_url}/sports/{sport}/odds"
        #     params = {
        #         'apiKey': self.api_key,
        #         'regions': 'us',
        #         'markets': 'h2h',
        #     }
        #     response = requests.get(url, params=params, timeout=5)
        #     response.raise_for_status()
        #     data = response.json()
        #     return self._parse_odds(data, player, market)
        # except Exception as e:
        #     print(f"Error fetching odds from The Odds API: {e}")
        #     return None
        
        # For now, use mock data
        mock_provider = MockOddsProvider()
        return mock_provider.get_odds(player, market)
    
    def _map_market_to_sport(self, market: str) -> str:
        """Map prop market to sport code."""
        return 'americanfootball_nfl'


def get_best_odds(player: str, market: str, sportsbook: Optional[str] = None) -> Dict:
    """
    Get the best odds for a player prop across sportsbooks.
    
    Args:
        player: Player name (e.g., "Patrick Mahomes")
        market: Market type (e.g., "passing_yards")
        sportsbook: Specific sportsbook to query (optional)
    
    Returns:
        Dict with odds data including best line and which book has it
    """
    # Use mock provider for demo
    provider = MockOddsProvider()
    odds_data = provider.get_odds(player, market)
    
    if not odds_data:
        return {'error': f'No odds found for {player} {market}'}
    
    sportsbooks = odds_data['sportsbooks']
    
    if sportsbook:
        sportsbook_lower = sportsbook.lower()
        for sb_name, sb_odds in sportsbooks.items():
            if sb_name.lower() == sportsbook_lower:
                return {
                    'player': player,
                    'market': market,
                    'sportsbook': sb_name,
                    'odds': sb_odds,
                    'source': odds_data['source'],
                }
        return {'error': f'Sportsbook {sportsbook} not found'}
    
    # Return best over/under odds across all books
    best_over = None
    best_under = None
    best_over_book = None
    best_under_book = None
    best_line = None
    
    for sb_name, sb_odds in sportsbooks.items():
        over_odds = sb_odds.get('over', 0)
        under_odds = sb_odds.get('under', 0)
        line = sb_odds.get('line', 0)
        
        if best_over is None or over_odds > best_over:
            best_over = over_odds
            best_over_book = sb_name
        
        if best_under is None or under_odds > best_under:
            best_under = under_odds
            best_under_book = sb_name
        
        if best_line is None:
            best_line = line
    
    return {
        'player': player,
        'market': market,
        'line': best_line,
        'over': {'odds': best_over, 'sportsbook': best_over_book},
        'under': {'odds': best_under, 'sportsbook': best_under_book},
        'all_sportsbooks': sportsbooks,
        'source': odds_data['source'],
    }


def american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds."""
    if american_odds < 0:
        return 1 + (100 / abs(american_odds))
    else:
        return 1 + (american_odds / 100)


def decimal_to_american(decimal_odds: float) -> float:
    """Convert decimal odds to American odds."""
    if decimal_odds > 2:
        return (decimal_odds - 1) * 100
    else:
        return -100 / (decimal_odds - 1)


def american_to_implied_probability(american_odds: float) -> float:
    """Convert American odds to implied probability."""
    if american_odds < 0:
        return abs(american_odds) / (abs(american_odds) + 100)
    else:
        return 100 / (american_odds + 100)


def implied_probability_to_american(prob: float) -> float:
    """Convert implied probability to American odds."""
    if prob >= 0.5:
        return -(prob * 100) / (1 - prob)
    else:
        return ((1 - prob) * 100) / prob


# Common player names and markets for autocomplete
POPULAR_PLAYERS = [
    'Patrick Mahomes',
    'Travis Kelce',
    'Isaiah Pacheco',
    'Josh Allen',
    'Stefon Diggs',
    'Joe Burrow',
    'Ja\'Marr Chase',
    'Tyreek Hill',
    'Justin Herbert',
]

MARKETS = [
    'passing_yards',
    'receiving_yards',
    'rushing_yards',
    'passing_touchdowns',
    'receiving_touchdowns',
    'rushing_touchdowns',
]

SPORTSBOOKS = [
    'DraftKings',
    'FanDuel',
    'BetMGM',
    'PointsBet',
]
