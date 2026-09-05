# Teaching rules

- Keep all project files, comments, docstrings, documentation, test descriptions,
  output labels, and Git commit messages in English.
- Communicate with the user in Chinese, using short connected paragraphs and
  one clear next action. Explain English programming terms as needed.
- This is an educational industrial chiller simulation. Stage 1 has a water
  model and proportional controller. Stage 2 implements a tested OFF, STARTING,
  RUNNING, and FAULT operating sequence in main.py.
- Stage 2 implementation was completed first at the user's request. After the
  user prepares the public learning update, teach the completed state machine
  one concept at a time before adding PI/PID, PLC code, Structured Text, HMI,
  or communications.
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
