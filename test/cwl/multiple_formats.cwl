cwlVersion: v1.2
class: CommandLineTool
baseCommand: "true"
inputs:
  eo_file:
    type: File
    format: ["edam:format_4107", "edam:format_4119", "edam:format_4106"]
    inputBinding:
      position: 1
outputs: []

$namespaces:
  edam: http://edamontology.org/
$schemas:
  - http://localhost:8000/edamontology_adapted.org.owl