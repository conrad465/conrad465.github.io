import json
import re
import requests
from bs4 import BeautifulSoup

def scrape_events():
    url = 'https://www.thebostoncalendar.com/events'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        allowed_cats = ['art', 'date idea', 'festival', 'fair', 'food', 'music', 'seasonal']
        filtered_events = []
        
        for node in soup.select('li.event'):
            title_node = node.select_one('h3')
            time_node = node.select_one('.time')
            loc_node = node.select_one('.location')
            tags_node = node.select_one('.tags')
            desc_node = node.select_one('.description')
            
            title = title_node.text.strip() if title_node else ''
            time_str = re.sub(r'\s+', ' ', time_node.text).strip() if time_node else ''
            loc = loc_node.text.strip() if loc_node else 'Boston'
            tags = tags_node.text.lower() if tags_node else ''
            desc = desc_node.text.strip() if desc_node else ''
            
            # Filter recurring/ongoing
            if re.search(r'recurring|ongoing|every', title, re.I) or re.search(r'recurring|ongoing|every', desc, re.I) or 'recurring' in tags:
                continue
                
            # Filter for weekend
            if not re.search(r'Friday|Saturday|Sunday|Fri|Sat|Sun', time_str, re.I) and not re.search(r'Friday|Saturday|Sunday', title, re.I):
                continue
                
            # Filter by category
            has_cat = any(c in tags for c in allowed_cats) or any(c in desc.lower() for c in allowed_cats)
            if not has_cat:
                continue
                
            # Clean and format description
            clean_desc = re.sub(r'\s+', ' ', desc).strip()
            if len(clean_desc) > 100:
                clean_desc = clean_desc[:100] + '...'
                
            display_date = re.sub(r'(?:, \d{4}| at | \d{1,2}:\d{2}\s*(am|pm|AM|PM)).*', '', time_str).strip() or 'This Wknd'
            display_loc = loc.split(',')[0].strip()
            
            # Format HTML identically to the previous Javascript logic
            display_str = f"<span style='color:#6fe3a5;'>{display_date}</span>  |  <span style='font-weight:600;'>{title}</span>  |  {display_loc}  |  <span style='opacity:0.8; font-size: 21px;'>{clean_desc}</span>"
            filtered_events.append(display_str)
            
        # Fallback if no events match criteria
        if not filtered_events:
            filtered_events.append("<span style='color:#6fe3a5;'>This Wknd</span>  |  <span style='font-weight:600;'>No matching events found</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>Filters yielded zero results.</span>")
            
        with open('events.json', 'w') as f:
            json.dump(filtered_events, f)
            
    except Exception as e:
        print(f"Scrape failed: {e}")
        # If scraper fails, write an error message to the JSON so the iPad knows
        error_event = [f"<span style='color:#ff8a75;'>System Error</span>  |  <span style='font-weight:600;'>Scrape Failed</span>  |  GitHub Actions  |  <span style='opacity:0.8; font-size: 21px;'>{str(e)[:100]}</span>"]
        with open('events.json', 'w') as f:
            json.dump(error_event, f)

if __name__ == '__main__':
    scrape_events()