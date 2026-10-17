# Solana Meme Scanner (free starter)

This Streamlit app discovers Solana tokens through DEX Screener's latest token-profile and boost endpoints, retrieves pair metrics, filters them, and ranks by a simple **momentum** heuristic.

## Run locally

1. Install Python 3.10 or later.
2. In this folder run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.
4. Open the local URL shown in the terminal.

## Optional free-tier deployment

Push the files to a GitHub repository, then deploy `app.py` using Streamlit Community Cloud, subject to its current free-tier policies. No API key is required for the DEX Screener endpoints used here.

## Important limitations

- Latest profile/boost endpoints **are not an exhaustive new-pair stream**. The app may miss newly launched tokens.
- Ranking is a heuristic momentum score, **not** a safety assessment or prediction.
- Holder concentration, mint/freeze permissions, wallet bundles, and liquidity-lock status are **not checked**.
- The dashboard refreshes data when rerun, with 60-second caching. It does not continuously run or send alerts in the background.
- DEX Screener API limits and response formats can change. Respect published rate limits.
- Market cap uses FDV as a fallback when market cap is unavailable.
- Never connect a wallet or provide a private key to this app.
