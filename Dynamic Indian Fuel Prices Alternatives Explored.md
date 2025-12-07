# **Architectural Strategies for Real-Time Fuel Price Acquisition in India: Beyond Static Lookups**

## **Executive Summary**

The digitization of utility services in India has created a compelling demand for real-time data access, yet the specific vertical of retail fuel pricing remains fragmented and technically opaque. Since the Government of India's strategic shift to a daily dynamic pricing model in June 2017, the retail selling price (RSP) of petrol and diesel has become a highly volatile variable, fluctuating daily at 06:00 AM IST in response to global crude benchmarks and currency exchange rates. This transition rendered traditional static data models obsolete, creating a significant engineering challenge for developers seeking to integrate fuel cost estimation into logistics, travel, or expense management applications without incurring the high operational costs of commercial APIs.

This report provides an exhaustive technical analysis of the fuel data landscape in India. It critically evaluates the proposed "static client-side lookup" architecture, identifying fundamental flaws related to data staleness and geospatial mismatch. In response to the query for "better ways," the report proposes and details the implementation of a **Git Scraping** architecture. This serverless, zero-cost pattern leverages the infrastructure of version control systems to perform Extract-Transform-Load (ETL) operations, effectively treating a GitHub repository as a self-updating, high-availability database. By synthesizing data from unofficial aggregators like GoodReturns and MyPetrolPrice, developers can construct a robust, maintenance-free pricing engine that rivals paid commercial services in accuracy and reliability.

## **1\. Introduction**

In the contemporary digital ecosystem, the expectation for real-time data is ubiquitous. Whether for a logistics fleet manager calculating the marginal cost of a delivery route or a consumer estimating the expense of a weekend road trip, the accuracy of input data—specifically fuel costs—is paramount. In the Indian context, this data point has evolved from a regulated, static value to a dynamic, market-linked variable. This evolution presents a unique set of challenges for application developers who must balance data accuracy with acquisition costs.

### **1.1 The User's Dilemma: Buy vs. Build in a Volatile Market**

The central problem articulated involves a trade-off between cost and accuracy. Reliable Application Programming Interfaces (APIs) that provide daily fuel prices, such as those offered by Zyla Labs or APIClub, operate on commercial models that can be prohibitively expensive for free or early-stage applications.2 Conversely, the user's proposed alternative—a "static client-side lookup"—attempts to circumvent these costs but introduces severe risks regarding data validity. The query explicitly seeks a middle ground: a system that offers the dynamic freshness of an API with the cost structure of a static file.

### **1.2 The Failure of Open Government Data**

A primary friction point in this domain is the absence of a standardized, machine-readable Open Government Data (OGD) endpoint. While the Ministry of Petroleum and Natural Gas and the Petroleum Planning and Analysis Cell (PPAC) publish extensive macro-economic data, including crude basket prices and import volumes 4, they do not offer a public REST API for daily retail prices at the city level. The official channels provided by Oil Marketing Companies (OMCs) like Indian Oil Corporation (IOCL) rely on legacy interaction models, such as SMS-based queries or Captcha-protected web portals, which are hostile to automated consumption.6 This vacuum has necessitated the rise of third-party aggregators and scraping-based solutions.

### **1.3 Scope of the Report**

This document aims to serve as a definitive architectural guide for solving this specific data acquisition problem. We will dissect the pricing mechanism to understand the data's "heartbeat," critique the limitations of reverse geocoding, and then construct a detailed blueprint for a scraping-based solution. Special emphasis will be placed on "Git Scraping"—a technique that utilizes Continuous Integration (CI) workflows to automate data harvesting—as the optimal solution for the user's requirements.

## **2\. The Indian Fuel Pricing Mechanism: A Data Engineering Perspective**

To design an effective data pipeline, one must first understand the behavior, frequency, and granularity of the data source. The pricing of petrol and diesel in India is not merely a number; it is a complex derivative of global economics and local taxation, governed by strict temporal and spatial rules.

### **2.1 Historical Context and the Shift to Dynamic Pricing**

Prior to June 16, 2017, fuel prices in India were revised on the 1st and 16th of every month. This fortnightly cycle allowed application developers to cache price data for up to two weeks, making static lookups a viable strategy. The transition to **Daily Dynamic Pricing** fundamentally broke this model. The objective was to pass the benefit of even the smallest reduction in international crude oil prices to dealers and consumers, and to insulate OMCs from sharp volatility.

For a data architect, this shift implies that the "Time-to-Live" (TTL) of any fuel price data point is exactly 24 hours. A price fetched at 05:59 AM is historically interesting but operationally useless at 06:01 AM. This necessitates a system that is synchronized with the OMCs' update cycle.

### **2.2 The Anatomy of a Fuel Price**

The retail price paid by the consumer is the sum of several components, each contributing to the geographic variance of the data. Understanding this buildup is crucial for designing the database schema and normalization logic.

| Component | Description | Impact on Data |
| :---- | :---- | :---- |
| **Base Price** | Cost of crude \+ refining charges. | Uniform across India (mostly). |
| **Freight Charges** | Cost to transport fuel from refinery to depot. | Causes variation between districts. |
| **Excise Duty** | Central government tax. | Uniform across India. |
| **Dealer Commission** | Payment to the petrol pump owner. | Marginal variation. |
| **VAT / Sales Tax** | State-level tax (Ad Valorem \+ specific). | **Major variation between states.** |

This structure creates significant price disparities. For instance, data from December 2025 indicates that petrol in **Andhra Pradesh** trades at approximately ₹109.63 per liter, whereas in **Delhi** it is ₹94.77, and in the **Andaman & Nicobar Islands** it is as low as ₹82.46.7 Even within a state, prices vary by district due to transportation costs. For example, in Maharashtra, the price in **Mumbai** (₹103.50) differs from **Pune** (₹104.19) and **Amravati** (₹104.55).7

**Implication for Reverse Geocoding:** The variation is not just state-level but district-level. A user in the outskirts of a metro city might fall into a different pricing zone than the city center. A robust system must resolve location to the specific "pricing city," not just the state.

### **2.3 The 06:00 AM Synchronization Challenge**

The synchronization of price updates is a hard constraint. OMCs push the new rates to the central servers and dealer terminals effective 06:00 AM Indian Standard Time (IST).1

* **The Aggregator Lag:** Secondary sources (Tier 2 websites like GoodReturns or MyPetrolPrice) rely on their own scraping or data entry mechanisms. They typically reflect the new prices between 06:15 AM and 07:00 AM IST.  
* **The Scraper Window:** An automated scraper designed to fetch this data should arguably be scheduled for **06:30 AM IST** to ensure it captures the updated values while avoiding the potential inconsistencies of the switch-over minute. Running the scraper at midnight, for example, would result in serving "yesterday's" price for the first six hours of the day—a critical error for a "real-time" application.

## **3\. Analysis of the "Static Lookup" Proposal**

The user's initial proposal involves a "static client-side lookup using reverse geocoding." While this approach minimizes server costs and latency, a rigorous analysis reveals it to be structurally fundamentally flawed for the specific use case of dynamic fuel pricing.

### **3.1 The Temporal Decay of Static Data**

The definition of "static" implies data that does not change frequently (e.g., country codes, state names). Fuel prices, by definition, are dynamic.

* **The Update Paradox:** If the app relies on a static JSON file bundled within the application package (assets/prices.json), that file is obsolete the moment the app is published. To update the prices, the developer would need to push a new version of the app to the Google Play Store or Apple App Store *every single day*. Given the review times (24-48 hours) for app updates, this is impossible.  
* **The "Config File" Workaround:** The developer could host the JSON file on a server and have the app download it on launch. While this solves the update problem, it ceases to be a "static client-side lookup" and becomes a network-dependent fetch. If the app is downloading a file daily, the "static" advantage is lost, and we are back to the problem of *generating* that file daily.

### **3.2 The Geospatial Mismatch: Reverse Geocoding vs. Market Zones**

Reverse geocoding is the process of converting coordinates (Latitude/Longitude) into a human-readable address. The output of a geocoding API typically follows an administrative hierarchy: Country \-\> State \-\> District \-\> City \-\> Locality.

* **The Granularity Gap:** Fuel pricing zones do not always map 1:1 with administrative boundaries. A "Fuel City" might be a cluster of petrol pumps that spans across two municipal borders, or a single district might have multiple pricing zones based on distance from the fuel depot.  
* **The "Nearest Neighbor" Problem:** A user standing on a highway (e.g., coordinates 19.07, 72.87) might generate a reverse geocode result of "Village X." If "Village X" is not in the static pricing database, the lookup fails. The app needs complex logic to find the *nearest* city in the database to the user's location, requiring geospatial queries (e.g., Haversine formula) rather than simple string matching.

### **3.3 The Hidden Costs of Client-Side Geocoding**

The proposal assumes reverse geocoding is a "free" or low-cost utility, but this is often a misconception at scale.

* **Google Maps Platform:** The Geocoding API costs approximately $5.00 per 1,000 requests after the initial free tier. For an app with moderate usage, this can quickly exceed the cost of a paid fuel API.  
* **Device-Native Geocoders:** Android (android.location.Geocoder) and iOS (CLGeocoder) offer free reverse geocoding. However, they are rate-limited and offer less consistent nomenclature (e.g., returning "Bengaluru" vs "Bangalore"), which breaks exact-match lookups against a database.

**Verdict:** The static lookup model is technically feasible *only if* it serves as the consumption layer for a file that is dynamically generated and hosted remotely. It cannot be static in the true sense.

## **4\. Architectural Pattern A: The Self-Updating Database (ETL)**

The user asks: "Can we have a DB that auto-updates its prices based on scraped city fuel prices from websites (once per day)?"  
This describes a classic Extract-Transform-Load (ETL) pipeline. This is a standard and highly effective pattern for creating "unofficial" APIs from public data.

### **4.1 Ingestion Strategies: Analyzing Tier 2 Aggregators**

Since no official API exists, the system must ingest data from "Tier 2" aggregators—websites that display fuel prices in HTML tables. Based on the research, two primary targets emerge:

**Target 1: GoodReturns.in** 7

* **Structure:** This site provides a clean, consolidated table for major cities and state capitals. The HTML structure typically involves a div with class gold\_silver\_table or specific table classes.11  
* **Pros:** High uptime, predictable URL structure (/petrol-price.html), and simple HTML that parses easily with standard libraries like BeautifulSoup.  
* **Cons:** Limited coverage. It focuses on major metro cities (Mumbai, Delhi, Chennai, Kolkata) and state capitals. It may miss smaller districts or towns.7

**Target 2: MyPetrolPrice.com** 12

* **Structure:** This site offers significantly higher granularity, covering hundreds of cities and districts. However, the data is often nested deeper (State Page \-\> City Page).  
* **Pros:** Exhaustive coverage, often including historical trends and charts.13  
* **Cons:** More complex scraping logic required to traverse the hierarchy. Higher likelihood of anti-scraping measures due to the value of their data.

**Target 3: NDTV and Other News Sites** 1

* **Structure:** News sites like NDTV often have dedicated fuel sub-domains.  
* **Pros:** Reliable infrastructure.  
* **Cons:** The "Fuel" sections are often embedded as widgets or interactive maps, which might require a headless browser (Selenium/Puppeteer) to render, increasing the complexity and resource cost of the scraper.14

### **4.2 Data Normalization and Entity Resolution**

A critical component of this architecture is the "Transform" layer. Raw scraped data is rarely ready for consumption.

* **Currency Normalization:** Scrapers will extract strings like "₹ 103.50". The pipeline must strip the symbol and cast the string to a floating-point number (103.50) for storage.  
* **City Name Standardization:** This is the most complex step. The scraper might ingest "Bangalore," but the user's geocoder might return "Bengaluru."  
  * **Solution:** The database must maintain an **Alias Table**.  
  * *Schema:* CityID: 1, Name: "Bengaluru", Aliases:.  
  * During the ETL process, incoming names are matched against this alias list to ensure data consistency.

### **4.3 Database Selection and Schema Design**

For a dataset of this size (approx. 700 cities x 2 fuel types), the choice of database is flexible.

* **Relational (PostgreSQL/MySQL):** Good for structured data and historical querying.  
  * *Table prices\_daily:* city\_id (PK), petrol, diesel, date.  
* **NoSQL (MongoDB/Firebase):** Excellent for flexible schemas if the scraper adds new fields (e.g., CNG, LPG) later.  
* **Flat JSON:** Given the small total size (less than 1MB for all India prices), a simple JSON file is often the most performant "database."

**Hosting Costs:** A traditional approach would involve hosting this database on a Virtual Private Server (VPS) like EC2 or DigitalOcean Droplets ($5/month) and running a cron job. While functional, this incurs a monthly cost and maintenance burden (OS updates, security patches), which violates the user's preference for a "better," potentially free solution.

## **5\. Architectural Pattern B: Git Scraping (The Superior Alternative)**

The user explicitly asks for "better ways." In the context of 2025's development landscape, **Git Scraping** is the superior architectural pattern for low-frequency, high-value data datasets like daily fuel prices. It eliminates the need for a dedicated database server, driving costs to zero while maximizing reliability.15

### **5.1 The Philosophy of "Flat Data" and Serverless ETL**

Git Scraping, a concept championed by data engineers like Simon Willison, inverts the traditional web scraping model. Instead of a server querying a database, the **repository itself** becomes the database.

* **The Mechanism:** A CI/CD runner (like GitHub Actions) spins up a temporary virtual machine, runs the scraping script, saves the output as a file (JSON/CSV), and **commits** it back to the repository.  
* **The "Server":** GitHub's infrastructure hosts the file. When the file is updated, the new version is instantly available via a public URL.  
* **History:** Version control (Git) automatically handles history. Every day's commit represents a snapshot of that day's prices, creating an immutable audit trail without writing a single line of database archival code.15

### **5.2 Implementation Blueprint: The GitHub Actions Workflow**

To implement this, the developer defines a workflow file (e.g., .github/workflows/scrape.yml). This file dictates the schedule and the commands to run.

**The Workflow Logic:**

1. **Trigger:** cron: '30 0 \* \* \*' (Runs at 00:30 UTC, which is 06:00 AM IST).  
2. **Environment:** ubuntu-latest.  
3. **Steps:**  
   * Checkout the repository code.  
   * Install Python and dependencies (requests, beautifulsoup4, pandas).  
   * Execute the extraction script (python scrape\_prices.py).  
   * Check if data.json has changed.  
   * If changed, commit and push the new data.json back to the main branch.

### **5.3 Advantages Over Traditional Database Hosting**

* **Zero Cost:** GitHub Actions offers 2,000 free minutes per month for public repositories.17 A daily scraper running for 1 minute uses only \~30 minutes/month, well within the free tier.  
* **Infinite Scalability:** The data is served via raw.githubusercontent.com or GitHub Pages, which are backed by global CDNs. This infrastructure can handle millions of requests without the developer paying for bandwidth or worrying about server crashes.  
* **Maintenance-Free:** There is no database engine to patch, no server OS to secure, and no uptime monitoring required for the infrastructure.

## **6\. Implementation Deep Dive: Building the Pipeline**

This section provides the specific technical details required to build the Git Scraping solution, addressing the "how-to" aspect of the user's request.

### **6.1 Target Analysis: GoodReturns vs. MyPetrolPrice**

Based on the research snippets, we can construct a matrix to select the best target for the scraper.

| Feature | GoodReturns | MyPetrolPrice | Recommendation |
| :---- | :---- | :---- | :---- |
| **URL Structure** | Flat (/petrol-price.html) | Hierarchical (State \-\> City) | **GoodReturns** for simplicity. |
| **HTML Structure** | Clean tables (class="gold\_silver\_table") | Nested lists/tables | **GoodReturns** for parsing ease. |
| **Granularity** | Major Cities & Capitals | Extensive (Districts/Towns) | **MyPetrolPrice** for coverage. |
| **Anti-Scraping** | Moderate | High (Captchas often reported) | **GoodReturns** is safer. |

**Strategy:** Start by scraping **GoodReturns** to build the MVP. It offers the highest return on investment for effort. If district-level granularity is essential later, a second scraper for MyPetrolPrice can be added.

### **6.2 The Extraction Logic (Python/BeautifulSoup)**

The core of the system is the Python script. The logic involves fetching the page, parsing the DOM, and extracting the relevant rows.

**Key Technical Considerations:**

* **User-Agent Rotation:** The scraper must identify itself as a legitimate browser to avoid being blocked by the server's firewall (WAF).  
* **Error Handling:** The script must be robust. If the website structure changes (e.g., class name changes from gold\_silver\_table to rates\_table), the script should fail gracefully, perhaps by not committing any data, so the API continues to serve the last known good data rather than an empty file.

**Sample Logic Flow:**

1. requests.get(url) returns the HTML.  
2. BeautifulSoup(html) creates the DOM tree.  
3. soup.find("div", class\_="gold\_silver\_table") locates the pricing container.  
4. Iterate over tr (table rows).  
5. Extract td as City and td as Price.  
6. Clean the price string (replace('₹', '')).  
7. Append to a Python list of dictionaries.  
8. json.dump(data) to prices.json.

### **6.3 Handling Anti-Scraping Defenses**

While Tier 2 aggregators are public, they may implement basic defenses.

* **Rate Limiting:** If scraping multiple pages (e.g., traversing states on MyPetrolPrice), the script *must* implement a delay (time.sleep(2)) between requests. This is not just good etiquette; it prevents IP bans.  
* **IP Rotation:** GitHub Actions uses a pool of Azure IP addresses. These are generally trusted, but if they get blocked, the workflow might fail. In such cases, using a proxy service (even a free tier one) within the script might be necessary, though usually overkill for a once-a-day fetch.  
* **Robots.txt Compliance:** Research indicates that while some paths are disallowed, main pricing pages are often accessible to bots to allow search indexing.18 However, it is ethical to respect the Crawl-delay directive if present.

## **7\. The Consumption Layer: Client-Side Integration**

Once the data is live on GitHub, the client application (Mobile or Web) needs to consume it intelligently.

### **7.1 Fetching and Caching Strategies**

The client should *not* hit the GitHub URL every time the user opens the app.

* **Session Caching:** Fetch the prices.json once per app session or once per day. Store it in local storage (AsyncStorage in React Native, SharedPreferences in Android).  
* **ETag Validation:** GitHub servers support ETags. The client can send a request with If-None-Match. If the file hasn't changed (e.g., the user re-opens the app 1 hour later), GitHub returns 304 Not Modified, saving bandwidth and processing time.

### **7.2 Fuzzy Matching for Robust City Selection**

This is the bridge between the **User's Location** and the **Scraped Data**.

* **The Challenge:** The user's GPS reverse geocoding returns "Gurugram," but the JSON has "Gurgaon."  
* **The Solution:** Implement a client-side fuzzy matching algorithm using the **Levenshtein Distance** metric.  
  * When the user is in "Gurugram," the app iterates through the keys in prices.json.  
  * It calculates the "edit distance" between "Gurugram" and every city in the list.  
  * "Gurgaon" will have a low edit distance (high similarity).  
  * The app selects the closest match automatically.  
  * *Optimization:* For performance, map the user's location to the *State* first, then fuzzy match only against cities within that State.

## **8\. Comparative Market Analysis**

To fully justify the "Build" approach (Git Scraping), we must compare it against the "Buy" options available in the market.

### **8.1 Commercial APIs vs. Open Source**

Several providers offer paid APIs for this data.

* **Zyla Labs:** Offers a "Fuel Prices in India API" starting at \~$25/month for 1,000 requests. It provides clean JSON but effectively just scrapes the same sources we identified.2  
* **APIClub:** Offers a similar service with "Real-Time" promises. However, given the 6 AM update cycle, "Real-Time" is a marketing term for "Daily".3  
* **SurePass:** Focuses on identity verification but offers a fuel API as a side utility. Likely uses a similar scraping backend.20

**Verdict:** Paying $25-$50/month for data that updates once a day and is publicly available on HTML pages is an inefficient allocation of resources for a startup or indie developer. The Git Scraping method offers 95% of the utility for 0% of the cost.

### **8.2 Review of Existing Open Source Projects**

A search of GitHub reveals several attempts to solve this problem, validating the demand.

* **gokulkrishh/fuel-price:** Uses a Node.js backend on Glitch. While functional, Glitch apps "sleep" after inactivity, causing high latency for the first user.21  
* **FuelBook-API:** A Python/Flask app hosted on Heroku.22 With Heroku ending its free tier, this project is likely broken or costing money.  
* **fuel-price-api (Django):** Another scraper-based project.23

**The Pattern of Abandonment:** Many of these repos haven't been updated in years.24 This suggests that maintaining a *server* (even a free one) is a hurdle. Git Scraping removes the server maintenance entirely, making it a more sustainable model for open-source utilities.

## **9\. Conclusion**

The "static client-side lookup" proposed to the user is a fundamentally flawed approach for the dynamic reality of India's fuel pricing market. It fails to account for the daily volatility introduced in 2017 and the geospatial complexity of pricing zones.

However, the user does not need to resort to expensive commercial APIs. The **Git Scraping** architecture represents the optimal "Better Way." By leveraging GitHub Actions to perform a daily scrape of aggregator sites like GoodReturns, and serving the data as a static JSON file via GitHub Pages, the user can achieve a system that is:

1. **Auto-Updating:** Synchronized with the 6 AM daily price change.  
2. **Cost-Free:** Utilizing free tiers of CI/CD and CDN hosting.  
3. **Robust:** Inherently versioned and serverless.

This approach transforms the problem from a "Database Management" challenge into a "Data Pipeline" challenge, offering a professional-grade solution that is scalable, maintainable, and aligned with modern serverless engineering practices. The recommendation is to proceed immediately with building a Python-based Git Scraper targeting Tier 2 aggregators as the primary data source.

#### **Works cited**

1. Petrol Price in India | Check Latest Petrol Rates in India Today \- Hindustan Times, accessed December 5, 2025, [https://www.hindustantimes.com/fuel-prices/petrol](https://www.hindustantimes.com/fuel-prices/petrol)  
2. Fuel Prices in India API \- Zyla API Hub, accessed December 5, 2025, [https://zylalabs.com/api-marketplace/data/fuel+prices+in+india+api/324](https://zylalabs.com/api-marketplace/data/fuel+prices+in+india+api/324)  
3. Fuel Price API for Real-Time Diesel, and Petrol Rates \- APIclub.in, accessed December 5, 2025, [https://www.apiclub.in/product/fuel\_price\_api](https://www.apiclub.in/product/fuel_price_api)  
4. Home | Petroleum Planning & Analysis Cell | Government of India, accessed December 5, 2025, [https://ppac.gov.in/](https://ppac.gov.in/)  
5. International Prices of Crude Oil (Indian Basket), Petrol and Diesel | Petroleum Planning & Analysis Cell | Government of India, accessed December 5, 2025, [https://ppac.gov.in/prices/international-prices-of-crude-oil](https://ppac.gov.in/prices/international-prices-of-crude-oil)  
6. Petrol and Diesel Price : Indian Oil Corporation | Petrol Price in India, accessed December 5, 2025, [https://iocl.com/petrol-diesel-price](https://iocl.com/petrol-diesel-price)  
7. Petrol Price Today (5th Dec, 2025), Petrol Rate in India \- Goodreturns, accessed December 5, 2025, [https://www.goodreturns.in/petrol-price.html](https://www.goodreturns.in/petrol-price.html)  
8. Fuel Prices In India Today | Dec 05 | Petrol, Diesel & CNG Rates \- V3Cars, accessed December 5, 2025, [https://www.v3cars.com/fuel-price-in-india](https://www.v3cars.com/fuel-price-in-india)  
9. Fuel Price in India Today (05 December, 2025\) | Check Fuel Rate / Cost Today \- CarDekho, accessed December 5, 2025, [https://www.cardekho.com/fuel-price](https://www.cardekho.com/fuel-price)  
10. Diesel Price in India \- Check Latest Diesel Prices 05 Dec 2025 \- BankBazaar, accessed December 5, 2025, [https://www.bankbazaar.com/fuel/diesel-price-india.html](https://www.bankbazaar.com/fuel/diesel-price-india.html)  
11. Build Fuel Price Tracker Using Python \- GeeksforGeeks, accessed December 5, 2025, [https://www.geeksforgeeks.org/python/build-fuel-price-tracker-using-python/](https://www.geeksforgeeks.org/python/build-fuel-price-tracker-using-python/)  
12. Diesel Price in India \- MyPetrolPrice, accessed December 5, 2025, [https://www.mypetrolprice.com/diesel-price-in-india.aspx](https://www.mypetrolprice.com/diesel-price-in-india.aspx)  
13. Petrol Price in India \- MyPetrolPrice, accessed December 5, 2025, [https://www.mypetrolprice.com/petrol-price-in-india.aspx](https://www.mypetrolprice.com/petrol-price-in-india.aspx)  
14. Petrol and Diesel Prices in India \- NDTV, accessed December 5, 2025, [https://www.ndtv.com/fuel-prices](https://www.ndtv.com/fuel-prices)  
15. Simon Willison on git-scraping, accessed December 5, 2025, [https://simonwillison.net/tags/git-scraping/](https://simonwillison.net/tags/git-scraping/)  
16. Actions · GitHub Marketplace \- Flat Data, accessed December 5, 2025, [https://github.com/marketplace/actions/flat-data](https://github.com/marketplace/actions/flat-data)  
17. swyxio/gh-action-data-scraping \- GitHub, accessed December 5, 2025, [https://github.com/swyxio/gh-action-data-scraping](https://github.com/swyxio/gh-action-data-scraping)  
18. accessed January 1, 1970, [https://www.goodreturns.in/robots.txt](https://www.goodreturns.in/robots.txt)  
19. accessed January 1, 1970, [https://www.mypetrolprice.com/robots.txt](https://www.mypetrolprice.com/robots.txt)  
20. Fuel-prices-api \- Surepass, accessed December 5, 2025, [https://surepass.io/fuel-prices-api/](https://surepass.io/fuel-prices-api/)  
21. gokulkrishh/fuel-price: Check fuel prices daily in most of the states in India \- GitHub, accessed December 5, 2025, [https://github.com/gokulkrishh/fuel-price](https://github.com/gokulkrishh/fuel-price)  
22. API for the FuelBook Android App Project \- GitHub, accessed December 5, 2025, [https://github.com/shreyansh818bytes/FuelBook-API](https://github.com/shreyansh818bytes/FuelBook-API)  
23. AnkitVats21/fuel-price-api \- GitHub, accessed December 5, 2025, [https://github.com/AnkitVats21/fuel-price-api](https://github.com/AnkitVats21/fuel-price-api)  
24. tekina/fuel\_prices\_india: Fetch latest fuel prices for major Indian cities \- GitHub, accessed December 5, 2025, [https://github.com/tekina/fuel\_prices\_india](https://github.com/tekina/fuel_prices_india)