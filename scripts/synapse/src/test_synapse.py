from unittest import TestCase
from src.synapse import SynPipeline, SynManager, SynResource

import json


class SynapseTests(TestCase):

    def test_add_pipeline_success(self):
        data = """
        {
    	    "name": "myname",
	        "properties": {
		        "activities": [{
			        "name": "myactivity",
			        "type": "exampletype",
			        "data": "data"
		        }]
	        }
        }
        """
        pipeline = SynPipeline(json.loads(data))
        manager = SynManager()

        manager.add_pipeline(pipeline)

        assert pipeline == manager.resources[SynPipeline][0]

    def test_pipeline_not_equal(self):
        "tests if pipelines are not equal"

        data1 = """
        {
    	    "name": "myname",
	        "properties": {
		        "activities": [{
			        "name": "myactivity",
			        "type": "exampletype",
			        "data": "data"
		        }]
	        }
        }
        """

        data2 = """
        {
    	    "name": "myname",
	        "properties": {
		        "activities": [{
			        "name": "myactivity2",
			        "type": "exampletype2",
			        "data": "data"
		        }]
	        }
        }
        """

        p1 = SynPipeline(json.loads(data1))
        p2 = SynPipeline(json.loads(data2))

        self.assertNotEqual(p1, p2)

    def test_create_syn_resource(self):
        sample = '{"name": "myname", "properties": {"prop1": 1, "prop2": 2}}'
        got = SynResource(json.loads(sample))

        self.assertEqual(got.name, 'myname')
        self.assertDictEqual(got.properties, {'prop1': 1, 'prop2': 2})
