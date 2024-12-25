# Twitter Trending Topics Scraper

## Overview
This project is a Python-based web scraper that logs into Twitter, fetches the top trending hashtags from the "What's Happening" section, and stores the results in a MongoDB database along with metadata such as the time of scraping and a unique identifier. It uses Selenium for browser automation and a rotating proxy service to ensure stable operation. The scraper is triggered via a simple Flask web interface that also displays the results.
---

## Features
- Logs into Twitter with credentials.
- Scrapes the top 5 trending topics from the "What's Happening" section on the homepage.
- Uses a rotating proxy for reliable access.
- Stores scraped data in a MongoDB database, including:
  - Top 5 trending topics
  - Timestamp of the scraping
  - Proxy IP address used
  - Unique identifier for the run.
- Simple Flask web interface to trigger the scraper and display results.
---

## Prerequisites
1. Python 3.7+
2. Google Chrome installed.
3. ChromeDriver (compatible with your Chrome version).
4. MongoDB cluster (connection details).
5. ProxyMesh account for rotating proxies.
6. Twitter credentials (username, email, password).
---

## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file and configure the following environment variables:
   ```python
   MONGOUSER=your_mongo_username
   MONGOPASS=your_mongo_password
   MONGOAPPNAME=your_mongo_appname  # Optional
   PROXYMESH_HOSTNAME=your_proxymesh_host
   PROXYMESH_PORT=your_proxymesh_port
   PROXYMESH_USERNAME=your_proxymesh_username
   PROXYMESH_PASSWORD=your_proxymesh_password
   DRIVER_PATH=path_to_chromedriver
   TWITTER_USER=your_twitter_username
   TWITTER_PASS=your_twitter_password
   TWITTER_USER_MAIL=your_twitter_email
   ```
---

## How to Use

1. Start the Flask server:
   ```bash
   python script.py
   ```

2. Open browser and navigate to: http://127.0.0.1:5000/

3. Click the "Run Script" link to trigger the scraper.

4. View the scraped data on the results page, including:
   - Top trending topics
   - Timestamp
   - Proxy IP used
   - JSON extract of the stored data.
---

## File Structure
```
.
├── script.py             # Main script for scraping and Flask server
├── templates/
│   ├── index.html        # Homepage for the web interface
│   ├── result.html       # Page to display results
├── .env                  # Environment variables (ignored in version control)
└── requirements.txt      # Python dependencies
```

---
## Example Output

### Twitter Trending Topics
These are the most happening topics as on 2024-12-26T02:54:19.703964:

- Manti Te
- H-1B
- Nate Burleson
- Kay Adams

The IP address used for this query was 45.32.72.75.

#### JSON Extract:
```json
{
    "_id": "676c6d36a1082d0da0692007",
    "datetime": "2024-12-26T02:08:14.625164",
    "ip_address": "45.77.125.219",
    "trend1": "Rudy Gobert",
    "trend2": "Mariah Carey",
    "trend3": "Cam Sutton",
    "trend4": "Kay Adams",
    "trend5": null,
    "unique_id": "c21adf60-6c1f-492f-8ffc-1b474ae54c3a"
}

```

Click here to run the query again

## Note:
- The `trend5` field may be `null` if there are fewer than 5 trending topics shown on the whats happening section on the twitter homepage.
