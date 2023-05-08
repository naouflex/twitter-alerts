import tweepy
import os,sys
import base64
import requests
import seaborn as sns
from dotenv import load_dotenv

import psycopg2
import json
import requests
import pandas as pd
from time import sleep

load_dotenv()

import os
import tweepy

def post_tweet_private(content=None, max_attempts=3):
    attempt = 1

    while attempt <= max_attempts:
        try:
            consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
            consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
            access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
            access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
            bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

            auth = tweepy.OAuth1UserHandler(
                consumer_key,
                consumer_secret,
                access_token,
                access_token_secret
            )

            api = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                bearer_token=bearer_token
            )

            current_user = api.get_me()
            print(current_user.data.id)
            recipient_id = current_user.data.id

            dm = api.create_direct_message(
                participant_id=recipient_id,
                text=content
            )

            print("Direct message sent successfully.")
            return True
        except Exception as e:
            if attempt == max_attempts:
                print("Error: Unable to send direct message.")
                import traceback
                traceback.print_exc()
            else:
                attempt += 1
                print("\nRetrying... (attempt {}/{})".format(attempt, max_attempts))


def post_tweet(content=None, filename=None, max_attempts=3):
    attempt = 1

    while attempt <= max_attempts:
        try:
            # Set up API keys and access tokens
            consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
            consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
            access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
            access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
            bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")

            # OAuth process, using the keys and tokens
            auth = tweepy.OAuth1UserHandler(
                consumer_key, 
                consumer_secret, 
                access_token, 
                access_token_secret
            )

            # Creation of the actual interface, using authentication
            api = tweepy.Client(
                consumer_key=consumer_key, 
                consumer_secret=consumer_secret, 
                access_token=access_token, 
                access_token_secret=access_token_secret,
                bearer_token=bearer_token
            )

            api2 = tweepy.API(auth, wait_on_rate_limit = True)
            
            # Upload image if provided
            if filename is not None:
                # Check if the file is a png file
                if filename.lower().endswith('.png'):
                    with open(filename, 'rb') as image_file:
                        media = api2.media_upload(filename, file=image_file)
                        media_id = media.media_id
                else:
                    raise ValueError("Image file must be a png file.")
            else:
                media_id = None

            # Create the tweet with or without the image
            if media_id is not None:
                tweet = api.create_tweet(text=content, media_ids=[media_id])
            else:
                tweet = api.create_tweet(text=content)

            return tweet
        except Exception as e:
            if attempt == max_attempts:
                print("Error: Unable to post tweet.")
                import traceback
                traceback.print_exc()
            else:
                attempt += 1
                print("\nRetrying... (attempt {}/{})".format(attempt, max_attempts))
    pass



#get data from https://www.inverse.finance/api/oppyS
def get_apy_data(retry_attempts=5, retry_delay=5):
    url = "https://www.inverse.finance/api/oppys"

    for attempt in range(retry_attempts):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data:
                break
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < retry_attempts - 1:
                sleep(retry_delay)
            else:
                print("Max retry attempts reached. Returning empty DataFrame.")
                return pd.DataFrame()
    else:
        print("No data received. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.json_normalize(data["pools"])

    numeric_cols = [
        "tvlUsd",
        "apyBase",
        "apyReward",
        "apy",
        "apyPct1D",
        "apyPct7D",
        "apyPct30D",
        "mu",
        "sigma",
        "count",
        "il7d",
        "apyBase7d",
        "apyMean30d",
        "volumeUsd1d",
        "volumeUsd7d",
        "apyBaseInception"
    ]

    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

    df_sorted = df.sort_values(by=["apy"], ascending=False)

    return df_sorted



def get_top_apy(type):
    df = get_apy_data()
    df = df[[
        "project",
        "symbol",
        "tvlUsd",
        "apy"
        ]]
    
    # list of key owrds
    volatile = ["VELO","INV","INV","WETH","DBR","ETH"]
    stable = ["CUSD","USDC","FRAX","USD+","MAI","3POOL"]
    exclude = ["EULER"]
    # excludes if symbol includes 'EULER'
    df = df[~df.symbol.str.contains('|'.join(exclude))]
    #get top 5 rows
    if type == 'volatile':
        df = df[df.symbol.str.contains('|'.join(volatile))]
    elif type == 'stable':
        df = df[df.symbol.str.contains('|'.join(stable))]

    df = df.head(5)
    return df

def post_stable(test=False):

    #post_tweet(content="", filename="test.png")
    table = get_top_apy('stable')

    message = "💪🏼 Top 5 APR Stable : \n" +\
    "🔸" + table.iloc[0]['symbol'] +": " + "{:.2%}".format(table.iloc[0]['apy'] / 100) + "\n" +\
    "🔸" + table.iloc[1]['symbol'] +": " + "{:.2%}".format(table.iloc[1]['apy'] / 100) + "\n" +\
    "🔸" + table.iloc[2]['symbol'] +": " + "{:.2%}".format(table.iloc[2]['apy'] / 100) + "\n" +\
    "🔸" + table.iloc[3]['symbol'] +": " + "{:.2%}".format(table.iloc[3]['apy'] / 100) + "\n" +\
    "🔸" + table.iloc[4]['symbol'] +": " + "{:.2%}".format(table.iloc[4]['apy'] / 100) + "\n" +"\n" +\
    "https://inverse.finance/yield"

    print(message)
    #message = message + " " + message.split()[-1]
    if test:
        post_tweet_private(content=message)
    else:
        post_tweet(content=message)


def post_volatile(test=False):
    
        #post_tweet(content="", filename="test.png")
        table = get_top_apy('volatile')
    
        message = "🚀 Top 5 APR Volatile : \n" +\
        "🔹" + table.iloc[0]['symbol'] +": " + "{:.2%}".format(table.iloc[0]['apy'] / 100) + "\n" +\
        "🔹" + table.iloc[1]['symbol'] +": " + "{:.2%}".format(table.iloc[1]['apy'] / 100) + "\n" +\
        "🔹" + table.iloc[2]['symbol'] +": " + "{:.2%}".format(table.iloc[2]['apy'] / 100) + "\n" +\
        "🔹" + table.iloc[3]['symbol'] +": " + "{:.2%}".format(table.iloc[3]['apy'] / 100) + "\n" +\
        "🔸" + table.iloc[4]['symbol'] +": " + "{:.2%}".format(table.iloc[4]['apy'] / 100) + "\n" +"\n" +\
        "https://inverse.finance/yield"
    
        print(message)
        #message = message + " " + message.split()[-1]    
        if test:
            post_tweet_private(content=message)
        else:
            post_tweet(content=message)


def get_liquidity_data(retry_attempts=5, retry_delay=5):
    url = "https://www.inverse.finance/api/transparency/liquidity?cacheFirst=true"

    for attempt in range(retry_attempts):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data:
                break
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < retry_attempts - 1:
                sleep(retry_delay)
            else:
                print("Max retry attempts reached. Returning empty DataFrame.")
                return pd.DataFrame()
    else:
        print("No data received. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.json_normalize(data["liquidity"])

    numeric_cols = [
        "chainId",
        "decimals",
        "tvl",
        "ownedAmount",
        "perc",
        "pairingDepth",
        "dolaBalance",
        "dolaWeight",
        "rewardDay"
    ]

    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

    df = df[df.lpName.str.contains('DOLA')]
    df = df[df.deduce.isnull()]

    df_sorted = df.sort_values(by=["apy"], ascending=False)

    return df_sorted



# get the sum from the tvl column from liquidity data
def get_total_liquidity():
    df = get_liquidity_data()
    df = df[[
        "tvl"
        ]]
    total_liquidity = df.sum()
    #format to currency
    total_liquidity = "${:,.2f}".format(total_liquidity[0])
    return total_liquidity

def get_average_dola_weight():
    df = get_liquidity_data()
    average_dola_weight = (df['dolaWeight'].fillna(0) * df['tvl']).sum() / df['tvl'].sum() / 100
    # format to percentage
    average_dola_weight = "{:.2%}".format(average_dola_weight)
    return average_dola_weight



def get_protocol_owned():
    df = get_liquidity_data()
    df = df[[
        "ownedAmount"
        ]]
    protocol_owned = df.sum()
    #format to currency
    protocol_owned = "${:,.2f}".format(protocol_owned[0])
    return protocol_owned

def get_avg_apy():
    df = get_liquidity_data()
    avg_apy = (df['apy'].fillna(0) * df['tvl']).sum() / df['tvl'].sum() / 100
    # format to percentage
    avg_apy = "{:.2%}".format(avg_apy)
    return avg_apy



def post_liquidity(test=False):
    message = "DOLA Liquidity Snapshot: \n" +\
    "📈 Total Liquidity: " + get_total_liquidity() + "\n" +\
    " Σ  Average DOLA Weight: " + get_average_dola_weight() + "\n" +\
    "💰 Protocol Owned: " + get_protocol_owned() + "\n" +\
    "➡️ Average APY: " + get_avg_apy() + "\n"
    
    print(message)
    if test:
        post_tweet_private(content=message)
    else:
        post_tweet(content=message)

def get_alerts_from_db(alert_ids, since=None):
    # Replace the placeholders with your actual PostgreSQL database credentials
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),

    )

    cur = conn.cursor()
    if since:
        cur.execute("SELECT created_at, alert_id, message FROM alerts_logmessage WHERE alert_id = ANY(%s) AND created_at > %s ORDER BY created_at DESC", (alert_ids, since))
    else:
        cur.execute("SELECT created_at, alert_id, message FROM alerts_logmessage WHERE alert_id = ANY(%s) ORDER BY created_at DESC", (alert_ids,))
    rows = cur.fetchall()
    conn.close()

    print(f"Rows fetched: {len(rows)}")  # Debugging line

    # Create a DataFrame from the rows
    df = pd.DataFrame(rows, columns=['created_at', 'alert_id', 'message'])

    # Convert the 'message' column from JSON strings to dictionaries
    df['message'] = df['message'].apply(json.loads)

    return df

def check_and_send_tweet(alert):
    for field in alert['fields']:
        if field['name'] == 'USD value':
            value = float(field['value'].replace(',', ''))
            if value > 1000000:
                # Send tweet with the required information
                tweet = f"Alert: A transaction worth ${value:,.0f} just happened! Alert ID: {alert['alert_id']}."
                post_tweet_private(tweet)
            else :
                # Send tweet with the required information
                tweet = f"Not posted : Alert: A transaction worth ${value:,.0f} just happened! Alert ID: {alert['alert_id']}."
                post_tweet_private(tweet)


def monitor_database(alert_ids, poll_interval=60, max_attempts=3):
    attempt = 1
    while attempt <= max_attempts:
        try:
            last_check_time = None
            while True:
                if last_check_time is None:
                    new_alerts = get_alerts_from_db(alert_ids)
                else:
                    new_alerts = get_alerts_from_db(alert_ids, since=last_check_time)
                
                if not new_alerts.empty:
                    last_check_time = new_alerts['created_at'].max()

                    for index, row in new_alerts.iterrows():
                        check_and_send_tweet(row['message'])

                sleep(poll_interval)

        except Exception as e:
            if attempt == max_attempts:
                print("Error: Unable to monitor database.")
                import traceback
                traceback.print_exc()
            else:
                attempt += 1
                print("\nRetrying... (attempt {}/{})".format(attempt, max_attempts))


