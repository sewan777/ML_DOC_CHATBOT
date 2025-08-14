#!/usr/bin/env python3
"""
Demo script to test the conversational form and tool-agents system
"""

import os
from dotenv import load_dotenv
from conversational_form import ConversationalForm
from tool_agents import create_tool_agents_manager, parse_natural_date, validate_user_input

# Load environment variables
load_dotenv()

def test_conversational_form():
    """Test the conversational form functionality"""
    print("=== Testing Conversational Form ===")
    
    form = ConversationalForm()
    
    # Test appointment request detection
    test_messages = [
        "I need help with machine learning",
        "Can you call me back?",
        "I'd like to schedule an appointment",
        "John Smith",
        "+1234567890",
        "john@example.com",
        "next Monday at 2 PM",
        "I want to discuss machine learning algorithms"
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        result = form.process_message(message)
        print(f"Bot: {result['response']}")
        print(f"State: {result['state']}")
        
        if result.get('action') == 'reset':
            form.reset()
            print("Form reset!")

def test_date_parsing():
    """Test natural language date parsing"""
    print("\n=== Testing Date Parsing ===")
    
    test_dates = [
        "tomorrow",
        "next Monday",
        "next Friday",
        "December 25th",
        "in 3 days",
        "next week"
    ]
    
    for date_text in test_dates:
        parsed_date = parse_natural_date(date_text)
        print(f"'{date_text}' -> {parsed_date}")

def test_validation():
    """Test input validation"""
    print("\n=== Testing Input Validation ===")
    
    test_cases = [
        ("email", "john@example.com"),
        ("email", "invalid-email"),
        ("phone", "+1234567890"),
        ("phone", "invalid-phone"),
        ("date", "2024-12-25"),
        ("date", "2020-01-01")  # Past date
    ]
    
    for input_type, value in test_cases:
        result = validate_user_input(input_type, value)
        print(f"{input_type}: '{value}' -> {result}")

def test_tool_agents():
    """Test the tool agents system"""
    print("\n=== Testing Tool Agents System ===")
    
    # Check if we have the API key
    if not os.getenv('GOOGLE_API_KEY'):
        print("GOOGLE_API_KEY not found. Skipping tool agents test.")
        return
    
    try:
        manager = create_tool_agents_manager(os.getenv('GOOGLE_API_KEY'))
        
        test_messages = [
            "What's the weather like?",  # General query
            "I need a callback",  # Appointment request
            "My name is John Smith",  # Form input
        ]
        
        for message in test_messages:
            print(f"\nUser: {message}")
            result = manager.process_message(message)
            print(f"Bot: {result['response']}")
            print(f"State: {result['state']}")
            
    except Exception as e:
        print(f"Error testing tool agents: {e}")

def main():
    """Run all tests"""
    print("🤖 Starting Demo Tests for Conversational Form & Tool Agents\n")
    
    test_conversational_form()
    test_date_parsing()
    test_validation()
    test_tool_agents()
    
    print("\n✅ Demo tests completed!")

if __name__ == "__main__":
    main()