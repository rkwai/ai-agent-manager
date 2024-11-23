import warnings
import pytest

@pytest.fixture(autouse=True)
def ignore_pydantic_warnings():
    warnings.filterwarnings(
        "ignore",
        message=".*'type_params' parameter of 'typing.ForwardRef._evaluate'.*",
        category=DeprecationWarning
    ) 