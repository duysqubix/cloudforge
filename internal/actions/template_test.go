package action

import (
	"reflect"
	"testing"

	"github.com/davecgh/go-spew/spew"
)

func TestDecodeActionTemplate(t *testing.T) {

	template := `[
			{
				"file": "exampleTrigger.json",
				"type": "trigger",
				"add":[
					{"path":"$.add.path", "value": "add1"},
					{"path":"$.add.path2", "value": "add2"}
				],
				"remove": [
					{"path": "$.remove.path", "value":"remove1"},
					{"path": "$.remove.path2","value": "remove2"}
				],
				"update": [
					{"path": "$.update.path", "value":"update1"},
					{"path": "$.update.path2","value": "update2"}
				]
				
			},
			{
				"file": "exampleLinkedService.json",
				"type": "linkedService",
				"add":[
					{"path":"$.add.path","value": "add1"},
					{"path":"$.add.path2","value": "add2"}
				],
				"remove": [
					{"path": "$.remove.path","value": "remove1"},
					{"path": "$.remove.path2","value": "remove2"}
				],
				"update": [
					{"path": "$.update.path","value": "update1"},
					{"path": "$.update.path2","value": "update2"}
				]
			}
		]`

	t.Run("Decode Update Actions", func(t *testing.T) {
		want := []JsonAction{
			UpdateAction{
				jsonAction{
					Path:  "$.update.path",
					Value: "update1",
				},
			},
			UpdateAction{
				jsonAction{
					Path:  "$.update.path2",
					Value: "update2",
				},
			},
		}

		var got []JsonAction
		actions := NewActionFile(template).ActionTemplates[0].JsonActions

		for _, action := range actions {

			switch action.(type) {
			case UpdateAction:
				got = append(got, action)
			default:
				continue
			}
		}

		if !reflect.DeepEqual(want, got) {
			t.Errorf("got %v, want %v", spew.Sdump(got), spew.Sdump(want))
		}
	})

	t.Run("Decode Remove Actions", func(t *testing.T) {
		want := []JsonAction{
			RemoveAction{
				jsonAction{
					Path:  "$.remove.path",
					Value: "remove1",
				},
			},
			RemoveAction{
				jsonAction{
					Path:  "$.remove.path2",
					Value: "remove2",
				},
			},
		}

		var got []JsonAction
		actions := NewActionFile(template).ActionTemplates[0].JsonActions

		for _, action := range actions {

			switch action.(type) {
			case RemoveAction:
				got = append(got, action)
			default:
				continue
			}
		}

		if !reflect.DeepEqual(want, got) {
			t.Errorf("got %v, want %v", spew.Sdump(got), spew.Sdump(want))
		}
	})

	t.Run("Decode Add Actions", func(t *testing.T) {
		want := []JsonAction{
			AddAction{
				jsonAction{
					Path:  "$.add.path",
					Value: "add1",
				},
			},
			AddAction{
				jsonAction{
					Path:  "$.add.path2",
					Value: "add2",
				},
			},
		}

		var addActions []JsonAction
		actions := NewActionFile(template).ActionTemplates[0].JsonActions

		for _, action := range actions {

			switch action.(type) {
			case AddAction:
				addActions = append(addActions, action)
			default:
				continue
			}
		}

		if !reflect.DeepEqual(want, addActions) {
			t.Errorf("got %v, want %v", spew.Sdump(addActions), spew.Sdump(want))
		}
	})

	t.Run("Decode Action File", func(t *testing.T) {

		want := 2
		got := len(NewActionFile(template).ActionTemplates)

		if want != got {
			t.Errorf("want %v, got %v", want, got)
		}
	})

	t.Run("Decode Action Template Trigger FilePath", func(t *testing.T) {
		triggerTemplateIndex := 0

		want := "trigger/exampleTrigger.json"

		got := NewActionFile(template).
			ActionTemplates[triggerTemplateIndex].
			TargetFile.
			String()

		if want != got {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("Decode Action Template Trigger Type", func(t *testing.T) {
		triggerTemplateIndex := 0

		want := TriggerType

		got := NewActionFile(template).
			ActionTemplates[triggerTemplateIndex].
			TemplateType

		if want != got {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("Decode Action Template LinkedService FilePath", func(t *testing.T) {
		triggerTemplateIndex := 1

		want := "linkedService/exampleLinkedService.json"

		got := NewActionFile(template).
			ActionTemplates[triggerTemplateIndex].
			TargetFile.
			String()

		if want != got {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("Decode Action Template LinkedService Type", func(t *testing.T) {
		triggerTemplateIndex := 1

		want := LinkedServiceType

		got := NewActionFile(template).
			ActionTemplates[triggerTemplateIndex].
			TemplateType

		if want != got {
			t.Errorf("got %v, want %v", got, want)
		}
	})
}
