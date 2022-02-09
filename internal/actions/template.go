package action

import "encoding/json"

type templateType string

const (
	TriggerType       templateType = "trigger"
	LinkedServiceType templateType = "linkedService"
)

type ActionTemplate struct {
	TemplateType templateType
	JsonActions  []JsonAction
}

// decode json object into template object
func (a *ActionTemplate) Decode(data string) {
	var decode map[string]string

	if err := json.Unmarshal([]byte(data), &decode); err != nil {
		log.Fatal(err)
	}

}
