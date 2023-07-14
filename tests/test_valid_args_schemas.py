import json
from pathlib import Path

import fractal_faim_hcs
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

FRACTAL_TASKS_CORE_DIR = Path(fractal_faim_hcs.__file__).parent
with (FRACTAL_TASKS_CORE_DIR / "__FRACTAL_MANIFEST__.json").open("r") as f:
    MANIFEST = json.load(f)
TASK_LIST = MANIFEST["task_list"]
PACKAGE = "fractal_faim_hcs"


def test_manifest_has_args_schemas_is_true():
    debug(MANIFEST)
    assert MANIFEST["has_args_schemas"]


def test_task_functions_have_valid_signatures():
    """
    Test that task functions have valid signatures.
    """
    for _ind_task, task in enumerate(TASK_LIST):
        function_name = Path(task["executable"]).with_suffix("").name
        task_function = _extract_function(
            task["executable"], function_name, package_name=PACKAGE
        )
        _validate_function_signature(task_function)


def test_args_schemas_are_up_to_date():
    """
    Test that args_schema attributes in the manifest are up-to-date
    """
    for ind_task, task in enumerate(TASK_LIST):
        print(f"Now handling {task['executable']}")
        old_schema = TASK_LIST[ind_task]["args_schema"]
        new_schema = create_schema_for_single_task(task["executable"], package=PACKAGE)
        # The following step is required because some arguments may have a
        # default which has a non-JSON type (e.g. a tuple), which we need to
        # convert to JSON type (i.e. an array) before comparison.
        new_schema = json.loads(json.dumps(new_schema))
        assert new_schema == old_schema


@pytest.mark.parametrize(
    "jsonschema_validator",
    [Draft7Validator, Draft201909Validator, Draft202012Validator],
)
def test_args_schema_comply_with_jsonschema_specs(jsonschema_validator):
    """
    FIXME: it is not clear whether this test is actually useful
    """
    for ind_task, task in enumerate(TASK_LIST):
        schema = TASK_LIST[ind_task]["args_schema"]
        my_validator = jsonschema_validator(schema=schema)
        my_validator.check_schema(my_validator.schema)
        print(
            f"Schema for task {task['executable']} is valid for "
            f"{jsonschema_validator}."
        )
