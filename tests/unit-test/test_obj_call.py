from unittest import mock

from src.utils import TestObjCall


def test_obj_call():
    mock_func_a = mock.Mock()  # Create a mock object
    mock_func_b = mock.Mock()
    mock_func_c = mock.Mock()

    with (
        mock.patch("src.utils.TestObjCall.func_a", side_effect=mock_func_a),  # Use it as a side effect
        mock.patch("src.utils.TestObjCall.func_b", side_effect=mock_func_b),
        mock.patch("src.utils.TestObjCall.func_c", side_effect=mock_func_c),
        mock.patch("src.utils.TestObjCall.func_a", wraps=TestObjCall.func_a) as func_d_wrapper,
    ):
        # The code runs and things happen
        obj = TestObjCall()
        actual_return_a = obj.func_a("I Called a")
        actual_return_b_1 = obj.func_b("I Called b", "once")
        actual_return_b_2 = obj.func_b("I Called b", "twice")
        # I didn't call c
        actual_return_d = obj.func_d("I", "called", "d", "one")

    # Now you can see what happened to some extent

    # func_a
    print("------func_a")
    print(f"{mock_func_a.call_args = }")
    print(f"{mock_func_a.called = }")
    print(f"{mock_func_a.call_count = }")
    print(f"{mock_func_a.call_args_list = }\n")

    # func_b
    print("------func_b")
    print(f"{mock_func_b.call_args = }")
    print(f"{mock_func_b.called = }")
    print(f"{mock_func_b.call_count = }")
    print(f"{mock_func_b.call_args_list = }\n")

    # func_c
    print("------func_c")
    print(f"{mock_func_c.call_args = }")
    print(f"{mock_func_c.called = }")
    print(f"{mock_func_c.call_count = }")
    print(f"{mock_func_c.call_args_list = }")

    # func_d
    print("------func_c")
    print(f"{mock_func_c.call_args = }")
    print(f"{mock_func_c.called = }")
    print(f"{mock_func_c.call_count = }")
    print(f"{mock_func_c.call_args_list = }")

    # Actual returns
    print(f"{actual_return_a = }")  # not the real output
    print(f"{actual_return_b_1 = }")  # not the real output
    print(f"{actual_return_b_2 = }")  # not the real output
    print(f"{actual_return_d = }")  # the REAL output
