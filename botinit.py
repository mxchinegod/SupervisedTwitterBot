#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import tweepy, time, sys
 
# This is initialization for Twitter OAUTH
CONSUMER_KEY = ''#keep the quotes, replace this with your consumer key
CONSUMER_SECRET = ''#keep the quotes, replace this with your consumer secret key
ACCESS_KEY = ''#keep the quotes, replace this with your access token
ACCESS_SECRET = ''#keep the quotes, replace this with your access token secret
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# This is the tweeting module
def tweeter():
    tweet = raw_input('What would you like to tweet?\n')
    if len(tweet) > 140:
        print('It\'s over 140 characters...')
    else:
        print('\n Tweet live.')
        api.update_status(status=tweet)
        time.sleep(.5)
  
# This is the service for a favoriting job that occurs 2 times a day.
def favoriter():
    favstr = raw_input('Favorite based on which hashtag or mention?\n')
    

# This is the list of favorites and the option to remove those that aren't favoriting back.
def list():
    n = 0
    for user in tweepy.Cursor(api.followers, screen_name="The_LazySC").items():
        n += 1
        print user.screen_name
        int(n)
    print('\n'), n, ('followers.\n')
    time.sleep(1)
    # Mutual destruction
    isitmutual = raw_input('Do you want to unfollow those who do not follow you currently? [Y/N]: ')
    if (isitmutual == 'y' or 'Y'):
            followers = api.followers_ids("The_LazySC")
            friends = api.friends_ids("The_LazySC")
            for f in friends:
                if f not in followers:
                    print "Unfollow {0}?".format(api.get_user(f).screen_name)
                    if raw_input("Y/N?") == 'y' or 'Y':
                        api.destroy_friendship(f)
        
# This is the menu
ans=True
while ans:
    print("""
    1. Post status.
    2. Favoriting..
    3. Hashtag/Mention follower.
    4. List followers/unfollow.
    5. Exit operation.
    """)
    ans=raw_input("What would you like to do? [1-5]: ")
    if ans=="1":
      print("\n Post status.")
      tweeter()
    elif ans=="2":
      print("\n Turn favoriting on.")
      favoriter()
    elif ans=="3":
      print("\n Turn hashtag follow on.")
    elif ans=="4":
      list()
    elif ans=="5":
        print("\n Exiting...")
        ans = None
    else:
       print("\n Not a bot command.")
