# -*- coding: utf-8 -*-
from __future__ import print_function
from twitter import Twitter, OAuth, TwitterHTTPError
import os
import sys
import time
import random
import mysql.connector
from mysql.connector import errorcode
import json
import threading

# TWITTER BOT
class TwitterBot(object):
    def __init__(self, config_file=str(os.path.dirname(os.path.realpath(__file__)) + "/OAUTH.txt")):
        # this variable contains the configuration for the bot
        self.BOT_CONFIG = {}

        # this variable contains the authorized connection to the Twitter API
        self.TWITTER_CONNECTION = None

        self.bot_setup(config_file)

        # Used for random timers
        random.seed()

    def wait_on_action(self):
        min_time = 0
        max_time = 0
        if "FOLLOW_BACKOFF_MIN_SECONDS" in self.BOT_CONFIG:
            min_time = int(self.BOT_CONFIG["FOLLOW_BACKOFF_MIN_SECONDS"])

        if "FOLLOW_BACKOFF_MAX_SECONDS" in self.BOT_CONFIG:
            max_time = int(self.BOT_CONFIG["FOLLOW_BACKOFF_MAX_SECONDS"])

        if min_time > max_time:
            temp = min_time
            min_time = max_time
            max_time = temp

        wait_time = random.randint(min_time, max_time)

        if wait_time > 0:
            print("Choosing time between %d and %d - waiting %d seconds before action" % (min_time, max_time, wait_time))
            time.sleep(wait_time)

        return wait_time

    def bot_setup(self, config_file=str(os.path.dirname(os.path.realpath(__file__)) + "/OAUTH.txt")):

        with open(config_file, "r") as in_file:
            for line in in_file:
                line = line.split(":")
                parameter = line[0].strip()
                value = line[1].strip()

                if parameter in ["USERS_KEEP_FOLLOWING", "USERS_KEEP_UNMUTED", "USERS_KEEP_MUTED"]:
                    if value != "":
                        self.BOT_CONFIG[parameter] = set([int(x) for x in value.split(",")])
                    else:
                        self.BOT_CONFIG[parameter] = set()
                elif parameter in ["FOLLOW_BACKOFF_MIN_SECONDS", "FOLLOW_BACKOFF_MAX_SECONDS"]:
                    self.BOT_CONFIG[parameter] = int(value)
                else:
                    self.BOT_CONFIG[parameter] = value

        # make sure that the config file specifies all required parameters
        required_parameters = ["OAUTH_TOKEN", "OAUTH_SECRET", "CONSUMER_KEY",
                               "CONSUMER_SECRET", "TWITTER_HANDLE",
                               "ALREADY_FOLLOWED_FILE",
                               "FOLLOWERS_FILE", "FOLLOWS_FILE"]

        missing_parameters = []

        for required_parameter in required_parameters:
            if (required_parameter not in self.BOT_CONFIG or
                    self.BOT_CONFIG[required_parameter] == ""):
                missing_parameters.append(required_parameter)

        if len(missing_parameters) > 0:
            self.BOT_CONFIG = {}
            raise Exception("Please edit %s to include the following parameters: %s.\n\n"
                            "The bot cannot run unless these parameters are specified."
                            % (config_file, ", ".join(missing_parameters)))

        # make sure all of the sync files exist locally
        for sync_file in [self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"],
                          self.BOT_CONFIG["FOLLOWS_FILE"],
                          self.BOT_CONFIG["FOLLOWERS_FILE"]]:
            if not os.path.isfile(sync_file):
                with open(sync_file, "w") as out_file:
                    out_file.write("")

        # check how old the follower sync files are and recommend updating them
        # if they are old
        if (time.time() - os.path.getmtime(self.BOT_CONFIG["FOLLOWS_FILE"]) > 86400 or
                time.time() - os.path.getmtime(self.BOT_CONFIG["FOLLOWERS_FILE"]) > 86400):
            print("Warning: Your Twitter follower sync files are more than a day old. "
                  "Run a command to sync the followers list.", file=sys.stderr)

        # create an authorized connection to the Twitter API
        self.TWITTER_CONNECTION = Twitter(auth=OAuth(self.BOT_CONFIG["OAUTH_TOKEN"],
                                                     self.BOT_CONFIG["OAUTH_SECRET"],
                                                     self.BOT_CONFIG["CONSUMER_KEY"],
                                                     self.BOT_CONFIG["CONSUMER_SECRET"]))

    def sync_follows(self):
        """
            Syncs the user's followers and follows locally so it isn't necessary
            to repeatedly look them up via the Twitter API.

            It is important to run this method at least daily so the bot is working
            with a relatively up-to-date version of the user's follows.

            Do not run this method too often, however, or it will quickly cause your
            bot to get rate limited by the Twitter API.
        """

        # sync the user's followers (accounts following the user)
        followers_status = self.TWITTER_CONNECTION.followers.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])
        followers = set(followers_status["ids"])
        next_cursor = followers_status["next_cursor"]

        with open(self.BOT_CONFIG["FOLLOWERS_FILE"], "w") as out_file:
            for follower in followers:
                out_file.write("%s\n" % (follower))

        while next_cursor != 0:
            followers_status = self.TWITTER_CONNECTION.followers.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"],
                                                                     cursor=next_cursor)
            followers = set(followers_status["ids"])
            next_cursor = followers_status["next_cursor"]

            with open(self.BOT_CONFIG["FOLLOWERS_FILE"], "a") as out_file:
                for follower in followers:
                    out_file.write("%s\n" % (follower))

        # sync the user's follows (accounts the user is following)
        following_status = self.TWITTER_CONNECTION.friends.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])
        following = set(following_status["ids"])
        next_cursor = following_status["next_cursor"]

        with open(self.BOT_CONFIG["FOLLOWS_FILE"], "w") as out_file:
            for follow in following:
                out_file.write("%s\n" % (follow))

        while next_cursor != 0:
            following_status = self.TWITTER_CONNECTION.friends.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"],
                                                                   cursor=next_cursor)
            following = set(following_status["ids"])
            next_cursor = following_status["next_cursor"]

            with open(self.BOT_CONFIG["FOLLOWS_FILE"], "a") as out_file:
                for follow in following:
                    out_file.write("%s\n" % (follow))

    def get_do_not_follow_list(self):
        """
            Returns the set of users the bot has already followed in the past.
        """

        dnf_list = []
        with open(self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"], "r") as in_file:
            for line in in_file:
                dnf_list.append(int(line))

        return set(dnf_list)

    def get_followers_list(self):
        """
            Returns the set of users that are currently following the user.
        """

        followers_list = []
        with open(self.BOT_CONFIG["FOLLOWERS_FILE"], "r") as in_file:
            for line in in_file:
                followers_list.append(int(line))

        return set(followers_list)

    def get_follows_list(self):
        """
            Returns the set of users that the user is currently following.
        """

        follows_list = []
        with open(self.BOT_CONFIG["FOLLOWS_FILE"], "r") as in_file:
            for line in in_file:
                follows_list.append(int(line))

        return set(follows_list)

    def search_tweets(self, phrase, count=100, result_type="recent"):
        """
            Returns a list of tweets matching a phrase (hashtag, word, etc.).
        """

        return self.TWITTER_CONNECTION.search.tweets(q=phrase, result_type=result_type, count=count)

    def auto_fav(self, phrase, favcount, result_type="recent"):
        """
            Favorites tweets that match a phrase (hashtag, word, etc.).
        """

        result = self.search_tweets(phrase, favcount, result_type)

        for tweet in result["statuses"]:
            try:
                # don't favorite your own tweets
                if tweet["user"]["screen_name"] == self.BOT_CONFIG["TWITTER_HANDLE"]:
                    continue

                result = self.TWITTER_CONNECTION.favorites.create(_id=tweet["id"])
                print("Favorited: %s" % (result["text"].encode("utf-8")), file=sys.stdout)

            # when you have already favorited a tweet, this error is thrown
            except TwitterHTTPError as api_error:
                # quit on rate limit errors
                if "rate limit" in str(api_error).lower():
                    print("You have been rate limited. "
                          "Wait a while before running the bot again.", file=sys.stderr)
                    return

                if "you have already favorited this status" not in str(api_error).lower():
                    print("Error: %s" % (str(api_error)), file=sys.stderr)

    def auto_rt(self, phrase, rtcount, result_type="recent"):
        """
            Retweets tweets that match a phrase (hashtag, word, etc.).
        """

        result = self.search_tweets(phrase, rtcount, result_type)

        for tweet in result["statuses"]:
            try:
                # don't retweet your own tweets
                if tweet["user"]["screen_name"] == self.BOT_CONFIG["TWITTER_HANDLE"]:
                    continue

                result = self.TWITTER_CONNECTION.statuses.retweet(id=tweet["id"])
                print("Retweeted: %s" % (result["text"].encode("utf-8")), file=sys.stdout)

            # when you have already retweeted a tweet, this error is thrown
            except TwitterHTTPError as api_error:
                # quit on rate limit errors
                if "rate limit" in str(api_error).lower():
                    print("You have been rate limited. "
                          "Wait a while before running the bot again.", file=sys.stderr)
                    return

                print("Error: %s" % (str(api_error)), file=sys.stderr)

    def auto_follow(self, phrase, hashcount, result_type="recent"):
        """
            Follows anyone who tweets about a phrase (hashtag, word, etc.).
        """

        result = self.search_tweets(phrase, hashcount, result_type)
        following = self.get_follows_list()
        do_not_follow = self.get_do_not_follow_list()

        for tweet in result["statuses"]:
            try:
                if (tweet["user"]["screen_name"] != self.BOT_CONFIG["TWITTER_HANDLE"] and
                        tweet["user"]["id"] not in following and
                        tweet["user"]["id"] not in do_not_follow):

                    self.wait_on_action()

                    self.TWITTER_CONNECTION.friendships.create(user_id=tweet["user"]["id"], follow=False)
                    following.update(set([tweet["user"]["id"]]))

                    print("Followed %s" %
                          (tweet["user"]["screen_name"]), file=sys.stdout)

            except TwitterHTTPError as api_error:
                # quit on rate limit errors
                if "unable to follow more people at this time" in str(api_error).lower():
                    print("You are unable to follow more people at this time. "
                          "Wait a while before running the bot again or gain "
                          "more followers.", file=sys.stderr)
                    return

                # don't print "already requested to follow" errors - they're
                # frequent
                if "already requested to follow" not in str(api_error).lower():
                    print("Error: %s" % (str(api_error)), file=sys.stderr)

    def auto_follow_followers(self,count=None):
        """
            Follows back everyone who has followed you.
        """

        following = self.get_follows_list()
        followers = self.get_followers_list()

        not_following_back = followers - following
        not_following_back = list(not_following_back)[:count]
        for user_id in not_following_back:
            try:
                self.wait_on_action()

                self.TWITTER_CONNECTION.friendships.create(user_id=user_id, follow=False)
            except TwitterHTTPError as api_error:
                # quit on rate limit errors
                if "unable to follow more people at this time" in str(api_error).lower():
                    print("You are unable to follow more people at this time. "
                          "Wait a while before running the bot again or gain "
                          "more followers.", file=sys.stderr)
                    return

                # don't print "already requested to follow" errors - they're frequent
                if "already requested to follow" not in str(api_error).lower():
                    print("Error: %s" % (str(api_error)), file=sys.stderr)

    def auto_follow_followers_of_user(self, user_twitter_handle, count=100):
        """
            Follows the followers of a specified user.
        """

        following = self.get_follows_list()
        followers_of_user = set(self.TWITTER_CONNECTION.followers.ids(screen_name=user_twitter_handle)["ids"][:count])
        do_not_follow = self.get_do_not_follow_list()

        for user_id in followers_of_user:
            try:
                if (user_id not in following and
                        user_id not in do_not_follow):

                    self.wait_on_action()

                    self.TWITTER_CONNECTION.friendships.create(user_id=user_id, follow=False)
                    print("Followed %s" % user_id, file=sys.stdout)

            except TwitterHTTPError as api_error:
                # quit on rate limit errors
                if "unable to follow more people at this time" in str(api_error).lower():
                    print("You are unable to follow more people at this time. "
                          "Wait a while before running the bot again or gain "
                          "more followers.", file=sys.stderr)
                    return

                # don't print "already requested to follow" errors - they're
                # frequent
                if "already requested to follow" not in str(api_error).lower():
                    print("Error: %s" % (str(api_error)), file=sys.stderr)

    def auto_unfollow_nonfollowers(self,count=None):
        """
            Unfollows everyone who hasn't followed you back.
        """

        following = self.get_follows_list()
        followers = self.get_followers_list()

        not_following_back = following - followers
        not_following_back = list(not_following_back)[:count]
        # update the "already followed" file with users who didn't follow back
        already_followed = set(not_following_back)
        already_followed_list = []
        with open(self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"], "r") as in_file:
            for line in in_file:
                already_followed_list.append(int(line))

        already_followed.update(set(already_followed_list))

        with open(self.BOT_CONFIG["ALREADY_FOLLOWED_FILE"], "w") as out_file:
            for val in already_followed:
                out_file.write(str(val) + "\n")

        for user_id in not_following_back:
            if user_id not in self.BOT_CONFIG["USERS_KEEP_FOLLOWING"]:

                self.wait_on_action()

                self.TWITTER_CONNECTION.friendships.destroy(user_id=user_id)
                print("Unfollowed %d" % (user_id), file=sys.stdout)

    def auto_unfollow_all_followers(self,count=None):
        """
            Unfollows everyone that you are following(except those who you have specified not to)
        """
        following = self.get_follows_list()

        for user_id in following:
            if user_id not in self.BOT_CONFIG["USERS_KEEP_FOLLOWING"]:

                self.wait_on_action()

                self.TWITTER_CONNECTION.friendships.destroy(user_id=user_id)
                print("Unfollowed %d" % (user_id), file=sys.stdout)

    def auto_mute_following(self):
        """
            Mutes everyone that you are following.
        """

        following = self.get_follows_list()
        muted = set(self.TWITTER_CONNECTION.mutes.users.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])["ids"])

        not_muted = following - muted

        for user_id in not_muted:
            if user_id not in self.BOT_CONFIG["USERS_KEEP_UNMUTED"]:
                self.TWITTER_CONNECTION.mutes.users.create(user_id=user_id)
                print("Muted %d" % (user_id), file=sys.stdout)

    def auto_unmute(self):
        """
            Unmutes everyone that you have muted.
        """

        muted = set(self.TWITTER_CONNECTION.mutes.users.ids(screen_name=self.BOT_CONFIG["TWITTER_HANDLE"])["ids"])

        for user_id in muted:
            if user_id not in self.BOT_CONFIG["USERS_KEEP_MUTED"]:
                self.TWITTER_CONNECTION.mutes.users.destroy(user_id=user_id)
                print("Unmuted %d" % (user_id), file=sys.stdout)

    def send_tweet(self):
        message = raw_input("     What is your tweet?: ")
        return self.TWITTER_CONNECTION.statuses.update(status=message)
    
    def mine(self):
        WORLD_WOE_ID = 1
        US_WOE_ID = 23424977
        q = raw_input("     What hashtag or phrase would you like to run algorithms on?: ")
        count = 100000
        # See https://dev.twitter.com/docs/api/1.1/get/search/tweets
        search_results = self.TWITTER_CONNECTION.search.tweets(q=q, count=count)
        statuses = search_results['statuses']
        # Iterate through 5 more batches of results by following the cursor
        for _ in range(100):
            print('Length of statuses'), len(statuses)
            try:
                next_results = search_results['search_metadata']['next_results']
            except KeyError, e: # No more results when next_results doesn't exist
                break
        # Create a dictionary from next_results, which has the following form:
        # ?max_id=313519052523986943&q=NCAA&include_entities=1
        kwargs = dict([ kv.split('=') for kv in next_results[1:].split("&") ])
        search_results = self.TWITTER_CONNECTION.search.tweets(**kwargs)
        statuses += search_results['statuses']
        # Show one sample search result by slicing the list...
        print(json.dumps(statuses[0], indent=1))
        status_texts = [ status['text']
        for status in statuses ]
        screen_names = [ user_mention['screen_name']
        for status in statuses
        for user_mention in status['entities']['user_mentions'] ]
        hashtags = [ hashtag['text']
        for status in statuses
        for hashtag in status['entities']['hashtags'] ]
        # Compute a collection of all words from all tweets
        words = [ w
        for t in status_texts
        for w in t.split() ]
        # Explore the first 5 items for each...
        print(json.dumps(status_texts[0:100], indent=1))
        print(json.dumps(screen_names[0:100], indent=1))
        print(json.dumps(hashtags[0:100], indent=1))
        print(json.dumps(words[0:100], indent=1))
        
        from collections import Counter
        for item in [words, screen_names, hashtags]:
            c = Counter(item)
            print(c.most_common()[:10]) # top 10
            print
        from prettytable import PrettyTable
        for label, data in (('Word', words),
                ('Screen Name', screen_names),
                ('Hashtag', hashtags)):
            pt = PrettyTable(field_names=[label, 'Count'])
            c = Counter(data)
            [ pt.add_row(kv) for kv in c.most_common()[:10] ]
            pt.align[label], pt.align['Count'] = 'l', 'r' # Set column alignment
            print(pt)
        retweets = [
        # Store out a tuple of these three values ...
        (status['retweet_count'],
        status['retweeted_status']['user']['screen_name'],
        status['text'])
        # ... for each status ...
        for status in statuses
        # ... so long as the status meets this condition.
        if status.has_key('retweeted_status')
        ]
        # Slice off the first 5 from the sorted results and display each item in the tuple
        pt = PrettyTable(field_names=['Count', 'Screen Name', 'Text'])
        [ pt.add_row(row) for row in sorted(retweets, reverse=True)[:5] ]
        pt.max_width['Text'] = 50
        pt.align= 'l'
        print(pt)
        # Using underscores while unpacking values in
        # a tuple is idiomatic for discarding them
        counts = [count for count, _, _ in retweets]
    
        print(counts)
        
# MENU CLASS  
class menu():
    # This is the menu
    def Menu(self):
        while True:
                print("""
                1. Post status.
                2. Favoriting.
                3. Hashtag follower.
                4. List followers/unfollow.
                5. Basic mention repeater.
                6. Data Mine.
                7. Exit operation.
                """)
                ans=raw_input("     What would you like to do? [1-7]: ")
                if ans=="1":
                    print("\n Post status.")
                    my_bot = TwitterBot()
                    my_bot.send_tweet()
                elif ans=="2":
                    print("\n Turn favoriting on.")
                    favterm = raw_input("     What is the favoriting term?: ")
                    favcount = raw_input("     How many posts?: ")
                    bot = TwitterBot()
                    bot.auto_fav(favterm,int(favcount))
                elif ans=="3":
                    print("\n Turn hashtag follow on.")
                    hashtag = raw_input("     What is the phrase or hashtag you want to follow based on?: ")
                    hashcount = raw_input("     How many posts?: ")
                    bot = TwitterBot()
                    bot.auto_follow(hashtag,int(hashcount))
                elif ans=="4":
                    print("\n Printing follower IDs:")
                    bot = TwitterBot()
                    bot.sync_follows()
                    followers = bot.get_followers_list()
                    print(followers)
                    opt = raw_input("     Unfollow those who do not follow back? [Y/N]: ")
                    if opt == ("Y" or "y"):
                        bot = TwitterBot()
                        bot.auto_unfollow_nonfollowers()
                elif ans=="5":
                    print("\n Turn auto-retweet on.")
                    hashphrase = raw_input("     What is the phrase or hashtag you want to retweet based on?: ")
                    rtcount = raw_input("     How many posts?: ")
                    bot = TwitterBot()
                    bot.auto_rt(hashphrase,int(rtcount))
                elif ans=="6":
                    inst = TwitterBot()
                    bot = threading.Thread(target=inst.mine())
                    bot.start()
                    bot.join()
                elif ans=="7":
                    print("\n Exiting...")
                    sys.exit()
                else:
                    print("\n Not a bot command.")
                    
# DRM & INITIALIZATION BLOCK
print("\n     Snakey Login (v. 1.0.4)")
username = raw_input("     User: ")
password = raw_input("     Password: ")
drm = mysql.connector.connect(user='', password='',
                          host='',
                          database='')
try:
    cursor = drm.cursor(buffered=True)
    query0 = ("SELECT " + username + " FROM Users ")
    query1 = ("SELECT `" + password + "` FROM Passwords ")
    cursor.execute(query0)
    cursor.execute(query1)
    sync = TwitterBot()
    sync.sync_follows()
    cursor.close()
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_BAD_FIELD_ERROR:
        print("\n Incorrect username and/or password.")
        cursor.close()
        time.sleep(1)
        sys.exit()
    else:
        print(err)
print ("\n Connection Established.\n")
time.sleep(1)
menuinit = menu()
menuinit.Menu()