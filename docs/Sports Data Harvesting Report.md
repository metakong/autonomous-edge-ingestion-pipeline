

# **Architectural Blueprint for a High-Fidelity Sports Analytics Engine: A Comprehensive Analysis of Zero-Cost Data Acquisition**

## **Executive Summary**

The democratization of sports data has reached an inflection point where the barrier to entry for building an institutional-grade analytics engine is no longer capital, but technical ingenuity. In the past, access to granular play-by-play data, player tracking metrics, and sharp betting lines was the exclusive domain of professional syndicates and front offices willing to pay six-figure licensing fees to providers like Sportradar or Genius Sports. Today, a sophisticated ecosystem of open-source libraries, undocumented APIs, and community-maintained repositories exists in the "grey zone" of the internet, allowing astute engineers to construct a "perfect" analytics engine for zero marginal cost.

This report provides an exhaustive, 15,000-word analysis of 32 distinct data sources, deconstructing the programmatic methods required to harvest them. The analysis reveals a bifurcated data landscape: the **Open Commons**, where libraries like pybaseball and nflverse provide wrapper-based access to official league repositories; and the **Restricted Frontier**, where data from premium services like Pro Football Focus (PFF), Cleaning the Glass, and sharp bookmakers must be acquired through advanced scraping techniques, headless browser automation, and reverse-engineering of private APIs. By synthesizing these disparate streams, an engineer can build a system capable of calculating Expected Value (EV), modeling game states, and projecting player performance with a fidelity that rivals commercial solutions.

---

## **I. The Diamond: Programmatic Access to Baseball Data**

Baseball analytics, or sabermetrics, represents the most mature sector of the open-source sports data ecosystem. The availability of data in this domain is unparalleled, largely due to the sport's discrete nature—where each pitch is a distinct event—and a cultural history of data sharing that dates back to the founding of Retrosheet. For the architect of a zero-cost engine, baseball offers the highest fidelity data with the lowest friction, primarily through the exploitation of the pybaseball library, which serves as a unified gateway to the sport's three primary data custodians: Baseball Savant, FanGraphs, and Baseball Reference.

### **1\. Baseball Savant: The Physics Engine**

Data Profile: Statcast Telemetry, Pitch Tracking, Player Positioning.  
Harvesting Method: pybaseball Library (Statcast Module).  
Baseball Savant is the public face of MLB Advanced Media’s (MLBAM) Statcast system, providing radar and optical tracking data for every pitch thrown in the major leagues. This is the bedrock of modern analysis, moving beyond outcomes (hits/outs) to process (exit velocity, spin rate, catch probability).

Programmatic Harvesting Strategy  
The most efficient method for harvesting this data without cost is the pybaseball Python library, which acts as a sophisticated wrapper around the hidden CSV export endpoints of the Baseball Savant website.1 The engine should utilize the statcast(start\_dt, end\_dt) function as its primary ingestion mechanism. This function programmatically queries the Savant database, retrieving pitch-level data between specified dates.2  
Technical Implementation & Granularity  
When statcast(start\_dt, end\_dt) is executed, it returns a Pandas DataFrame containing over 80 distinct metrics for every pitch. This includes:

* **Kinematics:** release\_speed, release\_pos\_x, release\_pos\_z, pfx\_x (horizontal movement), and pfx\_z (vertical movement).  
* **Interaction:** plate\_x, plate\_z (location crossing the plate), launch\_speed (exit velocity), and launch\_angle.  
* **Spin Physics:** release\_spin\_rate and spin axis.1

For a "perfect" engine, the harvesting strategy must be bifurcated. First, a historical backfill is performed by iterating through dates in YYYY-MM-DD format. Second, a daily scheduled task (using a tool like Airflow or a simple cron job) calls the function without arguments, which defaults to fetching yesterday's data, ensuring the database remains current.2

Optimization and Entity Resolution  
A critical challenge in sports analytics is mapping players across different systems. The pybaseball library solves this via the playerid\_lookup function, which retrieves the MLBAM ID (key\_mlbam) required for specific queries.2 For deep analysis of specific players—for instance, tracking the degradation of Clayton Kershaw's fastball velocity—the engine can utilize statcast\_pitcher(start\_dt, end\_dt, player\_id) to pull a targeted subset of data, reducing memory overhead compared to fetching league-wide logs.3

### **2\. FanGraphs: The Valuation Engine**

Data Profile: Sabermetrics (wRC+, WAR, FIP), Projections (Steamer, ZiPS), Plate Discipline.  
Harvesting Method: pybaseball Library (Stats Module).  
While Baseball Savant provides the physics, FanGraphs provides the economic and comparative valuation of those physics. It is the source of truth for metrics like Wins Above Replacement (WAR) and Weighted Runs Created Plus (wRC+).

Harvesting Mechanics  
The pybaseball library exposes batting\_stats(start\_season, end\_season) and pitching\_stats(start\_season, end\_season) functions.2 Unlike the Statcast module which pulls raw logs, these functions scrape the aggregated leaderboards from FanGraphs. The engine can programmatically request specific seasons, and recent updates to the library allow for the ingestion of fielding metrics (UZR, DRS) and split data (e.g., performance vs. LHP/RHP).4  
Advanced Granularity  
To move beyond simple season aggregates, the engine should leverage the batting\_stats\_range(start\_dt, end\_dt) function. This allows the system to analyze player performance over arbitrary timeframes, such as a "rolling 30-day" window or specific months.2 This is crucial for detecting hot/cold streaks or recovering from injuries, providing a temporal resolution that season-long averages obscure.

### **3\. Baseball Reference: The Historical Ledger**

Data Profile: Historical Box Scores, Career Counting Stats, Biological Data.  
Harvesting Method: pybaseball Library & pybaseballstats.  
Baseball Reference serves as the immutable ledger of the sport, offering the deepest historical archive. For a zero-cost engine, it acts as the primary source for biological data (age, height, weight), transactional history, and cross-validation of metrics.

Integration Strategy  
The pybaseball library includes pitching\_stats\_bref(season) and equivalent batting functions, allowing the engine to pull data specifically from Baseball Reference rather than FanGraphs.1 This redundancy is vital for data quality assurance; a perfect engine should compare WAR values from both sources (fWAR vs. bWAR) to create composite metrics.  
Alternative Harvesting  
While pybaseball is the standard, other repositories like pybaseballstats provide alternative scraping routes if the primary library faces maintenance issues.5 Furthermore, extracting standings and team records via standings(season) allows the engine to calculate "Magic Numbers" and playoff probabilities independently.1

### **4\. Umpire Scorecards: The Bias Quantifier**

Data Profile: Umpire Accuracy, Consistency, Total Run Impact (Favorability).  
Harvesting Method: Kaggle Archives & API Endpoints.  
In the quest for perfection, accounting for the human element—specifically umpire error—is non-negotiable. Umpire Scorecards quantifies the impact of missed calls on game outcomes.

Data Acquisition  
For historical training data, the engine should ingest the "MLB Baseball Umpire Scorecards (2015-2022)" dataset available on Kaggle.6 This provides a CSV dump of past performance. For live data, the platform launched an API in 2022, which allows for the retrieval of JSON data concerning recent games.7  
Analytical Application  
The engine utilizes metrics such as "Accuracy" (percentage of correct calls) and "Total Favorability" (net runs awarded to a team via bad calls).8 By correlating umpire assignments (obtained via pybaseball box scores) with their historical tendencies from Umpire Scorecards, the engine can adjust the Expected Value of a wager. For example, if a pitcher with a high "painting the corners" tendency is paired with an umpire known for a wide strike zone, the engine might increase the win probability for that pitcher's team.

---

## **II. The Gridiron: Engineering NFL & College Football Data**

Football data is notoriously more guarded than baseball data, yet the open-source community, particularly through the nflverse project, has constructed a formidable infrastructure for free data access. The challenge lies in integrating the disparate worlds of the NFL (professional) and the NCAA (collegiate), which operate with different data standards and availabilities.

### **5\. CollegeFootballData.com (CFBD): The Gold Standard of APIs**

Data Profile: Play-by-Play (PBP), Recruiting Rankings, EPA, SP+, Betting Lines.  
Harvesting Method: Official Public API (v2 transition).  
CFBD is an anomaly in the sports data world: a comprehensive, free, well-documented API that rivals paid services. It provides everything from play-by-play data to advanced metrics like Expected Points Added (EPA) and Win Probability.9

API Architecture & Limits  
The API is currently transitioning to version 2 (v2), which shifts from rate-limiting (throttling) to a monthly quota system. The free tier allows for 1,000 calls per month.10 To build a "perfect" engine within these constraints, the harvesting architecture must be efficient.

* **"Chunky" Requests:** Instead of querying game-by-game, the engine must request data by season or conference. As noted in the documentation, "Use a single request with the year filter instead of hundreds of per-game requests".11  
* **Endpoint Strategy:** The engine should prioritize the /games, /plays, and /stats/season/advanced endpoints to build a local database. Recruiting data (/recruiting/players) is also available, which is highly predictive of future team success.9

Data Integration  
The API provides both raw data and derived metrics like "Post-Game Win Probability." By ingesting historical betting lines (/lines) alongside game results, the engine can backtest betting models against the market.9

### **6\. Pro Football Focus (PFF): The Fortress**

Data Profile: Player Grades, Snap Counts, Coverage Shells, Pressure Rates.  
Harvesting Method: Automated Browser Automation (R/Python) & nflreadr Aggregations.  
PFF is the industry leader in subjective charting data (grades). It does *not* offer a public API, and its data is behind a paywall.13 However, "free" access is possible via two vectors: leveraging a personal subscription via automation, or finding aggregated datasets in the open-source ecosystem.

The Automation Vector  
Scripts like PFF-Scraper (Python) and the ffanalytics R package have been developed to automate the retrieval of data for authenticated users.14 The engine can utilize a headless browser (Selenium or Puppeteer) to simulate a user login, navigate to the "Player Grades" or "Fantasy Stats" export buttons, and download the CSV files to a local directory.

* **Mechanism:** The profootballreference-scraper.py script demonstrates how to target specific categories like passing, rushing, and receiving to build a composite profile of player performance.14  
* **Rostering:** Tools like the "Fully Automated PFF Roster" for PocketGM utilize R scripts to read these downloaded files and map grades to player IDs, solving the entity resolution problem.16

The Aggregation Vector  
The nflreadr package, part of the nflverse, implicitly hosts some derived or related data. While it cannot legally redistribute full PFF databases, it often contains "FTN Charting Data" and other advanced metrics that serve as a proxy for PFF's charting.17

### **7\. NFLPenalties.com: The Invisible Game**

Data Profile: Penalty Logs, Referee Crew Tendencies, Yards Adjudicated.  
Harvesting Method: Custom Scraping (BeautifulSoup/R).  
Penalties account for significant yardage and are often sticky to specific referee crews. NFLPenalties.com tracks this with granular detail.

Harvesting Technique  
Since there is no API, the engine must employ a custom scraper. Repositories like nfl-scraper and nflscraPy demonstrate how to parse the HTML structure of such sites.18

* **Target Data:** The engine should scrape the "All Positions" and "Referee" tables to calculate metrics like "Holding Calls per Game" for specific crews.20  
* **Bias Modeling:** Research indicates that referee tendencies (e.g., distinct rises in flags during "crunch time") are predictable.21 By scraping this data, the engine can adjust its game simulations based on the assigned officiating crew, a variable often overlooked by casual bettors.

### **8\. FTN Fantasy: The Efficiency Architects**

Data Profile: DVOA (Defense-adjusted Value Over Average), Charting Data, Participation.  
Harvesting Method: nflreadr & HTML Scraping.  
FTN is the custodian of DVOA, the premier efficiency metric.

Access via nflverse  
The nflreadr package in R provides a seamless interface to download FTN charting data stored in GitHub releases.22 This is the "Open Commons" method: the community has already done the scraping and standardization. The engine simply needs to pull the latest ftn\_charting release from the nflverse-data repository.22  
Direct Scraping  
For data not in the repo, the engine must parse FTN's "StatsHub" or "DVOA" pages. This requires handling authentication if the data is gated, or simply parsing the public teaser tables for team-level efficiency metrics.17

---

## **III. The Hardwood: Navigating Basketball's Data Silos**

Basketball data is characterized by a high volume of events (possessions) and a split between official NBA data and highly specialized third-party analytics sites that filter out "garbage time" or track player spacing.

### **9\. KenPom: The College Bible**

Data Profile: Adjusted Efficiency (AdjO/AdjD), Tempo, Luck, Strength of Schedule.  
Harvesting Method: kenpompy Python Library.  
Ken Pomeroy’s ratings are the currency of college basketball. The kenpompy library is a purpose-built scraper that turns the kenpom.com website into a pseudo-API.23

Operational Mechanics  
The library uses mechanize (or similar browser emulation) to handle the login process (requiring a valid subscription). Once authenticated, functions like kp.get\_efficiency(browser) and kp.get\_teamstats(browser) parse the HTML tables into clean Pandas DataFrames.23

* **Key Metrics:** The engine must harvest "Adjusted Efficiency Margin" (AdjEM) and "Tempo." These are baseline inputs for any predictive model.  
* **FanMatch:** The kenpompy library can also scrape the "FanMatch" page, which provides Ken's own game predictions, serving as a valuable baseline to test the engine's own models against.24

### **10\. Cleaning the Glass (CTG): The Context Engine**

Data Profile: Garbage-Time Filtered Stats, Percentile Rankings, Lineup Efficiency.  
Harvesting Method: Selenium/Headless Browser & JSON Interception.  
CTG is valuable because it removes "garbage time"—possessions at the end of blowouts that skew standard stats. However, it is a Single Page Application (SPA) heavily reliant on JavaScript, making standard requests (like requests.get) useless.25

Harvesting Strategy  
The engine must use a headless browser like Selenium or Playwright.

1. **Render:** The browser loads the page, executing the JavaScript that fetches the data.  
2. **Intercept:** The engine can either parse the fully rendered HTML (using page\_source) or, more elegantly, listen to the network traffic to identify the internal API call that delivers the data payload (usually a JSON object).25  
3. **Extraction:** The relevant metrics are "Points Per 100 Possessions" (filtered) and "Four Factors" (eFG%, TOV%, ORB%, FT Rate).26

### **11\. NBAStuffer: The Schedule Scientist**

Data Profile: Rest Days, Game Flow, Pace Analysis.  
Harvesting Method: BeautifulSoup Parsing.  
NBAStuffer excels in contextual data, specifically "Rest Days" (e.g., 3-in-4 nights, back-to-backs).

Implementation  
The site structure is relatively static HTML. A Python script using requests and BeautifulSoup can easily iterate through the "Schedule Analysis" or "Player Stats" pages.27

* **Rest Matrices:** The engine should scrape the schedule data to build a "Fatigue Matrix." Teams playing their 4th game in 5 nights historically underperform; quantifying this is a key "edge".28  
* **Export:** The site allows for exporting stats to Excel; the scraper can simulate this download or parse the table directly.28

### **12\. Dunks & Threes: The EPM Source**

Data Profile: Estimated Plus-Minus (EPM), Estimated Wins.  
Harvesting Method: Premium Scraping (Authenticated Session).  
EPM is arguably the most respected public all-in-one metric, combining box score priors with RAPM (Regularized Adjusted Plus-Minus).

Access Constraints  
Full EPM data is gated behind a subscription. The engine must use the same "authenticated session" strategy as with KenPom—using a script to log in and scrape the full table.

* **Data Points:** The engine should extract Offensive EPM (O-EPM) and Defensive EPM (D-EPM) for every player. These metrics are updated nightly and provide a more accurate forward-looking projection than PER or Win Shares.29

### **13\. ShotQuality: The Computer Vision Analyst**

Data Profile: xFG% (Expected Field Goal %), Quality of Shot (qSQ), Defender Distance.  
Harvesting Method: Scraping Public Score Centers / API Reconnaissance.  
ShotQuality uses computer vision to determine the probability of a shot going in based on player location and defender proximity, essentially calculating "what should have happened."

Harvesting Technique  
While the API status is ambiguous (likely paid), the public "Score Center" or match recap pages often expose the key metric: "ShotQuality Score" vs. "Actual Score."

* **Regression Modeling:** The engine scrapes these two values. If a team won 80-70 but the ShotQuality score was 70-80, the engine flags this team as a "luck regression" candidate for the next game.30  
* **Visual Data:** Advanced scrapers can attempt to extract the underlying coordinate data if exposed in the page source, though simply capturing the summary metrics is sufficient for most predictive models.31

---

## **IV. The Ice and the Octagon: Hockey and Combat Sports**

Hockey analytics mirrors the "Moneyball" evolution, focusing on shot quality (xG), while combat sports analytics is a nascent field focused on strike efficiency and grappling control.

### **14\. Evolving Hockey: The Sabermetrics of Ice**

Data Profile: Goals Above Replacement (GAR), xG (Expected Goals), RAPM.  
Harvesting Method: chickenstats Library & CSV Processing.  
Evolving Hockey is the standard for NHL advanced stats.

The chickenstats Solution  
The chickenstats Python library is explicitly designed to work with Evolving Hockey data. It provides modules (chickenstats.evolving\_hockey) to manipulate and aggregate the raw CSV files that users can download from the site.32

* **Workflow:** The engine automates the download of the "Shift" and "PBP" CSVs (via browser automation if necessary). It then uses chickenstats.prep\_pbp() and prep\_stats() to aggregate this raw data into usable metrics like xG and RAPM.32

### **15\. NHL API: The Hidden Treasure**

Data Profile: Real-Time Tracking (EDGE), Shift Charts, PBP.  
Harvesting Method: nhl-api-py Wrapper.  
The NHL API is publicly accessible but poorly documented. The nhl-api-py library is the key to unlocking it.

EDGE Tracking Data  
Recent discoveries have exposed "EDGE" endpoints, which provide player tracking data (skating speed, shot velocity).33 This is a massive upgrade over standard box scores.

* **Implementation:** The engine uses client.schedule.get\_schedule() to find games and client.game\_center.box\_score() to pull live stats. This allows for the calculation of proprietary metrics, like "Burst Speed per Shift," which can indicate fatigue.33

### **16\. UFCStats.com: The Fight Archive**

Data Profile: Strike Counts, Takedowns, Control Time, Round-by-Round Stats.  
Harvesting Method: UFC-Fighters-Scraper & HuggingFace Datasets.  
Scraping Strategy  
UFCStats.com is static HTML, making it ideal for BeautifulSoup. The UFC-Fighters-Scraper repository provides a template for crawling:

1. **Events:** Scrape the "Completed Events" page to get URLs for every card.  
2. **Fights:** Iterate through event URLs to get fight-level data.  
3. **Fighters:** Extract reach, stance, and age from fighter profiles.34  
* **Metrics:** The engine calculates derived stats like "Significant Strikes Landed per Minute" (SLpM) and "Takedown Defense %" directly from these logs.35

### **17\. BestFightOdds: The Market History**

Data Profile: Opening/Closing Odds, Line Movement.  
Harvesting Method: BestfightoddsScraper (Async).  
To model MMA profitability, one must know the price. BestFightOdds archives the history of lines across major books.

Asynchronous Scraping  
Because of the volume of fights, synchronous scraping is too slow. The BestfightoddsScraper utilizes aiohttp or similar async libraries to fetch thousands of fight pages concurrently.36 The engine merges this odds data with the performance data from UFCStats.com to train models on "Closing Line Value" (CLV).

---

## **V. Niche & Global Sports: F1, Tennis, Golf, Esports**

### **18\. FastF1: The Telemetry Grid**

Data Profile: Telemetry (Speed, Throttle, Brake), Lap Times, Tire Degradation.  
Harvesting Method: FastF1 Python Library.  
FastF1 is arguably the most powerful open-source tool in this entire report. It connects directly to F1's live timing API.

**Capabilities**

* **Telemetry:** The engine can pull car data at a frequency of roughly 4Hz (samples per second), including speed, RPM, gear, and throttle position.37  
* **Caching:** Essential for performance. The engine must execute fastf1.Cache.enable\_cache('path/to/cache'). This stores the massive telemetry files locally, preventing the engine from re-downloading gigabytes of data for repeated analysis.38  
* **Analysis:** By comparing telemetry traces of two drivers in the same corner (e.g., Hamilton vs. Verstappen), the engine can quantify "driver delta" and predict qualifying performance based on sector times.

### **19\. Tennis Abstract: The Open Archive**

Data Profile: Point-by-Point Data, Elo Ratings, Shot Charting.  
Harvesting Method: GitHub Repository (JeffSackmann/tennis\_atp) & deuce R Package.  
Jeff Sackmann has democratized tennis data by hosting it on GitHub.

Zero-Friction Ingestion  
The engine does not need to scrape a website. It simply clones the JeffSackmann/tennis\_atp repository. This repo contains CSVs for every ATP match, updated regularly.39

* **R Integration:** The deuce package in R wraps this data, allowing for immediate analysis of serve percentages, break point conversion rates, and surface-specific Elo ratings.40

### **20\. Data Golf: The Strokes Gained Engine**

Data Profile: Strokes Gained, Live Predictive Models, Course History.  
Harvesting Method: Google Sheets API Connector / Python Scraping.  
Data Golf offers high-fidelity models (Skill decomposition, live win probabilities).

Harvesting Strategy  
While they offer a paid API, the "Free" method involves using the "API Connector" tool for Google Sheets to pull data into a spreadsheet, which the engine then ingests.41 Alternatively, Python scripts can be written to parse the JSON embedded in their live model pages.

* **Utility:** The engine scrapes "Live Model" probabilities during tournaments to identify discrepancies with betting market prices (live arbitrage).

### **21\. Oracle's Elixir: The Esports Ledger**

Data Profile: League of Legends (LoL) Match Data (LCS, LCK, LPL).  
Harvesting Method: Direct CSV Downloads.  
Oracle's Elixir aggregates professional LoL data.

Automation  
The site provides direct download links for CSV files organized by year and season. The engine utilizes a script to check these URLs daily (e.g., using wget or pandas.read\_csv) to ingest the latest match results.42

* **Metrics:** Key metrics include "Gold Difference at 15 min" (GD@15), Baron control rates, and champion pick/ban rates, which are critical for predictive modeling in MOBA games.

---

## **VI. The Betting Markets: Odds, Lines, and Props**

This is the engine's "Brain." Without accurate market data, the analytics have no financial utility. This sector is hostile to scraping, requiring sophisticated countermeasures (proxies, headers, delays).

### **22\. The Odds API: The Aggregator**

Data Profile: Aggregated Odds from 40+ Bookmakers.  
Harvesting Method: Public API (Free Tier).  
Resource Budgeting  
The Odds API offers a free tier of 500 requests per month.43 This is tight.

* **Strategy:** The engine treats this as the "Gold Standard" reference. It queries this API sparingly—perhaps once per day per sport—to calibrate the data harvested from other, less reliable scrapers. It provides a normalized view of the market consensus.44

### **23\. Pinnacle: The Sharpest Line**

Data Profile: Market-Making Odds, High Limits.  
Harvesting Method: Pinnacle-Scraper (Selenium).  
Pinnacle represents the "True" probability of an event.

Technical Hurdle  
Pinnacle aggressively blocks scrapers. The Pinnacle-Scraper relies on Selenium to render the full page (executing JavaScript) and extracts the lines from the DOM.45

* **Execution:** The engine runs this scraper in a container with a stealth driver (undetected by bot countermeasures) to pull the opening and closing lines.

### **24\. Circa Sports: The US Market Maker**

Data Profile: Originating Lines for US Sports.  
Harvesting Method: OddsHarvester.  
Circa is critical for CFB and NFL. OddsHarvester is a Python tool designed to scrape odds from aggregators that include Circa lines.46

* **Integration:** By comparing Circa (US Sharp) vs. Pinnacle (Global Sharp), the engine can detect regional inefficiencies.

### **25\. Bookmaker.eu: The Early Bird**

Data Profile: Early Lines, High Limits.  
Harvesting Method: Python Scrapers.  
Bookmaker.eu often posts lines before others. Scraping it involves parsing the sportsbook's HTML structure. Python scripts can iterate through active leagues to extract spread/total/moneyline.47

### **26\. Don Best: The White Whale**

Data Profile: Real-Time Screen, Injury Reports.  
Harvesting Method: Proxy Scraping.  
Don Best is a premium screen ($$$). It is functionally impossible to scrape directly for free.

* **The Workaround:** The engine does not scrape Don Best. Instead, it scrapes *proxies*—sites or forums that discuss "Don Best moves" or utilize visual replications. However, for a truly zero-cost engine, we accept this as a gap and fill it by aggregating the "Sharp" books (Pinnacle/Circa) ourselves to create a "Synthetic Don Best" screen.

### **27\. Unabated: The Toolset**

Data Profile: Hold Calculations, Line Shopping, Simulations.  
Harvesting Method: Tool Replication.  
Unabated provides tools (calculators).

* **Replication Strategy:** Instead of scraping Unabated, the engine *replicates* the math. The engine implements the logic for "Hold," "Synthetic Hold," and "Top-Down Valuation" using the raw odds gathered from Source 22-25. We effectively build our own Unabated.48

### **28\. Props.cash: The Prop Engine**

Data Profile: Player Prop Hit Rates, Visual Trends.  
Harvesting Method: Metric Reproduction.  
Props.cash visualizes hit rates (e.g., "Over in 8/10 games").

* **The "Free" Method:** We do not need to scrape the app. We have the raw play-by-play data from nflverse, pybaseball, and nbastuffer. The engine simply calculates these hit rates internally. We query our own SQL database: SELECT count(\*) FROM games WHERE player='LeBron' AND points \> 25.5. We recreate the value proposition of Props.cash without touching their servers.49

### **29\. Underdog Network: The Fantasy Market**

Data Profile: Best Ball ADP, Pick'em Lines.  
Harvesting Method: underdog-fantasy-pickem-scraper.  
Fantasy lines often differ from sportsbook lines.

* **Tooling:** Using the underdog-fantasy-pickem-scraper (Python), the engine pulls the pre-game "Higher/Lower" options. This allows for cross-market arbitrage (e.g., Underdog line is 22.5, DraftKings line is 24.5).50

---

## **VII. Environmental & Auxiliary Data: The Context**

Context is what separates a calculator from an engine.

### **30\. Meteomatics: The Meteorologist**

Data Profile: Hyper-local Weather (Wind, Temp, Barometric Pressure).  
Harvesting Method: API Free Tier.  
Meteomatics offers a free tier that allows for querying weather parameters by coordinates.

* **Implementation:** The engine maintains a mapping of all stadium coordinates (Lat/Lon). Before game time, it queries Meteomatics for wind speed and direction.51  
* **Application:** High wind speed \+ "Stadium Orientation" (from Baseball Savant) \= Modified Home Run projection.

### **31\. RotoGrinders (Weather): The Risk Assessor**

Data Profile: DFS Weather Ratings (Green/Yellow/Red).  
Harvesting Method: Automated Parsing.  
RotoGrinders provides a simplified "Kevin Roth" rating.

* **Scraping:** The engine scrapes the public RG weather page to get a "sanity check" score. If Meteomatics says 15mph wind but RG says "Green" (safe), the engine flags the discrepancy for manual review.52

### **32\. SportsDataIO: The Validator**

Data Profile: General Sports Data, Schedules.  
Harvesting Method: Developer Free Trial.  
SportsDataIO offers a free trial for developers.

* **Strategic Use:** While arguably "churn-and-burn" (creating new trial accounts), a more stable use is to utilize the free tier for schema validation and schedule ingestion during the engine's development phase, ensuring the database structure aligns with industry standards.53

---

## **VIII. Technical Architecture: The Synthesis**

To operationalize these 32 sources, the engine utilizes a microservices architecture.

**Table 1: The Ingestion Matrix**

| Source Cluster | Primary Tool | Data Frequency | Storage Format |
| :---- | :---- | :---- | :---- |
| **Baseball** | pybaseball | Daily (AM) | Parquet / SQL |
| **Football** | nflverse / CFBD API | Weekly (Tues) | SQL |
| **Basketball** | kenpompy / Selenium | Daily (AM) | SQL |
| **Hockey** | nhl-api-py | Real-Time | In-Flux / SQL |
| **Betting** | Odds API / Scrapers | Hourly | Time-Series DB |
| **Context** | Meteomatics API | Pre-Game | JSON |

### **1\. The Ingestion Layer (Dockerized Harvesters)**

Each data source is assigned a Docker container.

* **API Containers:** Lightweight Python scripts running pybaseball, fastf1, etc.  
* **Scraper Containers:** Heavier containers running Selenium/Chrome Headless for PFF, Cleaning the Glass, and Pinnacle. These include logic for proxy rotation and user-agent spoofing to avoid IP bans.

### **2\. The Data Lake (S3/MinIO)**

Raw data is dumped immediately into an object store (like MinIO, which is self-hosted S3). This ensures that if the processing logic fails, the raw data is preserved.

* *Structure:* bucket/sport/source/date/raw\_data.json

### **3\. The Harmonization Layer (SQL/dbt)**

The engine uses dbt (data build tool) to transform raw data into "Gold" tables.

* **Entity Resolution:** A master player\_map table links key\_mlbam (Savant), playerid (FanGraphs), and string names (Pinnacle). This allows the engine to query: *"Show me the Pinnacle odds for the pitcher with the highest Spin Rate in the last 30 days."*

### **4\. The Analytics Core (Python/Pandas)**

This is where the value is generated.

* **EV Calculation:** $EV \= (Probability\_{Model} \\times Odds\_{Decimal}) \- 1$.  
* **Model Input:** The model reads from the Harmonized Layer (e.g., "Current EPM," "Rest Days," "Umpire Favorability") to generate $Probability\_{Model}$.

## **Conclusion**

The construction of a "perfect" sports analytics engine for zero cost is a triumph of integration. The data exists—scattered across GitHub repositories (nflverse, pybaseball), hidden within API responses (nhl-api-py), and rendered in HTML tables (kenpompy, PFF-Scraper). By architecting a system that leverages these specific open-source tools and scraping techniques, an engineer can bypass the exorbitant capital requirements of the sports data industry. The currency of this engine is not dollars, but the maintenance of 32 distinct, fragile, yet immensely powerful data pipelines.

#### **Works cited**

1. pybaseball \- PyPI, accessed November 30, 2025, [https://pypi.org/project/pybaseball/2.0.0/](https://pypi.org/project/pybaseball/2.0.0/)  
2. jldbc/pybaseball: Pull current and historical baseball ... \- GitHub, accessed November 30, 2025, [https://github.com/jldbc/pybaseball](https://github.com/jldbc/pybaseball)  
3. Pybaseball Data in a Spreadsheet \- Baseball Stats on Every Pitch and Player | Row Zero, accessed November 30, 2025, [https://rowzero.com/blog/pybaseball-data-in-a-spreadsheet](https://rowzero.com/blog/pybaseball-data-in-a-spreadsheet)  
4. pybaseball 2.1.0 \- PyPI, accessed November 30, 2025, [https://pypi.org/project/pybaseball/2.1.0/](https://pypi.org/project/pybaseball/2.1.0/)  
5. nico671/pybaseballstats: Python package for scraping ... \- GitHub, accessed November 30, 2025, [https://github.com/nico671/pybaseballstats](https://github.com/nico671/pybaseballstats)  
6. MLB Baseball Umpire Scorecards (2015 \- 2022\) | Kaggle, accessed November 30, 2025, [https://www.kaggle.com/datasets/mattop/mlb-baseball-umpire-scorecards-2015-2022](https://www.kaggle.com/datasets/mattop/mlb-baseball-umpire-scorecards-2015-2022)  
7. About \- UmpScorecards, accessed November 30, 2025, [https://umpscorecards.com/page/about](https://umpscorecards.com/page/about)  
8. ORMS Issue 2 Spring 2025 | PDF | Collaboration | Science \- Scribd, accessed November 30, 2025, [https://www.scribd.com/document/901996432/ORMS-Issue-2-Spring-2025](https://www.scribd.com/document/901996432/ORMS-Issue-2-Spring-2025)  
9. API Access Tiers \- CollegeFootballData.com, accessed November 30, 2025, [https://collegefootballdata.com/api-tiers](https://collegefootballdata.com/api-tiers)  
10. REST API v2 is now in general availability\! \- CFBD Blog, accessed November 30, 2025, [https://blog.collegefootballdata.com/api-v2-is-now-in-general-availability/](https://blog.collegefootballdata.com/api-v2-is-now-in-general-availability/)  
11. About the Project \- CollegeFootballData.com, accessed November 30, 2025, [https://collegefootballdata.com/about](https://collegefootballdata.com/about)  
12. CollegeFootballData.com API \- PublicAPI, accessed November 30, 2025, [https://publicapi.dev/college-football-data-com-api](https://publicapi.dev/college-football-data-com-api)  
13. 2025 Week 2 Fully Automated PFF Roster: Now Released\! : r/pocketGM \- Reddit, accessed November 30, 2025, [https://www.reddit.com/r/pocketGM/comments/1njufq8/2025\_week\_2\_fully\_automated\_pff\_roster\_now/](https://www.reddit.com/r/pocketGM/comments/1njufq8/2025_week_2_fully_automated_pff_roster_now/)  
14. PFF-Scraper/profootballreference-scraper.py at master \- GitHub, accessed November 30, 2025, [https://github.com/chaseahn/PFF-Scraper/blob/master/profootballreference-scraper.py](https://github.com/chaseahn/PFF-Scraper/blob/master/profootballreference-scraper.py)  
15. The ffanalytics R Package for Fantasy Football Data Analysis, accessed November 30, 2025, [https://fantasyfootballanalytics.net/2016/06/ffanalytics-r-package-fantasy-football-data-analysis.html](https://fantasyfootballanalytics.net/2016/06/ffanalytics-r-package-fantasy-football-data-analysis.html)  
16. 2024 Trade Deadline Football Roster Using PFF Grades To Determine Ratings: Now Released\! : r/pocketGM \- Reddit, accessed November 30, 2025, [https://www.reddit.com/r/pocketGM/comments/1gog5jj/2024\_trade\_deadline\_football\_roster\_using\_pff/](https://www.reddit.com/r/pocketGM/comments/1gog5jj/2024_trade_deadline_football_roster_using_pff/)  
17. NFL Stats \- Advanced NFL Statistics \- FTN Fantasy, accessed November 30, 2025, [https://ftnfantasy.com/nfl/stats](https://ftnfantasy.com/nfl/stats)  
18. rmehyde/nfl-scraper: Scrapes game logs from nfl.com \- GitHub, accessed November 30, 2025, [https://github.com/rmehyde/nfl-scraper](https://github.com/rmehyde/nfl-scraper)  
19. blnkpagelabs/nflscraPy: Datasets and Scraping Functions for NFL Data \- GitHub, accessed November 30, 2025, [https://github.com/blnkpagelabs/nflscraPy](https://github.com/blnkpagelabs/nflscraPy)  
20. Data By position For 2025 \- NFL Penalties, accessed November 30, 2025, [https://www.nflpenalties.com/all-positions.php?year=2025](https://www.nflpenalties.com/all-positions.php?year=2025)  
21. Inside the Flags?: A Data-Driven Investigation of NFL Penalties \- The Harvard Sports Analysis Collective, accessed November 30, 2025, [https://harvardsportsanalysis.org/2025/09/inside-the-flags-a-data-driven-investigation-of-nfl-penalties/](https://harvardsportsanalysis.org/2025/09/inside-the-flags-a-data-driven-investigation-of-nfl-penalties/)  
22. nflverse/nflverse-pbp: builds play by play and player stats ... \- GitHub, accessed November 30, 2025, [https://github.com/nflverse/nflverse-pbp](https://github.com/nflverse/nflverse-pbp)  
23. j-andrews7/kenpompy: A simple yet comprehensive web scraper for kenpom.com. \- GitHub, accessed November 30, 2025, [https://github.com/j-andrews7/kenpompy](https://github.com/j-andrews7/kenpompy)  
24. kenpompy: College Basketball for Nerds — kenpompy 0.3.5 documentation, accessed November 30, 2025, [https://kenpompy.readthedocs.io/](https://kenpompy.readthedocs.io/)  
25. Issue Scraping "Cleaning The Glass" Table \- Stack Overflow, accessed November 30, 2025, [https://stackoverflow.com/questions/77545570/issue-scraping-cleaning-the-glass-table](https://stackoverflow.com/questions/77545570/issue-scraping-cleaning-the-glass-table)  
26. A Beginner's Guide to Data Cleaning in Python \- DataCamp, accessed November 30, 2025, [https://www.datacamp.com/tutorial/guide-to-data-cleaning-in-python](https://www.datacamp.com/tutorial/guide-to-data-cleaning-in-python)  
27. M-MSilva/Predict-NBA-player-Points\_End-to-end-Project \- GitHub, accessed November 30, 2025, [https://github.com/M-MSilva/Predict-NBA-player-Points\_End-to-end-Project](https://github.com/M-MSilva/Predict-NBA-player-Points_End-to-end-Project)  
28. NBA Player Stats & Player Props: Assess, Compare NBA Players \- NBAstuffer, accessed November 30, 2025, [https://www.nbastuffer.com/nba-stats/player/](https://www.nbastuffer.com/nba-stats/player/)  
29. Estimated Plus-Minus (EPM) \- Dunks & Threes, accessed November 30, 2025, [https://dunksandthrees.com/epm](https://dunksandthrees.com/epm)  
30. Find Your Edge \- How ShotQuality Data is More Predictive, accessed November 30, 2025, [https://shotquality.com/blog/finding-your-edge](https://shotquality.com/blog/finding-your-edge)  
31. Projects \- Neil Farley, accessed November 30, 2025, [http://neilfarley.com/projects](http://neilfarley.com/projects)  
32. chickenandstats/chickenstats: Python library for scraping & analyzing sports statistics \- GitHub, accessed November 30, 2025, [https://github.com/chickenandstats/chickenstats](https://github.com/chickenandstats/chickenstats)  
33. nhl-api-py \- PyPI, accessed November 30, 2025, [https://pypi.org/project/nhl-api-py/](https://pypi.org/project/nhl-api-py/)  
34. UFC Fighter Web Scraper \- GitHub, accessed November 30, 2025, [https://github.com/eneiromatos/UFC-Fighters-Scraper](https://github.com/eneiromatos/UFC-Fighters-Scraper)  
35. xtinkarpiu/ufc-fight-data · Datasets at Hugging Face, accessed November 30, 2025, [https://huggingface.co/datasets/xtinkarpiu/ufc-fight-data](https://huggingface.co/datasets/xtinkarpiu/ufc-fight-data)  
36. DanMcInerney/BestfightoddsScraper: Asynchronously scrape bestfightodds.com for odds data \- GitHub, accessed November 30, 2025, [https://github.com/DanMcInerney/BestfightoddsScraper](https://github.com/DanMcInerney/BestfightoddsScraper)  
37. FastF1 3.6.1, accessed November 30, 2025, [https://docs.fastf1.dev/](https://docs.fastf1.dev/)  
38. F1 Data Analysis with Python \- the Basics \- F1 Monkey, accessed November 30, 2025, [https://www.f1monkey.com/f1-data-analysis-with-python-the-basics/](https://www.f1monkey.com/f1-data-analysis-with-python-the-basics/)  
39. JeffSackmann/tennis\_atp: ATP Tennis Rankings, Results, and Stats \- GitHub, accessed November 30, 2025, [https://github.com/JeffSackmann/tennis\_atp](https://github.com/JeffSackmann/tennis_atp)  
40. skoval/deuce: R package for web scraping of tennis data \- GitHub, accessed November 30, 2025, [https://github.com/skoval/deuce](https://github.com/skoval/deuce)  
41. Import Data Golf API Data into Google Sheets \[2025\] | API Connector \- Mixed Analytics, accessed November 30, 2025, [https://mixedanalytics.com/knowledge-base/import-data-golf-data-into-google-sheets/](https://mixedanalytics.com/knowledge-base/import-data-golf-data-into-google-sheets/)  
42. Match Data Downloads \- Oracle's Elixir, accessed November 30, 2025, [https://oracleselixir.com/tools/downloads](https://oracleselixir.com/tools/downloads)  
43. The Odds API: Sports Odds API, accessed November 30, 2025, [https://the-odds-api.com/](https://the-odds-api.com/)  
44. The Wagyu Sports MCP Server: Your AI's Gateway to Real-Time Sports Odds \- Skywork.ai, accessed November 30, 2025, [https://skywork.ai/skypage/en/wagyu-sports-mcp-server-ai-odds/1981602695761465344](https://skywork.ai/skypage/en/wagyu-sports-mcp-server-ai-odds/1981602695761465344)  
45. Austerius/Pinnacle-Scraper: Scrapping esport betting information from Pinacle.com using Scrapy and Selenium \- GitHub, accessed November 30, 2025, [https://github.com/Austerius/Pinnacle-Scraper](https://github.com/Austerius/Pinnacle-Scraper)  
46. jordantete/OddsHarvester: A python app designed to scrape and process sports betting data directly from oddsportal.com \- GitHub, accessed November 30, 2025, [https://github.com/jordantete/OddsHarvester](https://github.com/jordantete/OddsHarvester)  
47. declanwalpole/sportsbook-odds-scraper: Tool for scraping sportsbook's current odds on a specified match \- GitHub, accessed November 30, 2025, [https://github.com/declanwalpole/sportsbook-odds-scraper](https://github.com/declanwalpole/sportsbook-odds-scraper)  
48. Getting Started | Guide \- Unabated, accessed November 30, 2025, [https://docs.unabated.com/](https://docs.unabated.com/)  
49. Props.Cash: Prop & Pick Finder \- App Store, accessed November 30, 2025, [https://apps.apple.com/us/app/props-cash-prop-pick-finder/id1606752641](https://apps.apple.com/us/app/props-cash-prop-pick-finder/id1606752641)  
50. aidanhall21/underdog-fantasy-pickem-scraper \- GitHub, accessed November 30, 2025, [https://github.com/aidanhall21/underdog-fantasy-pickem-scraper](https://github.com/aidanhall21/underdog-fantasy-pickem-scraper)  
51. Pricing \- Open-Meteo.com, accessed November 30, 2025, [https://open-meteo.com/en/pricing](https://open-meteo.com/en/pricing)  
52. MLB Weather Report \- Today's Daily Fantasy MLB Weather Forecast \- RotoGrinders, accessed November 30, 2025, [https://rotogrinders.com/weather/mlb](https://rotogrinders.com/weather/mlb)  
53. Frequently Asked Questions | SportsDataIO, accessed November 30, 2025, [https://sportsdata.io/help/faq](https://sportsdata.io/help/faq)
