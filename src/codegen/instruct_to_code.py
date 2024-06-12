import ast

import ollama

import inspect

from src.utils import get_marked_functions_and_docstrings
from src.intent.intent_manager import IntentManagerFactory
from src.web_handler.calendar_api import CalendarAPI


def get_processable_docstrings(modules) -> str:
    docstring_list = []

    for intent_module in modules:
        # Creates docstrings for each function in the module
        functions_info = get_marked_functions_and_docstrings(intent_module)
        module_docstring = docstring_to_code(functions_info, intent_module)
        docstring_list.append(module_docstring)

    docstring_merged = "\n".join([item for sublist in docstring_list for item in sublist])
    return docstring_merged


def docstring_to_code(functions_info, module):
    docstring_list = []
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
        func_string += f'        """\n'
        func_string += f'        {info.docstring}\n'
        func_string += f'        """\n'
        func_string += f'        pass\n'

        docstring_list.append(func_string)
    return docstring_list


def get_default_prompt(prompt: str = None, docstrings: str = None):
    global messages
    messages = []
    messages.append(
        {"role": "system",
         "content": "Your task is to implement the solution to a given task using python functions."
                    "Every task is solvable using one or more of the functions provided in the module."
                    "Only output valid python code. For time and date, use valid datetime strings"
                    "The code you are given will be executed directly and needs to work."
         }
    )
    messages.append({
        "role": "system",
        "content": f"You are given a module with the following functions:\n {docstrings}"
    })
    messages.append(
        {"role": "system",
         "content": "DO NOT DEFINE NEW METHODS OR CLASSES"
         }
    )
    messages.append(
        {"role": "user",
         "content": "delete the next 3 appointments from the calendar"
         }
    )
    messages.append(
        {"role": "assistant",
         "content": "delete_next_appointment()\n"
                    "delete_next_appointment()\n"
                    "delete_next_appointment()\n"
         }
    )
    messages.append(
        {"role": "user",
         "content": f"{prompt}"
         }
    )
    return messages


def one_off(user_input: str):
    docstring = get_processable_docstrings([CalendarAPI])
    chat_messages = get_default_prompt(user_input, docstring)
    ollama_response = ollama.chat(model='llama3', messages=chat_messages)
    generated_code = ollama_response['message']['content']
    print(generated_code)

    # check AST for more than one function call
    tree = ast.parse(generated_code)
    func_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    num_func_calls = sum(isinstance(node, ast.Call) for node in ast.walk(tree))
    if num_func_calls > 1:
        raise Exception("Code generated uses a function other than the one provided")

    valid_function_names = get_marked_functions_and_docstrings(CalendarAPI).keys()
    if 'delete_next_appointment' not in generated_code:
        raise Exception("Code generated uses a function other than the one provided")

    # return the actual function call form the generated code from ast
    return func_calls[0] if func_calls else None


if __name__ == '__main__':
    one_off("delete the next appointment from the calendar")

    '''
    intent_manager = IntentManagerFactory.get_intent_manager_with_unknown_intent()

    intent_modules = [
        CalendarAPI
    ]

    docstrings = get_processable_docstrings(intent_modules)

    #write to file
    with open('./generated_code.py', 'w') as f:
        f.write(docstrings)

    messages = get_default_prompt(prompt="delete the next 5 appointments from the calendar", docstrings=docstrings)

    response = ollama.chat(model='llama3', messages=messages)
    print(response['message']['content'])
    '''
