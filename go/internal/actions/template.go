package action

import (
	"encoding/json"
	"fmt"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
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

// deserializes json action template json into object
func (a *ActionTemplate) Decode(data string) {
	var decode map[string]interface{}

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

	//validate required keys exist
	for _, requiredKey := range requiredActionTemplateKeys {
		if !contains(requiredKey) {
			log.Fatalf("Action template does not contain required key: %s", requiredKey)
		}
	}

	// get template type
	tType := templateType(decode["type"].(string))

	// get targetName
	fName := decode["file"]

	// validate template type
	if (tType != TriggerType) && (tType != LinkedServiceType) {
		log.Fatalf("Unknown Template type detected: %v", tType)
	}

	fullPathStr := fmt.Sprintf("%s/%s", string(tType), fName)
	targetPath := pathlib.NewPathAfero(fullPathStr, afero.NewOsFs())

	actions := []JsonAction{}

	// process add actions
	if _, ok := decode["add"]; ok {
		for _, a := range decode["add"].([]interface{}) {
			jStr, _ := json.Marshal(a)
			action, err := NewAddAction(string(jStr[:]))
			if err != nil {
				log.Fatalf("Unable to parse json action: %+v: %+v", string(jStr[:]), err)
			}

			actions = append(actions, action)
		}
	}

	// process remove actions
	if _, ok := decode["remove"]; ok {
		for _, a := range decode["remove"].([]interface{}) {
			jStr, _ := json.Marshal(a)
			action, err := NewRemoveAction(string(jStr[:]))
			if err != nil {
				log.Fatalf("Unable to parse json action: %+v: %+v", string(jStr[:]), err)
			}

			actions = append(actions, action)
		}
	}

	// processs update actions
	if _, ok := decode["update"]; ok {
		for _, a := range decode["update"].([]interface{}) {
			jStr, _ := json.Marshal(a)
			action, err := NewUpdateAction(string(jStr[:]))
			if err != nil {
				log.Fatalf("Unable to parse json action: %+v: %+v", string(jStr[:]), err)
			}

			actions = append(actions, action)
		}
	}
	// set attributes
	a.TargetFile = targetPath
	a.TemplateType = tType
	a.JsonActions = actions
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

		actionTemplate := NewActionTemplate(string(templateStr[:]))
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
