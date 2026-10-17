import time
import requests
import pandas as pd
import streamlit as st

BASE = 'https://api.dexscreener.com'
st.set_page_config(page_title='Solana Meme Scanner', layout='wide')
st.title('Solana Meme Scanner')
st.caption('Experimental research dashboard. Not investment advice. Public discovery endpoints are not an exhaustive feed of new launches.')

@st.cache_data(ttl=60)
def get_candidates():
    session = requests.Session()
    session.headers['User-Agent'] = 'SolanaMemeScanner/1.0'
    addresses = set()
    for endpoint in ('/token-profiles/latest/v1', '/token-boosts/latest/v1'):
        try:
            r = session.get(BASE + endpoint, timeout=12)
            r.raise_for_status()
            for item in r.json():
                if item.get('chainId') == 'solana' and item.get('tokenAddress'):
                    addresses.add(item['tokenAddress'])
        except (requests.RequestException, ValueError) as e:
            st.warning(f'Could not fetch {endpoint}: {e}')
    pairs = {}
    tokens = list(addresses)
    for start in range(0, len(tokens), 30):
        try:
            r = session.get(BASE + '/tokens/v1/solana/' + ','.join(tokens[start:start+30]), timeout=20)
            r.raise_for_status()
            for p in r.json():
                if p.get('chainId') != 'solana':
                    continue
                key = p.get('baseToken', {}).get('address', '')
                if not key:
                    continue
                if key not in pairs or float(p.get('liquidity', {}).get('usd') or 0) > float(pairs[key].get('liquidity', {}).get('usd') or 0):
                    pairs[key] = p
        except (requests.RequestException, ValueError) as e:
            st.warning(f'Could not fetch token batch: {e}')
    return list(pairs.values())

with st.sidebar:
    st.header('Filters')
    min_mc = st.number_input('Minimum market cap ($)', value=15000, min_value=0, step=5000)
    max_mc = st.number_input('Maximum market cap ($)', value=500000, min_value=0, step=50000)
    min_liq = st.number_input('Minimum liquidity ($)', value=10000, min_value=0, step=5000)
    min_vol = st.number_input('Minimum 1h volume ($)', value=20000, min_value=0, step=5000)
    max_age = st.slider('Maximum pair age (hours)', 1, 72, 6)
    if st.button('Refresh now'):
        st.cache_data.clear()

try:
    raw = get_candidates()
except Exception as e:
    st.error(f'Unable to retrieve data: {e}')
    raw = []
now_ms = time.time() * 1000
rows = []
for p in raw:
    try:
        created = p.get('pairCreatedAt')
        if not created:
            continue
        age = (now_ms - float(created)) / 3_600_000
        if age < 0:
            continue
        mc = float(p.get('marketCap') or p.get('fdv') or 0)
        liq = float((p.get('liquidity') or {}).get('usd') or 0)
        vol = float((p.get('volume') or {}).get('h1') or 0)
        tx = (p.get('txns') or {}).get('h1') or {}
        buys, sells = int(tx.get('buys') or 0), int(tx.get('sells') or 0)
        if not (min_mc <= mc <= max_mc and liq >= min_liq and vol >= min_vol and age <= max_age):
            continue
        # Momentum score only. No on-chain safety assertions.
        score = round(35 * min(vol / max(liq, 1), 3) / 3 + 35 * buys / max(buys + sells, 1) + 30 * min(liq / max(mc, 1), 0.5) / 0.5)
        rows.append({'Token': p.get('baseToken', {}).get('symbol', '?'), 'Market cap $': round(mc), 'Liquidity $': round(liq), 'Volume 1h $': round(vol), 'Buys 1h': buys, 'Sells 1h': sells, 'Age hours': round(age, 2), 'Momentum score /100': score, 'DEX Screener': p.get('url', ''), 'Contract': p.get('baseToken', {}).get('address', '')})
    except (ValueError, TypeError, OverflowError):
        continue
st.metric('Discovered token pairs', len(raw))
st.metric('Matching candidates', len(rows))
st.warning('This is NOT a rug-pull safety score. Holder concentration, mint/freeze authority, bundles, and liquidity locks are not checked. Discovery endpoints may miss many launches. Market cap may use FDV fallback.')
if rows:
    df = pd.DataFrame(rows).sort_values('Momentum score /100', ascending=False)
    st.dataframe(df, hide_index=True, use_container_width=True, column_config={'DEX Screener': st.column_config.LinkColumn('DEX Screener')})
    st.download_button('Download CSV', df.to_csv(index=False), file_name='solana_candidates.csv', mime='text/csv')
else:
    st.info('No candidates match these filters in the current discovery sample. Try lowering the thresholds.')
st.caption('Data: DEX Screener public API. Cache refreshes at most every 60 seconds on rerun. This is not a background alert service.')
