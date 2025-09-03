# coinscan

## Cryptocurrency Analysis

This project contains a script to analyze cryptocurrency data from Binance and CoinMarketCap.

### How to Run

1.  **Install Dependencies:**

    Install the required Python libraries using pip:

    ```bash
    pip install -r coin_analysis/requirements.txt
    ```

2.  **Configure API Keys:**

    Open the `coin_analysis/analysis.py` file and replace the placeholder API keys for Binance and CoinMarketCap with your actual keys:

    ```python
    BINANCE_API_KEY = "YOUR_BINANCE_API_KEY"
    BINANCE_API_SECRET = "YOUR_BINANCE_API_SECRET"
    COINMARKETCAP_API_KEY = "YOUR_COINMARKETCAP_API_KEY"
    ```

3.  **Run the Analysis:**

    Execute the script from the root of the project directory:

    ```bash
    python /mnt/c/Users/leizh/Src/coinscan/coin_analysis/analysis.py
    ```

4.  **View the Results:**

    The script will create a directory named `analysis_output` inside the `coin_analysis` directory. This directory will contain the generated report (`report.md`) and the associated data files.
