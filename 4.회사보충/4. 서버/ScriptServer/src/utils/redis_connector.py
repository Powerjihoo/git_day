import redis

# class RedisConnector(metaclass=SingletonInstance):
class RedisConnector():

    def __init__(self, host:str="localhost", port:int=56379, db:int=0):
        self.conn = redis.StrictRedis(host=host, port=port, db=db)
    
    def get_redis_info(self, section:str):
        """
        section list
         - Clients
         - Memory
         - Persistence
         - Stats
         - Replication
         - CPU
         - Cluster
         - Keyspace
        """
        return self.conn.info(section)
        