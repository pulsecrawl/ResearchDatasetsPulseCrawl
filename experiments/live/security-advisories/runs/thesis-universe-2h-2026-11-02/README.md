# Security advisories: two-hour thesis-universe run

This evidence contains four scheduled site executions at 30-minute intervals. Each execution allowed up to 1,500 URLs, crawl depth five, and a 1,680-second execution window. The run used the public PulseCrawl 0.4.0 package and the longer of the robots delay or 0.5 seconds between same-origin requests.

- Sites: 8
- Successful site executions: 32/32
- Pages fetched: 34529
- Published rows: 3092
- Unique target-record URLs: 3092
- Complete rows: 3092

Start with `readable-output/site-summary.csv`, then inspect `readable-output/records-preview.csv` and `readable-output/pages-preview.csv`. The unsuffixed CSV and Parquet files contain the complete tables.
