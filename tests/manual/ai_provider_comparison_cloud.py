#!/usr/bin/env python3
"""
AI Provider Comparison Test - Cloud Providers
==============================================

Tests and compares cloud AI providers:
- OpenAI (GPT-4, GPT-3.5-turbo)
- Anthropic Claude (Claude 3.5 Sonnet, Claude 3 Opus)
- Google Gemini (Gemini Pro, Gemini Pro Vision)

Measures:
- Response quality
- Response time
- Token usage
- Cost per query
- Consistency
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Pricing (as of December 2024)
PRICING = {
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    },
    "anthropic": {
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    },
    "google": {
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},  # Per 1K tokens
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},  # Cheaper/faster
        "gemini-pro": {"input": 0.0005, "output": 0.0015},  # Legacy (if available)
    }
}

# Test prompts (varied complexity)
TEST_PROMPTS = [
    {
        "name": "Simple Greeting",
        "prompt": "Hello! How are you today?",
        "complexity": "low",
        "expected_tokens": 50
    },
    {
        "name": "Empathy Training",
        "prompt": "I'm feeling really stressed about my job. My boss keeps criticizing my work, and I don't know how to handle it. Can you help me improve my communication skills?",
        "complexity": "medium",
        "expected_tokens": 200
    },
    {
        "name": "Complex Analysis",
        "prompt": "Analyze the following conversation and provide detailed feedback on communication skills, empathy, active listening, and suggest three specific exercises to improve:\n\nUser: 'I don't think you understand what I'm going through.'\nResponse: 'I'm here to listen. Can you tell me more about what you're experiencing?'\nUser: 'It's just... everything feels overwhelming right now.'\n\nProvide a comprehensive analysis with specific examples and actionable advice.",
        "complexity": "high",
        "expected_tokens": 500
    },
    {
        "name": "Creative Writing",
        "prompt": "Write a short dialogue between two people where one person is practicing active listening skills. Make it realistic and include both verbal and non-verbal cues.",
        "complexity": "medium",
        "expected_tokens": 300
    },
    {
        "name": "Technical Explanation",
        "prompt": "Explain how the Socializer app's memory encryption system works, including the role of Fernet encryption, user-specific keys, and secure storage. Be detailed but clear.",
        "complexity": "high",
        "expected_tokens": 400
    }
]


class AIProviderTester:
    """Tests different AI providers with standardized prompts"""
    
    def __init__(self):
        self.results = []
        self.check_api_keys()
    
    def check_api_keys(self):
        """Check if API keys are available"""
        print("\n🔑 Checking API Keys...")
        
        keys = {
            "OpenAI": os.getenv("OPENAI_API_KEY"),
            "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "Google": os.getenv("GOOGLE_API_KEY")
        }
        
        for provider, key in keys.items():
            status = "✅ Found" if key else "❌ Missing"
            print(f"  {provider}: {status}")
        
        if not all(keys.values()):
            print("\n⚠️  Some API keys are missing. Those providers will be skipped.")
    
    def test_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """Test OpenAI models"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant specializing in social skills training and empathy coaching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            end_time = time.time()
            
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate cost
            pricing = PRICING["openai"].get(model, PRICING["openai"]["gpt-3.5-turbo"])
            cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
            
            return {
                "provider": "OpenAI",
                "model": model,
                "response": response.choices[0].message.content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
                "response_time": round(end_time - start_time, 2),
                "status": "success"
            }
        except Exception as e:
            return {
                "provider": "OpenAI",
                "model": model,
                "status": "error",
                "error": str(e)
            }
    
    def test_anthropic(self, prompt: str, model: str = "claude-3-sonnet-20240229") -> Dict[str, Any]:
        """Test Anthropic Claude models"""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            start_time = time.time()
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                system="You are a helpful AI assistant specializing in social skills training and empathy coaching."
            )
            end_time = time.time()
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            pricing = PRICING["anthropic"].get(model, PRICING["anthropic"]["claude-3-sonnet-20240229"])
            cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
            
            return {
                "provider": "Anthropic",
                "model": model,
                "response": response.content[0].text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
                "response_time": round(end_time - start_time, 2),
                "status": "success"
            }
        except Exception as e:
            return {
                "provider": "Anthropic",
                "model": model,
                "status": "error",
                "error": str(e)
            }
    
    def test_google(self, prompt: str, model: str = "gemini-1.5-flash") -> Dict[str, Any]:
        """Test Google Gemini models"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.7,
                max_tokens=1000
            )
            
            start_time = time.time()
            response = llm.invoke(prompt)
            end_time = time.time()
            
            # Estimate tokens (Google doesn't always provide exact counts)
            # Rough estimate: 1 token ≈ 4 characters
            input_tokens = len(prompt) // 4
            output_tokens = len(response.content) // 4
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            pricing = PRICING["google"].get(model, PRICING["google"]["gemini-1.5-flash"])
            cost = (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])
            
            return {
                "provider": "Google",
                "model": model,
                "response": response.content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
                "response_time": round(end_time - start_time, 2),
                "status": "success",
                "note": "Token counts are estimates"
            }
        except Exception as e:
            return {
                "provider": "Google",
                "model": model,
                "status": "error",
                "error": str(e)
            }
    
    def run_comparison(self):
        """Run comparison across all providers and models"""
        print("\n" + "=" * 80)
        print("🤖 AI PROVIDER COMPARISON TEST - CLOUD PROVIDERS")
        print("=" * 80)
        
        # Test configurations
        test_configs = [
            ("OpenAI", "gpt-3.5-turbo", self.test_openai),
            ("OpenAI", "gpt-4-turbo", self.test_openai),
            ("Anthropic", "claude-3-haiku-20240307", self.test_anthropic),
            ("Anthropic", "claude-3-sonnet-20240229", self.test_anthropic),
            # Gemini temporarily disabled due to LangChain API issues
            # ("Google", "gemini-1.5-flash", self.test_google),
            # ("Google", "gemini-1.5-pro", self.test_google),
        ]
        
        print("\n⚠️  Note: Gemini tests temporarily disabled due to API compatibility issues")
        print("   OpenAI and Anthropic tests will run completely\n")
        
        for test_prompt in TEST_PROMPTS:
            print(f"\n\n📝 TEST: {test_prompt['name']} (Complexity: {test_prompt['complexity'].upper()})")
            print("-" * 80)
            
            for provider, model, test_func in test_configs:
                print(f"\n🔄 Testing {provider} - {model}...")
                
                result = test_func(test_prompt['prompt'], model)
                result.update({
                    "test_name": test_prompt['name'],
                    "complexity": test_prompt['complexity'],
                    "timestamp": datetime.now().isoformat()
                })
                
                self.results.append(result)
                
                if result['status'] == 'success':
                    print(f"  ✅ Success")
                    print(f"  ⏱️  Response Time: {result['response_time']}s")
                    print(f"  🎫 Tokens: {result['total_tokens']} (in: {result['input_tokens']}, out: {result['output_tokens']})")
                    print(f"  💰 Cost: ${result['cost_usd']}")
                    print(f"  📄 Response: {result['response'][:100]}...")
                else:
                    print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
                
                # Small delay between requests
                time.sleep(1)
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_comparison_cloud_{timestamp}.json"
        filepath = Path(project_root) / "tests" / "manual" / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n\n💾 Results saved to: {filename}")
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print("📊 SUMMARY STATISTICS")
        print("=" * 80)
        
        # Group by provider and model
        by_model = {}
        for result in self.results:
            if result['status'] != 'success':
                continue
            
            key = f"{result['provider']} - {result['model']}"
            if key not in by_model:
                by_model[key] = {
                    "costs": [],
                    "times": [],
                    "tokens": []
                }
            
            by_model[key]['costs'].append(result['cost_usd'])
            by_model[key]['times'].append(result['response_time'])
            by_model[key]['tokens'].append(result['total_tokens'])
        
        print("\n| Provider & Model | Avg Cost | Avg Time | Avg Tokens | Total Cost |")
        print("|------------------|----------|----------|------------|------------|")
        
        for model, stats in sorted(by_model.items()):
            avg_cost = sum(stats['costs']) / len(stats['costs'])
            avg_time = sum(stats['times']) / len(stats['times'])
            avg_tokens = sum(stats['tokens']) / len(stats['tokens'])
            total_cost = sum(stats['costs'])
            
            print(f"| {model:<32} | ${avg_cost:.6f} | {avg_time:.2f}s | {avg_tokens:>10.0f} | ${total_cost:.6f} |")
        
        # Overall statistics
        all_success = [r for r in self.results if r['status'] == 'success']
        if all_success:
            total_cost = sum(r['cost_usd'] for r in all_success)
            total_tests = len(all_success)
            
            print(f"\n📈 TOTALS:")
            print(f"  Total Tests Run: {total_tests}")
            print(f"  Total Cost: ${total_cost:.6f}")
            print(f"  Average Cost per Query: ${total_cost/total_tests:.6f}")


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print(" AI PROVIDER COMPARISON - CLOUD PROVIDERS")
    print(" Tests: OpenAI, Anthropic Claude, Google Gemini")
    print("=" * 80)
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path(project_root) / '.env'
    load_dotenv(env_path)
    
    tester = AIProviderTester()
    tester.run_comparison()
    
    print("\n✅ Cloud AI comparison test complete!")
    print("\n📝 Next steps:")
    print("  1. Review results in tests/manual/ai_comparison_cloud_*.json")
    print("  2. Run local AI tests (requires LM Studio/Ollama running)")
    print("  3. Compare cloud vs local results")


if __name__ == "__main__":
    main()
