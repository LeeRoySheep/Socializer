"""
Gemini API Diagnostic Tool
===========================

Step-by-step diagnosis of Gemini API configuration to identify issues.

This script will:
1. Check if API key is loaded
2. Verify API key format
3. Test API connectivity
4. Check model availability
5. Test free tier model (gemini-2.0-flash-exp)
6. Provide recommendations

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import os
from dotenv import load_dotenv
from typing import Dict, Any
import traceback


class GeminiDiagnostics:
    """
    Comprehensive diagnostics for Gemini API configuration.
    
    This class provides step-by-step diagnosis to identify and resolve
    issues with Google Gemini API setup and usage.
    """
    
    def __init__(self):
        """Initialize diagnostics by loading environment variables."""
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def step_1_check_env_file(self) -> bool:
        """
        Step 1: Check if .env file exists and is readable.
        
        Returns:
            bool: True if .env file is properly configured
        """
        print("\n" + "="*70)
        print("STEP 1: Check .env File")
        print("="*70)
        
        env_path = Path(".env")
        
        if not env_path.exists():
            print("❌ .env file not found!")
            print("   Create a .env file in the project root with:")
            print("   GOOGLE_API_KEY=your_api_key_here")
            self.results["env_file"] = {"status": "fail", "reason": "File not found"}
            return False
        
        print(f"✅ .env file found at: {env_path.absolute()}")
        
        # Check if it contains GOOGLE_API_KEY
        with open(env_path, 'r') as f:
            content = f.read()
            if "GOOGLE_API_KEY" in content:
                print("✅ GOOGLE_API_KEY entry found in .env")
                self.results["env_file"] = {"status": "pass"}
                return True
            else:
                print("❌ GOOGLE_API_KEY not found in .env file")
                print("   Add this line to your .env:")
                print("   GOOGLE_API_KEY=your_api_key_here")
                self.results["env_file"] = {"status": "fail", "reason": "Key not in file"}
                return False
    
    def step_2_check_api_key_loaded(self) -> bool:
        """
        Step 2: Check if API key is loaded into environment.
        
        Returns:
            bool: True if API key is loaded
        """
        print("\n" + "="*70)
        print("STEP 2: Check API Key Loading")
        print("="*70)
        
        if not self.api_key:
            print("❌ GOOGLE_API_KEY not loaded from environment")
            print("   Possible issues:")
            print("   - .env file not in project root")
            print("   - dotenv not loaded before accessing environment")
            print("   - Key has wrong name in .env")
            self.results["key_loaded"] = {"status": "fail", "reason": "Not loaded"}
            return False
        
        print("✅ API key loaded successfully")
        print(f"   Key preview: {self.api_key[:15]}...{self.api_key[-4:]}")
        self.results["key_loaded"] = {"status": "pass", "key_preview": f"{self.api_key[:15]}...{self.api_key[-4:]}"}
        return True
    
    def step_3_validate_key_format(self) -> bool:
        """
        Step 3: Validate API key format.
        
        Google API keys should start with 'AIza' and be 39 characters long.
        
        Returns:
            bool: True if key format is valid
        """
        print("\n" + "="*70)
        print("STEP 3: Validate API Key Format")
        print("="*70)
        
        if not self.api_key:
            print("❌ No API key to validate")
            self.results["key_format"] = {"status": "fail", "reason": "No key"}
            return False
        
        # Check format
        is_valid = True
        issues = []
        
        # Google API keys typically start with 'AIza'
        if not self.api_key.startswith("AIza"):
            issues.append("Key doesn't start with 'AIza' (unusual for Google API keys)")
            print(f"⚠️  Key starts with: {self.api_key[:4]}")
        else:
            print(f"✅ Key starts with 'AIza'")
        
        # Typical length is 39 characters
        key_length = len(self.api_key)
        if key_length != 39:
            issues.append(f"Key length is {key_length}, expected 39")
            print(f"⚠️  Key length: {key_length} characters (expected 39)")
        else:
            print(f"✅ Key length: {key_length} characters")
        
        # Check for common issues
        if " " in self.api_key:
            issues.append("Key contains spaces")
            print("❌ Key contains spaces!")
            is_valid = False
        
        if "\n" in self.api_key or "\r" in self.api_key:
            issues.append("Key contains newlines")
            print("❌ Key contains newlines!")
            is_valid = False
        
        if issues:
            print("\n⚠️  Format warnings:")
            for issue in issues:
                print(f"   - {issue}")
        
        self.results["key_format"] = {
            "status": "pass" if is_valid else "warning",
            "length": key_length,
            "issues": issues
        }
        
        return True  # Continue even with warnings
    
    def step_4_test_api_connection(self) -> bool:
        """
        Step 4: Test API connectivity with a simple request.
        
        Returns:
            bool: True if API connection successful
        """
        print("\n" + "="*70)
        print("STEP 4: Test API Connection")
        print("="*70)
        
        if not self.api_key:
            print("❌ No API key available for testing")
            self.results["api_connection"] = {"status": "fail", "reason": "No key"}
            return False
        
        try:
            print("📡 Attempting to connect to Gemini API...")
            
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Try to create a client (doesn't make API call yet)
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.api_key,
                temperature=0.3
            )
            
            print("✅ Client created successfully")
            print("📡 Making test API call...")
            
            # Make a simple test call
            response = llm.invoke("Say 'Hello' in one word")
            
            print(f"✅ API connection successful!")
            print(f"   Response: {response.content}")
            
            self.results["api_connection"] = {
                "status": "pass",
                "response": str(response.content)
            }
            
            return True
            
        except ImportError as e:
            print(f"❌ Missing required package: {e}")
            print("   Run: pip install langchain-google-genai")
            self.results["api_connection"] = {"status": "fail", "reason": "Missing package"}
            return False
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ API connection failed: {error_msg}")
            
            # Provide specific guidance based on error
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                print("\n🔍 Diagnosis: Invalid API Key")
                print("   Your API key format may be correct but the key itself is invalid.")
                print("   Please verify your key at: https://makersuite.google.com/app/apikey")
                
            elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
                print("\n🔍 Diagnosis: Quota or Rate Limit Issue")
                print("   You may have exceeded your API quota or rate limit.")
                print("   Check your usage at: https://console.cloud.google.com/")
                
            elif "permission" in error_msg.lower() or "403" in error_msg:
                print("\n🔍 Diagnosis: Permission Denied")
                print("   Your API key may not have permission to use Gemini API.")
                print("   Enable Gemini API at: https://console.cloud.google.com/")
            
            print(f"\n📋 Full error details:")
            print(f"   {error_msg}")
            
            self.results["api_connection"] = {
                "status": "fail",
                "error": error_msg
            }
            
            return False
    
    def step_5_check_free_tier_model(self) -> bool:
        """
        Step 5: Verify free tier model (gemini-2.0-flash-exp) is accessible.
        
        Returns:
            bool: True if free tier model is available
        """
        print("\n" + "="*70)
        print("STEP 5: Check Free Tier Model Access")
        print("="*70)
        
        if not self.api_key:
            print("❌ No API key available")
            self.results["free_tier"] = {"status": "fail", "reason": "No key"}
            return False
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            print("🔍 Testing: gemini-2.0-flash-exp (Free Tier)")
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.api_key,
                temperature=0.3
            )
            
            response = llm.invoke("What is 2+2? Answer with just the number.")
            
            print(f"✅ Free tier model working!")
            print(f"   Model: gemini-2.0-flash-exp")
            print(f"   Response: {response.content}")
            
            self.results["free_tier"] = {
                "status": "pass",
                "model": "gemini-2.0-flash-exp",
                "response": str(response.content)
            }
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Free tier model failed: {error_msg}")
            
            if "not found" in error_msg.lower() or "404" in error_msg:
                print("\n🔍 Diagnosis: Model Not Available")
                print("   The free tier model may have changed or been removed.")
                print("   Try these alternatives:")
                print("   - gemini-1.5-flash (may require payment)")
                print("   - gemini-1.5-pro (requires payment)")
            
            self.results["free_tier"] = {
                "status": "fail",
                "error": error_msg
            }
            
            return False
    
    def step_6_check_current_llm_config(self) -> bool:
        """
        Step 6: Check what LLM is currently configured in the system.
        
        Returns:
            bool: True if configuration check succeeds
        """
        print("\n" + "="*70)
        print("STEP 6: Check Current System Configuration")
        print("="*70)
        
        try:
            from llm_config import LLMSettings
            
            print("📋 Current LLM Settings:")
            print(f"   Provider: {LLMSettings.DEFAULT_PROVIDER}")
            print(f"   Model: {LLMSettings.DEFAULT_MODEL}")
            print(f"   Temperature: {LLMSettings.DEFAULT_TEMPERATURE}")
            print(f"   Max Tokens: {LLMSettings.DEFAULT_MAX_TOKENS}")
            
            print("\n🔑 Provider Status:")
            status = LLMSettings.get_provider_status()
            for provider, available in status.items():
                icon = "✅" if available else "❌"
                print(f"   {icon} {provider.upper()}: {'Available' if available else 'API key missing'}")
            
            # Check if Gemini is enabled
            if LLMSettings.DEFAULT_PROVIDER == "gemini":
                print("\n✅ System is configured to use Gemini")
                if status.get("gemini"):
                    print("✅ Gemini API key is available")
                else:
                    print("❌ Gemini API key is NOT available")
                    print("   But provider is set to 'gemini' - this will cause errors!")
            else:
                print(f"\n⚠️  System is configured to use: {LLMSettings.DEFAULT_PROVIDER}")
                print("   To use Gemini, update llm_config.py:")
                print('   DEFAULT_PROVIDER = "gemini"')
                print('   DEFAULT_MODEL = "gemini-2.0-flash-exp"')
            
            self.results["system_config"] = {
                "status": "pass",
                "provider": LLMSettings.DEFAULT_PROVIDER,
                "model": LLMSettings.DEFAULT_MODEL,
                "gemini_available": status.get("gemini", False)
            }
            
            return True
            
        except ImportError as e:
            print(f"❌ Could not load LLM configuration: {e}")
            self.results["system_config"] = {"status": "fail", "error": str(e)}
            return False
    
    def generate_report(self):
        """
        Generate a comprehensive diagnosis report.
        
        Provides actionable recommendations based on all test results.
        """
        print("\n" + "="*70)
        print("📊 DIAGNOSIS SUMMARY")
        print("="*70)
        
        all_passed = all(
            result.get("status") == "pass" 
            for result in self.results.values()
        )
        
        print("\n📋 Test Results:")
        for step, result in self.results.items():
            status = result.get("status", "unknown")
            icon = "✅" if status == "pass" else ("⚠️ " if status == "warning" else "❌")
            print(f"   {icon} {step.replace('_', ' ').title()}: {status.upper()}")
        
        if all_passed:
            print("\n" + "🎉"*35)
            print("✅ ALL TESTS PASSED! Gemini API is working correctly!")
            print("🎉"*35)
            print("""
Your Gemini configuration is correct and working:
✅ API key is properly configured
✅ API connection is working
✅ Free tier model is accessible
✅ System is ready to use Gemini

To use Gemini in your application:
1. Set DEFAULT_PROVIDER = "gemini" in llm_config.py
2. Set DEFAULT_MODEL = "gemini-2.0-flash-exp" (free tier)
3. Restart your server
""")
        else:
            print("\n" + "❌"*35)
            print("⚠️  ISSUES FOUND - See recommendations below")
            print("❌"*35)
            
            print("\n🔧 RECOMMENDED ACTIONS:\n")
            
            # Provide specific recommendations
            if self.results.get("env_file", {}).get("status") == "fail":
                print("1. Create or fix .env file:")
                print("   - Create .env in project root")
                print("   - Add: GOOGLE_API_KEY=your_key_here")
                print()
            
            if self.results.get("key_loaded", {}).get("status") == "fail":
                print("2. Ensure API key is loaded:")
                print("   - Check .env file location")
                print("   - Verify key name is 'GOOGLE_API_KEY'")
                print("   - Restart your application")
                print()
            
            if self.results.get("api_connection", {}).get("status") == "fail":
                print("3. Fix API connection:")
                error = self.results.get("api_connection", {}).get("error", "")
                if "invalid" in error.lower():
                    print("   - Get a valid API key from: https://makersuite.google.com/app/apikey")
                    print("   - Ensure Gemini API is enabled in Google Cloud Console")
                elif "quota" in error.lower():
                    print("   - Check your API quota/usage")
                    print("   - Wait for quota reset or upgrade plan")
                else:
                    print("   - Verify API key is correct")
                    print("   - Check internet connection")
                    print("   - Review error message above")
                print()
            
            if self.results.get("system_config", {}).get("provider") != "gemini":
                print("4. Update system configuration:")
                print("   - Edit llm_config.py")
                print('   - Set: DEFAULT_PROVIDER = "gemini"')
                print('   - Set: DEFAULT_MODEL = "gemini-2.0-flash-exp"')
                print("   - Restart application")
                print()
        
        print("\n📚 Additional Resources:")
        print("   - Get API key: https://makersuite.google.com/app/apikey")
        print("   - Gemini docs: https://ai.google.dev/")
        print("   - API pricing: https://ai.google.dev/pricing")
        print("   - Google Cloud Console: https://console.cloud.google.com/")
        print()
    
    def run_full_diagnosis(self) -> bool:
        """
        Run complete step-by-step diagnosis.
        
        Returns:
            bool: True if all checks pass
        """
        print("\n" + "🔍"*35)
        print("GEMINI API DIAGNOSTICS")
        print("🔍"*35)
        print("\nThis will check your Gemini API configuration step-by-step.\n")
        
        # Run all steps
        steps = [
            self.step_1_check_env_file,
            self.step_2_check_api_key_loaded,
            self.step_3_validate_key_format,
            self.step_4_test_api_connection,
            self.step_5_check_free_tier_model,
            self.step_6_check_current_llm_config,
        ]
        
        continue_diagnosis = True
        
        for step in steps:
            try:
                result = step()
                # Some steps are warnings, not blockers
                if not result and step != self.step_3_validate_key_format:
                    # Only step 3 can have warnings and continue
                    if step == self.step_1_check_env_file or step == self.step_2_check_api_key_loaded:
                        continue_diagnosis = False
                        break
            except Exception as e:
                print(f"\n❌ Error in {step.__name__}: {e}")
                traceback.print_exc()
                continue_diagnosis = False
                break
        
        # Generate final report
        self.generate_report()
        
        return continue_diagnosis


def main():
    """Main entry point for diagnostics."""
    diagnostics = GeminiDiagnostics()
    success = diagnostics.run_full_diagnosis()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
