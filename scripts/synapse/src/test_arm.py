from unittest import TestCase
from synapse.src import AzDependency
from src.arm import ArmTemplate


class ArmTests(TestCase):

    def test_base_class_invalid(self):
        with self.assertRaises(NotImplementedError):
            t = ArmTemplate()
            t.workspaceId()

    def test_arm_resource_creation(self):

        name = "MyResourceName"
        properties = {"activities": [1, 2], "foo": "bar"}

        dep = AzDependency("MyResourceName", "MyTypeReference")
