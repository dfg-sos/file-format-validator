cwlVersion: v1.2
class: CommandLineTool
baseCommand: "true"
inputs:
  eo_file:
    type: File
    format: "edam:format_4110"
    inputBinding:
      position: 1
outputs: []

$namespaces:
  edam: http://edamontology.org/
$schemas:
  - http://localhost:8000/edamontology_adapted.org.owl