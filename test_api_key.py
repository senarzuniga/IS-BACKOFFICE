"""
Test script to verify OpenAI API key is working
Run with: python test_api_key.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from openai_key_manager import get_openai_api_key
    
    api_key = get_openai_api_key()
    
    if api_key:
        print("✅ API key loaded successfully")
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"   Key: {masked}")
        
        # Optional: Test actual API call
        test_api = input("\nTest actual API call? (y/n): ").lower()
        if test_api == 'y':
            try:
                import openai
                openai.api_key = api_key
                # Simple test call
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say 'API key works!'"}],
                    max_tokens=10
                )
                print(f"✅ API test successful: {response.choices[0].message.content}")
            except ImportError:
                print("⚠️ OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                print(f"❌ API test failed: {e}")
    else:
        print("❌ No API key found")
        
except Exception as e:
    print(f"❌ Error: {e}")
