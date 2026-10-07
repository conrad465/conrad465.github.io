import json
import re
import datetime
from bs4 import BeautifulSoup
import cloudscraper

def scrape_events():
    today = datetime.date.today()
    
    # Target the upcoming Saturday to center the weekend query
    days_ahead = 5 - today.weekday() # 5 is Saturday
    if days_ahead < -1:
        days_ahead += 7
    target = today + datetime.timedelta(days=days_ahead)
    
    url = 'https://www.thebostoncalendar.com/events'
    
    # Properly encode the array of tags using a list of tuples
    params = [
        ('day', target.day),
        ('year', target.year),
        ('month', target.month),
        ('weekend', 1),
        ('tags[]', 'Date Idea'),
        ('tags[]', 'Festivals & Fairs'),
        ('tags[]', 'Food'),
        ('tags[]', 'Music')
    ]
    
    events_by_day = {"Friday": [], "Saturday": [], "Sunday": []}
    
    try:
        print(f"Fetching from: {url}")
        
        # Mimic a real desktop browser to bypass Cloudflare 403 blocks
        scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        })
        
        response = scraper.get(url, params=params, timeout=15)
        response.raise_for_status() # Force the script into the except block if blocked
        
        soup = BeautifulSoup(response.text, 'html.parser')
        current_day = "Saturday" # Default fallback
        
        # Read the HTML page top-to-bottom
        for element in soup.find_all(['h2', 'li']):
            
            if element.name == 'h2':
                text = element.text.lower()
                if 'friday' in text:
                    current_day = "Friday"
                elif 'saturday' in text:
                    current_day = "Saturday"
                elif 'sunday' in text:
                    current_day = "Sunday"
                    
            elif element.name == 'li' and 'event' in element.get('class', []):
                title_node = element.select_one('h3')
                loc_node = element.select_one('.location')
                desc_node = element.select_one('.description')
                tags_node = element.select_one('.tags')
                
                title = title_node.text.strip() if title_node else ''
                loc = loc_node.text.strip() if loc_node else 'Boston'
                desc = desc_node.text.strip() if desc_node else ''
                tags = tags_node.text.lower() if tags_node else ''
                
                if re.search(r'recurring|ongoing|every|weekly', title, re.I) or re.search(r'recurring|ongoing|every|weekly', desc, re.I) or 'recurring' in tags:
                    continue
                    
                clean_desc = re.sub(r'\s+', ' ', desc).strip()
                if len(clean_desc) > 100:
                    clean_desc = clean_desc[:100] + '...'
                    
                display_loc = loc.split(',')[0].strip()
                
                display_str = f"<span style='font-weight:600;'>{title}</span>  |  {display_loc}  |  <span style='opacity:0.8; font-size: 21px;'>{clean_desc}</span>"
                events_by_day[current_day].append(display_str)
                
    except Exception as e:
        # If the scrape fails, we'll now see the exact HTTP error pushed to the dashboard
        err = f"<span style='color:#ff8a75;'>System Error</span>  |  <span style='font-weight:600;'>Scrape Failed</span>  |  <span style='opacity:0.8; font-size: 21px;'>{str(e)[:60]}</span>"
        events_by_day = {"Friday": [err], "Saturday": [err], "Sunday": [err]}

    for day in ["Friday", "Saturday", "Sunday"]:
        if not events_by_day[day]:
            events_by_day[day] = [f"<span style='font-weight:600;'>No matching events found</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>No selected categories running this day.</span>"]
            
    with open('events.json', 'w') as f:
        json.dump(events_by_day, f)

if __name__ == '__main__':
    scrape_events()
