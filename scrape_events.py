import json
import re
import requests
from bs4 import BeautifulSoup
import datetime

def scrape_events():
    today = datetime.date.today()
    
    # Calculate the upcoming Saturday (The Boston Calendar centers weekend queries on Saturday)
    days_ahead = 5 - today.weekday() # 5 is Saturday
    if days_ahead < -1: # If it is Sunday (-1), keep it on the current weekend. Otherwise skip to next.
        days_ahead += 7
    target = today + datetime.timedelta(days=days_ahead)
    
    # Using your exact URL format, but making the date dynamic so it never breaks
    url = f'https://www.thebostoncalendar.com/events?day={target.day}&year={target.year}&month={target.month}&weekend=1&tags%5B%5D=Date+Idea&tags%5B%5D=Festivals+%26+Fairs&tags%5B%5D=Food&tags%5B%5D=Music'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    events_by_day = {"Friday": [], "Saturday": [], "Sunday": []}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for node in soup.select('li.event'):
            title_node = node.select_one('h3')
            time_node = node.select_one('.time')
            loc_node = node.select_one('.location')
            desc_node = node.select_one('.description')
            tags_node = node.select_one('.tags')
            
            title = title_node.text.strip() if title_node else ''
            time_str = re.sub(r'\s+', ' ', time_node.text).strip() if time_node else ''
            loc = loc_node.text.strip() if loc_node else 'Boston'
            desc = desc_node.text.strip() if desc_node else ''
            tags = tags_node.text.lower() if tags_node else ''
            
            # Skip recurring/ongoing events
            if re.search(r'recurring|ongoing|every|weekly', title, re.I) or re.search(r'recurring|ongoing|every|weekly', desc, re.I) or 'recurring' in tags:
                continue
                
            clean_desc = re.sub(r'\s+', ' ', desc).strip()
            if len(clean_desc) > 100:
                clean_desc = clean_desc[:100] + '...'
                
            display_loc = loc.split(',')[0].strip()
            
            # We removed the date from the string itself because the bar label (FRI/SAT/SUN) will handle it!
            display_str = f"<span style='font-weight:600;'>{title}</span>  |  {display_loc}  |  <span style='opacity:0.8; font-size: 21px;'>{clean_desc}</span>"
            
            # Sort into the correct day bucket
            if re.search(r'Friday|Fri', time_str, re.I):
                events_by_day["Friday"].append(display_str)
            elif re.search(r'Saturday|Sat', time_str, re.I):
                events_by_day["Saturday"].append(display_str)
            elif re.search(r'Sunday|Sun', time_str, re.I):
                events_by_day["Sunday"].append(display_str)
                
    except Exception as e:
        err = f"<span style='color:#ff8a75;'>System Error</span>  |  <span style='font-weight:600;'>Scrape Failed</span>  |  <span style='opacity:0.8; font-size: 21px;'>{str(e)[:60]}</span>"
        events_by_day = {"Friday": [err], "Saturday": [err], "Sunday": [err]}

    # Fill in blanks if a specific day has zero matching events
    for day in ["Friday", "Saturday", "Sunday"]:
        if not events_by_day[day]:
            events_by_day[day] = [f"<span style='font-weight:600;'>No matching events found</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>No selected categories running this day.</span>"]
            
    with open('events.json', 'w') as f:
        json.dump(events_by_day, f)

if __name__ == '__main__':
    scrape_events()
