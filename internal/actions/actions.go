/*

 Datafactory related logic

*/

package action

import (
	"encoding/json"
	"errors"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("action")

const (
	AddActionType    jsonActionType = "add"
	RemoveActionType jsonActionType = "remove"
	UpdateActionType jsonActionType = "update"
)

// elements within a json action
type actionElement string

// identifies the type of json action
type jsonActionType string

// Sets action of json object
type JsonAction interface {
	// Absolute path of json
	Path() actionElement

	// Target of action
	Value() actionElement

	// identifies type of json action
	Type() jsonActionType

	// Decodes json string into Json Action
	Decode(data string) (JsonAction, error)
}

func NewAddAction(data string) (JsonAction, error) {
	return New(AddActionType, data)
}

func NewRemoveAction(data string) (JsonAction, error) {
	return New(RemoveActionType, data)
}

func NewUpdateAction(data string) (JsonAction, error) {
	return New(UpdateActionType, data)
}

func New(action jsonActionType, data string) (JsonAction, error) {
	switch action {
	case AddActionType:
		return AddAction{}.Decode(data)
	case RemoveActionType:
		return RemoveAction{}.Decode(data)
	case UpdateActionType:
		return UpdateAction{}.Decode(data)
	default:
		return nil, errors.New("Invalid action type")
	}
}

/******* Add Action ******/
type jsonAction struct {
	Path  actionElement `json:"path"`
	Value actionElement `json:"value"`
}

type AddAction struct {
	jsonAction
}

func (a *AddAction) UnmarshalJSON(b []byte) error {
	return json.Unmarshal(b, &a.jsonAction)
}

func (a AddAction) Type() jsonActionType {
	return AddActionType
}

func (a AddAction) Path() actionElement {
	return a.jsonAction.Path
}

func (a AddAction) Value() actionElement {
	return a.jsonAction.Value
}

func (a AddAction) Decode(data string) (JsonAction, error) {
	var addAction AddAction

	if err := json.Unmarshal([]byte(data), &addAction); err != nil {
		return nil, err
	}

	return addAction, nil
}

/******* Remove Action ******/
type RemoveAction struct {
	jsonAction
}

func (a *RemoveAction) UnmarshalJSON(b []byte) error {
	return json.Unmarshal(b, &a.jsonAction)
}

func (a RemoveAction) Type() jsonActionType {
	return RemoveActionType
}

func (a RemoveAction) Path() actionElement {
	return a.jsonAction.Path
}

func (a RemoveAction) Value() actionElement {
	return a.jsonAction.Value
}

func (a RemoveAction) Decode(data string) (JsonAction, error) {
	var removeAction RemoveAction

	if err := json.Unmarshal([]byte(data), &removeAction); err != nil {
		return nil, err
	}

	return removeAction, nil
}

/*******  Update Action ******/
type UpdateAction struct {
	jsonAction
}

func (a UpdateAction) Type() jsonActionType {
	return UpdateActionType
}

func (a UpdateAction) Path() actionElement {
	return a.jsonAction.Path
}

func (a UpdateAction) Value() actionElement {
	return a.jsonAction.Value
}

func (a UpdateAction) Decode(data string) (JsonAction, error) {
	var updateAction UpdateAction

	if err := json.Unmarshal([]byte(data), &updateAction); err != nil {
		return nil, err
	}

	return updateAction, nil
}
