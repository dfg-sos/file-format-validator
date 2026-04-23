cwlVersion: v1.2
class: Workflow

inputs:
  tif_test_input: File

outputs: 
  copied_tif:
    type: File
    outputSource: copy/tif_test_output

steps:
  copy:
    run:
      cwlVersion: v1.2
      class: CommandLineTool
      baseCommand: cp
      inputs:
        infile:
          type: File
          format: http://edamontology.org/format_4109
          inputBinding:
            position: 1
        output_filename:
          type: string
          default: copied.tif
          inputBinding:
            position: 2
      outputs:
        tif_test_output:
          type: File
          format: http://edamontology.org/format_4109
          outputBinding:
            glob: $(inputs.output_filename)
    in:
      infile: tif_test_input
    out: [tif_test_output]

  check:
    run:
      cwlVersion: v1.2
      class: CommandLineTool
      baseCommand: "true"
      inputs:
        infile:
          type: File
          format: http://edamontology.org/format_4109
          inputBinding:
            position: 1
      outputs: {}
    in:
      infile: copy/tif_test_output
    out: []