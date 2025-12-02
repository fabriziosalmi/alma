
import asyncio
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(".")

from alma.core.llm_service import initialize_llm, LocalStudioLLM, TinyLLM
from alma.core.config import get_settings

class TestLLMResilience(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Reset the global instance before each test
        import alma.core.llm_service
        alma.core.llm_service._llm_instance = None

    async def test_tier1_cloud_success(self):
        """Test that we use Cloud (Tier 1) when available."""
        print("\n--- Testing Tier 1: Cloud Success ---")
        
        # Create a mock module for alma.core.llm_qwen
        mock_qwen_module = MagicMock()
        mock_qwen_class = MagicMock()
        mock_qwen_instance = MagicMock()
        mock_qwen_instance._initialize = MagicMock(return_value=asyncio.Future())
        mock_qwen_instance._initialize.return_value.set_result(None)
        
        mock_qwen_class.return_value = mock_qwen_instance
        mock_qwen_module.Qwen3LLM = mock_qwen_class
        
        # Patch sys.modules to return our mock module
        with patch.dict(sys.modules, {"alma.core.llm_qwen": mock_qwen_module}):
            # Run
            llm = await initialize_llm()
            
            # Verify
            self.assertEqual(llm, mock_qwen_instance)
            print("✓ Successfully initialized Tier 1 (Cloud)")

    @patch("alma.core.llm_service.httpx.AsyncClient")
    async def test_tier2_local_mesh_success(self, MockClient):
        """Test fallback to Local Mesh (Tier 2) when Cloud fails."""
        print("\n--- Testing Tier 2: Local Mesh Success ---")
        
        # Ensure alma.core.llm_qwen raises ImportError
        with patch.dict(sys.modules):
            if "alma.core.llm_qwen" in sys.modules:
                del sys.modules["alma.core.llm_qwen"]
            
            # Also need to make sure the real import fails if it exists on disk
            # We can force the import to fail by patching builtins.__import__ or just ensuring the mock above is NOT present
            # Actually, if we just don't patch sys.modules with the mock, and the real one fails (due to missing deps), it works.
            # But to be safe, let's mock it to raise ImportError.
            
            # Simpler approach: Patch the local import inside initialize_llm? No, can't easily.
            # We will rely on the fact that we are NOT providing the mock module, 
            # AND we will patch 'builtins.__import__' to fail for this specific module if needed,
            # OR we can just assume it fails or mock the class constructor to raise.
            
            # Let's try a different strategy: Mock the Qwen3LLM class to raise Exception if it IS imported.
            # But if it's not imported, we get ImportError.
            
            # Let's use a mock module that raises an error on init
            mock_qwen_module = MagicMock()
            mock_qwen_module.Qwen3LLM.side_effect = ImportError("Simulated Cloud Failure")
            
            with patch.dict(sys.modules, {"alma.core.llm_qwen": mock_qwen_module}):
                 # Setup Local Mesh to succeed (mocking httpx)
                mock_client_instance = MagicMock()
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                
                # Mock response for _initialize check
                mock_resp = MagicMock()
                mock_resp.raise_for_status.return_value = None
                mock_client_instance.get.return_value = asyncio.Future()
                mock_client_instance.get.return_value.set_result(mock_resp)
                
                MockClient.return_value = mock_client_instance
                
                # Run
                llm = await initialize_llm()
                
                # Verify
                self.assertIsInstance(llm, LocalStudioLLM)
                print("✓ Successfully fell back to Tier 2 (Local Mesh)")

    @patch("alma.core.llm_service.httpx.AsyncClient")
    async def test_tier3_panic_mode(self, MockClient):
        """Test fallback to Panic Mode (Tier 3) when everything fails."""
        print("\n--- Testing Tier 3: Panic Mode ---")
        
        # Mock Cloud Failure
        mock_qwen_module = MagicMock()
        mock_qwen_module.Qwen3LLM.side_effect = Exception("Simulated Cloud Failure")
        
        with patch.dict(sys.modules, {"alma.core.llm_qwen": mock_qwen_module}):
            # Setup Local Mesh to fail
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            
            # Mock exception during _initialize check
            mock_client_instance.get.side_effect = Exception("Connection Refused")
            
            MockClient.return_value = mock_client_instance
            
            # Run
            llm = await initialize_llm()
            
            # Verify
            self.assertIsInstance(llm, TinyLLM)
            print("✓ Successfully fell back to Tier 3 (Panic Mode)")

if __name__ == "__main__":
    unittest.main()
