import json

class JSON:
    # no difference from json.loads function
    def loads(*args, **kwargs):
        return json.loads(*args, **kwargs)

    # recursively converts input object into dict, allowing for complex json
    def dumps(*args, **kwargs):
        return json.dumps(*args, **kwargs, default=lambda o: o.__dict__)