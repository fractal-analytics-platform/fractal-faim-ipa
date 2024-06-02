import json
import sys
import typing
from pathlib import Path
from typing import Optional, Union

import fractal_faim_ipa
import pytest
from devtools import debug
from fractal_tasks_core.dev.lib_args_schemas import (
    create_schema_for_single_task,
)
from fractal_tasks_core.dev.lib_signature_constraints import (
    _extract_function,
    _validate_function_signature,
)
from jsonschema.validators import (
    Draft7Validator,
    Draft201909Validator,
    Draft202012Validator,
)

FRACTAL_TASKS_CORE_DIR = Path(fractal_faim_ipa.__file__).parent
PACKAGE_NAME = "fractal_faim_ipa"
with (FRACTAL_TASKS_CORE_DIR / "__FRACTAL_MANIFEST__.json").open("r") as f:
    MANIFEST = json.load(f)
TASK_LIST = MANIFEST["task_list"]


def test_validate_function_signature():  # noqa C901
    """
    Showcase the expected behavior of _validate_function_signature
    """

    def fun1(x: int):
        pass

    _validate_function_signature(fun1)

    def fun2(x, *args):
        pass

    # Fail because of args
    with pytest.raises(ValueError):
        _validate_function_signature(fun2)

    def fun3(x, **kwargs):
        pass

    # Fail because of kwargs
    with pytest.raises(ValueError):
        _validate_function_signature(fun3)

    def fun4(x: Optional[str] = None):
        pass

    _validate_function_signature(fun4)

    def fun5(x: Optional[str]):
        pass

    _validate_function_signature(fun5)

    def fun6(x: Optional[str] = "asd"):
        pass

    # Fail because of not-None default value for optional parameter
    with pytest.raises(ValueError):
        _validate_function_signature(fun6)

    # NOTE: this test is only valid for python >= 3.10
    if (sys.version_info.major, sys.version_info.minor) >= (3, 10):

        def fun7(x: str | int):
            pass

        # Fail because of "|" not supported
        with pytest.raises(ValueError):
            _validate_function_signature(fun7)

    def fun8(x: Union[str, None] = "asd"):
        pass

    # Fail because Union not supported
    with pytest.raises(ValueError):
        _validate_function_signature(fun8)

    def fun9(x: typing.Union[str, int]):
        pass

    # Fail because Union not supported
    with pytest.raises(ValueError):
        _validate_function_signature(fun9)


def test_manifest_has_args_schemas_is_true():
    debug(MANIFEST)
    assert MANIFEST["has_args_schemas"]


def test_task_functions_have_valid_signatures():
    """
    Test that task functions have valid signatures.
    """
    for task in TASK_LIST:
        for key in ["executable_non_parallel", "executable_parallel"]:
            value = task.get(key, None)
            if value is not None:
                function_name = Path(task[key]).with_suffix("").name
                task_function = _extract_function(
                    task[key], function_name, package_name=PACKAGE_NAME
                )
                _validate_function_signature(task_function)


def test_args_schemas_are_up_to_date():
    """
    Test that args_schema attributes in the manifest are up-to-date
    """
    for ind_task, task in enumerate(TASK_LIST):
        for kind in ["non_parallel", "parallel"]:
            key = f"executable_{kind}"
            value = task.get(key, None)
            if value is not None:
                print(f"Now handling {task[key]}")
                old_schema = TASK_LIST[ind_task].get(f"args_schema_{kind}", None)
                assert old_schema is not None
                new_schema = create_schema_for_single_task(
                    task[key], package=PACKAGE_NAME
                )
                # The following step is required because some arguments may
                # have a default which has a non-JSON type (e.g. a tuple),
                # which we need to convert to JSON type (i.e. an array) before
                # comparison.
                new_schema = json.loads(json.dumps(new_schema))
                assert new_schema == old_schema


@pytest.mark.parametrize(
    "jsonschema_validator",
    [Draft7Validator, Draft201909Validator, Draft202012Validator],
)
def test_args_schema_comply_with_jsonschema_specs(jsonschema_validator):
    """
    This test is actually useful, see
    https://github.com/fractal-analytics-platform/fractal-tasks-core/issues/564.
    """
    for task in TASK_LIST:
        for kind in ["non_parallel", "parallel"]:
            key = f"executable_{kind}"
            value = task.get(key, None)
            if value is not None:
                schema = task[f"args_schema_{kind}"]
                my_validator = jsonschema_validator(schema=schema)
                my_validator.check_schema(my_validator.schema)
                print(
                    f"Schema for task {task[key]} is valid for "
                    f"{jsonschema_validator}."
                )
