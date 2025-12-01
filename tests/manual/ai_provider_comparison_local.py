#!/usr/bin/env python3
"""
AI Provider Comparison Test - Local Providers
=============================================

Tests and compares local AI providers:
- LM Studio (local models via OpenAI-compatible API)
- Ollama (local models)

Measures:
- Response quality
- Response time
- Resource usage
- Model size vs performance
- Cost: $0 (free/local)

⚠️ REQUIREMENTS:
  - LM Studio running on http://localhost:1234
  - OR Ollama running on http://localhost:11434
  - Models downloaded and loaded
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import requests

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Test prompts (same as cloud tests for comparison)
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
]


class LocalAIProviderTester:
    """Tests local AI providers"""
    
    def __init__(self):
        self.results = []
        self.check_local_servers()
    
    def check_local_servers(self):
        """Check if local AI servers are running"""
        print("\n🔍 Checking Local AI Servers...")
        
        servers = {
            "LM Studio": "http://localhost:1234/v1/models",
            "Ollama": "http://localhost:11434/api/tags"
        }
        
        self.available_servers = {}
        
        for name, url in servers.items():
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"  ✅ {name}: Running")
                    self.available_servers[name] = True
                    
                    if name == "Ollama":
                        models = response.json().get('models', [])
                        print(f"     Available models: {', '.join([m['name'] for m in models[:3]])}...")
                else:
                    print(f"  ⚠️  {name}: Server responded with status {response.status_code}")
                    self.available_servers[name] = False
            except requests.exceptions.ConnectionError:
                print(f"  ❌ {name}: Not running")
                self.available_servers[name] = False
            except Exception as e:
                print(f"  ❌ {name}: Error - {str(e)}")
                self.available_servers[name] = False
        
        if not any(self.available_servers.values()):
            print("\n⚠️  WARNING: No local AI servers are running!")
            print("\n📋 To start LM Studio:")
            print("   1. Open LM Studio")
            print("   2. Load a model (e.g., Llama 2, Mistral)")
            print("   3. Start the server (default: http://localhost:1234)")
            print("\n📋 To start Ollama:")
            print("   1. Install Ollama: https://ollama.ai")
            print("   2. Run: ollama run llama2")
            print("   3. Server starts automatically on http://localhost:11434")
    
    def test_lm_studio(self, prompt: str, model: str = "local-model") -> Dict[str, Any]:
        """Test LM Studio models"""
        try:
            from openai import OpenAI
            
            # LM Studio uses OpenAI-compatible API
            client = OpenAI(
                base_url="http://localhost:1234/v1",
                api_key="lm-studio"  # Dummy key for local
            )
            
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
            
            # Try to get model info
            try:
                models_response = requests.get("http://localhost:1234/v1/models")
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    if models_data.get('data'):
                        actual_model = models_data['data'][0]['id']
                    else:
                        actual_model = model
                else:
                    actual_model = model
            except:
                actual_model = model
            
            input_tokens = response.usage.prompt_tokens if response.usage else len(prompt) // 4
            output_tokens = response.usage.completion_tokens if response.usage else len(response.choices[0].message.content) // 4
            total_tokens = input_tokens + output_tokens
            
            return {
                "provider": "LM Studio",
                "model": actual_model,
                "response": response.choices[0].message.content,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": 0.0,  # FREE!
                "response_time": round(end_time - start_time, 2),
                "status": "success",
                "note": "Local model - no API costs"
            }
        except Exception as e:
            return {
                "provider": "LM Studio",
                "model": model,
                "status": "error",
                "error": str(e)
            }
    
    def test_ollama(self, prompt: str, model: str = "llama2") -> Dict[str, Any]:
        """Test Ollama models"""
        try:
            start_time = time.time()
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": f"You are a helpful AI assistant specializing in social skills training and empathy coaching.\n\nUser: {prompt}\n\nAssistant:",
                    "stream": False
                },
                timeout=60
            )
            
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                # Estimate tokens
                input_tokens = len(prompt) // 4
                output_tokens = len(data['response']) // 4
                total_tokens = input_tokens + output_tokens
                
                return {
                    "provider": "Ollama",
                    "model": model,
                    "response": data['response'],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": 0.0,  # FREE!
                    "response_time": round(end_time - start_time, 2),
                    "status": "success",
                    "note": "Local model - no API costs",
                    "eval_count": data.get('eval_count'),
                    "eval_duration": data.get('eval_duration')
                }
            else:
                return {
                    "provider": "Ollama",
                    "model": model,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "provider": "Ollama",
                "model": model,
                "status": "error",
                "error": str(e)
            }
    
    def run_comparison(self):
        """Run comparison across available local providers"""
        print("\n" + "=" * 80)
        print("🏠 AI PROVIDER COMPARISON TEST - LOCAL PROVIDERS")
        print("=" * 80)
        
        if not any(self.available_servers.values()):
            print("\n❌ No local AI servers available. Please start LM Studio or Ollama.")
            return
        
        # Test configurations (only test available servers)
        test_configs = []
        
        if self.available_servers.get("LM Studio"):
            test_configs.append(("LM Studio", "local-model", self.test_lm_studio))
        
        if self.available_servers.get("Ollama"):
            # Test multiple Ollama models if available
            test_configs.extend([
                ("Ollama", "llama2", self.test_ollama),
                ("Ollama", "mistral", self.test_ollama),
            ])
        
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
                    print(f"  💰 Cost: $0.00 (FREE - Local)")
                    print(f"  📄 Response: {result['response'][:100]}...")
                else:
                    print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
                
                # Small delay between requests
                time.sleep(0.5)
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_comparison_local_{timestamp}.json"
        filepath = Path(project_root) / "tests" / "manual" / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n\n💾 Results saved to: {filename}")
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print("📊 SUMMARY STATISTICS - LOCAL AI")
        print("=" * 80)
        
        # Group by provider and model
        by_model = {}
        for result in self.results:
            if result['status'] != 'success':
                continue
            
            key = f"{result['provider']} - {result['model']}"
            if key not in by_model:
                by_model[key] = {
                    "times": [],
                    "tokens": []
                }
            
            by_model[key]['times'].append(result['response_time'])
            by_model[key]['tokens'].append(result['total_tokens'])
        
        print("\n| Provider & Model | Avg Time | Avg Tokens | Cost | Notes |")
        print("|------------------|----------|------------|------|-------|")
        
        for model, stats in sorted(by_model.items()):
            avg_time = sum(stats['times']) / len(stats['times'])
            avg_tokens = sum(stats['tokens']) / len(stats['tokens'])
            
            print(f"| {model:<32} | {avg_time:.2f}s | {avg_tokens:>10.0f} | FREE | Local |")
        
        # Overall statistics
        all_success = [r for r in self.results if r['status'] == 'success']
        if all_success:
            total_tests = len(all_success)
            avg_time = sum(r['response_time'] for r in all_success) / total_tests
            
            print(f"\n📈 TOTALS:")
            print(f"  Total Tests Run: {total_tests}")
            print(f"  Average Response Time: {avg_time:.2f}s")
            print(f"  Total Cost: $0.00 (FREE - All local)")
            print(f"\n💡 Advantages:")
            print(f"  ✅ No API costs")
            print(f"  ✅ Complete data privacy")
            print(f"  ✅ Offline capability")
            print(f"  ✅ No rate limits")


def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print(" AI PROVIDER COMPARISON - LOCAL PROVIDERS")
    print(" Tests: LM Studio, Ollama")
    print("=" * 80)
    
    print("\n⚠️  IMPORTANT: Make sure you have started your local AI server!")
    print("\n📋 Required:")
    print("  - LM Studio: http://localhost:1234 OR")
    print("  - Ollama: http://localhost:11434")
    print("\n")
    
    input("Press ENTER when your local AI server is running...")
    
    tester = LocalAIProviderTester()
    tester.run_comparison()
    
    print("\n✅ Local AI comparison test complete!")
    print("\n📝 Next steps:")
    print("  1. Review results in tests/manual/ai_comparison_local_*.json")
    print("  2. Compare with cloud results")
    print("  3. Decide best provider for your use case")


if __name__ == "__main__":
    main()
