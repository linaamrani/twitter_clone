import linked_list

class Node:
    def __init__(self, data=None, next_node=None):
        self.data = data
        self.next_node = next_node

class Data:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class HashTable:
    def __init__(self, size):
        self.size = size
        self.hash_table = [None] * size

    def hashFunction(self, key):
        return (key) % self.size

    def put(self, key, value):
        hashvalue = self.hashFunction(key)
        if self.hash_table[hashvalue] is None:
            self.hash_table[hashvalue] = Node(Data(key, value), None)
        else:
            node = self.hash_table[hashvalue]
            while node.next_node:
                node = node.next_node

            node.next_node = Node(Data(key, value), None)

    def get(self, key):
        hashvalue = self.hashFunction(key)
        values = linked_list.LinkedList()
        if self.hash_table[hashvalue] is not None:
            node = self.hash_table[hashvalue]
            if node.next_node is None:
                return node.data.value
            while node.next_node:

                if key == node.data.key:
                    values.insert_at_end(node.data.value)
                node = node.next_node

            if key == node.data.key:
                values.insert_at_end(node.data.value)
                return values
        return None

    def print_table(self):
        print("{")
        for i, val in enumerate(self.hash_table):
            if val is not None:
                llist_string = ""
                node = val
                if node.next_node:
                    while node.next_node:
                        llist_string += (
                            str(node.data.key) + " : " +
                            str(node.data.value) + " --> "
                        )
                        node = node.next_node
                    llist_string += (
                        str(node.data.key) + " : " +
                        str(node.data.value) + " --> None"
                    )
                    print(f"    [{i}] {llist_string}")
                else:
                    print(f"    [{i}] {val.data.key} : {val.data.value}")
            else:
                print(f"    [{i}] {val}")
        print("}")
        return ''
