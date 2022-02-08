/*

 Datafactory related logic

*/

package internal

type jsonActionType string

const (
	addActionType    jsonActionType = "add"
	removeActionType jsonActionType = "remove"
	updateActionType jsonActionType = "update"
)

type jsonPath string `json:"path"`
type jsonValue string `json:"value"`

type JsonAction interface {
	Type() jsonActionType
}

// holds add action information
type addAction struct {
	path  jsonPath
	value jsonValue
}

func (a addAction) Type() jsonActionType {
	return addActionType
}

// holds remove action information
type removeAction struct {
	path jsonPath 
	value jsonValue
}

func (a removeAction) Type() jsonActionType{
	return removeActionType
}

// holds update action information
type updateAction struct {
	path jsonPath 
	value jsonValue
}

func (a updateAction) Type() jsonActionType{
	return updateActionType

