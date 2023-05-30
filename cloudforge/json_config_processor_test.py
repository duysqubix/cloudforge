import json

from .json_config_processor import Action, SynapseWorkspaceConfiguration


def test_action_update():
    action_data = {
        "name": "test",
        "path": "$.key1",
        "action": "update",
        "value": "updated_value",
    }
    action = Action(action_data)
    json_data = {"key1": "initial_value", "key2": "other_value"}
    updated_data = action.execute(json_data)
    assert updated_data["key1"] == "updated_value"


def test_synapse_configuration_parsing():
    config_json = '{"linkedService": [{"name": "LKS_AKV_SecretStore", "path": "$.properties.typeProperties.baseUrl", "action": "update", "value": "https://new_url"}]}'
    config = SynapseWorkspaceConfiguration(config_json)
    assert len(config.actions_map["linkedService"]) == 1
    assert isinstance(config.actions_map["linkedService"][0], Action)


def test_synapse_configuration_execute_actions(tmp_path):
    # Create temporary JSON file
    json_file = tmp_path / "LKS_AKV_SecretStore.json"
    json_data = {"properties": {"typeProperties": {"baseUrl": "https://old_url"}}}
    json_file.write_text(json.dumps(json_data))

    # Load configuration
    config_json = '{"linkedService": [{"name": "LKS_AKV_SecretStore", "path": "$.properties.typeProperties.baseUrl", "action": "update", "value": "https://new_url"}]}'
    config = SynapseWorkspaceConfiguration(config_json)

    # Execute actions
    modified_files = config.execute_actions("linkedService", tmp_path)

    # Verify updated data
    assert len(modified_files) == 1
    assert (
        modified_files[str(json_file)]["properties"]["typeProperties"]["baseUrl"]
        == "https://new_url"
    )


def test_action_update_array_element():
    action_data = {
        "name": "UpdateArrayElement",
        "path": "$.example_array[1].name",
        "action": "update",
        "value": "NewName",
    }
    action = Action(action_data)
    json_data = {
        "example_array": [
            {"id": 1, "name": "Item1"},
            {"id": 2, "name": "Item2"},
            {"id": 3, "name": "Item3"},
        ]
    }
    expected_updated_data = {
        "example_array": [
            {"id": 1, "name": "Item1"},
            {"id": 2, "name": "NewName"},
            {"id": 3, "name": "Item3"},
        ]
    }

    updated_json_data = action.update(json_data)
    assert updated_json_data == expected_updated_data


def test_action_update_array_element():
    action_data = {
        "name": "UpdateArrayElement",
        "path": "$.example_array[1].name",
        "action": "update",
        "value": "NewName",
    }
    action = Action(action_data)
    json_data = {
        "example_array": [
            {"id": 1, "name": "Item1"},
            {"id": 2, "name": "Item2"},
            {"id": 3, "name": "Item3"},
        ]
    }
    expected_updated_data = {
        "example_array": [
            {"id": 1, "name": "Item1"},
            {"id": 2, "name": "NewName"},
            {"id": 3, "name": "Item3"},
        ]
    }

    updated_json_data = action.update(json_data)
    assert updated_json_data == expected_updated_data


def test_action_update_nested_array_element_by_index():
    action_data = {
        "name": "UpdateNestedArrayElement",
        "path": "$.example_array[0].nested_array[1].name",
        "action": "update",
        "value": "NewNestedName",
    }
    action = Action(action_data)
    json_data = {
        "example_array": [
            {"id": 1, "nested_array": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]},
            {"id": 2, "nested_array": [{"id": 3, "name": "C"}, {"id": 4, "name": "D"}]},
        ]
    }
    updated_json = action.update(json_data)

    assert (
        updated_json["example_array"][0]["nested_array"][1]["name"] == "NewNestedName"
    )


def test_validate_path():
    action = Action(
        {
            "name": "test_action",
            "path": "$.properties.typeProperties.baseUrl",
            "action": "update",
            "value": "https://new-url.com/",
        }
    )

    json_data = {
        "properties": {
            "typeProperties": {
                "baseUrl": "https://old-url.com/",
            },
        },
    }

    assert action.validate_path(json_data)  # Valid path

    action.path = "$.invalid.path"
    assert not action.validate_path(json_data)  # Invalid path
