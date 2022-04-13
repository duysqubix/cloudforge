from unittest import TestCase
from src import ARM_SCHEMA, ARM_VERSION, AzDependency
from src.arm import *


class ArmTests(TestCase):

    def test_base_class_invalid(self):
        with self.assertRaises(NotImplementedError):
            t = ArmTemplate()
            t.workspaceId

    def test_arm_resource_creation(self):

        name = "MyResourceName"
        properties = {"activities": [1, 2], "foo": "bar"}

        dep = AzDependency("MyResourceName", "MyTypeReference")

        armr = ArmResource(name=name, properties=properties)

        armr.add_dep(dep)

        self.assertEqual(armr.name, name)
        self.assertEqual(armr.properties, properties)
        self.assertListEqual(armr.depends_on, [dep])
        self.assertEqual(armr.api_version, "2019-06-01-preview")
        self.assertEqual(armr.type, "")

    def test_arm_resource_equality(self):
        name = "MyResourceName"
        properties = {"activities": [1, 2], "foo": "bar"}

        dep = AzDependency("MyResourceName", "MyTypeReference")
        armr1 = ArmResource(name=name, properties=properties)
        armr1.add_dep(dep)

        armr2 = ArmResource(name=name, properties=properties)
        armr2.add_dep(dep)

        self.assertEqual(armr1, armr2)

    def test_arm_resource_inequality_name(self):
        properties = {"activities": [1, 2], "foo": "bar"}

        dep = AzDependency("MyResourceName", "MyTypeReference")
        armr1 = ArmResource(name="MyResource", properties=properties)
        armr1.add_dep(dep)

        armr2 = ArmResource(name="MyResourceName", properties=properties)
        armr2.add_dep(dep)

        self.assertNotEqual(armr1, armr2)

    def test_arm_resource_inequality_properties(self):
        name = "MyResourceName"
        properties = {"activities": [1, 2, 3], "foo": "bar"}
        properties2 = {"activities": [1], "foo": "bar"}

        dep = AzDependency("MyResourceName", "MyTypeReference")
        armr1 = ArmResource(name=name, properties=properties)
        armr1.add_dep(dep)

        armr2 = ArmResource(name=name, properties=properties2)

        armr2.add_dep(dep)

        self.assertNotEqual(armr1, armr2)

    def test_arm_resource_inequality_dependencies(self):
        name = "MyResourceName"
        properties = {"activities": [1, 2], "foo": "bar"}

        dep = AzDependency("MyResourceName", "MyTypeReference")
        dep2 = AzDependency("MyOtherResourceName", "OtherReference")
        armr1 = ArmResource(name=name, properties=properties)
        armr1.add_dep(dep)

        armr2 = ArmResource(name=name, properties=properties)
        armr2.add_dep(dep2)

        self.assertNotEqual(armr1, armr2)

    def test_arm_resource_pipeline_resource_equality(self):
        self.assertEqual(ArmSynPipeline('myname', {}),
                         ArmSynPipeline('myname', {}))

    def test_arm_get_dependencies_formatted(self):
        dep = AzDependency("MyResourceName", "MyTypeReference")
        dep2 = AzDependency("MyOtherResourceName", "OtherReference")

        armr = ArmResource(name="MyResourceName",
                           properties={
                               "activities": [1, 2],
                               "foo": "bar"
                           },
                           workspace_name="workSpaceName")

        armr.add_dep(dep)
        armr.add_dep(dep2)

        want = [
            "/workSpaceName/myTypes/MyResourceName",
            "/workSpaceName/others/MyOtherResourceName"
        ]

        got = armr.get_dependencies(prefix="/workSpaceName")
        self.assertListEqual(got, want)

    def test_generate_ArmSynPipeline_resource(self):
        self.maxDiff = 5000
        want = {
            "name":
            "myWorkspace/MyResourceName",
            "type":
            "Microsoft.Synapse/workspaces/pipelines",
            "apiVersion":
            ARM_VERSION,
            "properties": {
                "a": 1
            },
            "dependsOn": [
                "Microsoft.Synapse/workspaces/myWorkspace/datasets/MyDataset",
                "Microsoft.Synapse/workspaces/myWorkspace/pipelines/MyPipeline"
            ]
        }

        syn = ArmSynPipeline(name="MyResourceName",
                             properties={"a": 1},
                             workspace_name="myWorkspace")

        syn.add_dep(AzDependency("MyDataset", "DatasetReference"),
                    AzDependency("MyPipeline", "PipelineReference"))

        got = syn.to_arm_json(
            prefix="Microsoft.Synapse/workspaces/myWorkspace")

        for want_k, want_v in want.items():
            if isinstance(want_v, list):
                got_v = got[want_k]
                self.assertListEqual(want_v, got_v)

    def test_generate_arm_template(self):
        want = {
            "$schema":
            ARM_SCHEMA,
            "contentVersion":
            "1.0.0.0",
            "resources": [{
                "name":
                "myWorkspace/MyResourceName",
                "type":
                "Microsoft.Synapse/workspaces/pipelines",
                "apiVersion":
                ARM_VERSION,
                "properties": {
                    "a": 1
                },
                "dependsOn": [
                    "Microsoft.Synapse/workspaces/myWorkspace/datasets/MyDataset",
                    "Microsoft.Synapse/workspaces/myWorkspace/pipelines/MyPipeline"
                ]
            }]
        }

        syn = ArmSynPipeline(name="MyResourceName",
                             properties={"a": 1},
                             workspace_name="")

        syn.add_dep(AzDependency("MyDataset", "DatasetReference"),
                    AzDependency("MyPipeline", "PipelineReference"))

        template = SynArmTemplate(workspace_name="myWorkspace")

        template.add_resource(syn)
        got = template.to_arm_json()
        self.maxDiff = 5000
        self.assertDictEqual(got, want)
