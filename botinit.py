#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import tweepy, time, os, sys, random
from twitter import TwitterHTTPError

# This is initialization for Twitter OAUTH
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OAUTH.txt')) as f:
    words = f.readlines()
    data = [w.replace('\n','') for w in words]

CONSUMER_KEY = data[0]
CONSUMER_SECRET = data[1]
ACCESS_KEY = data[2]
ACCESS_SECRET = data[3]
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

f.close()

    
def __init__(self):
        self.TWITTER_CONNECTION = None
        random.seed()
    
# This is the tweeting module
def tweeter():
       tweet = raw_input('What would you like to tweet?\n')
       if len(tweet) > 140:
           print('It\'s over 140 characters...')
       else:
           print('\n Tweet live.')
           api.update_status(status=tweet)
           time.sleep(.5)
   
   # This is the tweet search module
def search_tweets(self, phrase, count=100, result_type="recent"):
   
           return self.TWITTER_CONNECTION.search.tweets(q=phrase, result_type=result_type, count=count)
           
# This is the service for a favoriting job
def favoriter(self, phrase, count=100, result_type="recent"):
           
       result = self.search_tweets(phrase, count, result_type)
       
       for tweet in result["statuses"]:
           try:
               # don't favorite your own tweets
               if tweet["user"]["screen_name"] == user_handle:
                   continue
                   
               result = self.TWITTER_CONNECTION.favorites.create(_id=tweet["id"])
               print("Favorited: %s" % (result["text"].encode("utf-8")), file==sys.stdout)
               
           # when you have already favorited a tweet, this error is thrown
           except TwitterHTTPError as api_error:
               # quit on rate limit errors
               if "rate limit" in str(api_error).lower():
                   print("You have been rate limited. "
                       "Wait a while before running the bot again.", file==sys.stderr)
                   return
                   
               if "you have already favorited this status" not in str(api_error).lower():
                   print("Error: %s" % (str(api_error)), file==sys.stderr)
   # This is the list of favorites and the option to remove those that aren't favoriting back.
def list():
    n = 0
    for user in tweepy.Cursor(api.followers, screen_name=user_handle).items():
        n += 1
        print user.screen_name
        int(n)
    print('\n'), n + 1, ('followers.\n')
    time.sleep(1)
    # Mutual destruction
    isitmutual = raw_input('Do you want to unfollow those who do not follow you currently? [Y/N]: ')

    if (isitmutual == 'y' or 'Y'):
            followers = api.followers_ids(user_handle)
            friends = api.friends_ids(user_handle)
            for f in friends:
                if f not in followers:
                    print "Unfollow {0}?".format(api.get_user(f).screen_name)
                    if raw_input("Y/N?") == 'y' or 'Y':
                        api.destroy_friendship(f)
    else:
        menu()
# This is the menu
def menu():
     ans=True
     while ans:
            print("""
            1. Post status.
            2. Favoriting.
            3. Hashtag follower.
            4. List followers/unfollow.
            5. Basic mention repeater.
            6. Exit operation.
            """)
            ans=raw_input("What would you like to do? [1-6]: ")
            if ans=="1":
                print("\n Post status.")
                tweeter()
            elif ans=="2":
                print("\n Turn favoriting on.")
                hashtag=raw_input('\n Hashtag? :')
                # This part needs to be programmed.
                menu()
            elif ans=="3":
                print("\n Turn hashtag follow on.")
            elif ans=="4":
                list()
            elif ans=="5":
                # This part needs to run repeater.py
                menu()
            elif ans=="6":
                print("\n Exiting...")
                ans = None
            else:
                print("\n Not a bot command.")
    
user_handle = raw_input('What is your Twitter handle?\n')
if len(user_handle) < 1:
    print(' Invalid username. Aborting...')
else:
    menu()