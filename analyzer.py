import os
import json
from warnings import warn
from googleapiclient import discovery

def get_client():
    return discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=os.environ['PERSPECTIVE_API_KEY'],
        discoveryServiceUrl=os.environ['SERVICE_URL'],
        static_discovery=False,
    )  

def get_attr():
    # Load json
    with open('config.json', mode='r') as f:
        loaded = json.load(f)
    res = loaded.get('Attributes')
    if not res:
        raise ValueError('Attributes not found in config')
    return res


class Analyzer:
    def __init__(self):
        self.client = get_client()
        self.thresholds = get_attr()
        self.attributes = {}
        for attr in self.thresholds:
            self.attributes[attr] = {}

    def __call__(self, text):      
        analyze_request = {
            'comment': { 'text': text },
            'requestedAttributes': self.attributes,
            'languages': ['en']
        }

        # Get response
        res = self.client.comments().analyze(body=analyze_request).execute()

        # Check response valid
        if not res or 'attributeScores' not in res:
            warn(f'Invalid Response: Text of [{text}] returned: [{res}]')
            return None

        # Build map for {Response: Score}
        scores = res['attributeScores']
        map = {}
        exceeded = []
        for attribute in scores:
            try:
                confidence = scores[attribute]['summaryScore']['value']
            except KeyError:
                warn(f'Invalid Key while Parsing: [{text}]. Response: [{res}]')
                return None
            map[attribute] = confidence
            if confidence >= self.thresholds[attribute]:
                exceeded.append(attribute)  # Add if over threshold

        return exceeded, map
        