# Teaching rules

- Keep all project files, comments, docstrings, documentation, test descriptions,
  output labels, and Git commit messages in English.
- Communicate with the user in Chinese, using short connected paragraphs and
  one clear next action. Explain English programming terms as needed.
- This is an educational industrial chiller simulation. The current scope is
  Stage 1: a water-temperature model and a proportional controller.
- Wait until the user understands the current stage before adding state
  machines, alarms, PI/PID control, PLC code, Structured Text, HMI, or communications.
- Introduce one verifiable concept at a time. Explain each new file and function,
  including its purpose, inputs, outputs, and engineering units.
- Prefer the Python standard library, plain functions, explicit units, and
  minimal changes.
- After changing control logic, run `python -m unittest discover -s tests -v`
  and `python main.py`.
- Input validation is separate from equipment alarm handling and a FAULT state.
- Do not present this model as a specific manufacturer's product implementation.
- Obtain user confirmation before uploading code, changing remote repositories,
  or installing software.
