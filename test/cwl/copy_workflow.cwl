cwlVersion: v1.2
class: Workflow

inputs:
  eo_file: File

outputs:
  copy:
    type: File
    outputSource: copy/copy_output

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
        copy_output:
          type: File
          outputBinding:
            glob: $(inputs.output_filename)
    in:
      infile: eo_file
    out: [copy_output]

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
      infile: copy/copy_output
    out: []