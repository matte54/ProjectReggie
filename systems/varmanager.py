import json
import os
import threading

from systems.logger import log, debug_on


class VarManager:
    def __init__(self, filepath="./data/etc/vars.json"):
        self.varpath = filepath
        self._lock = threading.Lock()  # Thread safety
        self._cache = self._load_vars()  # Load into memory

    def _load_vars(self):
        """Load JSON data from the file, handling errors gracefully."""
        if not os.path.exists(self.varpath):
            return {}  # Return an empty dictionary if the file doesn't exist
        try:
            with open(self.varpath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log(f"[VARMANAGER] Error reading vars.json: {e}")
            return {}  # Return an empty dictionary if file is corrupted

    def write(self, varname, varvalue):
        """Writes a variable to the JSON file safely."""
        with self._lock:
            self._cache[varname] = varvalue  # Update cache
            self._write_json(self._cache)

    def read(self, varname):
        """Reads a variable, returning None if it doesn't exist."""
        return self._cache.get(varname, None)

    def _write_json(self, data):
        """Safely writes JSON data to the file using atomic write."""
        temp_path = self.varpath + ".tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, self.varpath)  # Atomic operation
        except IOError as e:
            log(f"[VARMANAGER] Error writing vars.json: {e}")

    def delete(self, varname):
        """Deletes a variable from the JSON file."""
        with self._lock:
            if varname in self._cache:
                del self._cache[varname]
                self._write_json(self._cache)
            else:
                log(f"[VARMANAGER] {varname} does not exist in vars.json")
