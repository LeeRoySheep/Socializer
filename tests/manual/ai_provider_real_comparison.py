#!/usr/bin/env python3
"""
AI Provider Real Comparison Test
================================

PURPOSE:
    Tests ACTUAL LLM providers using Socializer's LLMManager implementation.
    This tests the real system integration, not just raw API calls.

LOCATION: 
    tests/manual/ai_provider_real_comparison.py

DEPENDENCIES:
    - llm_manager.py: LLMManager class for provider switching
    - llm_config.py: LLMSettings with model configurations
    - .env: API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY)

PROVIDERS TESTED:
    - OpenAI: gpt-4o-mini, gpt-4-turbo (Paid, cloud)
    - Anthropic Claude: claude-sonnet-4-0 (Paid, cloud - Latest Claude 4.0)
    - Google Gemini: gemini-2.0-flash-exp (FREE tier experimental, cloud)
    - LM Studio: local-model (FREE, local at http://localhost:1234/v1)

MEASUREMENTS:
    - Response quality (manual evaluation)
    - Response time (seconds)
    - Token usage (estimated)
    - Cost per query (USD)
    - Success rate (%)

TRACEABILITY:
    - Model names sourced from llm_config.py GEMINI_OPTIONS/OPENAI_OPTIONS/CLAUDE_OPTIONS
    - Pricing sourced from provider documentation (December 2024)
    - Results saved to: tests/manual/ai_real_comparison_YYYYMMDD_HHMMSS.json

USAGE:
    python tests/manual/ai_provider_real_comparison.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import YOUR actual LLM manager
from llm_manager import LLMManager, LLMProvider
from llm_config import LLMSettings

# ==============================================================================
# PRICING CONFIGURATION
# ==============================================================================
# Source: Official provider documentation (December 2024)
# Units: USD per 1,000 tokens
# Traceability: OpenAI/Anthropic/Google pricing pages
# Last updated: December 1, 2025
# ==============================================================================

PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-sonnet-4-0": {"input": 0.003, "output": 0.015},
    "claude-opus-4-0": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # FREE
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
}

# ==============================================================================
# TEST PROMPTS
# ==============================================================================
# Purpose: Realistic social skills training scenarios to test AI responses
# Complexity levels: low, medium, high (based on context and analysis depth required)
# Traceability: Aligned with Socializer's core use cases (empathy, communication)
# ==============================================================================

TEST_PROMPTS = [
    {
        "name": "Simple Greeting",
        "prompt": "Hello! How are you today?",
        "complexity": "low",
    },
    {
        "name": "Empathy Scenario",
        "prompt": "I'm feeling really stressed about my job. My boss keeps criticizing my work, and I don't know how to handle it. Can you help me improve my communication skills?",
        "complexity": "medium",
    },
    {
        "name": "Conversation Analysis",
        "prompt": "Analyze this conversation and provide feedback:\n\nUser: 'I don't think you understand what I'm going through.'\nResponse: 'I'm here to listen. Can you tell me more?'\nUser: 'It's just overwhelming.'\n\nWhat communication skills were demonstrated? Provide 2 specific improvements.",
        "complexity": "high",
    },
]


class RealAITester:
    """
    Tests AI providers using Socializer's actual LLMManager.
    
    PURPOSE:
        Compare different AI providers for cost and performance in the context
        of Socializer's social skills training use case.
    
    ARCHITECTURE:
        Uses llm_manager.LLMManager to initialize providers, ensuring tests match
        actual production behavior.
    
    MEASUREMENTS:
        - response_time: Seconds from invoke to response
        - input_tokens: Estimated tokens in prompt (chars / 4)
        - output_tokens: Estimated tokens in response (chars / 4)
        - cost_usd: Calculated from pricing table
        - status: 'success' or 'error'
    
    OUTPUT:
        - Console: Real-time test progress
        - JSON file: Complete results with timestamp
        - Summary table: Aggregated statistics
    
    TRACEABILITY:
        Results saved to: tests/manual/ai_real_comparison_{timestamp}.json
    """
    
    def __init__(self):
        self.results = []
        self.check_api_keys()
    
    def check_api_keys(self):
        """Check available API keys"""
        print("\n🔑 Checking API Keys...")
        
        keys = {
            "OpenAI": os.getenv("OPENAI_API_KEY"),
            "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "Google": os.getenv("GOOGLE_API_KEY"),
        }
        
        self.available_providers = {}
        for provider, key in keys.items():
            has_key = bool(key)
            status = "✅ Available" if has_key else "❌ Missing"
            print(f"  {provider}: {status}")
            self.available_providers[provider] = has_key
    
    def test_provider(self, provider: str, model: str, prompt: str) -> Dict[str, Any]:
        """Test a single provider/model combination"""
        try:
            # Use YOUR LLMManager!
            print(f"    Creating LLM: {provider}/{model}...")
            llm = LLMManager.get_llm(
                provider=provider,
                model=model,
                temperature=0.7
            )
            
            # Time the response
            start_time = time.time()
            response = llm.invoke(prompt)
            end_time = time.time()
            
            # Extract content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            input_tokens = len(prompt) // 4
            output_tokens = len(response_text) // 4
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            pricing = PRICING.get(model, {"input": 0, "output": 0})
            cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
            
            return {
                "provider": provider,
                "model": model,
                "response": response_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
                "response_time": round(end_time - start_time, 2),
                "status": "success",
                "note": "FREE" if cost == 0 else None
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"    ❌ Error: {error_msg[:100]}...")
            return {
                "provider": provider,
                "model": model,
                "status": "error",
                "error": error_msg
            }
    
    def run_tests(self):
        """Run all tests"""
        print("\n" + "=" * 80)
        print("🤖 AI PROVIDER REAL COMPARISON - Using Socializer LLMManager")
        print("=" * 80)
        
        # Test configurations (only available providers)
        test_configs = []
        
        if self.available_providers.get("OpenAI"):
            test_configs.extend([
                (LLMProvider.OPENAI, "gpt-4o-mini"),
                (LLMProvider.OPENAI, "gpt-4-turbo"),
            ])
        
        if self.available_providers.get("Anthropic"):
            test_configs.extend([
                # Claude 4.0 models - Source: llm_config.py CLAUDE_OPTIONS
                (LLMProvider.CLAUDE, "claude-sonnet-4-0"),  # Latest Claude 4.0
            ])
        
        if self.available_providers.get("Google"):
            test_configs.extend([
                # Using gemini-2.0-flash-exp (FREE tier experimental model)
                # Source: llm_config.py GEMINI_OPTIONS
                (LLMProvider.GEMINI, "gemini-2.0-flash-exp"),
            ])
        
        # Local LM Studio - Always try to connect (free, localhost)
        # Default: http://localhost:1234/v1 (standard LM Studio port)
        # Source: llm_config.py LM_STUDIO_OPTIONS
        test_configs.append((LLMProvider.LM_STUDIO, "local-model"))
        
        if not test_configs:
            print("\n❌ No API keys available. Please set at least one:")
            print("   - OPENAI_API_KEY")
            print("   - ANTHROPIC_API_KEY")
            print("   - GOOGLE_API_KEY")
            return
        
        print(f"\n📋 Testing {len(test_configs)} providers with {len(TEST_PROMPTS)} prompts")
        print(f"   Total tests: {len(test_configs) * len(TEST_PROMPTS)}\n")
        
        test_number = 0
        total_tests = len(test_configs) * len(TEST_PROMPTS)
        
        for test_prompt in TEST_PROMPTS:
            print(f"\n\n{'='*80}")
            print(f"📝 TEST: {test_prompt['name']} (Complexity: {test_prompt['complexity'].upper()})")
            print(f"{'='*80}")
            print(f"Prompt: {test_prompt['prompt'][:80]}...")
            print("-" * 80)
            
            for provider, model in test_configs:
                test_number += 1
                print(f"\n[{test_number}/{total_tests}] 🔄 Testing {provider}/{model}...")
                
                result = self.test_provider(provider, model, test_prompt['prompt'])
                result.update({
                    "test_name": test_prompt['name'],
                    "complexity": test_prompt['complexity'],
                    "timestamp": datetime.now().isoformat()
                })
                
                self.results.append(result)
                
                if result['status'] == 'success':
                    print(f"  ✅ Success!")
                    print(f"  ⏱️  Time: {result['response_time']}s")
                    print(f"  🎫 Tokens: {result['total_tokens']} (in: {result['input_tokens']}, out: {result['output_tokens']})")
                    if result['cost_usd'] > 0:
                        print(f"  💰 Cost: ${result['cost_usd']}")
                    else:
                        print(f"  💰 Cost: FREE")
                    print(f"  📄 Response: {result['response'][:150]}...")
                else:
                    print(f"  ❌ Failed: {result.get('error', 'Unknown error')[:100]}")
                
                # Delay between requests to avoid rate limits
                time.sleep(1)
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_real_comparison_{timestamp}.json"
        filepath = Path(project_root) / "tests" / "manual" / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                "metadata": {
                    "test_date": datetime.now().isoformat(),
                    "providers_tested": list(set(r['provider'] for r in self.results if r['status'] == 'success')),
                    "total_tests": len(self.results),
                    "successful_tests": sum(1 for r in self.results if r['status'] == 'success'),
                    "failed_tests": sum(1 for r in self.results if r['status'] == 'error'),
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n\n💾 Full results saved to: {filename}")
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print("📊 SUMMARY - AI PROVIDER COMPARISON")
        print("=" * 80)
        
        # Group by model
        by_model = {}
        for result in self.results:
            if result['status'] != 'success':
                continue
            
            key = f"{result['provider']}/{result['model']}"
            if key not in by_model:
                by_model[key] = {
                    "costs": [],
                    "times": [],
                    "tokens": [],
                    "tests": 0
                }
            
            by_model[key]['costs'].append(result['cost_usd'])
            by_model[key]['times'].append(result['response_time'])
            by_model[key]['tokens'].append(result['total_tokens'])
            by_model[key]['tests'] += 1
        
        print("\n| Provider/Model | Tests | Avg Time | Avg Tokens | Avg Cost | Total Cost |")
        print("|----------------|-------|----------|------------|----------|------------|")
        
        total_cost = 0
        for model, stats in sorted(by_model.items()):
            avg_cost = sum(stats['costs']) / len(stats['costs'])
            avg_time = sum(stats['times']) / len(stats['times'])
            avg_tokens = sum(stats['tokens']) / len(stats['tokens'])
            model_total = sum(stats['costs'])
            total_cost += model_total
            
            cost_str = "FREE" if avg_cost == 0 else f"${avg_cost:.6f}"
            total_str = "FREE" if model_total == 0 else f"${model_total:.6f}"
            
            print(f"| {model:<30} | {stats['tests']:>5} | {avg_time:>7.2f}s | {avg_tokens:>10.0f} | {cost_str:>8} | {total_str:>10} |")
        
        # Overall statistics
        all_success = [r for r in self.results if r['status'] == 'success']
        if all_success:
            print(f"\n📈 OVERALL:")
            print(f"  ✅ Successful tests: {len(all_success)}/{len(self.results)}")
            print(f"  💰 Total cost: ${total_cost:.6f}")
            if len(all_success) > 0:
                print(f"  📊 Average cost per query: ${total_cost/len(all_success):.6f}")
            print(f"  ⏱️  Average response time: {sum(r['response_time'] for r in all_success)/len(all_success):.2f}s")
        
        # Failed tests
        failed = [r for r in self.results if r['status'] == 'error']
        if failed:
            print(f"\n⚠️  FAILED TESTS: {len(failed)}")
            for fail in failed:
                print(f"  - {fail['provider']}/{fail['model']}: {fail.get('error', 'Unknown')[:60]}")


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print(" AI PROVIDER REAL COMPARISON TEST")
    print(" Using Socializer's LLMManager - Testing Real Implementation")
    print("=" * 80)
    
    # Load environment variables
    env_path = Path(project_root) / '.env'
    load_dotenv(env_path)
    
    print(f"\n📂 Project: {project_root}")
    print(f"📋 Current defaults: {LLMSettings.DEFAULT_PROVIDER}/{LLMSettings.DEFAULT_MODEL}")
    
    tester = RealAITester()
    tester.run_tests()
    
    print("\n✅ Testing complete!")
    print("\n📝 Next steps:")
    print("  1. Review detailed results in tests/manual/ai_real_comparison_*.json")
    print("  2. Check cost/performance trade-offs")
    print("  3. Update LLMSettings.DEFAULT_MODEL in llm_config.py if needed")
    print("  4. Run local AI tests for comparison (free but slower)")


if __name__ == "__main__":
    main()
