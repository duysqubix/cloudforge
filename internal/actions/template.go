package action

import (
	"encoding/json"

	"github.com/chigopher/pathlib"
)

type templateType string
type JsonDecode interface {
	Decode(data string)
}

const (
	TriggerType       templateType = "trigger"
	LinkedServiceType templateType = "linkedService"
)

var requiredActionTemplateKeys = []string{
	"file", "type",
}
var validActionTemplateKeys = []string{
	"file", "type", "add", "remove", "update",
}

// maps a template type to possible actions
type ActionTemplate struct {
	TargetFile   *pathlib.Path
	TemplateType templateType
	JsonActions  []JsonAction
}

// holds an entire action file that consists of
// action templates
type ActionFile struct {
	ActionTemplates []ActionTemplate
}

// decodes json
func (a *ActionTemplate) Decode(data string) {
	var decode map[string]string
	var actionTemplate ActionTemplate

	if err := json.Unmarshal([]byte(data), &decode); err != nil {
		log.Fatal(err)
	}

	// anonymous function needs to be here in order to
	// calculatre length of `decode` after unmarshalling
	contains := func(item string) bool {
		set := make(map[string]struct{}, len(decode))
		for s := range decode {
			set[s] = struct{}{}
		}
		_, ok := set[item]
		return ok
	}

	for _, requiredKey := range requiredActionTemplateKeys {
		if !contains(requiredKey) {
			log.Fatalf("Action template does not contain required key: %s", requiredKey)
		}
	}
}

// decode json object into action file structure
func (a *ActionFile) Decode(data string) {
	var decoded []map[string]interface{}

	if err := json.Unmarshal([]byte(data), &decoded); err != nil {
		log.Fatalf("Unable to parse file, %v\n", err)
	}

	var actionTemplates = make([]ActionTemplate, 0, len(decoded))

	for _, template := range decoded {
		templateStr, _ := json.Marshal(template)

		actionTemplate := NewActionTemplate(string(templateStr))
		actionTemplates = append(actionTemplates, actionTemplate)
	}

	a.ActionTemplates = actionTemplates
}

func NewActionTemplate(data string) ActionTemplate {
	actionTemplate := ActionTemplate{}
	actionTemplate.Decode(data)
	return actionTemplate
}

func NewActionFile(data string) ActionFile {
	actionFile := ActionFile{}
	actionFile.Decode(data)

	return actionFile
}
