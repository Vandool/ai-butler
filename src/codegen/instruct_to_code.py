import ollama

import inspect

from src.utils import get_marked_functions_and_docstrings
from src.intent.intent_manager import IntentManagerFactory
from src.web_handler.calendar_api import CalendarAPI


def get_processable_docstrings(modules) -> str:
    string_list = []

    for intent_module in modules:
        functions_info = get_marked_functions_and_docstrings(intent_module)
        # format to actual python code
        docstring_to_code(string_list, functions_info, intent_module)

    string_list = '\n'.join(string_list)
    return string_list


def docstring_to_code(docstrings, functions_info, module):
    for name, info in functions_info.items():
        # add parameters with type
        parameters = ""
        if info.has_slots:
            sig = inspect.signature(getattr(module, name))
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    parameters += f"{param_name}: {param.annotation}, "
                else:
                    parameters += f"{param_name}, "

        if parameters:
            parameters = parameters[:-2]

        func_string = f"def {name}({parameters}):\n"
        func_string += f'    """\n'
        func_string += f'    {info.docstring}\n'
        func_string += f'    """\n'
        func_string += f'    pass\n'

        docstrings.append(func_string)


if __name__ == '__main__':
    intent_manager = IntentManagerFactory.get_intent_manager_with_unknown_intent()

    intent_modules = [
        CalendarAPI
    ]

    docstrings = get_processable_docstrings(intent_modules)

    #write to file
    with open('./generated_code.py', 'w') as f:
        f.write(docstrings)

    messages = []
    messages.append(
        {"role": "system",
         "content": "Your task is to implement the solution to a given task using python functions."
                    "Every task is solvable using one or more of the functions provided in the module."
                    "Only output valid python code. For time and date, use valid datetime strings"
                    "Do not implement new methods or use methods that are not given to you."
         }
    )
    messages.append(
        {"role": "system",
         "content": "Today is the 9th of June 2024\n"
         }
    )
    messages.append(
        {"role": "user",
         "content": "delete the next 3 appointments from the calendar"
         }
    )
    messages.append(
        {"role": "assistant",
         "content": "delete_appointment()\n"
                    "delete_appointment()\n"
                    "delete_appointment()\n"
         }
    )
    messages.append(
        {"role": "user",
         "content": "schedule a new meeting for next 13th of june 2PM with Dr. Doofenschmirz and cancel any other appointments that overlap"
         }
    )

    response = ollama.chat(model='llama3', messages=messages)
    print(response['message']['content'])




