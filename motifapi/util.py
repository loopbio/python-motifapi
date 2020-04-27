import os
import json


def get_experiment_metadata():
    try:
        mdf = os.environ['MOTIF_METADATA_JSON_PATH']
        with open(mdf, 'r') as f:
            return json.load(f)
    except KeyError:
        # not defined
        pass
    except Exception as exc:
        print("Error parsing metadata file", exc)

    return {}
