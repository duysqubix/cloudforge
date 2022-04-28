package action

import (
	"reflect"
	"testing"
)

func TestJsonActions(t *testing.T) {
	exampleActionJson := `{"path": "$.my.example.path", "value":"myvalue"}`

	t.Run("Decode Json Action", func(t *testing.T) {

		want := []string{"$.my.example.path", "myvalue"}

		for _, actionType := range []jsonActionType{AddActionType, RemoveActionType, UpdateActionType} {

			action, err := New(actionType, exampleActionJson)

			if err != nil {
				t.Errorf("Error occured: %v", err)
			}

			got := []string{string(action.Path()), string(action.Value())}

			if !reflect.DeepEqual(want, got) {
				t.Errorf("wanted %v, got %v for action %v", want, got, actionType)
			}
		}
	})

	t.Run("Decode Json Action -- Raise Error", func(t *testing.T) {

		var NotExistActionType jsonActionType
		got, err := New(NotExistActionType, "{}")

		if err == nil {
			t.Errorf("Should have failed: got %v, want %v", got, nil)
		}
	})
}
