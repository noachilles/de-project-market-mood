import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# SET
r.set("test:price:005930", 75000)

# GET
price = r.get("test:price:005930")

print("Redis GET result:", price)
