import datetime
import random

from google.appengine.api import memcache
from google.appengine.ext import db


def from_milliseconds(millis):
    return datetime.datetime.utcfromtimestamp(millis / 1000)


def to_milliseconds(date_time):
    delta = date_time - from_milliseconds(0)
    return int(round(delta.total_seconds() * 1000))


class ShardedCounterConfig(db.Expando):
    """
    Represents the sharded counter config, that helps us figure out how many shards to use for a sharded counter
    __key__ == name property in ShardedCounter
    """
    name = db.StringProperty(required=True)
    shards = db.IntegerProperty(default=1)

    @classmethod
    def cache_key(cls, name):
        return 'shard_config_' + name

    @classmethod
    def get_sharded_config(cls, name):
        cache_key = ShardedCounterConfig.cache_key(name)
        config = memcache.get(cache_key)
        if not config:
            ''' Try fetching from datastore '''
            config = ShardedCounterConfig.get_or_insert(name, name=name, shards=20)
            memcache.set(cache_key, config, time=86400)
        return config


class CrashReport(db.Expando):
    """
    Represents an Crash Report item
    """
    name = db.StringProperty(required=True)  # key_name and not the sharded key name
    crash = db.TextProperty(required=True)
    fingerprint = db.StringProperty(required=True)
    date_time = db.DateTimeProperty(required=True, default=datetime.datetime.utcnow())
    count = db.IntegerProperty(default=0)

    @classmethod
    def get_count(cls, name):
        total = memcache.get(name)
        if total is None:
            total = 0
            q = CrashReport.all()
            q.filter('name = ', name)
            for counter in q.run():
                total += counter.count
            memcache.set(name, str(total))
        ''' total can be a string (when cached) '''
        return int(total)

    @classmethod
    def add_or_remove(cls, fingerprint, crash, is_add=True, delta=1):
        key_name = CrashReport.key_name(fingerprint)
        config = ShardedCounterConfig.get_sharded_config(key_name)
        shards = config.shards
        shard_to_use = random.randint(0, shards-1)
        shard_key_name = key_name + '_' + str(shard_to_use)
        crash_report = CrashReport.get_or_insert(shard_key_name, name=key_name, crash=crash, fingerprint=fingerprint)
        if is_add:
            crash_report.count += delta
            crash_report.put()
            memcache.incr(key_name, delta, initial_value=0)
        else:
            crash_report.count -= delta
            crash_report.put()
            memcache.decr(key_name, delta)
        return crash_report

    @classmethod
    def get_crash(cls, fingerprint):
        q = CrashReport.all()
        q.filter('name =', CrashReport.key_name(fingerprint))
        crash_report = q.get()
        if not crash_report:
            return None
        else:
            return crash_report

    @classmethod
    def key_name(cls, name):
        return cls.kind() + '_' + name

    @classmethod
    def to_json(cls, entity):
        return {
            'key': entity.key(),
            'crash': entity.crash,
            'fingerprint': entity.fingerprint,
            'time': to_milliseconds(entity.date_time),  # in millis
            'count': cls.get_count(entity.name)
        }


class Link(object):
    """
    Represents a link (essentially contains the url, title and active properties).
    """
    def __init__(self, title, url, active=False):
        self.title = title
        self.url = url
        self.active = active
