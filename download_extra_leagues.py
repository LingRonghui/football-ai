"""
Download remaining extra leagues that failed due to the Season format bug.
"""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.database.league import LeagueDatabase
from src.network.leagues.league import League
from src.preprocessing.statistics import StatisticsEngine


def main():
    print("=" * 60)
    print("ProphitBet - 补充下载剩余联赛")
    print("=" * 60)
    
    db = LeagueDatabase()
    basic_stats = StatisticsEngine.get_basic_stat_columns()
    
    # Extra leagues that failed previously
    leagues_to_download = [
        {"country": "Norway", "name": "Eliteserien", "league_id": "eliteserien", "start_year": 2015, "stats": basic_stats},
        {"country": "Brazil", "name": "Serie-A", "league_id": "brazil_serie_a", "start_year": 2015, "stats": basic_stats},
        {"country": "USA", "name": "MLS", "league_id": "mls", "start_year": 2015, "stats": basic_stats},
        {"country": "Finland", "name": "Veikkausliiga", "league_id": "veikkausliiga", "start_year": 2015, "stats": basic_stats},
    ]
    
    available_leagues = {f"{l.country} - {l.name}": l for l in db.leagues}
    
    success_count = 0
    failed_leagues = []
    
    for league_info in leagues_to_download:
        key = f"{league_info['country']} - {league_info['name']}"
        
        if key not in available_leagues:
            print(f"[跳过] 未找到联赛: {key}")
            failed_leagues.append(key)
            continue
        
        base_league = available_leagues[key]
        
        if db.league_exists(league_info['league_id']):
            print(f"[已存在] {league_info['league_id']} ({key})")
            success_count += 1
            continue
        
        print(f"\n[下载中] {league_info['league_id']} ({key})...")
        print(f"  起始年份: {league_info['start_year']}")
        
        try:
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
    print(f"补充下载完成！成功: {success_count}/{len(leagues_to_download)}")
    if failed_leagues:
        print(f"失败: {len(failed_leagues)}")
        for l in failed_leagues:
            print(f"  - {l}")
    print("=" * 60)


if __name__ == "__main__":
    main()
