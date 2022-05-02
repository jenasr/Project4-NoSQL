#! /usr/bin/env python3
import sqlite3
import redis
import uuid

def make_top_10s(view_dec):
    sqlite3.register_converter('GUID', lambda b: uuid.UUID(bytes_le=b))
    sqlite3.register_adapter(uuid.UUID, lambda u: memoryview(u.bytes_le))
    con = sqlite3.connect("DB/Shards/stats1.db", detect_types=sqlite3.PARSE_DECLTYPES)
    db = con.cursor()
    db.execute("ATTACH DATABASE 'DB/Shards/user_profiles.db' As 'up'")
    db.execute("ATTACH DATABASE 'DB/Shards/stats2.db' As 's2'")
    db.execute("ATTACH DATABASE 'DB/Shards/stats3.db' AS 's3'")
    if view_dec == "wins":
        column = "number_won"
    else:
        column = "streak"

    cur = db.execute(f"SELECT username, {column} FROM {view_dec} JOIN up.users ON {view_dec}.unique_id=up.users.unique_id ORDER BY {column} DESC LIMIT 10")
    looking_for = cur.fetchall()
    cur = db.execute(f"SELECT username, {column} FROM s2.{view_dec} JOIN up.users ON s2.{view_dec}.unique_id=up.users.unique_id ORDER BY {column} DESC LIMIT 10")
    looking_for += cur.fetchall()
    cur = db.execute(f"SELECT username, {column} FROM s3.{view_dec} JOIN up.users ON s3.{view_dec}.unique_id=up.users.unique_id ORDER BY {column} DESC LIMIT 10")
    looking_for += cur.fetchall()
    #looking_for.sort(key = lambda x: x[1])

    r = redis.Redis(host='localhost', port=6379, db=0)
    set_key = f"Top 10 {view_dec}"
    p = r.pipeline()
    p.multi()
    for index, tup in enumerate(looking_for):
        r.zrem(set_key, tup[0])
        r.zadd(set_key, tup[1], tup[0])
    p.execute()









if __name__ == '__main__':
    make_top_10s("wins")
    make_top_10s("streaks")