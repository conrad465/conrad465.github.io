import json
import re
import datetime
import urllib.parse
import html
import requests
import xml.etree.ElementTree as ET

def update_events():
    today = datetime.date.today()
    
    # Lock onto the Friday of the *current* week (Monday=0 ... Sunday=6).
    # This prevents the scraper from rolling forward to next weekend when it runs on Sat/Sun.
    days_to_friday = 4 - today.weekday() 
    friday = today + datetime.timedelta(days=days_to_friday)
    saturday = friday + datetime.timedelta(days=1)
    sunday = friday + datetime.timedelta(days=2)
    monday = friday + datetime.timedelta(days=3)
    
    # Format dates exactly as the API expects
    gte_date = f"{friday.strftime('%Y-%m-%d')}T04:00:00.000Z"
    lte_date = f"{monday.strftime('%Y-%m-%d')}T03:59:59.000Z"
    
    # Reconstruct the Meet Boston JSON filter
    base_filter = {
        "active": True,
        "$and": [
            {"categories.catId": {"$in": ["228","183","209","208","182","97","98","224","223","141","132","135","206","91","178","95","86","216","204","89","90","113","136","85","185","197","199","94","230","142","88","217","92","187","222","138","108","233","139","215","93","114","87","96","144","237","202","236"]}},
            {"categories.catId": {"$nin": ["105"]}},
            {"eventTypeId": {"$nin": [1062]}},
            {"categories.catId": {"$in": ["86","91","92"]}}
        ],
        "dates": {
            "$elemMatch": {
                "eventDate": {
                    "$gte": {"$date": gte_date},
                    "$lte": {"$date": lte_date}
                }
            }
        },
        "sites": {"$in": ["primary"]}
    }
    
    options = {
        "limit": 30,
        "fields": {"recId": 1, "title": 1, "startDate": 1, "endDate": 1, "nextDate": 1, "description": 1, "categories": 1},
        "sort": {"nextDate": 1, "rank": 1, "title_sort": 1}
    }
    
    encoded_filter = urllib.parse.quote(json.dumps(base_filter, separators=(',', ':')))
    encoded_options = urllib.parse.quote(json.dumps(options, separators=(',', ':')))
    
    url = f"https://www.meetboston.com/event/rss/?filter={encoded_filter}&options={encoded_options}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    events_by_day = {"Friday": [], "Saturday": [], "Sunday": []}
    
    try:
        print(f"Fetching RSS feed for weekend of {friday}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        for item in root.findall('./channel/item'):
            title_node = item.find('title')
            desc_node = item.find('description')
            pub_date_node = item.find('pubDate')
            
            title = html.unescape(title_node.text).strip() if title_node is not None else ''
            description_raw = desc_node.text if desc_node is not None else ''
            pub_date_raw = pub_date_node.text if pub_date_node is not None else ''
            
            # 1. Parse the actual multi-day span from the description text
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+to\s+(\d{2}/\d{2}/\d{4})', description_raw)
            active_days = []
            
            if date_match:
                start_date = datetime.datetime.strptime(date_match.group(1), "%m/%d/%Y").date()
                end_date = datetime.datetime.strptime(date_match.group(2), "%m/%d/%Y").date()
                
                # If a festival runs Friday through Sunday, it will now appear on all 3 days
                if start_date <= friday <= end_date: active_days.append("Friday")
                if start_date <= saturday <= end_date: active_days.append("Saturday")
                if start_date <= sunday <= end_date: active_days.append("Sunday")
            else:
                # Fallback to pubDate if the description parsing fails
                if "Fri" in pub_date_raw: active_days.append("Friday")
                elif "Sat" in pub_date_raw: active_days.append("Saturday")
                elif "Sun" in pub_date_raw: active_days.append("Sunday")
            
            if not active_days:
                continue
                
            # 2. Extract clean text description
            clean_desc = ""
            p_match = re.search(r'<p.*?>(.*?)</p>', description_raw, re.IGNORECASE | re.DOTALL)
            if p_match:
                raw_text = re.sub(r'<[^>]+>', ' ', p_match.group(1))
                clean_desc = html.unescape(raw_text).strip()
                clean_desc = re.sub(r'\s+', ' ', clean_desc)
            
            if len(clean_desc) > 100:
                clean_desc = clean_desc[:100] + '...'
            elif not clean_desc:
                clean_desc = "See event page for details."
                
            display_str = f"<span style='font-weight:600;'>{title}</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>{clean_desc}</span>"
            
            for day in active_days:
                events_by_day[day].append(display_str)
                
    except Exception as e:
        err = f"<span style='color:#ff8a75;'>System Error</span>  |  <span style='font-weight:600;'>RSS Failed</span>  |  <span style='opacity:0.8; font-size: 21px;'>{str(e)[:60]}</span>"
        events_by_day = {"Friday": [err], "Saturday": [err], "Sunday": [err]}

    # Fill in blank states
    for day in ["Friday", "Saturday", "Sunday"]:
        if not events_by_day[day]:
            events_by_day[day] = [f"<span style='font-weight:600;'>No matching events found</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>No events scheduled for this day.</span>"]
            
    with open('events.json', 'w') as f:
        json.dump(events_by_day, f)

if __name__ == '__main__':
    update_events()
