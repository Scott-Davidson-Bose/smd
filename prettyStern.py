#!/usr/bin/env python
# Usage: `stern -n <namespace> . --tail 10 | python prettyStern.py`
import sys
import json

END_COLOR = "\033[0m"

def ascii_color_string_for(s):
    return "\033[38;5;" + str(hash(s) % 256) + "m"

# use stdin if it's full
if not sys.stdin.isatty():
    input_stream = sys.stdin

# otherwise, read the given filename
else:
    try:
        input_filename = sys.argv[1]
    except IndexError:
        message = 'need filename as first argument if stdin is not full'
        raise IndexError(message)
    else:
        input_stream = open(input_filename, 'rU')

for line in input_stream:
    try:
        pod, container, potential_json = line.split(" ", 2)

        podColor = ascii_color_string_for(pod)
        containerColor = ascii_color_string_for(container)
        sys.stdout.write(podColor + pod + END_COLOR + " ")
        sys.stdout.write(containerColor + container + END_COLOR + " ")
        try:
            jsonObject = json.loads(potential_json)
            sys.stdout.write(json.dumps(jsonObject, sort_keys=False, indent=4))
            sys.stdout.write("\n")
        except ValueError:
            sys.stdout.write(potential_json)
    except:
        sys.stdout.write(line)



