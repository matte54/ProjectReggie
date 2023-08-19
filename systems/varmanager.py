import json
import os

from systems.logger import log, debug_on


class VarManager:
    def __init__(self):
        self.varpath = "./data/etc/vars.json"

    def write(self, varname, varvalue):
        # added this to make sure the vars file exists for adding the first entry
        vardata = {varname: varvalue}
        if not os.path.exists(self.varpath):
            self.write_json(self.varpath, vardata)

        # open var file and add entry
        with open(self.varpath, "r") as f:
            data = json.load(f)
        data[varname] = varvalue
        self.write_json(self.varpath, data)

    def read(self, varname):
        with open(self.varpath, "r") as f:
            data = json.load(f)
        if varname in data:
            return data[varname]
        else:
            log(f'[ERROR] {varname} does not exist in vars.json')
            return None
            # raise ValueError(f'{varname} does not exist in vars.json')

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
