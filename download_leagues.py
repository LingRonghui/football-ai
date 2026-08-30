"""
Download league data for the matches found on China Sports Lottery.
Leagues: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie, Liga-1, Eliteserien, Brazil Serie A, MLS, Veikkausliiga
"""
import os
import sys

# Change to project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.database.league import LeagueDatabase
from src.network.leagues.league import League
from src.preprocessing.statistics import StatisticsEngine


def main():
    print("=" * 60)
    print("ProphitBet - 竞彩联赛数据下载")
    print("=" * 60)
    
    db = LeagueDatabase()
    
    # Stat columns
    basic_stats = StatisticsEngine.get_basic_stat_columns()
    extended_stats = StatisticsEngine.get_extended_stat_columns()
    main_stats = basic_stats + extended_stats  # For main leagues
    extra_stats = basic_stats  # For extra leagues
    
    # Leagues to download (matching China Sports Lottery matches)
    leagues_to_download = [
        # Main leagues (五大联赛 + 荷甲 + 葡超)
        {"country": "England", "name": "Premier-League", "league_id": "premier_league", "start_year": 2015, "stats": main_stats},
        {"country": "Spain", "name": "La-Liga", "league_id": "la_liga", "start_year": 2015, "stats": main_stats},
        {"country": "Italy", "name": "Serie-A", "league_id": "serie_a", "start_year": 2015, "stats": main_stats},
        {"country": "Germany", "name": "Bundesliga-1", "league_id": "bundesliga", "start_year": 2015, "stats": main_stats},
        {"country": "France", "name": "Ligue-1", "league_id": "ligue_1", "start_year": 2015, "stats": main_stats},
        {"country": "Netherlands", "name": "Eredivisie", "league_id": "eredivisie", "start_year": 2015, "stats": main_stats},
        {"country": "Portugal", "name": "Liga-1", "league_id": "portugal_liga", "start_year": 2015, "stats": main_stats},
        # Extra leagues (挪超、巴甲、美职、芬超)
        {"country": "Norway", "name": "Eliteserien", "league_id": "eliteserien", "start_year": 2015, "stats": extra_stats},
        {"country": "Brazil", "name": "Serie-A", "league_id": "brazil_serie_a", "start_year": 2015, "stats": extra_stats},
        {"country": "USA", "name": "MLS", "league_id": "mls", "start_year": 2015, "stats": extra_stats},
        {"country": "Finland", "name": "Veikkausliiga", "league_id": "veikkausliiga", "start_year": 2015, "stats": extra_stats},
    ]
    
    # Find league configs
    available_leagues = {f"{l.country} - {l.name}": l for l in db.leagues}
    
    print(f"\n共找到 {len(available_leagues)} 个可用联赛")
    print(f"需要下载 {len(leagues_to_download)} 个联赛数据\n")
    
    success_count = 0
    failed_leagues = []
    
    for league_info in leagues_to_download:
        key = f"{league_info['country']} - {league_info['name']}"
        
        if key not in available_leagues:
            print(f"[跳过] 未找到联赛: {key}")
            failed_leagues.append(key)
            continue
        
        base_league = available_leagues[key]
        
        # Check if already exists
        if db.league_exists(league_info['league_id']):
            print(f"[已存在] {league_info['league_id']} ({key})")
            success_count += 1
            continue
        
        print(f"\n[下载中] {league_info['league_id']} ({key})...")
        print(f"  起始年份: {league_info['start_year']}")
        
        try:
            # Create league object
            league = League(
                country=base_league.country,
                name=base_league.name,
                league_id=league_info['league_id'],
                start_year=league_info['start_year'],
                category=base_league.category,
                url=base_league.url,
                fixture=base_league.fixture,
                stats_columns=league_info['stats'],
                match_history_window=3,
                goal_diff_margin=2,
                odd_1_range=None,
                odd_x_range=None,
                odd_2_range=None,
            )
            
            df = db.create_league(league=league)
            
            if df is not None and len(df) > 0:
                print(f"[成功] {league_info['league_id']}: 下载了 {len(df)} 场比赛数据")
                print(f"  赛季范围: {df['Season'].min()} - {df['Season'].max()}")
                success_count += 1
            else:
                print(f"[失败] {league_info['league_id']}: 未获取到数据")
                failed_leagues.append(key)
        except Exception as e:
            print(f"[错误] {league_info['league_id']}: {e}")
            import traceback
            traceback.print_exc()
            failed_leagues.append(key)
    
    print("\n" + "=" * 60)
    print(f"下载完成！成功: {success_count}/{len(leagues_to_download)}")
    if failed_leagues:
        print(f"失败/跳过: {len(failed_leagues)}")
        for l in failed_leagues:
            print(f"  - {l}")
    print("=" * 60)


if __name__ == "__main__":
    main()
