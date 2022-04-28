from unittest import TestCase
from src import RESOURCE_MAP
from src.synapse import *
import random
import json


class SynapseTests(TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_ignore_dependency(self):
        dep1 = AzDependency("MyDep1", "LinkedServiceReference", ignore=False)
        dep2 = AzDependency("MyDep2", "LinkedServiceReference", ignore=True)

    def test_notebook_format_python_code_multiline(self):
        sample = {
            "name": "MyNotebook",
            "properties": {
                "cells": [
                    {
                        "cell_type":
                        "code",
                        "source": [
                            "class bdist_rpm ( Command):\r\n", "\r\n",
                            "    user_options = [    ('bdist-base=', \r\n",
                            "    None,\r\n",
                            "         \"base directory for creating built distributions\"),        ('rpm-base=', None,\r\n",
                            "         \"base directory for creating RPMs (defaults to \\\"rpm\\\" under \"\r\n",
                            "         \"--bdist-base; must be specified for RPM 2)\"),\r\n",
                            "        ( 'dist-dir=',   'd',\r\n",
                            "         \"directory to put final RPM files in \"\r\n",
                            "         \"(and .spec files if --spec-only)\") ,        ('source-only', None,         \"only generate source RPM\"),\r\n",
                            "        ('binary-only', None,\r\n",
                            "         \"only generate binary RPM\") ]\r\n",
                            "         \r\n",
                            "    def _format_changelog(self, changelog):\r\n",
                            "        if not changelog:\r\n",
                            "            return changelog\r\n",
                            "        new_changelog = []\r\n",
                            "        for line in string.split(string.strip(changelog), '\\n'):\r\n",
                            "            line = string.strip(line)\r\n",
                            "            if line[0 ] =='*' :\r\n",
                            "                new_changelog.extend ( [''  ])\r\n",
                            "            elif line[0] == '-':\r\n",
                            "                new_changelog.append(line )\r\n",
                            "            else:\r\n",
                            "                new_changelog.append('  '+ line)"
                        ],
                        "execution_count":
                        1
                    },
                ]
            }
        }

        want = [
            "class bdist_rpm(Command):\r\n", 
            "    user_options = [\r\n", "        ('bdist-base=', None,\r\n",
            "         \"base directory for creating built distributions\"),\r\n",
            "        ('rpm-base=', None,\r\n",
            "         \"base directory for creating RPMs (defaults to \\\"rpm\\\" under \"\r\n",
            "         \"--bdist-base; must be specified for RPM 2)\"),\r\n",
            "        ('dist-dir=', 'd', \"directory to put final RPM files in \"\r\n",
            "         \"(and .spec files if --spec-only)\"),\r\n",
            "        ('source-only', None, \"only generate source RPM\"),\r\n",
            "        ('binary-only', None, \"only generate binary RPM\")\r\n",
            "    ]\r\n", 
            "    def _format_changelog(self, changelog):\r\n",
            "        if not changelog:\r\n",
            "            return changelog\r\n",
            "        new_changelog = []\r\n",
            "        for line in string.split(string.strip(changelog), '\\n'):\r\n",
            "            line = string.strip(line)\r\n",
            "            if line[0] == '*':\r\n",
            "                new_changelog.extend([''])\r\n",
            "            elif line[0] == '-':\r\n",
            "                new_changelog.append(line)\r\n",
            "            else:\r\n",
            "                new_changelog.append('  ' + line)\r\n"
        ]

        notebook = SynNotebook(sample)
        notebook.format_code()
        got = notebook.properties['cells'][0]['source']
        self.assertListEqual(got, want)

    def test_notebook_format_python_line_magic_command_ignore_mult_cells(self):
        """Test should ignore the line that is a magic link command"""
        sample = {
            "name": "MyNotebook",
            "properties": {
                "cells": [{
                    "cell_type":
                    "code",
                    "source": [
                        "%run SuperDuperSpeedyAlgorithims\r\n",
                        "f ( a = 3, b = 4 )\r\n",
                    ],
                    "execution_count":
                    1
                }, {
                    "cell_type": "code",
                    "source": ["%run AnotherNotPythonLine\r\n"],
                    "execution_count": 2
                }]
            }
        }

        notebook = SynNotebook(sample)
        notebook.format_code()
        got = notebook.properties['cells'][0]['source']

        self.assertListEqual(
            got, ["%run SuperDuperSpeedyAlgorithims\r\n", "f(a=3, b=4)\r\n"])

        got = notebook.properties['cells'][1]['source']

        self.assertListEqual(got, ["%run AnotherNotPythonLine\r\n"])

    def test_notebook_format_python_line_magic_command_ignore(self):
        """Test should ignore the line that is a magic link command"""
        sample = {
            "name": "MyNotebook",
            "properties": {
                "cells": [
                    {
                        "cell_type":
                        "code",
                        "source": [
                            "%run MyOtherFileThisIsNotAValidPythonLine\r\n",
                            "f ( a = 1, b = 2 )\r\n",
                        ],
                        "execution_count":
                        1
                    },
                ]
            }
        }

        want = [
            "%run MyOtherFileThisIsNotAValidPythonLine\r\n", "f(a=1, b=2)\r\n"
        ]

        notebook = SynNotebook(sample)
        notebook.format_code()
        got = notebook.properties['cells'][0]['source']
        self.assertListEqual(got, want)

    def test_notebook_format_python_code_block(self):
        sample = {
            "name": "MyNotebook",
            "properties": {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": [
                            "f ( a = 1, b = 2 )\r\n",
                        ],
                        "execution_count": 1
                    },
                ]
            }
        }

        want = ["f(a=1, b=2)\r\n"]

        notebook = SynNotebook(sample)
        notebook.format_code()
        got = notebook.properties['cells'][0]['source']
        self.assertListEqual(got, want)

    def test_null_in_json(self):
        """Test if null parses correctly"""

        sample = {
            "name": "MyResource",
            "properties": {
                "dataset": {
                    "referenceName": "MyDataset",
                    "type": "DatasetReference"
                },
                "other": {
                    "linkedService": {
                        "type": "LinkedServiceReference",
                        "referenceName": "MyLinkedService"
                    }
                },
                "nullField": None
            }
        }

        azr = SynResource(sample)
        azr.populate_dependencies()
        want = [
            AzDependency("MyDataset", "DatasetReference"),
            AzDependency("MyLinkedService", "LinkedServiceReference")
        ]

        got = azr.deptracker

        self.assertListEqual(want, got)

    def test_populate_dependencies_ignored(self):
        "Tests ignored dependencies on a resource"

        sample = {
            "name": "MyResource",
            "properties": {
                "dataset": {
                    "referenceName": "MyDataset",
                    "type": "DatasetReference"
                },
                "other": {
                    "linkedService": {
                        "type": "SqlPoolReference",
                        "referenceName": "MySqlPool"
                    }
                },
                "other2": {
                    "type": "LinkedServiceReference",
                    "referenceName": "MyLinkedService"
                },
                "other3": {
                    "type": "BigDataPoolReference",
                    "referenceName": "MyBigPool"
                }
            }
        }

        azr = SynResource(sample)
        azr.populate_dependencies()
        want = [
            AzDependency("MyDataset", "DatasetReference"),
            AzDependency("MyLinkedService", "LinkedServiceReference")
        ]

        want = 2  # number of ignored depedencies based on type
        got = sum(map(lambda x: 1 if x.ignore is True else 0, azr.deptracker))

        self.assertEqual(want, got)

    def test_populate_dependencies_duplicate(self):
        "Test duplicate dependencies on a resource"

        sample = {
            "name": "MyResource",
            "properties": {
                "dataset": {
                    "referenceName": "MyDataset",
                    "type": "DatasetReference"
                },
                "other": {
                    "linkedService": {
                        "type": "LinkedServiceReference",
                        "referenceName": "MyLinkedService"
                    }
                },
                "other2": {
                    "type": "LinkedServiceReference",
                    "referenceName": "MyLinkedService"
                }
            }
        }

        azr = SynResource(sample)
        azr.populate_dependencies()
        want = [
            AzDependency("MyDataset", "DatasetReference"),
            AzDependency("MyLinkedService", "LinkedServiceReference")
        ]

        got = azr.deptracker

        self.assertListEqual(want, got)

    def test_populate_dependencies_multiple(self):
        "Test multiple dependencies on a resource"

        sample = {
            "name": "MyResource",
            "properties": {
                "dataset": {
                    "referenceName": "MyDataset",
                    "type": "DatasetReference"
                },
                "other": {
                    "linkedService": {
                        "type": "LinkedServiceReference",
                        "referenceName": "MyLinkedService"
                    }
                }
            }
        }

        azr = SynResource(sample)
        azr.populate_dependencies()
        want = [
            AzDependency("MyDataset", "DatasetReference"),
            AzDependency("MyLinkedService", "LinkedServiceReference")
        ]

        got = azr.deptracker

        self.assertListEqual(want, got)

    def test_populate_dependencies_not_pipelines(self):
        "Populate resource dependencies of NOT type pipeline"
        sample = {
            "name": "MyResource",
            "properties": {
                "dataset": {
                    "referenceName": "MyDataset",
                    "type": "DatasetReference"
                }
            }
        }
        azr = SynResource(sample)
        azr.populate_dependencies()

        want = AzDependency("MyDataset", "DatasetReference")
        got = azr.deptracker[0]
        self.assertEqual(got, want)

    def test_populate_dependencies_pipelines(self):
        "Populate resource dependencies of type pipeline"

        sample = {
            "name": "MyResource",
            "properties": {
                "activities": [{
                    "dataset": {
                        "referenceName": "MyDataset",
                        "type": "DatasetReference"
                    }
                }]
            }
        }

        azr = SynResource(sample)
        azr.populate_dependencies()

        want = AzDependency("MyDataset", "DatasetReference")
        self.assertEqual(want, azr.deptracker[0])

    def test_dependency_format_ARM(self):
        "Test proper dependecy ARM format"
        name = "MyDependency"
        type = "MyDependencyReference"

        dep = AzDependency(name, type)
        self.assertEqual(dep.formatARM(), "/myDependencys/MyDependency")

    def test_dependency_format_ARM_Prefix(self):
        "Test formatting of dependency with added suffix"
        name = "MyDep"
        type = "MyDepReference"

        dep = AzDependency(name, type)

        got = dep.formatARM(prefix="/an/example")
        want = "/an/example/myDeps/MyDep"

        self.assertEqual(got, want)

    def test_dependency_format_ARM_Suffix(self):
        "Test formatting of dependency with added suffix"
        name = "MyDep"
        type = "MyDepReference"

        dep = AzDependency(name, type)

        got = dep.formatARM(suffix="/v1")
        want = "/myDeps/MyDep/v1"

        self.assertEqual(got, want)

    def test_add_pipeline_success(self):
        "Test add pipeline resource successfully"

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
        manager = SynManager(workspace_name="myworkspace")

        manager.add_resource('pipeline', json.loads(data))

        assert pipeline == manager.resources["pipeline"][0]

    def test_pipeline_not_equal(self):
        "Test pipeline resource objects are not equal"

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
        "Test creating a synapse resource"
        sample = '{"name": "myname", "properties": {"prop1": 1, "prop2": 2}}'
        got = SynResource(json.loads(sample))

        self.assertEqual(got.name, 'myname')
        self.assertDictEqual(got.properties, {'prop1': 1, 'prop2': 2})

    def test_syntoarm_valid_resource_creations(self):

        # this is dangerous, and i don't really like it
        valid_objs = [eval(x) for x in RESOURCE_MAP.keys()]
        resources = {}

        for idx in range(10):
            cl = random.choice(valid_objs)
            res = cl({
                "name": "MyName_%s" % idx,
                "properties": {
                    "activities": {},
                    "cells": [{
                        "source": ["import sys\r\n"]
                    }]
                },
                "activities": {}
            })

            arm = res.convert_to_arm(res)
            arm_name = arm.__class__.__name__
            resources[arm_name] = res.__class__.__name__

        for objArmClsName, objSynClsName in resources.items():
            want = RESOURCE_MAP[objSynClsName]
            got = objArmClsName
            self.assertEqual(got, want)
