import pytest

from nexuscli import exception
from nexuscli.api.repository import collection


@pytest.mark.parametrize('class_', [x for x in collection.get_classes_by_type('group')])
def test_configuration(class_, nexus_mock_http, faker):
    """Ensure the property returns the attributes required by Nexus"""
    x_member_names = faker.pylist(10, True, [str])

    if class_.RECIPE_NAME in ['docker', 'maven']:
        with pytest.raises(exception.FeatureNotImplemented):
            class_(name='dummy', member_names=x_member_names)
    else:
        repo = class_(name='dummy', member_names=x_member_names)

        assert repo.configuration['attributes']['group']['memberNames'] == x_member_names
