from redis import Redis


class MyQueue:
    _instance = None

    def __init__(self, host: str='localhost', port: int=6379, db: int=2):
        self.cache = Redis(host, port, db)

    @classmethod
    def get_instance(cls, host: str='localhost', port: int=6379, db: int=2):
        if cls._instance is None:
            cls._instance = cls(host, port, db)
        return cls._instance
    
    def put(self, data: dict, name: str="queues"):
        self.cache.lpush(name, str(data))

    def get(self, name: str="queues"):
        data = self.cache.lpop(name)
        return eval(data) if data else None

    def empty(self, name: str="queues"):
        data = self.cache.llen(name)
        return data == 0
    
    def check(self, name: str='queues'):
        data: list[dict] = [eval(i.decode('utf-8')) for i in self.cache.lrange(name, 0, -1)]
        d = {}
        for i in data:
            for k, v in i.items():
                d[k] = v
        return d
    

# Create the singleton queue instance

    # print(type(i), i.items())
# queue.put({'dsf': 5})
# queue.put({'ddf': 6})
# queue.put({'dff': 7})
# queue.put({'dgf': 8})
# queue.put({'dhf': 9})

# for i in range(queue.cache.llen('queues')):
#     queue.get()

# print(queue.cache.lrange('queues', 0, -1))



