import hashlib


def hashFunction(x):
    h = hashlib.sha256(x)  # we'll use sha256 just for this example
    return int(h.hexdigest(), base=16)


class BloomFilter:
    def __init__(self, m, k, hashFun):
        self.m = m
        self.vector = [0] * m
        self.k = k
        self.data = {}
        self.falsePositive = 0
        self.hashing = hashFun

    # Applying the k hashing functions on the key and getting the corresponding indices
    def get_index_values(self, key):
        hashed_values = []
        for num in range(self.k):
            hashed_values.append(self.hashing((key + str(num)).encode()))
        return [value % self.m for value in hashed_values]

    def insert(self, key, value):
        ix = self.get_index_values(key)
        for elem in ix:
            self.vector[elem] = 1

        self.data[key] = value

    def contains(self, key):
        ix = self.get_index_values(key)
        for elem in ix:
            if self.vector[elem] != 1:
                return False
        return True

    def get(self, key):
        if self.contains(key):
            if key in self.data.keys():
                return self.data[key]
            else:
                raise KeyError("No element with this key")
        else:
            raise KeyError("No element with this key")
