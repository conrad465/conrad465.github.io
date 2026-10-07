import json
import re
import datetime
import urllib.parse
import html
import requests
import xml.etree.ElementTree as ET

def update_events():
    today = datetime.date.today()
    
    # Target the upcoming Friday to Monday morning
    days_to_friday = 4 - today.weekday() # 4 is Friday
    if days_to_friday < 0:
        days_to_friday += 7
    
    friday = today + datetime.timedelta(days=days_to_friday)
    monday = friday + datetime.timedelta(days=3)
    
    # Format dates exactly as the API expects
    gte_date = f"{friday.strftime('%Y-%m-%d')}T04:00:00.000Z"
    lte_date = f"{monday.strftime('%Y-%m-%d')}T03:59:59.000Z"
    
    # Reconstruct the Meet Boston JSON filter dynamically
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
    
    # Safely URL-encode the JSON payloads
    encoded_filter = urllib.parse.quote(json.dumps(base_filter, separators=(',', ':')))
    encoded_options = urllib.parse.quote(json.dumps(options, separators=(',', ':')))
    
    url = f"https://www.meetboston.com/event/rss/?filter={encoded_filter}&options={encoded_options}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    events_by_day = {"Friday": [], "Saturday": [], "Sunday": []}
    
    try:
        print("Fetching RSS feed...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        
        # Loop through all events in the RSS channel
        for item in root.findall('./channel/item'):
            title_node = item.find('title')
            pub_date_node = item.find('pubDate')
            desc_node = item.find('description')
            
            title = html.unescape(title_node.text).strip() if title_node is not None else ''
            pub_date_raw = pub_date_node.text if pub_date_node is not None else ''
            description_raw = desc_node.text if desc_node is not None else ''
            
            # Use the RSS pubDate to bucket into Friday/Saturday/Sunday
            current_day = "Saturday" # Default fallback
            if pub_date_raw.startswith("Fri"): current_day = "Friday"
            elif pub_date_raw.startswith("Sat"): current_day = "Saturday"
            elif pub_date_raw.startswith("Sun"): current_day = "Sunday"
            elif pub_date_raw.startswith("Thu") or pub_date_raw.startswith("Wed"): continue # Skip weekday stragglers
            
            # The description contains HTML (CDDATA). Extract only the text inside the <p> tags.
            clean_desc = ""
            p_match = re.search(r'<p.*?>(.*?)</p>', description_raw, re.IGNORECASE | re.DOTALL)
            if p_match:
                # Strip out inner HTML tags (like <br> or <span>) and unescape HTML entities
                raw_text = re.sub(r'<[^>]+>', ' ', p_match.group(1))
                clean_desc = html.unescape(raw_text).strip()
                clean_desc = re.sub(r'\s+', ' ', clean_desc)
            
            if len(clean_desc) > 100:
                clean_desc = clean_desc[:100] + '...'
            elif not clean_desc:
                clean_desc = "See event page for details."
                
            display_str = f"<span style='font-weight:600;'>{title}</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>{clean_desc}</span>"
            events_by_day[current_day].append(display_str)
            
    except Exception as e:
        err = f"<span style='color:#ff8a75;'>System Error</span>  |  <span style='font-weight:600;'>RSS Failed</span>  |  <span style='opacity:0.8; font-size: 21px;'>{str(e)[:60]}</span>"
        events_by_day = {"Friday": [err], "Saturday": [err], "Sunday": [err]}

    for day in ["Friday", "Saturday", "Sunday"]:
        if not events_by_day[day]:
            events_by_day[day] = [f"<span style='font-weight:600;'>No matching events found</span>  |  Boston  |  <span style='opacity:0.8; font-size: 21px;'>No events scheduled for this day.</span>"]
            
    with open('events.json', 'w') as f:
        json.dump(events_by_day, f)

if __name__ == '__main__':
    update_events()
