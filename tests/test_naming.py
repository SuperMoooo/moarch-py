import pytest

from moarch_py.naming import InvalidNameError, ModuleName, ProjectName, singular


@pytest.mark.parametrize("typed", ["shop-api", "shop_api", "Shop Api", "shopApi"])
def test_every_spelling_of_a_project_name_gives_the_same_forms(typed: str) -> None:
    name = ProjectName.parse(typed)

    assert name.distribution == "shop-api"
    assert name.package == "shop_api"
    assert name.title == "Shop API"


@pytest.mark.parametrize(
    ("plural", "expected"),
    [
        ("orders", "order"),
        ("categories", "category"),
        ("addresses", "address"),
        ("boxes", "box"),
        ("status", "statu"),  # documented limit: irregular words need the singular typed
        ("access", "access"),
        ("data", "data"),
    ],
)
def test_singular(plural: str, expected: str) -> None:
    assert singular(plural) == expected


def test_a_multi_word_module_gets_a_name_for_every_place_it_appears() -> None:
    module = ModuleName.parse("order_items")

    assert module.package == "order_items"
    assert module.url_path == "order-items"
    assert module.table == "order_items"
    assert module.model_class == "OrderItem"
    assert module.singular_snake == "order_item"
    assert module.plural_title == "Order Items"


@pytest.mark.parametrize("typed", ["1orders", "orders.v2", "my/api", "", "class"])
def test_names_that_cannot_be_python_packages_are_rejected(typed: str) -> None:
    with pytest.raises(InvalidNameError):
        ProjectName.parse(typed)
