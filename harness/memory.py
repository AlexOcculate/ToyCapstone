# Line 1:  Define the Memory class that provides simple key-value storage for agent context.
class Memory:
    # Line 2:  Initialize with an empty dictionary to hold stored key-value pairs.
    def __init__(self):
        # Line 3:  The underlying storage is a plain dict mapping string keys to string values.
        self._store = {}

    # Line 4:  Store a value under a given key; overwrites if key already exists.
    def store(self, key, value):
        # Line 5:  Convert both key and value to strings for consistent storage format.
        self._store[str(key)] = str(value)

    # Line 6:  Recall a value by key; returns None if the key was never stored.
    def recall(self, key):
        # Line 7:  Use dict.get() to safely retrieve without raising KeyError on missing keys.
        return self._store.get(str(key))

    # Line 8:  List all currently stored keys (useful for debugging and the memory_list tool).
    def list_keys(self):
        # Line 9:  Return a sorted list of all keys for deterministic ordering in output.
        return sorted(self._store.keys())

    # Line 10:  Get a human-readable summary of all stored items (for trace logging).
    def summary(self):
        # Line 11:  If store is empty, return a message indicating no items are stored.
        if not self._store:
            # Line 12:  Return the "empty" indicator string.
            return "(empty)"
        # Line 13:  Build a formatted string showing all key=value pairs separated by semicolons.
        return "; ".join(f"{k}={v}" for k, v in sorted(self._store.items()))
