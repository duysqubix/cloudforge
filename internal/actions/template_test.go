package action

import (
	"fmt"
	"reflect"
	"testing"

	"github.com/chigopher/pathlib"
	"github.com/davecgh/go-spew/spew"
	"github.com/spf13/afero"
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

	t.Run("Decode Trigger Template", func(t *testing.T) {

		want := ActionTemplate{
			TargetFile:   pathlib.NewPathAfero("trigger/exampleTrigger.json", afero.NewOsFs()),
			TemplateType: TriggerType,
			JsonActions: []JsonAction{
				AddAction{jsonAction{Path: "$.add.path", Value: "add1"}},
				AddAction{jsonAction{Path: "$.add.path2", Value: "add2"}},
				RemoveAction{jsonAction{Path: "$.remove.path2", Value: "remove1"}},
				RemoveAction{jsonAction{Path: "$.remove.path2", Value: "remove2"}},
				UpdateAction{jsonAction{Path: "$.update.path2", Value: "update2"}},
				UpdateAction{jsonAction{Path: "$.update.path2", Value: "update2"}},
			},
		}

		got := NewActionFile(template)

		if !reflect.DeepEqual(got, want) {
			errMsg := fmt.Sprintf("got %+v\n\nwant%+v", spew.Sdump(got), spew.Sdump(want))
			t.Error(errMsg)
		}
	})
}
