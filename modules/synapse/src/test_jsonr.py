from unittest import TestCase

import os
import shutil
import tempfile
import copy
import json
import uuid

from src.jsonr import Action, ActionExecutioner, SynapseActionTemplate, InvalidDotNotation, MissingParameterError


class JsonRTests(TestCase):

    def setUp(self):
        self.maxDiff = None
        self.config = {
            "linkedService": [{
                "name": "MyLinkedService",
                "path": "$.properties.typeProperties.baseUrl",
                "value": "https://__MYTAG__.com",
                "action": "update"
            }],
        }

        self.exampleJson = {
            "properties": {
                "typeProperties": {
                    "baseUrl": "https://dummy.fake"
                },
                "annotations": [{
                    "type": "tag",
                    "name": "MyAnnotation"
                }]
            }
        }

        # make sure to add any file names to this property when actually
        # writing to a file, not including tempfiles or tempdirs
        self._fh_names = []

    def tearDown(self):
        for fh_name in self._fh_names:
            if os.path.exists(os.path.dirname(fh_name)):
                shutil.rmtree(os.path.dirname(fh_name))

    def test_action_template_read_from_memory(self):
        root = f"/tmp/workspace_{uuid.uuid4()}"
        filename = f"{root}/linkedService/MyLinkedService.json"
        self._fh_names.append(filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w+') as f:
            json.dump(self.exampleJson, f)

        sat = SynapseActionTemplate(self.config)  #type: ignore

        got = sat.process_synapse_workspace(root, inplace=False)
        want = {
            "properties": {
                "typeProperties": {
                    "baseUrl": "https://__MYTAG__.com"
                },
                "annotations": [{
                    "type": "tag",
                    "name": "MyAnnotation"
                }]
            }
        }

        self.assertDictEqual(got['linkedService'][0], want)

    def test_action_template_read_from_file(self):
        root = f"/tmp/workspace_{uuid.uuid4()}"
        filename = f"{root}/linkedService/MyLinkedService.json"
        self._fh_names.append(filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w+') as f:
            json.dump(self.exampleJson, f)

        sat = SynapseActionTemplate(self.config)  #type: ignore

        sat.process_synapse_workspace(root, inplace=True)

    def test_execute_update_action(self):

        jdata = copy.deepcopy(self.exampleJson)
        template = SynapseActionTemplate(
            config_data=copy.deepcopy(self.config))
        exc = ActionExecutioner()

        exc.execute(template._map['linkedService'][0], jdata)

        self.assertEqual(exc.target['properties']['typeProperties']['baseUrl'],
                         "https://__MYTAG__.com")

    def test_update_by_dot_notation(self):
        path = "$.properties.typeProperties.baseUrl"
        target = copy.deepcopy(self.exampleJson)

        ae = ActionExecutioner()  #type: ignore

        want = "https://superdummy.fake.com"
        target = ae.update_by_dot_notation(path, want, target)

        self.assertEqual(want,
                         target['properties']['typeProperties']['baseUrl'])

        path = "$.properties.annotations.0.name"
        want = "MyNewAnnotationTag"
        target = ae.update_by_dot_notation(path, want, target)
        self.assertEqual(want, target['properties']['annotations'][0]['name'])

    def test_parse_dot_notation_fail(self):
        path = "$properties.typeProperties.baseUrl"

        ae = ActionExecutioner()  #type: ignore

        with self.assertRaises(InvalidDotNotation):
            _ = ae._parse_dot_notation(path)

    def test_parse_dot_notation_pass(self):
        path = "$.properties.typeProperties.baseUrl"
        path2 = "$.properties.typeProperties.0.annotations.name"

        want1 = ['properties', 'typeProperties', 'baseUrl']
        want2 = ['properties', 'typeProperties', '0', 'annotations', 'name']
        ae = ActionExecutioner()  #type: ignore
        got1 = ae._parse_dot_notation(path)
        got2 = ae._parse_dot_notation(path2)

        self.assertListEqual(got1, want1)
        self.assertListEqual(got2, want2)

    def test_get_by_dot_notation_in_list(self):
        path2 = "$.properties.annotations.0.name"
        exampleJson = copy.deepcopy(self.exampleJson)
        exc = ActionExecutioner()

        self.assertEqual("MyAnnotation",
                         exc.get_by_dot_notation(path2, exampleJson))

    def test_get_by_dot_notation(self):
        path = "$.properties.typeProperties.baseUrl"
        exampleJson = copy.deepcopy(self.exampleJson)
        exc = ActionExecutioner()

        self.assertEqual("https://dummy.fake",
                         exc.get_by_dot_notation(path, exampleJson))

    def test_create_action_template(self):
        config = copy.deepcopy(self.config)

        at = SynapseActionTemplate(config_data=config)

        self.assertEqual(len(at._map['linkedService']), 1)

    def test_action_inequality(self):
        action1 = Action(name='myname',
                         path='mypath',
                         action='myaction',
                         value=None)  # type: ignore

        action2 = Action(name='myname',
                         path='mypath',
                         value='myvalue',
                         action='myaction')

        self.assertNotEqual(action1, action2)

    def test_action_equality(self):
        action1 = Action(name='myname',
                         path='mypath',
                         value='myvalue',
                         action='myaction')

        action2 = Action(name='myname',
                         path='mypath',
                         value='myvalue',
                         action='myaction')

        self.assertEqual(action1, action2)

    def test_create_action_from_dict_fail(self):
        d = {
            "name": "MyResource",
            "path": "$.properties.type",
            "action": "update"
        }

        with self.assertRaises(MissingParameterError):
            _ = Action.from_dict(d)

    def test_create_action_from_dict_success(self):
        d = {
            "name": "MyResource",
            "path": "$.properties.type",
            "value": "MyType",
            "action": "update"
        }

        action = Action.from_dict(d)
        self.assertEqual(action.name, d['name'])
        self.assertEqual(action.path, d['path'])
        self.assertEqual(action.value, d['value'])
        self.assertEqual(action.action, d['action'])
