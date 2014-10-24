#!/usr/bin/python
"""
Print filtered Twitter messages in real-time.

Usage:
    python get_twitter_data.py [config.json]

See:
  - config.json.sample for a sample config.json file
  - https://dev.twitter.com/apps/ generates parameters for "api" parameters
  - https://dev.twitter.com/docs/api/1.1/post/statuses/filter for "search"
"""

import sys
import os
import json
import twitter
import time
import shutil

ts = 0


def getApi(params):
    api = twitter.Api(
        params['api']['consumer_key'],
        params['api']['consumer_secret'],
        params['api']['access_token_key'],
        params['api']['access_token_secret'])
    return api


def verify(api):
    cred = api.VerifyCredentials()
    print "Verifying: "
    print cred


def postTweet(api, tweet):
    api.PostUpdate(tweet)


def getUserTweet(api, user, cnt, since):
    statuses = api.GetUserTimeline(screen_name=user, count=cnt, since_id=since)
    return statuses


def getUserTimelineTweet(api, cnt, since):
    statuses = api.GetHomeTimeline(count=cnt, since_id=since)
    return statuses


def getListTweet(api, lst_id, cnt, since):
    statuses = api.GetListTimeline(lst_id, None, count=cnt, since_id=since)
    return statuses


def writeTweetsToFile(tweets, filep, max_cnt):
    fileps = filep + '.twt'
    filepd = filep + '_detailed.twtj'
    fileps_arc = fileps + '_' + str(ts)
    filepd_arc = filepd + '_' + str(ts)

    if not os.path.exists(fileps):
        open(fileps, 'w').close()
    if not os.path.exists(filepd):
        open(filepd, 'w').close()

    moveFile(fileps, fileps_arc)
    moveFile(filepd, filepd_arc)

    fs = open(fileps, 'a')
    fd = open(filepd, 'a')

    for tweet in tweets:
        max_cnt = tweet.id
        break

    for tweet in tweets:
        fs.write('@')
        fs.write(tweet.user.screen_name)
        fs.write(': TYP: ')
        fs.write(tweet.text.encode('utf-8').strip())
        fs.write('\n\n')

        fd.write(tweet.AsJsonString())
        fd.write('\n')

    # Here Copy the file
    fsa = open(fileps_arc, 'r')
    fda = open(filepd_arc, 'r')
    for line in fsa:
        fs.write(line)
    for line in fda:
        fd.write(line)

    fs.close
    fd.close
    fsa.close
    fda.close

    os.remove(fileps_arc)
    os.remove(filepd_arc)

    return max_cnt


def getLists(api, user, list_cnt):
    return api.GetLists(screen_name=user, count=list_cnt)


def grabStoreListTweets(api, params):
    dirs = params['list_tweet']['dir']
    user = params['list_tweet']['user']
    list_cnt = params['list_tweet']['list_cnt']
    count = params['list_tweet']['count']

    twt_cfg_file = params['tweet_history']
    twt_cfg = json.load(open(twt_cfg_file))

    lists = getLists(api, user, list_cnt)

    for lst in lists:
        lst_name = lst.name
        lst_id = lst.id
        since = 0
        if twt_cfg['list_tweet'].get(lst_name):
            since = long(twt_cfg['list_tweet'].get(lst_name))

        print "Getting tweets for list... " + lst_name + " since: " + str(since)

        tweets = getListTweet(api, lst_id, count, since)
        filep = dirs + lst_name
        since = writeTweetsToFile(tweets, filep, since)
        twt_cfg['list_tweet'][lst_name] = since

    twt_cfg_hd = open(twt_cfg_file, 'w')
    json.dump(twt_cfg, twt_cfg_hd, indent=True)
    twt_cfg_hd.close


def grabStoreUsersTweets(api, params):
    dirs = params['user_tweet']['dir']
    users = params['user_tweet']['users']
    count = params['user_tweet']['count']

    twt_cfg_file = params['tweet_history']
    twt_cfg = json.load(open(twt_cfg_file))

    for user in users:
        since = 0
        if twt_cfg['user_tweet'].get(user):
            since = long(twt_cfg['user_tweet'].get(user))

        print "Getting tweets for user ... " + user + " since: " + str(since)

        tweets = getUserTweet(api, user, count, since)
        filep = dirs + user
        since = writeTweetsToFile(tweets, filep, since)
        twt_cfg['user_tweet'][user] = since

    twt_cfg_hd = open(twt_cfg_file, 'w')
    json.dump(twt_cfg, twt_cfg_hd, indent=True)
    twt_cfg_hd.close


def grabStoreUsersTimelineTweets(api, params):
    dirs = params['user_timeline']['dir']
    user = params['user_timeline']['user']
    count = params['user_timeline']['count']

    twt_cfg_file = params['tweet_history']
    twt_cfg = json.load(open(twt_cfg_file))

    since = 0
    if twt_cfg['user_timeline'].get(user):
        since = long(twt_cfg['user_timeline'].get(user))

    print "Getting tweets timeline for .. " + user + " since: " + str(since)

    filep = dirs + user

    tweets = getUserTimelineTweet(api, count, since)
    since = writeTweetsToFile(tweets, filep, since)
    twt_cfg['user_timeline'][user] = since

    twt_cfg_hd = open(twt_cfg_file, 'w')
    json.dump(twt_cfg, twt_cfg_hd, indent=True)
    twt_cfg_hd.close


def search(api, params):
    print "Searching ..."
    # users = params['user']
    # for user in users:
    #     print "User: " + user
    # print users
    grabStoreUsersTweets(api, params)
    exit(1)

    user = "narendramodi"
    # user="sanand0"
    # user="ShridharSattur"
    statuses = getUserTweet(api, user, 300)
    print statuses
    exit(1)
    # print [s.text for s in statuses]
    print [s.AsJsonString() for s in statuses]

    exit(1)

    r = api.request('statuses/filter', params['search'])
    out = open(params['save_tweets'], 'ab')
    for item in r.get_iterator():
        json.dump(item, out, separators=(',', ':'))
        out.write('\n')
        out.flush()


def moveFile(srcd, dstd):
    shutil.move(srcd, dstd)


if __name__ == '__main__':
    config_file = 'config.json'

    if len(sys.argv) > 2:
        print __doc__.strip()
        sys.exit(0)
    else:
        if len(sys.argv) == 2:
            config_file = sys.argv[1]

    ts = int(time.time())
    print "Reading config file: " + config_file + " timestamp: " + str(ts)

    params = json.load(open(config_file))
    api = getApi(params)
    grabStoreListTweets(api, params)
    grabStoreUsersTimelineTweets(api, params)
    grabStoreUsersTweets(api, params)

    # postTweet(api, "Tweeting .... ")
