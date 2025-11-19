"""
Unit tests for the AdvancedCognitiveEngine and its components.
"""
import unittest

from ai_cdn.core.cognitive import (
    AdvancedCognitiveEngine,
    FocusContext,
    RiskProfile,
    CommandRiskLevel,
    UserEmotionalStability,
    detect_context_shift,
    assess_risk,
    select_persona,
    SAFETY_OVERRIDE
)

class TestCognitiveLogic(unittest.TestCase):

    def test_detect_context_shift_no_change(self):
        """Tests that context remains when no new keywords are found."""
        initial_focus = FocusContext(active_resource_id="vm-123", current_topic="compute")
        new_focus = detect_context_shift("what is the status of it?", initial_focus)
        self.assertEqual(new_focus, initial_focus)

    def test_detect_context_shift_with_change(self):
        """Tests that a keyword shifts the context and clears the active resource."""
        initial_focus = FocusContext(active_resource_id="vm-123", current_topic="compute")
        new_focus = detect_context_shift("now let's talk about the database firewall", initial_focus)
        self.assertIsNone(new_focus.active_resource_id)
        self.assertEqual(new_focus.current_topic, "networking")
        self.assertGreater(new_focus.topic_confidence, 0.8)

    def test_assess_risk_low(self):
        """Tests that a benign intent with low frustration is LOW risk."""
        profile = assess_risk("get_vm_status", frustration=0.1)
        self.assertEqual(profile.command_risk_level, CommandRiskLevel.LOW)
        self.assertEqual(profile.user_emotional_stability, UserEmotionalStability.STABLE)
        self.assertFalse(profile.requires_step_up_auth)

    def test_assess_risk_medium(self):
        """Tests that a deploy intent with low frustration is MEDIUM risk."""
        profile = assess_risk("deploy_new_vm", frustration=0.2)
        self.assertEqual(profile.command_risk_level, CommandRiskLevel.MEDIUM)
        self.assertEqual(profile.user_emotional_stability, UserEmotionalStability.STABLE)

    def test_assess_risk_high_volatile(self):
        """Tests that a destructive intent with high frustration is CRITICAL."""
        profile = assess_risk("destroy_database", frustration=0.8)
        self.assertEqual(profile.command_risk_level, CommandRiskLevel.CRITICAL)
        self.assertEqual(profile.user_emotional_stability, UserEmotionalStability.VOLATILE)
        self.assertTrue(profile.requires_step_up_auth)
    
    def test_assess_risk_high_stable(self):
        """Tests that a destructive intent with low frustration is only HIGH risk."""
        profile = assess_risk("delete_vm", frustration=0.1)
        self.assertEqual(profile.command_risk_level, CommandRiskLevel.HIGH)
        self.assertEqual(profile.user_emotional_stability, UserEmotionalStability.STABLE)
        self.assertFalse(profile.requires_step_up_auth)

    def test_select_persona(self):
        """Tests the persona selection logic."""
        self.assertEqual(select_persona("generate_report"), "ARCHITECT")
        self.assertEqual(select_persona("suggest_architecture"), "ARCHITECT")
        self.assertEqual(select_persona("deploy_vm"), "OPERATOR")
        # Typo from prompt fixed in implementation, test reflects implementation
        self.assertEqual(select_persona("rollback_deployment"), "OPERATOR")
        self.assertEqual(select_persona("troubleshoot_network"), "MEDIC")
        self.assertEqual(select_persona("get_status"), "DEFAULT")

class TestAdvancedCognitiveEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = AdvancedCognitiveEngine()

    def test_process_advanced_normal_flow(self):
        """Tests a standard, non-critical processing flow."""
        self.engine.frustration_level = 0.2
        result = self.engine.process_advanced(
            user_input="please deploy a new web server",
            intent="deploy_vm"
        )
        
        self.assertIsNone(result.get("override"))
        self.assertEqual(result["persona"], "OPERATOR")
        self.assertEqual(result["risk_profile"].command_risk_level, CommandRiskLevel.MEDIUM)
        
    def test_process_advanced_safety_override(self):
        """Tests that a critical risk scenario triggers the safety override."""
        self.engine.frustration_level = 0.9 # High frustration
        result = self.engine.process_advanced(
            user_input="I hate this, just destroy the main database now!",
            intent="destroy_database"
        )
        
        self.assertEqual(result.get("override"), SAFETY_OVERRIDE)
        self.assertEqual(result["risk_profile"].command_risk_level, CommandRiskLevel.CRITICAL)

    def test_process_updates_focus_context(self):
        """Tests that the main process loop correctly updates the focus context."""
        self.engine.focus = FocusContext(active_resource_id="vm-101", current_topic="compute")
        
        # This input should trigger a context shift
        self.engine.process_advanced(
            user_input="okay, now about the storage for the new NFS volume",
            intent="create_storage"
        )
        
        # Check that the engine's internal focus has been updated
        self.assertEqual(self.engine.focus.current_topic, "storage")
        self.assertIsNone(self.engine.focus.active_resource_id, "Active resource should be cleared on topic shift")

if __name__ == "__main__":
    unittest.main()
