# tests/unit/test_state.py

import unittest
from datetime import datetime

# Module to be tested
from alma.core.state import ResourceState, diff_states

# The real schemas that our state module is now designed to work with
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint


class TestStateDiffer(unittest.TestCase):
    def setUp(self):
        """Set up common variables for tests."""
        self.now = datetime.now()
        self.db_fields = {"id": 1, "created_at": self.now, "updated_at": self.now}

    def test_no_changes_plan(self):
        """
        Tests that an empty plan is generated when desired and current states match.
        """
        desired_blueprint = SystemBlueprint(
            name="test-bp",
            resources=[
                ResourceDefinition(
                    name="server-1",
                    type="compute",
                    provider="fake",
                    specs={"image": "nginx:latest", "cpu": 1},
                ),
            ],
            **self.db_fields,
        )
        current_states = [
            ResourceState(
                id="server-1",
                type="compute",
                config={"image": "nginx:latest", "cpu": 1},
            )
        ]

        plan = diff_states(desired_blueprint, current_states)

        self.assertTrue(plan.is_empty)
        self.assertEqual(len(plan.to_create), 0)
        self.assertEqual(len(plan.to_update), 0)
        self.assertEqual(len(plan.to_delete), 0)
        self.assertIn("No changes", plan.to_rich_string())

    def test_create_only_plan(self):
        """
        Tests that a plan to create resources is generated correctly.
        """
        desired_blueprint = SystemBlueprint(
            name="test-bp",
            resources=[
                ResourceDefinition(
                    name="new-db",
                    type="compute",
                    provider="fake",
                    specs={"image": "postgres:15"},
                ),
            ],
            **self.db_fields,
        )
        current_states = []

        plan = diff_states(desired_blueprint, current_states)

        self.assertFalse(plan.is_empty)
        self.assertEqual(len(plan.to_create), 1)
        self.assertEqual(len(plan.to_update), 0)
        self.assertEqual(len(plan.to_delete), 0)
        self.assertEqual(plan.to_create[0].name, "new-db")

    def test_delete_only_plan(self):
        """
        Tests that a plan to delete resources is generated correctly.
        """
        desired_blueprint = SystemBlueprint(name="test-bp", resources=[], **self.db_fields)
        current_states = [
            ResourceState(
                id="old-cache",
                type="compute",
                config={"image": "redis:latest"},
            )
        ]

        plan = diff_states(desired_blueprint, current_states)

        self.assertFalse(plan.is_empty)
        self.assertEqual(len(plan.to_create), 0)
        self.assertEqual(len(plan.to_update), 0)
        self.assertEqual(len(plan.to_delete), 1)
        self.assertEqual(plan.to_delete[0].id, "old-cache")

    def test_update_only_plan(self):
        """
        Tests that a plan to update a resource is generated when its config changes.
        """
        desired_blueprint = SystemBlueprint(
            name="test-bp",
            resources=[
                ResourceDefinition(
                    name="web-server",
                    type="compute",
                    provider="fake",
                    specs={"image": "nginx:1.23", "cpu": 2},
                ),
            ],
            **self.db_fields,
        )
        current_states = [
            ResourceState(
                id="web-server",
                type="compute",
                config={"image": "nginx:1.22", "cpu": 1},
            )
        ]

        plan = diff_states(desired_blueprint, current_states)

        self.assertFalse(plan.is_empty)
        self.assertEqual(len(plan.to_create), 0)
        self.assertEqual(len(plan.to_update), 1)
        self.assertEqual(len(plan.to_delete), 0)

        current, desired = plan.to_update[0]
        self.assertEqual(current.id, "web-server")
        self.assertEqual(desired.name, "web-server")
        self.assertNotEqual(current.config, desired.specs)

    def test_mixed_plan(self):
        """
        Tests a complex plan involving create, update, and delete actions.
        """
        desired_blueprint = SystemBlueprint(
            name="test-bp",
            resources=[
                # To create
                ResourceDefinition(
                    name="new-api",
                    type="compute",
                    provider="fake",
                    specs={"image": "fastapi:latest"},
                ),
                # To update
                ResourceDefinition(
                    name="main-db", type="compute", provider="fake", specs={"memory": "8Gi"}
                ),
            ],
            **self.db_fields,
        )
        current_states = [
            # To update
            ResourceState(
                id="main-db",
                type="compute",
                config={"memory": "4Gi"},
            ),
            # To delete
            ResourceState(
                id="old-worker",
                type="compute",
                config={"image": "celery:latest"},
            ),
        ]

        plan = diff_states(desired_blueprint, current_states)

        self.assertFalse(plan.is_empty)
        self.assertEqual(len(plan.to_create), 1)
        self.assertEqual(plan.to_create[0].name, "new-api")

        self.assertEqual(len(plan.to_update), 1)
        self.assertEqual(plan.to_update[0][1].name, "main-db")

        self.assertEqual(len(plan.to_delete), 1)
        self.assertEqual(plan.to_delete[0].id, "old-worker")

        summary = plan.generate_description()
        self.assertIn("1 to create", summary)
        self.assertIn("1 to modify", summary)
        self.assertIn("1 to destroy", summary)


class TestPlanRichString:
    """Test Plan.to_rich_string method for coverage."""

    def test_to_rich_string_empty_plan(self):
        """Test rich string for empty plan."""
        from alma.core.state import Plan

        plan = Plan()
        rich_str = plan.to_rich_string()
        assert "No changes" in rich_str

    def test_to_rich_string_with_create(self):
        """Test rich string with create actions."""
        from alma.core.state import Plan

        resource = ResourceDefinition(
            name="vm1", type="compute", provider="proxmox", specs={"cpu": 2}
        )
        plan = Plan(to_create=[resource])
        rich_str = plan.to_rich_string()
        assert "CREATE" in rich_str
        assert "vm1" in rich_str

    def test_to_rich_string_with_update(self):
        """Test rich string with update actions."""
        from alma.core.state import Plan

        current = ResourceState(id="vm1", type="compute", config={"cpu": 2})
        desired = ResourceDefinition(
            name="vm1", type="compute", provider="proxmox", specs={"cpu": 4}
        )
        plan = Plan(to_update=[(current, desired)])
        rich_str = plan.to_rich_string()
        assert "MODIFY" in rich_str

    def test_to_rich_string_with_delete(self):
        """Test rich string with delete actions."""
        from alma.core.state import Plan

        resource = ResourceState(id="vm1", type="compute", config={})
        plan = Plan(to_delete=[resource])
        rich_str = plan.to_rich_string()
        assert "DESTROY" in rich_str
        assert "permanently deleted" in rich_str

    def test_to_rich_string_all_actions(self):
        """Test rich string with all actions."""
        from alma.core.state import Plan

        plan = Plan(
            to_create=[
                ResourceDefinition(name="vm2", type="compute", provider="proxmox", specs={})
            ],
            to_update=[
                (
                    ResourceState(id="vm1", type="compute", config={}),
                    ResourceDefinition(name="vm1", type="compute", provider="proxmox", specs={}),
                )
            ],
            to_delete=[ResourceState(id="vm0", type="compute", config={})],
        )
        rich_str = plan.to_rich_string()
        assert "Summary" in rich_str


if __name__ == "__main__":
    unittest.main()
