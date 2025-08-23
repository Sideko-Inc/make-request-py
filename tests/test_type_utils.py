from make_request.type_utils import NOT_GIVEN, NotGiven, NotGivenOr


class TestNotGiven:
    def test_bool_conversion(self):
        not_given = NotGiven()
        assert bool(not_given) is False
        assert not_given is not True

    def test_repr(self):
        not_given = NotGiven()
        assert repr(not_given) == "NOT_GIVEN"
        assert str(not_given) == "NOT_GIVEN"

    def test_singleton_behavior(self):
        # NOT_GIVEN should be the singleton instance
        assert isinstance(NOT_GIVEN, NotGiven)
        assert bool(NOT_GIVEN) is False
        assert repr(NOT_GIVEN) == "NOT_GIVEN"

    def test_equality_with_none(self):
        # NotGiven should not be equal to None
        assert NOT_GIVEN is not None
        assert NOT_GIVEN is not None

    def test_equality_with_false(self):
        # NotGiven should not be equal to False, even though bool() returns False
        assert NOT_GIVEN is not False
        assert NOT_GIVEN is not False

    def test_in_conditional(self):
        # Test using NotGiven in conditional statements
        if NOT_GIVEN:
            raise AssertionError("NOT_GIVEN should be falsy")
        else:
            assert True

        if not NOT_GIVEN:
            assert True
        else:
            raise AssertionError("NOT_GIVEN should be falsy")

    def test_type_annotation(self):
        # Test that NotGivenOr works as expected in type annotations
        # This is mainly a compile-time check, but we can test the types exist
        value: NotGivenOr[str] = "test"
        assert value == "test"

        value2: NotGivenOr[str] = NOT_GIVEN
        assert value2 is NOT_GIVEN

    def test_different_instances(self):
        # Test that different NotGiven instances behave the same
        not_given1 = NotGiven()
        not_given2 = NotGiven()

        assert bool(not_given1) is False
        assert bool(not_given2) is False
        assert repr(not_given1) == repr(not_given2) == "NOT_GIVEN"

        # They are different instances but behave the same
        assert not_given1 is not not_given2
        assert type(not_given1) is type(not_given2)
