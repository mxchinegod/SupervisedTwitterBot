import twitter
import json
import matplotlib.pyplot as plt

CONSUMER_KEY = 'z5sFXnNIoDT9MVxDQzogHcCNG'
CONSUMER_SECRET = '9KBOGBi3mZ0eCgoWlO9E8N5L9BZcddVhVf9rgFADF68vObp0dy'
OAUTH_TOKEN = '171555247-XIn2NWBmTnXcTmLrfIMFubUWyvPbaW1XDnOV0065'
OAUTH_TOKEN_SECRET = 'xim5xw8z4iKiV1PZjbm5K6G2xPqqNK7c2acvHBQUOyTg9'

auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                           CONSUMER_KEY, CONSUMER_SECRET)

twitter_api = twitter.Twitter(auth=auth)

print twitter_api

# Nothing to see by displaying twitter_api except that it's now a
# defined variable

#The Yahoo! Where on Earth ID for the entire globe is 1.

WORLD_WOE_ID = 1
US_WOE_ID = 23424977

# XXX: Set this variable to a trending topic,
# or anything else for that matter. The example query below
# was a trending topic when this content was being developed
# and is used throughout the remainder of this chapter.
q = '#Baltimore'
count = 100000
# See https://dev.twitter.com/docs/api/1.1/get/search/tweets
search_results = twitter_api.search.tweets(q=q, count=count)
statuses = search_results['statuses']
# Iterate through 5 more batches of results by following the cursor
for _ in range(100):
    print "Length of statuses", len(statuses)
    try:
        next_results = search_results['search_metadata']['next_results']
    except KeyError, e: # No more results when next_results doesn't exist
        break
# Create a dictionary from next_results, which has the following form:
# ?max_id=313519052523986943&q=NCAA&include_entities=1
kwargs = dict([ kv.split('=') for kv in next_results[1:].split("&") ])
search_results = twitter_api.search.tweets(**kwargs)
statuses += search_results['statuses']
# Show one sample search result by slicing the list...
print json.dumps(statuses[0], indent=1)

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
print json.dumps(status_texts[0:100], indent=1)
print json.dumps(screen_names[0:100], indent=1)
print json.dumps(hashtags[0:100], indent=1)
print json.dumps(words[0:100], indent=1)

from collections import Counter
for item in [words, screen_names, hashtags]:
    c = Counter(item)
    print c.most_common()[:10] # top 10
    print
from prettytable import PrettyTable
for label, data in (('Word', words),
        ('Screen Name', screen_names),
        ('Hashtag', hashtags)):
    pt = PrettyTable(field_names=[label, 'Count'])
    c = Counter(data)
    [ pt.add_row(kv) for kv in c.most_common()[:10] ]
    pt.align[label], pt.align['Count'] = 'l', 'r' # Set column alignment
    print pt
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
print pt

word_counts = sorted(Counter(words).values(), reverse=True)

plt.loglog(word_counts)
plt.ylabel("Freq")
plt.xlabel("Word Rank")
plt.show()
for label, data in (('Words', words),
                    ('Screen Names', screen_names),
                    ('Hashtags', hashtags)):
                    
    # Build a frequency map for each set of data
    # and plot the values
    c = Counter(data)
    plt.hist(c.values())
    
    # Add a title and y-label ...
    plt.title(label)
    plt.ylabel("Number of items in bin")
    plt.xlabel("Bins (number of times an item appeared)")
    
    # ... and display as a new figure
    plt.figure()

# Using underscores while unpacking values in
# a tuple is idiomatic for discarding them
counts = [count for count, _, _ in retweets]

plt.hist(counts)
plt.title("Retweets")
plt.xlabel('Bins (number of times retweeted)')
plt.ylabel('Number of tweets in bin')
plt.show()
print counts