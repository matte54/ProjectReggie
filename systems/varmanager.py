import json
import os
import threading

from systems.logger import log


class VarManager:
    def __init__(self, filepath="./data/etc/vars.json"):
        self.varpath = filepath
        self._lock = threading.Lock()

    def _load_vars(self):
        """Load JSON data from the file with error handling."""
        if not os.path.exists(self.varpath):
            return {}
        try:
            with open(self.varpath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            log(f"[VARMANAGER] Error reading vars.json: {e}")
            return {}

    def write(self, varname, varvalue):
        """Writes a variable to the JSON file."""
        with self._lock:
            data = self._load_vars()
            data[varname] = varvalue
            self._write_json(data)

    def read(self, varname):
        """Reads a variable from the JSON file."""
        data = self._load_vars()
        return data.get(varname, None)

    def _write_json(self, data):
        """Safely writes JSON data to the file."""
        temp_path = self.varpath + ".tmp"
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, self.varpath)  # Atomic write
        except IOError as e:
            log(f"[VARMANAGER] Error writing vars.json: {e}")

    def delete(self, varname):
        """Deletes a variable from the JSON file."""
        with self._lock:
            data = self._load_vars()
            if varname in data:
                del data[varname]
                self._write_json(data)
            else:
                log(f"[VARMANAGER] {varname} does not exist in vars.json")
