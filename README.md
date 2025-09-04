# coinscan

## 🚀 Cryptocurrency Market Analysis Project 🚀

This project provides a robust framework for analyzing cryptocurrency market data from Binance and CoinMarketCap, focusing on identifying valuable features for intraday trading strategies. It's designed for modularity and extensibility, allowing for easy integration of new analysis techniques.

### ✨ Experiment Design & Methodology ✨

Our analysis is structured to provide deep insights into the behavior of different segments of the cryptocurrency market.

#### 🎯 Goal

To predict virtual currency prices for intraday trading, identify valuable feature factors, and gain a comprehensive understanding of the current virtual currency trading market through statistical analysis of Binance spot trading pairs.

#### 🛠️ Methodology

1.  **Data Acquisition & Caching:**
    *   **Source:** Data is fetched from Binance (for trading pairs and historical k-line data) and CoinMarketCap (for market capitalization details).
    *   **Scope:** We retrieve all USDT trading pairs and their daily trading data for the last `N_DAYS` (currently configured to 7 days).
    *   **Efficiency:** To optimize performance and reduce API calls, all fetched data is intelligently cached locally in the `coin_analysis/fetched_data` directory. The system checks for existing local copies before making new API requests.

2.  **Intelligent Coin Grouping:**
    *   Cryptocurrencies are dynamically segmented into **Top**, **Mid**, and **Low** market capitalization groups.
    *   **Configurable Grouping Methods:** You can easily switch between different grouping strategies by adjusting the `GROUPING_METHOD` variable in `analysis.py`:
        *   `'terciles'`: Divides coins into three groups with an approximately equal number of members.
        *   `'thresholds'`: Groups coins based on predefined market capitalization ranges (e.g., < $100M, $100M-$1B, > $1B). These thresholds are configurable.
        *   `'kmeans'`: Utilizes the K-Means clustering algorithm to identify natural groupings based on market capitalization.

3.  **Comprehensive Group Analysis:**
    For each defined group, the system performs a multi-faceted analysis:

    *   **📊 Comparative Descriptive Statistics:** A single, elegant table provides a side-by-side comparison of key metrics across all groups, offering immediate insights into their fundamental differences.
        *   **Key Metrics:** Number of tokens, mean/median/min/max market cap, mean/median circulating supply ratio, average daily return, volatility (standard deviation of daily return), Annualized Sharpe Ratio, average 24h trading volume, and average turnover rate.

    *   **📈 Price Trend Consistency:** Visualizes and quantifies how consistently prices move within each group.
        *   **Visuals:** Normalized price trend plots over the 7-day period.
        *   **Metrics:** Daily returns correlation matrix.

    *   **📉 Risk & Return Profile:** Delves into the risk characteristics and return distributions.
        *   **Metrics:** Average Historical Volatility, Average Beta (relative to Bitcoin), Average VaR (Value-at-Risk) and CVaR (Conditional VaR) for tail risk, and Average Skewness and Kurtosis for return distribution shape.
        *   **Visuals:** Return distribution histograms for each group.

### 🚀 How to Get Started

1.  **Install Dependencies:**

    Ensure you have all necessary Python libraries by running:

    ```bash
    pip install -r coin_analysis/requirements.txt
    ```

2.  **Configure API Keys:**

    Open `coin_analysis/config.py` and replace the placeholder API keys with your actual Binance and CoinMarketCap credentials:

    ```python
    BINANCE_API_KEY = "YOUR_BINANCE_API_KEY"
    BINANCE_API_SECRET = "YOUR_BINANCE_API_SECRET"
    COINMARKETCAP_API_KEY = "YOUR_COINMARKETCAP_API_KEY"
    ```

3.  **Run the Analysis:**

    Execute the main script from your project's root directory:

    ```bash
    python coin_analysis/analysis.py
    ```

4.  **View the Results:**

    The script will generate a timestamped output directory (e.g., `analysis_output_YYYYMMDD_HHMM`) within `coin_analysis`. Inside, you'll find:
    *   `report.md`: A comprehensive Markdown report detailing all analyses, including tables and embedded plots.
    *   `combined_data.csv`: The raw combined data used for analysis.
    *   Individual group data CSVs and plot images.

### 📊 Expected Report Output (`report.md`)

The generated `report.md` will be a rich document, structured as follows:

*   **Overall Report Title:** "# Cryptocurrency Analysis Report"
*   **Market Cap Distribution:** A histogram visualizing the distribution of unlocked market caps across all coins.
*   **Comparative Descriptive Statistics:** A detailed table comparing key descriptive metrics across the Top, Mid, and Low market cap groups.
*   **Individual Group Analysis Sections (for Top, Mid, Low groups):**
    *   **Group Title:** "## [Group Name] Group Analysis"
    *   **Price Trend Consistency:**
        *   Normalized Price Trends plot (7 days).
        *   Daily Returns Correlation Matrix (table).
    *   **Risk and Return Analysis:**
        *   List of calculated risk/return metrics (e.g., Average Historical Volatility, Average Beta, Average VaR/CVaR, Average Skewness/Kurtosis).
        *   Daily Return Distribution plot (histogram).
    *   **Statistical Summary (Latest Day):** A summary table of the latest day's trading data for coins in that group.

This structured report provides a clear and actionable overview of the cryptocurrency market segments.
