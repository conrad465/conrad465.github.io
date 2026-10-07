import json
import re
import requests
from bs4 import BeautifulSoup
import datetime

def scrape_events():
    today = datetime.date.today()
    
    # Target the upcoming Saturday to center the weekend query
    days_ahead = 5 - today.weekday() # 5 is Saturday
    if days_ahead < -1:
        days_ahead += 7
    target = today + datetime.timedelta(days=days_ahead)
    
    # Dynamic URL using your exact tags and the calculated weekend date
    url = f'https://www.thebostoncalendar.com/events?day={target.day}&year={target.year}&month={target.month}&weekend=1&tags%5B%5D=Date+Idea&tags%5B%5D=Festivals+%26+Fairs&tags%5B%5D=Food&tags%5B%5D=Music'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    events_by_day = {"Friday": [], "Saturday": [], "Sunday": []}
    
    try:
        print(f"Fetching from: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        current_day = "Saturday" # Default fallback
        
        # Read the HTML page top-to-bottom
        for element in soup.find_all(['h2', 'li']):
            
            # When we see a header, figure out what day we are in
            if element.name == 'h2':
                text = element.text.lower()
                if 'friday' in text:
                    current_day = "Friday"
                elif 'saturday' in text:
                    current_day = "Saturday"
                elif 'sunday' in text:
                    current_day = "Sunday"
                    
            # When we see an event, put it into the bucket for the current_day
            elif element.name == 'li' and 'event' in element.get('class', []):
                title_node = element.select_one('h3')
                loc_node = element.select_one('.location')
                desc_node = element.select_one('.description')
                tags_node = element.select_one('.tags')
                
                title = title_node.text.strip() if title_node else ''
                loc = loc_node.text.strip() if loc_node else 'Boston'
                desc = desc_node.text.strip() if desc_node else ''
                tags = tags_node.text.lower() if tags_node else ''
                
                # Skip recurring/ongoing events
                if re.search(r'recurring|ongoing|every|weekly', title, re.I) or re.search(r'recurring|ongoing|every|weekly', desc, re.I) or 'recurring' in tags:
                    continue
                    
                # Clean up description text to fit the iPad screen
                clean_desc = re.sub(r'\s+', ' ', desc).strip()
                if len(clean_desc) > 100:
                    clean_desc = clean_desc[:100] + '...'
                    
                display_loc = loc.split(',')[0].strip()
                
                # Format the text with frosted glass inline styling
                display_str = f"<span style='font-weight:600;'>{title}</span>  |  {display_loc}  |  <span style='opacity:0.8; font-size: 21px;'>{clean_desc}</span>"
                
                # Add to the correct Friday/Saturday/Sunday list!
                events_by_day[current_day].append(display_str)
                
    except Exception as e:
        err = f"<span style='color:#ff8a75;'>System Error</span>  |  <span style='font-weight:600;'>Scrape Failed</span>  |  <span style='opacity:0.8; font-size: 21px;'>{str(e)[:60]}</span>"
        events_by_day = {"Friday": [err], "Saturday
